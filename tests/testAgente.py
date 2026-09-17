"""Verificações do agente: python testes_agente.py. Não executa treinamento."""

import json
import tempfile
import unittest
from itertools import product
from pathlib import Path

from agente import AgenteQLearning
from ambiente import AmbienteEstufa


class TestesAgente(unittest.TestCase):
    def test_01_tabela_zerada_e_linhas_independentes(self):
        a = AgenteQLearning()
        self.assertEqual(len(a.q_table), 27)
        self.assertTrue(all(len(linha) == 8 and all(x == 0 for x in linha) for linha in a.q_table))
        a.q_table[0][0] = 5
        self.assertEqual(a.q_table[1][0], 0)

    def test_02_indices_unicos(self):
        indices = {AgenteQLearning.indice_estado(s) for s in product(range(3), repeat=3)}
        self.assertEqual(indices, set(range(27)))

    def test_03_equacao_com_futuro_e_valor_anterior(self):
        a = AgenteQLearning()
        a.q_table[0][2] = 2
        a.q_table[13][4] = 4
        # 2 + 0.1 * (1 + 0.95 * 4 - 2) = 2.28.
        self.assertAlmostEqual(a.atualizar((0, 0, 0), 2, 1, (1, 1, 1)), 2.28)
        self.assertEqual(a.q_table[0][3], 0)
        self.assertEqual(a.q_table[13][4], 4)

    def test_04_terminal_real_remove_futuro(self):
        a = AgenteQLearning()
        a.q_table[0][2] = 2
        a.q_table[13][4] = 4
        self.assertAlmostEqual(a.atualizar((0, 0, 0), 2, 1, (1, 1, 1), terminado=True), 1.9)

    def test_05_truncamento_preserva_futuro(self):
        a = AgenteQLearning()
        a.q_table[0][2] = 2
        a.q_table[13][4] = 4
        self.assertAlmostEqual(a.atualizar((0, 0, 0), 2, 1, (1, 1, 1), truncado=True), 2.28)

    def test_06_avaliacao_ignora_epsilon_e_nao_aprende(self):
        a = AgenteQLearning(seed=42)
        a.q_table[0][3] = 5
        antes = [linha[:] for linha in a.q_table]
        for _ in range(30):
            self.assertEqual(a.escolher_acao((0, 0, 0), explorar=False), 3)
        self.assertEqual(a.q_table, antes)
        self.assertEqual(a.epsilon, 1)

    def test_07_exploracao_reproduzivel(self):
        a, b = AgenteQLearning(seed=42), AgenteQLearning(seed=42)
        a.q_table[0][0] = b.q_table[0][0] = 5
        escolhas = [a.escolher_acao((0, 0, 0)) for _ in range(100)]
        self.assertEqual(escolhas, [b.escolher_acao((0, 0, 0)) for _ in range(100)])
        self.assertEqual(set(escolhas), set(range(8)))

    def test_08_empates_somente_entre_maximos(self):
        a = AgenteQLearning(seed=42)
        a.q_table[0][2] = a.q_table[0][6] = 5
        escolhas = {a.escolher_acao((0, 0, 0), explorar=False) for _ in range(100)}
        self.assertEqual(escolhas, {2, 6})

    def test_09_decaimento_e_piso(self):
        a = AgenteQLearning()
        self.assertAlmostEqual(a.reduzir_epsilon(), .995)
        for _ in range(2000):
            a.reduzir_epsilon()
        self.assertEqual(a.epsilon, .05)

    def test_10_integracao_com_ambiente(self):
        env, a = AmbienteEstufa(), AgenteQLearning()
        estado = env.reset(valores_iniciais=(29, 40, 400))
        proximo, recompensa, fim, corte, _ = env.step(7)
        self.assertAlmostEqual(a.atualizar(estado, 7, recompensa, proximo, fim, corte), .017)
        self.assertEqual(sum(x != 0 for linha in a.q_table for x in linha), 1)

    def test_11_salvar_carregar_politica(self):
        a, b = AgenteQLearning(), AgenteQLearning()
        a.q_table[13][7] = -2.28
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'politica.json'
            a.salvar(arquivo)
            b.carregar(arquivo)
        self.assertEqual(a.q_table, b.q_table)

    def test_12_arquivo_invalido_preserva_tabela(self):
        a = AgenteQLearning()
        a.q_table[0][0] = 7
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'invalido.json'
            for tabela in ([], [[0] * 7 for _ in range(27)], [[True] * 8 for _ in range(27)]):
                arquivo.write_text(json.dumps({'formato': 'estufa-q-v1', 'q_table': tabela}), encoding='utf-8')
                with self.assertRaises(ValueError):
                    a.carregar(arquivo)
                self.assertEqual(a.q_table[0][0], 7)

    def test_13_entradas_invalidas(self):
        a = AgenteQLearning()
        for estado in ((3, 0, 0), (-1, 0, 0), (0, 0), (True, 0, 0)):
            with self.assertRaises(ValueError):
                a.escolher_acao(estado)
        for parametros in ({'alpha': 0}, {'gamma': 1}, {'epsilon': 2},
                           {'decaimento': 0}, {'alpha': float('nan')}):
            with self.assertRaises(ValueError):
                AgenteQLearning(**parametros)
        for acao in (-1, 8, True):
            with self.assertRaises(ValueError):
                a.atualizar((0, 0, 0), acao, 1, (1, 1, 1))
        with self.assertRaises(ValueError):
            a.atualizar((0, 0, 0), 0, float('inf'), (1, 1, 1))
        self.assertTrue(all(x == 0 for linha in a.q_table for x in linha))


if __name__ == '__main__':
    unittest.main(verbosity=2)
