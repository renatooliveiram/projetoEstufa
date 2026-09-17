"""Etapa 5: testes do ambiente. Execute: python testes.py

Usa apenas unittest, incluído no Python. Valores esperados vêm das regras
acordadas na Etapa 2. Ainda não testa Q-Learning, pois não foi implementado.
"""

import math
import unittest
from itertools import product

from ambiente import AmbienteEstufa


class TestesAmbiente(unittest.TestCase):
    def setUp(self):
        self.ambiente = AmbienteEstufa()

    def iniciar(self, valores=(29, 40, 400)):
        return self.ambiente.reset(valores_iniciais=valores)

    def test_01_primeiro_passo_da_demonstracao(self):
        self.iniciar()
        estado, recompensa, terminado, truncado, info = self.ambiente.step(7)
        for obtido, esperado in zip(self.ambiente.valores, (27.9, 44, 600)):
            self.assertAlmostEqual(obtido, esperado)
        self.assertEqual(estado, (2, 0, 1))
        self.assertAlmostEqual(recompensa, 0.17)
        self.assertFalse(terminado)
        self.assertFalse(truncado)
        self.assertEqual(info['passo'], 1)
        self.assertEqual(info['dentro_faixa'], (False, False, True))

    def test_02_oito_acoes_e_efeitos_independentes(self):
        # Oráculo numérico para uma mesma condição inicial (29, 40, 400).
        casos = (
            (0, (0, 0, 0), (28.9, 38, 400)),
            (1, (1, 0, 0), (28.9, 44, 400)),
            (2, (0, 1, 0), (27.9, 38, 400)),
            (3, (1, 1, 0), (27.9, 44, 400)),
            (4, (0, 0, 1), (28.9, 38, 600)),
            (5, (1, 0, 1), (28.9, 44, 600)),
            (6, (0, 1, 1), (27.9, 38, 600)),
            (7, (1, 1, 1), (27.9, 44, 600)),
        )
        for acao, equipamentos, esperado in casos:
            with self.subTest(acao=acao):
                self.iniciar()
                *_, info = self.ambiente.step(acao)
                self.assertEqual(info['equipamentos'], equipamentos)
                for valor, alvo in zip(self.ambiente.valores, esperado):
                    self.assertAlmostEqual(valor, alvo)

    def test_03_limites_das_categorias_sao_inclusivos(self):
        for indice, minimo, maximo in ((0, 20, 26), (1, 50, 70), (2, 600, 900)):
            for valor, categoria in ((minimo - .01, 0), (minimo, 1),
                                     (maximo, 1), (maximo + .01, 2)):
                with self.subTest(variavel=indice, valor=valor):
                    valores = [23, 60, 750]
                    valores[indice] = valor
                    self.assertEqual(self.iniciar(valores)[indice], categoria)

    def test_04_representacao_dos_27_estados(self):
        encontrados = set()
        for valores in product((18, 23, 30), (40, 60, 80), (400, 750, 1000)):
            encontrados.add(self.iniciar(valores))
        self.assertEqual(encontrados, set(product(range(3), repeat=3)))

    def test_05_recompensa_ideal_e_custo_dos_equipamentos(self):
        self.iniciar((23, 60, 750))
        for acao, recompensa in ((0, 3), (1, 2.95), (3, 2.90), (7, 2.85)):
            with self.subTest(acao=acao):
                self.assertAlmostEqual(self.ambiente.calcular_recompensa(acao), recompensa)
        self.assertEqual(self.ambiente.valores, (23, 60, 750))
        self.assertEqual(self.ambiente.passos, 0)

    def test_06_aproximacao_da_faixa_melhora_recompensa(self):
        # Demais variáveis e ação permanecem constantes em cada comparação.
        for indice, trajetorias in ((0, ((10, 18, 20), (40, 28, 26))),
                                   (1, ((0, 40, 50), (100, 80, 70))),
                                   (2, ((0, 500, 600), (1200, 1000, 900)))):
            for trajetoria in trajetorias:
                pontos = []
                for valor in trajetoria:
                    valores = [23, 60, 750]
                    valores[indice] = valor
                    self.iniciar(valores)
                    pontos.append(self.ambiente.calcular_recompensa(0))
                with self.subTest(variavel=indice, trajetoria=trajetoria):
                    self.assertLess(pontos[0], pontos[1])
                    self.assertLess(pontos[1], pontos[2])

    def test_07_penalidades_numericas(self):
        self.iniciar((31, 30, 300))  # -1 em cada variável.
        self.assertAlmostEqual(self.ambiente.calcular_recompensa(0), -3)
        self.assertAlmostEqual(self.ambiente.calcular_recompensa(7), -3.15)

    def test_08_saturacao_da_umidade(self):
        for inicial, acao, esperado in ((99, 1, 100), (1, 0, 0)):
            with self.subTest(inicial=inicial):
                self.iniciar((23, inicial, 750))
                self.ambiente.step(acao)
                self.assertEqual(self.ambiente.valores[1], esperado)

    def test_09_limites_em_episodios_com_condicoes_extremas(self):
        limites = ((10, 40), (0, 100), (0, 1200))
        for inicial in product(*limites):
            for acao in range(8):
                with self.subTest(inicial=inicial, acao=acao):
                    self.iniciar(inicial)
                    for _ in range(200):
                        self.ambiente.step(acao)
                        for valor, (minimo, maximo) in zip(self.ambiente.valores, limites):
                            self.assertTrue(math.isfinite(valor))
                            self.assertGreaterEqual(valor, minimo)
                            self.assertLessEqual(valor, maximo)

    def test_10_reset_reproduz_semente_e_zera_passos(self):
        estado = self.ambiente.reset(seed=42)
        valores = self.ambiente.valores
        self.ambiente.step(7)
        self.assertEqual(self.ambiente.reset(seed=42), estado)
        self.assertEqual(self.ambiente.valores, valores)
        self.assertEqual(self.ambiente.passos, 0)

    def test_11_sorteios_respeitam_faixas_iniciais(self):
        for seed in range(20):
            self.ambiente.reset(seed=seed)
            for valor, (minimo, maximo) in zip(self.ambiente.valores, ((18, 32), (30, 85), (200, 1100))):
                self.assertGreaterEqual(valor, minimo)
                self.assertLessEqual(valor, maximo)

    def test_12_corte_exatamente_no_passo_200_e_reinicio(self):
        self.iniciar()
        for passo in range(1, 201):
            _, _, terminado, truncado, info = self.ambiente.step(0)
            self.assertFalse(terminado)
            self.assertEqual(truncado, passo == 200)
            self.assertEqual(info['passo'], passo)
        with self.assertRaises(RuntimeError):
            self.ambiente.step(0)
        self.iniciar()
        self.assertFalse(self.ambiente.step(0)[3])

    def test_13_estado_ideal_nao_encerra_episodio(self):
        self.iniciar((23, 60, 750))
        estado, _, terminado, truncado, _ = self.ambiente.step(4)
        self.assertEqual(estado, (1, 1, 1))
        self.assertFalse(terminado)
        self.assertFalse(truncado)

    def test_14_acoes_invalidas_nao_alteram_ambiente(self):
        self.iniciar()
        for acao in (-1, 8, 1.5, '7', True, None):
            with self.subTest(acao=acao):
                with self.assertRaises(ValueError):
                    self.ambiente.step(acao)
                self.assertEqual(self.ambiente.valores, (29, 40, 400))
                self.assertEqual(self.ambiente.passos, 0)

    def test_15_exige_reset_antes_de_executar(self):
        with self.assertRaises(RuntimeError):
            self.ambiente.step(0)

    def test_16_rejeita_condicoes_iniciais_invalidas(self):
        for valores in ((9, 60, 750), (23, 101, 750), (23, 60, -1),
                        (float('nan'), 60, 750), (23, 60, float('inf')), (23, 60)):
            with self.subTest(valores=valores):
                with self.assertRaises(ValueError):
                    self.iniciar(valores)

    def test_17_duracao_personalizada_e_validacao(self):
        for valor in (0, -1, 1.5, True):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    AmbienteEstufa(max_passos=valor)
        ambiente = AmbienteEstufa(max_passos=1)
        ambiente.reset(seed=42)
        self.assertTrue(ambiente.step(0)[3])


if __name__ == '__main__':
    unittest.main(verbosity=2)