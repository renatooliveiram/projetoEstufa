"""Execução integrada: python main.py; opções em python main.py --help."""
import argparse
import json
import tempfile
from pathlib import Path

import config as cfg
from treinamento import treinar, salvar_resultados
from avaliacao import carregar_treino, avaliar, salvar_avaliacao


def executar(args):
    from graficos import gerar_graficos
    agente = digest = None
    if args.treino:
        args.treino = args.treino.resolve()
        agente, digest = carregar_treino(args.treino)
    args.saida.mkdir(parents=True, exist_ok=True)
    pasta = Path(tempfile.mkdtemp(prefix='execucao_', dir=args.saida)).resolve()
    if not args.treino:
        print('[1/3] Treinamento do zero', flush=True)
        agente, historico, resumo_treino = treinar(args.episodios, args.seed)
        treino = salvar_resultados(agente, historico, resumo_treino, pasta)
        agente, digest = carregar_treino(treino)
    else:
        print('[1/3] Reutilizando a tabela indicada, sem novo treino', flush=True)
        treino = args.treino
    print('[2/3] Avaliação com política fixa', flush=True)
    linhas, trajetorias, resumo = avaliar(agente, args.episodios_avaliacao, args.seed_avaliacao)
    resumo['pasta_treino'] = str(treino)
    resumo['sha256_q_table'] = digest
    resumo['parametros'] = {k: getattr(cfg, k) for k in dir(cfg) if k.isupper()}
    avaliacao = salvar_avaliacao(linhas, trajetorias, resumo, pasta)
    print('[3/3] Geração dos cinco gráficos', flush=True)
    graficos = gerar_graficos(treino, avaliacao, pasta)
    manifesto = {'treino': str(treino), 'avaliacao': str(avaliacao), 'graficos': str(graficos),
                 'treino_reutilizado': args.treino is not None, 'sha256_q_table': digest}
    (pasta / 'execucao.json').write_text(json.dumps(manifesto, indent=2), encoding='utf-8')
    print('\nPROJETO CONCLUÍDO')
    print('Indicador | Aleatório | Treinado')
    a, t = resumo['estrategias']['aleatorio'], resumo['estrategias']['treinado']
    for chave, nome in (('recompensa_total', 'Recompensa média por episódio'),
                        ('todas_ideais_pct', 'Todas as variáveis ideais (%)')):
        print(f'{nome}: {a[chave]:.2f} | {t[chave]:.2f}')
    print(f'Q-Table preservada na avaliação: {resumo["q_table_preservada"]}')
    print(f'Execução: {pasta}')
    print(f'Gráficos: {graficos}')
    print('Resultados anteriores preservados. Abra os PNGs na pasta indicada.')


def main():
    parser = argparse.ArgumentParser(description='Estufa inteligente: execução integrada.')
    parser.add_argument('--episodios', type=int, default=1000)
    parser.add_argument('--episodios-avaliacao', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--seed-avaliacao', type=int, default=2026)
    parser.add_argument('--saida', type=Path, default=Path(__file__).resolve().parent / 'resultados')
    parser.add_argument('--treino', type=Path, help='Reutiliza treino_...; ignora --episodios e --seed.')
    args = parser.parse_args()
    if args.episodios < 1 or args.episodios_avaliacao < 1:
        parser.error('As quantidades de episódios devem ser positivas.')
    try:
        executar(args)
    except ModuleNotFoundError as erro:
        parser.exit(1, f'Dependência ausente: {erro.name}. Instale requirements.txt com o mesmo Python.\n')
    except (OSError, ValueError, KeyError) as erro:
        parser.exit(1, f'Execução interrompida: {erro}\nConfira os caminhos e a configuração.\n')


if __name__ == '__main__':
    main()
