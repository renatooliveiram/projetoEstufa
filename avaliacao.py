"""Etapa 8: comparação pareada da política fixa com ações aleatórias."""
import argparse
import csv
import hashlib
import json
import platform
import random
import tempfile
from numbers import Integral
from pathlib import Path
from statistics import mean, stdev

import config as cfg
from agente import AgenteQLearning
from ambiente import AmbienteEstufa

VARIAVEIS = ('temperatura', 'umidade', 'luminosidade')


def carregar_treino(pasta):
    """Confere parâmetros para não avaliar silenciosamente outro ambiente."""
    pasta = Path(pasta)
    resumo = json.loads((pasta / 'resumo_treinamento.json').read_text(encoding='utf-8'))
    atuais = json.loads(json.dumps({k: getattr(cfg, k) for k in dir(cfg) if k.isupper()}))
    if resumo.get('parametros') != atuais:
        raise ValueError('config.py difere do treinamento. Restaure a configuração usada nele.')
    caminho = pasta / 'q_table.json'
    agente = AgenteQLearning()
    agente.carregar(caminho)
    return agente, hashlib.sha256(caminho.read_bytes()).hexdigest()


def avaliar(agente, episodios=100, seed=2026):
    """Não chama atualizar ou reduzir_epsilon; usa cópia da tabela recebida.

    A referência sorteia uniformemente entre as oito ações. As duas políticas
    recebem os mesmos valores iniciais por episódio. Transições não têm ruído.
    """
    if isinstance(episodios, bool) or not isinstance(episodios, Integral) or episodios < 1:
        raise ValueError('episodios deve ser um inteiro positivo.')
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError('seed deve ser um inteiro.')
    politica = AgenteQLearning(seed=seed + 2)
    politica.q_table = [linha[:] for linha in agente.q_table]
    original = [linha[:] for linha in politica.q_table]
    rng_inicial, rng_aleatorio = random.Random(seed), random.Random(seed + 1)
    linhas, trajetorias = [], []
    for episodio in range(1, episodios + 1):
        inicial = tuple(rng_inicial.uniform(a, b) for a, b in cfg.FAIXAS_INICIAIS)
        for nome in ('aleatorio', 'treinado'):
            ambiente = AmbienteEstufa()
            estado = ambiente.reset(valores_iniciais=inicial)
            total, todos = 0.0, 0
            adequados, desvios, somas = [0] * 3, [0.0] * 3, [0.0] * 3
            equipamentos, acoes = [0] * 3, [0] * cfg.NUM_ACOES
            while True:
                acao = (rng_aleatorio.randrange(cfg.NUM_ACOES) if nome == 'aleatorio'
                        else politica.escolher_acao(estado, explorar=False))
                estado, recompensa, fim, corte, info = ambiente.step(acao)
                total += recompensa
                todos += int(all(info['dentro_faixa']))
                acoes[acao] += 1
                registro = {'estrategia': nome, 'episodio': episodio,
                            'passo': ambiente.passos, 'acao': acao, 'recompensa': recompensa}
                for i, (variavel, (minimo, maximo)) in enumerate(zip(VARIAVEIS, cfg.FAIXAS_IDEAIS)):
                    x = info[variavel]
                    somas[i] += x
                    adequados[i] += int(info['dentro_faixa'][i])
                    desvios[i] += max(minimo - x, 0, x - maximo)
                    equipamentos[i] += info['equipamentos'][i]
                    registro[variavel] = x
                trajetorias.append(registro)
                if fim or corte:
                    break
            n = ambiente.passos
            linha = {'estrategia': nome, 'episodio': episodio, 'passos': n,
                     'recompensa_total': total, 'todas_ideais_pct': 100 * todos / n}
            for i, variavel in enumerate(VARIAVEIS):
                linha[f'{variavel}_inicial'] = inicial[i]
                linha[f'{variavel}_media'] = somas[i] / n
                linha[f'{variavel}_ideal_pct'] = 100 * adequados[i] / n
                linha[f'{variavel}_desvio_medio'] = desvios[i] / n
            for i, equipamento in enumerate(('irrigacao', 'ventilacao', 'iluminacao')):
                linha[f'{equipamento}_ligada_pct'] = 100 * equipamentos[i] / n
            linha.update({f'acao_{i}': valor for i, valor in enumerate(acoes)})
            linhas.append(linha)
    if politica.q_table != original:
        raise RuntimeError('A política foi alterada durante a avaliação.')

    resumo = {'episodios_por_estrategia': episodios, 'passos_por_episodio': cfg.MAX_PASSOS,
              'seed_iniciais': seed, 'seed_aleatorio': seed + 1, 'seed_desempates': seed + 2,
              'python': platform.python_version(), 'q_table_preservada': True,
              'exploracao_treinado': False, 'estrategias': {}}
    chaves = [k for k in linhas[0] if k not in ('estrategia', 'episodio', 'passos')
              and not k.endswith('_inicial')]
    por_nome = {}
    for nome in ('aleatorio', 'treinado'):
        conjunto = [x for x in linhas if x['estrategia'] == nome]
        por_nome[nome] = conjunto
        medias = {chave: mean(x[chave] for x in conjunto) for chave in chaves}
        medias['recompensa_desvio_padrao_episodios'] = (
            stdev(x['recompensa_total'] for x in conjunto) if episodios > 1 else 0.0)
        resumo['estrategias'][nome] = medias
    diferencas = [b['recompensa_total'] - a['recompensa_total']
                 for a, b in zip(por_nome['aleatorio'], por_nome['treinado'])]
    resumo['diferenca_media_recompensa_pareada'] = mean(diferencas)
    resumo['episodios_treinado_com_maior_recompensa'] = sum(d > 0 for d in diferencas)
    resumo['nota'] = ('Uma política treinada, um conjunto de condições iniciais e uma realização '
                      'aleatória por condição. Não comprova convergência, robustez a outros '
                      'treinamentos nem desempenho em estufas reais. Percentuais incluem '
                      'recuperação inicial e são calculados após cada ação.')
    return linhas, trajetorias, resumo


def salvar_avaliacao(linhas, trajetorias, resumo, pasta_base):
    base = Path(pasta_base)
    base.mkdir(parents=True, exist_ok=True)
    pasta = Path(tempfile.mkdtemp(prefix='avaliacao_', dir=base))
    for nome, dados in (('episodios_avaliacao.csv', linhas), ('trajetorias_avaliacao.csv', trajetorias)):
        with (pasta / nome).open('w', newline='', encoding='utf-8') as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(dados[0]))
            escritor.writeheader()
            escritor.writerows(dados)
    (pasta / 'resumo_avaliacao.json').write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return pasta


def main():
    parser = argparse.ArgumentParser(description='Avalia uma Q-Table sem continuar treinando.')
    parser.add_argument('--treino', type=Path, required=True, help='Pasta treino_... preservada.')
    parser.add_argument('--episodios', type=int, default=100)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--saida', type=Path, default=Path(__file__).resolve().parent / 'resultados')
    args = parser.parse_args()
    if args.episodios < 1:
        parser.error('--episodios deve ser positivo.')
    try:
        agente, digest = carregar_treino(args.treino)
    except (OSError, ValueError) as erro:
        parser.error(f'Não foi possível carregar o treinamento: {erro}')
    print(f'Avaliando {args.episodios} episódios por estratégia, sem treinamento...', flush=True)
    linhas, trajetorias, resumo = avaliar(agente, args.episodios, args.seed)
    resumo['pasta_treino'] = str(args.treino.resolve())
    resumo['sha256_q_table'] = digest
    resumo['parametros'] = {k: getattr(cfg, k) for k in dir(cfg) if k.isupper()}
    pasta = salvar_avaliacao(linhas, trajetorias, resumo, args.saida)
    a, t = resumo['estrategias']['aleatorio'], resumo['estrategias']['treinado']
    print('\nAVALIAÇÃO CONCLUÍDA')
    print('Indicador | Aleatório | Treinado')
    for chave, rotulo in (
        ('recompensa_total', 'Recompensa média por episódio'),
        ('temperatura_ideal_pct', 'Temperatura ideal (%)'),
        ('umidade_ideal_pct', 'Umidade ideal (%)'),
        ('luminosidade_ideal_pct', 'Luminosidade ideal (%)'),
        ('todas_ideais_pct', 'TODAS as variáveis ideais (%)'),
    ):
        print(f'{rotulo}: {a[chave]:.2f} | {t[chave]:.2f}')
    print(f'Q-Table preservada: {resumo["q_table_preservada"]}')
    print(f'Episódios com maior recompensa do treinado: '
          f'{resumo["episodios_treinado_com_maior_recompensa"]}/{args.episodios}')
    print(f'Resultados salvos em: {pasta.resolve()}')


if __name__ == '__main__':
    main()
