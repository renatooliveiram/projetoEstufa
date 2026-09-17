"""Etapa 9: gráficos a partir dos resultados existentes, sem treinar novamente."""
import argparse
import csv
import hashlib
import json
import math
import tempfile
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use('Agg')  # Salva imagens mesmo sem interface gráfica.
import matplotlib.pyplot as plt

CORES = {'aleatorio': '#C77732', 'treinado': '#187B80'}
ROTULOS = {'aleatorio': 'Aleatório', 'treinado': 'Treinado'}


def ler_csv(caminho):
    with Path(caminho).open(encoding='utf-8-sig', newline='') as arquivo:
        linhas = list(csv.DictReader(arquivo))
    if not linhas:
        raise ValueError(f'Arquivo vazio: {caminho}')
    return [{k: v if k == 'estrategia' else float(v) for k, v in linha.items()}
            for linha in linhas]


def media_movel(valores, janela=50):
    """Média dos últimos 50 episódios; prefixo usa os disponíveis, sem zeros."""
    if janela < 1:
        raise ValueError('A janela deve ser positiva.')
    return [mean(valores[max(0, i - janela + 1):i + 1]) for i in range(len(valores))]


def carregar_dados(treino, avaliacao, episodio=1):
    treino, avaliacao = Path(treino), Path(avaliacao)
    resumo = json.loads((avaliacao / 'resumo_avaliacao.json').read_text(encoding='utf-8'))
    treino_resumo = json.loads((treino / 'resumo_treinamento.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256((treino / 'q_table.json').read_bytes()).hexdigest()
    if digest != resumo['sha256_q_table'] or resumo['parametros'] != treino_resumo['parametros']:
        raise ValueError('A avaliação não corresponde à tabela/configuração desse treinamento.')
    historico = ler_csv(treino / 'historico_treinamento.csv')
    episodios = ler_csv(avaliacao / 'episodios_avaliacao.csv')
    trajetorias = ler_csv(avaliacao / 'trajetorias_avaliacao.csv')
    n = resumo['episodios_por_estrategia']
    passos = resumo['passos_por_episodio']
    if episodio not in range(1, n + 1):
        raise ValueError(f'O episódio ilustrativo deve estar entre 1 e {n}.')
    if [r['episodio'] for r in historico] != list(range(1, treino_resumo['episodios'] + 1)):
        raise ValueError('Histórico de treinamento incompleto ou fora de ordem.')
    grupos = {}
    for r in trajetorias:
        chave = (r['estrategia'], r['episodio'])
        grupos.setdefault(chave, []).append(r)
    esperados = {(nome, i) for nome in CORES for i in range(1, n + 1)}
    if set(grupos) != esperados or len(episodios) != 2 * n:
        raise ValueError('Episódios ou trajetórias incompletos.')
    if {(r['estrategia'], r['episodio']) for r in episodios} != esperados:
        raise ValueError('Episódios repetidos ou ausentes.')
    for chave, grupo in grupos.items():
        if [r['passo'] for r in grupo] != list(range(1, passos + 1)):
            raise ValueError(f'Trajetória incompleta: {chave}')
    for nome in CORES:
        parte = [r for r in episodios if r['estrategia'] == nome]
        for chave in ('recompensa_total', 'temperatura_ideal_pct', 'umidade_ideal_pct',
                      'luminosidade_ideal_pct', 'todas_ideais_pct'):
            if not math.isclose(mean(r[chave] for r in parte), resumo['estrategias'][nome][chave], abs_tol=1e-8):
                raise ValueError('Resumo e métricas por episódio não conferem.')
    return historico, episodios, grupos, resumo


def salvar(fig, pasta, nome, nota):
    fig.text(.08, .02, nota, fontsize=9, color='#52616B')
    fig.tight_layout(rect=(0, .055, 1, .95))
    fig.savefig(pasta / nome, dpi=180, facecolor='white')
    plt.close(fig)


def barras_comparadas(ax, episodios, chaves, rotulos):
    for deslocamento, nome in ((-.19, 'aleatorio'), (.19, 'treinado')):
        parte = [r for r in episodios if r['estrategia'] == nome]
        valores = [mean(r[c] for r in parte) for c in chaves]
        barras = ax.bar([i + deslocamento for i in range(len(chaves))], valores,
                        width=.36, color=CORES[nome], label=ROTULOS[nome])
        ax.bar_label(barras, labels=[f'{v:.2f}%' for v in valores], padding=4, fontsize=10)
    ax.set_xticks(range(len(rotulos)), rotulos)
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel('Passos (%)')
    ax.legend(loc='upper center', bbox_to_anchor=(.5, 1.16), ncol=2, frameon=False)


def gerar_graficos(treino, avaliacao, pasta_base, episodio=1):
    historico, episodios, grupos, resumo = carregar_dados(treino, avaliacao, episodio)
    base = Path(pasta_base)
    base.mkdir(parents=True, exist_ok=True)
    pasta = Path(tempfile.mkdtemp(prefix='graficos_', dir=base))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.grid': True, 'grid.alpha': .16, 'axes.axisbelow': True})
    n = resumo['episodios_por_estrategia']
    fig, eixos = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                             gridspec_kw={'height_ratios': [3, 1]})
    x = [r['episodio'] for r in historico]
    y = [r['recompensa_total'] for r in historico]
    fig.suptitle('Como o treinamento evoluiu?', fontsize=17, fontweight='bold')
    eixos[0].plot(x, y, color='#B8C9CF', linewidth=.7, label='Cada episódio')
    eixos[0].plot(x, media_movel(y), color=CORES['treinado'], linewidth=2,
                  label='Média móvel: últimos 50 episódios')
    eixos[0].set_ylabel('Recompensa total')
    eixos[0].legend(frameon=False)
    eixos[1].plot(x, [r['epsilon_usado'] for r in historico], color='#665A9E')
    eixos[1].set_ylabel('Epsilon usado')
    eixos[1].set_xlabel('Episódio de treinamento')
    eixos[1].set_ylim(0, 1.05)
    salvar(fig, pasta, '01_treinamento.png',
           'Treinamento com exploração variável. A média inicial usa os episódios disponíveis, sem preenchimento.')

    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.suptitle('Quanto tempo a estufa ficou na faixa ideal?', fontsize=17, fontweight='bold')
    barras_comparadas(ax, episodios,
                     ['temperatura_ideal_pct', 'umidade_ideal_pct', 'luminosidade_ideal_pct', 'todas_ideais_pct'],
                     ['Temperatura', 'Umidade', 'Luminosidade', 'Todas juntas'])
    salvar(fig, pasta, '02_faixas_ideais.png',
           f'Avaliação: {n} episódios por estratégia, com condições iniciais pareadas. Inclui a recuperação inicial.')

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.suptitle('Como as recompensas se comparam na avaliação?', fontsize=17, fontweight='bold')
    for nome in CORES:
        parte = sorted((r for r in episodios if r['estrategia'] == nome), key=lambda r: r['episodio'])
        ax.plot([r['episodio'] for r in parte], [r['recompensa_total'] for r in parte],
                color=CORES[nome], label=ROTULOS[nome], marker='.', markersize=4, linewidth=1)
    ax.set_xlabel('Episódio de avaliação (mesma condição inicial para as duas estratégias)')
    ax.set_ylabel('Recompensa total')
    ax.legend(frameon=False)
    salvar(fig, pasta, '03_recompensas_avaliacao.png',
           'Todos os episódios são mostrados. O agente treinado usa a tabela fixa e não explora nem aprende aqui.')

    fig, eixos = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle(f'Condições ambientais — episódio {episodio}', fontsize=17, fontweight='bold')
    nomes = ('temperatura', 'umidade', 'luminosidade')
    unidades = ('Temperatura (°C)', 'Umidade (índice %)', 'Luminosidade (lux)')
    for ax, variavel, unidade, faixa in zip(eixos, nomes, unidades, resumo['parametros']['FAIXAS_IDEAIS']):
        ax.axhspan(*faixa, color='#91B88D', alpha=.25, label='Faixa ideal')
        for nome in CORES:
            dados = grupos[(nome, episodio)]
            inicial = next(r for r in episodios if r['estrategia'] == nome and r['episodio'] == episodio)
            ax.plot([0] + [r['passo'] for r in dados],
                    [inicial[f'{variavel}_inicial']] + [r[variavel] for r in dados],
                    color=CORES[nome], label=ROTULOS[nome], linewidth=1.5)
        ax.set_ylabel(unidade)
    eixos[0].legend(loc='upper left', bbox_to_anchor=(0, 1.25), ncol=3, frameon=False)
    eixos[-1].set_xlabel('Passo de simulação (sem duração física calibrada)')
    salvar(fig, pasta, '04_condicoes_ambientais.png',
           f'Exemplo ilustrativo: episódio {episodio}. As conclusões gerais usam todos os {n} episódios, não apenas este.')

    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.suptitle('Com que frequência os equipamentos ficaram ligados?', fontsize=16, fontweight='bold')
    barras_comparadas(ax, episodios,
                     ['irrigacao_ligada_pct', 'ventilacao_ligada_pct', 'iluminacao_ligada_pct'],
                     ['Irrigação', 'Ventilação', 'Iluminação'])
    salvar(fig, pasta, '05_uso_equipamentos.png',
           'Percentual de passos ligados na avaliação. Não representa consumo medido de energia ou água.')
    manifesto = {'treino': str(Path(treino).resolve()), 'avaliacao': str(Path(avaliacao).resolve()),
                 'episodio_ilustrativo': episodio, 'janela_media_movel': 50,
                 'matplotlib': matplotlib.__version__, 'sha256_fontes': {}}
    for caminho in (Path(treino) / 'historico_treinamento.csv', Path(avaliacao) / 'episodios_avaliacao.csv',
                    Path(avaliacao) / 'trajetorias_avaliacao.csv', Path(avaliacao) / 'resumo_avaliacao.json'):
        manifesto['sha256_fontes'][caminho.name] = hashlib.sha256(caminho.read_bytes()).hexdigest()
    (pasta / 'origem_graficos.json').write_text(json.dumps(manifesto, indent=2), encoding='utf-8')
    return pasta


def main():
    parser = argparse.ArgumentParser(description='Gráficos dos resultados existentes da estufa.')
    parser.add_argument('--treino', type=Path, required=True)
    parser.add_argument('--avaliacao', type=Path, required=True)
    parser.add_argument('--episodio', type=int, default=1)
    parser.add_argument('--saida', type=Path, default=Path(__file__).resolve().parent / 'resultados')
    args = parser.parse_args()
    try:
        pasta = gerar_graficos(args.treino, args.avaliacao, args.saida, args.episodio)
    except (OSError, ValueError, KeyError) as erro:
        parser.error(str(erro))
    print('GRÁFICOS CONCLUÍDOS')
    print('5 imagens PNG geradas. Nenhum treinamento ou avaliação foi repetido.')
    print(f'Arquivos salvos em: {pasta.resolve()}')
    print('Abra os PNGs nessa pasta para visualizar.')


if __name__ == '__main__':
    main()
