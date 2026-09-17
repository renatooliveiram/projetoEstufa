"""Testes de integração do treinamento; python testes_treinamento.py."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agente import AgenteQLearning
from treinamento import treinar, salvar_resultados


class TestesTreinamento(unittest.TestCase):
    def test_01_contagens_e_decaimento_por_episodio(self):
        agente, historico, resumo = treinar(3, exibir=False)
        self.assertEqual(len(historico), 3)
        self.assertEqual(resumo['total_decisoes'], 600)
        self.assertEqual(sum(sum(x) for x in resumo['visitas_estado_acao']), 600)
        for i, linha in enumerate(historico):
            self.assertEqual(linha['passos'], 200)
            self.assertEqual(sum(linha[f'acao_{j}'] for j in range(8)), 200)
            self.assertAlmostEqual(linha['epsilon_usado'], .995 ** i)
            self.assertAlmostEqual(linha['epsilon_apos'], .995 ** (i + 1))
            self.assertTrue(0 <= linha['todas_ideais_pct'] <= 100)
        self.assertGreater(resumo['valores_q_nao_zero'], 0)
        self.assertAlmostEqual(agente.epsilon, .995 ** 3)

    def test_02_reprodutibilidade(self):
        a, h1, r1 = treinar(3, seed=42, exibir=False)
        b, h2, r2 = treinar(3, seed=42, exibir=False)
        self.assertEqual(a.q_table, b.q_table)
        self.assertEqual(h1, h2)
        self.assertEqual(r1, r2)

    def test_03_ultimo_passo_tambem_atualiza_sem_terminal_falso(self):
        chamadas = []
        original = AgenteQLearning.atualizar
        def observar(agente, estado, acao, recompensa, novo, terminado=False, truncado=False):
            chamadas.append((terminado, truncado))
            return original(agente, estado, acao, recompensa, novo, terminado, truncado)
        with patch.object(AgenteQLearning, 'atualizar', observar):
            treinar(2, exibir=False)
        self.assertEqual(len(chamadas), 400)
        self.assertEqual([i for i, (_, corte) in enumerate(chamadas) if corte], [199, 399])
        self.assertTrue(all(not fim for fim, _ in chamadas))

    def test_04_arquivos_consistentes_e_execucoes_preservadas(self):
        a, historico, resumo = treinar(2, exibir=False)
        with tempfile.TemporaryDirectory() as base:
            pasta = salvar_resultados(a, historico, resumo, base)
            outra = salvar_resultados(a, historico, resumo, base)
            self.assertNotEqual(pasta, outra)
            b = AgenteQLearning()
            b.carregar(pasta / 'q_table.json')
            self.assertEqual(a.q_table, b.q_table)
            with (pasta / 'historico_treinamento.csv').open(encoding='utf-8', newline='') as arquivo:
                linhas = list(csv.DictReader(arquivo))
            self.assertEqual(len(linhas), 2)
            self.assertAlmostEqual(float(linhas[-1]['recompensa_total']), historico[-1]['recompensa_total'])
            lido = json.loads((pasta / 'resumo_treinamento.json').read_text(encoding='utf-8'))
            self.assertEqual(lido['total_decisoes'], 400)

    def test_05_rejeita_quantidades_invalidas(self):
        for quantidade in (0, -1, True, 2.5):
            with self.assertRaises(ValueError):
                treinar(quantidade, exibir=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
