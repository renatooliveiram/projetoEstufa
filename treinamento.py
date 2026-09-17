"""Etapa 7: python treinamento.py. Usa apenas a biblioteca padrão do Python."""

import argparse
import csv
import json
import platform
import tempfile
from numbers import Integral
from pathlib import Path
from statistics import mean

import config as cfg
from agente import AgenteQLearning
from ambiente import AmbienteEstufa


def treinar(episodios=1000, seed=42, exibir=True):
    """Treina do zero e retorna agente, histórico e resumo; não grava arquivos.

    RNGs separados: ambiente recebe seed e agente recebe seed+1.
    O reset seguinte continua a sequência do ambiente sem repetir a semente.
    """
    if isinstance(episodios, bool) or not isinstance(episodios, Integral) or episodios <= 0:
        raise ValueError('episodios deve ser um inteiro positivo.')
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError('seed deve ser um inteiro.')
    ambiente = AmbienteEstufa()
    agente = AgenteQLearning(seed=seed + 1)
    historico = []
    visitas = [[0] * cfg.NUM_ACOES for _ in range(cfg.NUM_ESTADOS)]

    for episodio in range(1, episodios + 1):
        estado = ambiente.reset(seed=seed if episodio == 1 else None)
        epsilon_usado = agente.epsilon
        recompensa_total = 0.0
        ideais = [0, 0, 0]
        todos_ideais = 0
        acoes = [0] * cfg.NUM_ACOES
        while True:
            acao = agente.escolher_acao(estado, explorar=True)
            novo, recompensa, terminado, truncado, info = ambiente.step(acao)
            visitas[agente.indice_estado(estado)][acao] += 1
            # Usa o estado retornado por step ANTES de qualquer reset.
            agente.atualizar(estado, acao, recompensa, novo, terminado, truncado)
            recompensa_total += recompensa
            acoes[acao] += 1
            for i, adequado in enumerate(info['dentro_faixa']):
                ideais[i] += int(adequado)
            todos_ideais += int(all(info['dentro_faixa']))
            estado = novo
            if terminado or truncado:
                break
        agente.reduzir_epsilon()  # Uma vez por episódio.
        passos = ambiente.passos
        registro = {
            'episodio': episodio, 'passos': passos,
            'recompensa_total': recompensa_total,
            'recompensa_media_passo': recompensa_total / passos,
            'epsilon_usado': epsilon_usado, 'epsilon_apos': agente.epsilon,
            'temperatura_ideal_pct': 100 * ideais[0] / passos,
            'umidade_ideal_pct': 100 * ideais[1] / passos,
            'luz_ideal_pct': 100 * ideais[2] / passos,
            'todas_ideais_pct': 100 * todos_ideais / passos,
        }
        registro.update({f'acao_{i}': n for i, n in enumerate(acoes)})
        historico.append(registro)
        if exibir and (episodio == 1 or episodio % 100 == 0 or episodio == episodios):
            janela = historico[-100:]
            print(f'Episódio {episodio}/{episodios} | '
                  f'média dos últimos {len(janela)}: '
                  f'{mean(x["recompensa_total"] for x in janela):.2f} | '
                  f'epsilon usado: {epsilon_usado:.3f}', flush=True)

    janela = min(100, episodios)
    resumo = {
        'episodios': episodios, 'passos_por_episodio': cfg.MAX_PASSOS,
        'total_decisoes': sum(x['passos'] for x in historico),
        'seed_ambiente': seed, 'seed_agente': seed + 1,
        'python': platform.python_version(),
        'parametros': {nome: getattr(cfg, nome) for nome in dir(cfg) if nome.isupper()},
        'epsilon_final': agente.epsilon,
        'recompensa_primeiro_episodio': historico[0]['recompensa_total'],
        'recompensa_ultimo_episodio': historico[-1]['recompensa_total'],
        'janela_episodios': janela,
        'media_recompensa_inicio': mean(x['recompensa_total'] for x in historico[:janela]),
        'media_recompensa_final': mean(x['recompensa_total'] for x in historico[-janela:]),
        'todas_ideais_pct_inicio': mean(x['todas_ideais_pct'] for x in historico[:janela]),
        'todas_ideais_pct_final': mean(x['todas_ideais_pct'] for x in historico[-janela:]),
        'valores_q_nao_zero': sum(x != 0 for linha in agente.q_table for x in linha),
        'pares_estado_acao_visitados': sum(x > 0 for linha in visitas for x in linha),
        'visitas_estado_acao': visitas,
        'nota': 'Métricas de treinamento com exploração variável. Não substituem avaliação '
                'da política fixa contra uma referência em condições equivalentes. '
                'Janelas se sobrepõem em execuções com menos de 200 episódios.',
    }
    return agente, historico, resumo


def salvar_resultados(agente, historico, resumo, pasta_base):
    """Cada chamada cria uma pasta nova; q_table.json contém a política final."""
    base = Path(pasta_base)
    base.mkdir(parents=True, exist_ok=True)
    pasta = Path(tempfile.mkdtemp(prefix='treino_', dir=base))
    agente.salvar(pasta / 'q_table.json')
    with (pasta / 'historico_treinamento.csv').open('w', encoding='utf-8', newline='') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(historico[0]))
        escritor.writeheader()
        escritor.writerows(historico)
    (pasta / 'resumo_treinamento.json').write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8'
    )
    return pasta


def main():
    parser = argparse.ArgumentParser(description='Treinamento Q-Learning da estufa simulada.')
    parser.add_argument('--episodios', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--saida', type=Path, default=Path(__file__).resolve().parent / 'resultados')
    args = parser.parse_args()
    if args.episodios <= 0:
        parser.error('--episodios deve ser positivo.')
    print('Iniciando treinamento do zero: Q-Learning tabular.', flush=True)
    agente, historico, resumo = treinar(args.episodios, args.seed)
    pasta = salvar_resultados(agente, historico, resumo, args.saida)
    janela = resumo['janela_episodios']
    print('\nTREINAMENTO CONCLUÍDO')
    print(f'Decisões executadas: {resumo["total_decisoes"]}')
    print(f'Média dos primeiros {janela} episódios: {resumo["media_recompensa_inicio"]:.2f}')
    print(f'Média dos últimos {janela} episódios: {resumo["media_recompensa_final"]:.2f}')
    print(f'Tempo com TODAS as variáveis ideais (início/final): '
          f'{resumo["todas_ideais_pct_inicio"]:.2f}% / {resumo["todas_ideais_pct_final"]:.2f}%')
    print(f'Epsilon final: {agente.epsilon:.3f}')
    print(f'Valores Q diferentes de zero: {resumo["valores_q_nao_zero"]}/216')
    print(f'Resultados salvos em: {pasta.resolve()}')
    print('A confirmação do desempenho será feita na etapa de avaliação.')


if __name__ == '__main__':
    main()
