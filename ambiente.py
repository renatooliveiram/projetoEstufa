"""Estufa determinística com condições iniciais sorteadas e estados discretos."""

import math
import random
from numbers import Integral

import config as cfg


class AmbienteEstufa:
    """reset retorna estado; step retorna estado, recompensa, fim, corte, info.

    O estado é uma tupla de categorias (0: baixa, 1: ideal, 2: alta).
    Os valores contínuos permanecem disponíveis em info e em valores.
    """

    def __init__(self, max_passos=cfg.MAX_PASSOS):
        if isinstance(max_passos, bool) or not isinstance(max_passos, Integral) or max_passos <= 0:
            raise ValueError("max_passos deve ser um inteiro positivo.")
        self.max_passos = int(max_passos)
        self._rng = random.Random()
        self._valores = None
        self.passos = 0

    @property
    def valores(self):
        """Tupla imutável (temperatura, umidade, luminosidade)."""
        if self._valores is None:
            raise RuntimeError("Execute reset() antes de usar o ambiente.")
        return self._valores

    def reset(self, seed=None, valores_iniciais=None):
        """Reinicia; seed reproduz sorteios. Valores explícitos ajudam os testes."""
        if valores_iniciais is not None:
            valores = tuple(float(x) for x in valores_iniciais)
            if len(valores) != 3 or any(
                not math.isfinite(x) or not minimo <= x <= maximo
                for x, (minimo, maximo) in zip(valores, cfg.LIMITES)
            ):
                raise ValueError("Informe três valores finitos dentro dos limites da simulação.")
        else:
            if seed is not None:
                self._rng.seed(seed)
            valores = tuple(self._rng.uniform(a, b) for a, b in cfg.FAIXAS_INICIAIS)
        self._valores = valores
        self.passos = 0
        return self.discretizar()

    def discretizar(self):
        return tuple(
            0 if x < minimo else 2 if x > maximo else 1
            for x, (minimo, maximo) in zip(self.valores, cfg.FAIXAS_IDEAIS)
        )

    @staticmethod
    def _equipamentos(acao):
        if isinstance(acao, bool) or not isinstance(acao, Integral) or not 0 <= acao < cfg.NUM_ACOES:
            raise ValueError("A ação deve ser um inteiro entre 0 e 7.")
        return cfg.ACOES[int(acao)]

    def calcular_recompensa(self, acao):
        """Pontua os valores atuais, sem alterá-los, incluindo custo da ação."""
        equipamentos = self._equipamentos(acao)
        total = 0.0
        for x, (minimo, maximo), escala in zip(
            self.valores, cfg.FAIXAS_IDEAIS, cfg.ESCALAS_PENALIDADE
        ):
            distancia = max(minimo - x, 0.0, x - maximo)
            total += 1.0 if distancia == 0 else -min(cfg.PENALIDADE_MAXIMA, distancia / escala)
        return total - cfg.CUSTO_EQUIPAMENTO * sum(equipamentos)

    def step(self, acao):
        temperatura, umidade, luz = self.valores
        if self.passos >= self.max_passos:
            raise RuntimeError("Episódio encerrado por duração. Execute reset().")
        irrigacao, ventilacao, iluminacao = self._equipamentos(acao)
        novos = (
            temperatura + cfg.TAXA_TEMPERATURA * (cfg.TEMPERATURA_REFERENCIA - temperatura)
            - cfg.EFEITO_VENTILACAO * ventilacao,
            umidade - cfg.PERDA_UMIDADE + cfg.EFEITO_IRRIGACAO * irrigacao,
            luz + cfg.TAXA_LUZ * (cfg.LUZ_AMBIENTE + cfg.EFEITO_ILUMINACAO * iluminacao - luz),
        )
        self._valores = tuple(
            max(minimo, min(maximo, x))
            for x, (minimo, maximo) in zip(novos, cfg.LIMITES)
        )
        self.passos += 1
        estado = self.discretizar()
        info = {
            "temperatura": self.valores[0],
            "umidade": self.valores[1],
            "luminosidade": self.valores[2],
            "equipamentos": (irrigacao, ventilacao, iluminacao),
            "passo": self.passos,
            "dentro_faixa": tuple(categoria == 1 for categoria in estado),
        }
        # Não há terminal físico neste modelo; 200 passos são truncamento.
        return estado, self.calcular_recompensa(acao), False, self.passos >= self.max_passos, info


def demonstrar():
    """Ações manuais apenas para inspecionar o ambiente; não há agente ainda."""
    ambiente = AmbienteEstufa()
    estado = ambiente.reset(valores_iniciais=(29, 40, 400))
    print("Demonstração do ambiente: ações manuais, sem treinamento.")
    print(f"Inicial: {ambiente.valores}; estado={estado}")
    for acao in (7, 7, 7, 4, 4):
        estado, recompensa, _, _, info = ambiente.step(acao)
        print(
            f"Passo {info['passo']} | ação={acao} | "
            f"T={info['temperatura']:.2f} °C | U={info['umidade']:.2f}% | "
            f"L={info['luminosidade']:.2f} lux | estado={estado} | r={recompensa:.3f}"
        )


if __name__ == "__main__":
    demonstrar()
