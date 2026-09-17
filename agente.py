"""Q-Learning tabular: 27 estados, 8 ações, sem regras prontas de controle.

Execute `python agente.py` para uma demonstração de uma atualização.
A tabela usa listas do Python; não há dependências externas nesta etapa.
"""

import json
import math
import random
from numbers import Integral, Real
from pathlib import Path

import config as cfg


class AgenteQLearning:
    def __init__(self, alpha=cfg.ALPHA, gamma=cfg.GAMMA,
                 epsilon=cfg.EPSILON_INICIAL, epsilon_minimo=cfg.EPSILON_MINIMO,
                 decaimento=cfg.DECAIMENTO_EPSILON, seed=None):
        parametros = (alpha, gamma, epsilon, epsilon_minimo, decaimento)
        if any(isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x)
               for x in parametros):
            raise ValueError('Os parâmetros devem ser números finitos.')
        if not (0 < alpha <= 1 and 0 <= gamma < 1 and
                0 <= epsilon_minimo <= epsilon <= 1 and 0 < decaimento <= 1):
            raise ValueError('Verifique os intervalos de alpha, gamma, epsilon e decaimento.')
        self.alpha = float(alpha)
        self.gamma = float(gamma)
        self.epsilon = float(epsilon)
        self.epsilon_minimo = float(epsilon_minimo)
        self.decaimento = float(decaimento)
        self._rng = random.Random(seed)
        self.q_table = [[0.0 for _ in range(cfg.NUM_ACOES)] for _ in range(cfg.NUM_ESTADOS)]

    @staticmethod
    def indice_estado(estado):
        """(T, U, L) em categorias 0..2 -> índice 0..26."""
        if not isinstance(estado, (tuple, list)) or len(estado) != 3 or any(
            isinstance(x, bool) or not isinstance(x, Integral) or not 0 <= x <= 2
            for x in estado
        ):
            raise ValueError('O estado deve conter três categorias inteiras entre 0 e 2.')
        return int(9 * estado[0] + 3 * estado[1] + estado[2])

    def escolher_acao(self, estado, explorar=True):
        """Na avaliação, explorar=False ignora epsilon e não altera a tabela.

        Empates entre máximos são sorteados para não favorecer a ação 0.
        Isso também vale na avaliação e é reproduzível com a mesma semente.
        """
        indice = self.indice_estado(estado)
        if explorar and self._rng.random() < self.epsilon:
            return self._rng.randrange(cfg.NUM_ACOES)
        linha = self.q_table[indice]
        maior = max(linha)
        melhores = [acao for acao, valor in enumerate(linha) if valor == maior]
        return self._rng.choice(melhores)

    def atualizar(self, estado, acao, recompensa, novo_estado,
                  terminado=False, truncado=False):
        """Atualiza somente Q(s,a) e devolve o novo valor.

        O truncamento de 200 passos mantém o valor futuro. Apenas um terminal
        real elimina esse valor. Passe novo_estado de step, nunca o de reset.
        """
        indice = self.indice_estado(estado)
        proximo = self.indice_estado(novo_estado)
        if isinstance(acao, bool) or not isinstance(acao, Integral) or not 0 <= acao < cfg.NUM_ACOES:
            raise ValueError('A ação deve ser um inteiro entre 0 e 7.')
        if isinstance(recompensa, bool) or not isinstance(recompensa, Real) or not math.isfinite(recompensa):
            raise ValueError('A recompensa deve ser um número finito.')
        if not isinstance(terminado, bool) or not isinstance(truncado, bool):
            raise ValueError('terminado e truncado devem ser booleanos.')
        futuro = 0.0 if terminado else max(self.q_table[proximo])
        atual = self.q_table[indice][acao]
        alvo = float(recompensa) + self.gamma * futuro
        novo_valor = atual + self.alpha * (alvo - atual)
        if not math.isfinite(novo_valor):
            raise ValueError('Atualização resultou em valor não finito.')
        self.q_table[indice][acao] = novo_valor
        return novo_valor

    def reduzir_epsilon(self):
        """Chamar uma vez ao FINAL de cada episódio de treinamento."""
        self.epsilon = max(self.epsilon_minimo, self.epsilon * self.decaimento)
        return self.epsilon

    def salvar(self, caminho):
        """Salva a política em JSON; não é checkpoint completo do treinamento."""
        dados = {'formato': 'estufa-q-v1', 'q_table': self.q_table}
        Path(caminho).write_text(json.dumps(dados, allow_nan=False), encoding='utf-8')

    def carregar(self, caminho):
        """Valida a tabela antes de substituir; mantém parâmetros e RNG atuais."""
        dados = json.loads(Path(caminho).read_text(encoding='utf-8'))
        if not isinstance(dados, dict) or dados.get('formato') != 'estufa-q-v1':
            raise ValueError('Formato de política incompatível.')
        tabela = dados.get('q_table')
        if not isinstance(tabela, list) or len(tabela) != cfg.NUM_ESTADOS:
            raise ValueError('A tabela deve ter 27 linhas.')
        for linha in tabela:
            if not isinstance(linha, list) or len(linha) != cfg.NUM_ACOES or any(
                isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x)
                for x in linha
            ):
                raise ValueError('Cada linha deve ter 8 números finitos.')
        self.q_table = [[float(x) for x in linha] for linha in tabela]


def demonstrar():
    from ambiente import AmbienteEstufa

    ambiente = AmbienteEstufa()
    agente = AgenteQLearning(seed=42)
    estado = ambiente.reset(valores_iniciais=(29, 40, 400))
    # Ação fixa apenas para tornar o cálculo da demonstração reproduzível.
    acao = 7
    proximo, recompensa, terminado, truncado, _ = ambiente.step(acao)
    antes = agente.q_table[agente.indice_estado(estado)][acao]
    depois = agente.atualizar(estado, acao, recompensa, proximo, terminado, truncado)
    print('Demonstração de uma atualização Q-Learning; ainda sem treinamento completo.')
    print(f'Q-Table: {len(agente.q_table)} estados x {len(agente.q_table[0])} ações')
    print(f'Estado: {estado} | ação de demonstração: {acao} | novo estado: {proximo}')
    print(f'Recompensa: {recompensa:.3f}')
    print(f'Q antes: {antes:.5f} | Q depois: {depois:.5f}')
    print(f'Ação gulosa no estado original: {agente.escolher_acao(estado, explorar=False)}')
    print(f'Epsilon inicial: {agente.epsilon:.3f}')
    print(f'Epsilon após uma redução ilustrativa: {agente.reduzir_epsilon():.3f}')


if __name__ == '__main__':
    demonstrar()
