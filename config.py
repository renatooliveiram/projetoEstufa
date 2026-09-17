"""Parâmetros didáticos; não representam uma cultura ou sensor calibrado."""

# Ordem das variáveis: temperatura (°C), umidade (índice %), luz (lux).
LIMITES = ((10.0, 40.0), (0.0, 100.0), (0.0, 1200.0))
FAIXAS_IDEAIS = ((20.0, 26.0), (50.0, 70.0), (600.0, 900.0))
FAIXAS_INICIAIS = ((18.0, 32.0), (30.0, 85.0), (200.0, 1100.0))
ESCALAS_PENALIDADE = (5.0, 20.0, 300.0)
PENALIDADE_MAXIMA = 3.0
CUSTO_EQUIPAMENTO = 0.05
MAX_PASSOS = 200
TEMPERATURA_REFERENCIA = 28.0
TAXA_TEMPERATURA = 0.1
EFEITO_VENTILACAO = 1.0
PERDA_UMIDADE = 2.0
EFEITO_IRRIGACAO = 6.0
LUZ_AMBIENTE = 400.0
EFEITO_ILUMINACAO = 400.0
TAXA_LUZ = 0.5

# Cada ação define (irrigação, ventilação, iluminação) para aquele passo.
ACOES = (
    (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0),
    (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1),
)
NUM_ESTADOS = 27
NUM_ACOES = len(ACOES)

# Parâmetros iniciais de Q-Learning, ainda sujeitos à avaliação experimental.
ALPHA = 0.10  # Fração do erro usada em cada atualização.
GAMMA = 0.95  # Peso das recompensas futuras.
EPSILON_INICIAL = 1.0  # Probabilidade inicial de ação exploratória.
EPSILON_MINIMO = 0.05
DECAIMENTO_EPSILON = 0.995  # Multiplicador aplicado uma vez por episódio.
