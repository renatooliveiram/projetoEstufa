"""Execute python testes_avaliacao.py. Testes usam tabela sintética, sem treino."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agente import AgenteQLearning
from avaliacao import avaliar, salvar_avaliacao, carregar_treino
import config as cfg


class TestesAvaliacao(unittest.TestCase):
    def agente_fixo(self):
        a = AgenteQLearning(seed=42)
        for linha in a.q_table:
            linha[4] = 1.0  # Política sintética conhecida: somente luz ligada.
        return a

    def test_01_pares_com_mesmas_condicoes_iniciais(self):
        linhas, trajetorias, _ = avaliar(self.agente_fixo(), 3)
        self.assertEqual(len(linhas), 6)
        self.assertEqual(len(trajetorias), 1200)
        for a, t in zip(linhas[::2], linhas[1::2]):
            self.assertEqual(a['episodio'], t['episodio'])
            for variavel in ('temperatura', 'umidade', 'luminosidade'):
                self.assertEqual(a[f'{variavel}_inicial'], t[f'{variavel}_inicial'])
            self.assertEqual(a['passos'], 200)
            self.assertEqual(t['passos'], 200)

    def test_02_sem_exploracao_sem_atualizacao(self):
        a = self.agente_fixo()
        antes = [linha[:] for linha in a.q_table]
        with patch.object(AgenteQLearning, 'atualizar', side_effect=AssertionError('Não deve treinar')):
            with patch.object(AgenteQLearning, 'reduzir_epsilon', side_effect=AssertionError('Não deve decair')):
                _, trajetorias, resumo = avaliar(a, 2)
        self.assertEqual(a.q_table, antes)
        self.assertEqual(a.epsilon, 1.0)
        self.assertTrue(resumo['q_table_preservada'])
        self.assertTrue(all(x['acao'] == 4 for x in trajetorias if x['estrategia'] == 'treinado'))

    def test_03_metricas_conferem_com_trajetorias(self):
        linhas, trajetorias, resumo = avaliar(self.agente_fixo(), 2)
        for linha in linhas:
            dados = [x for x in trajetorias if x['estrategia'] == linha['estrategia']
                     and x['episodio'] == linha['episodio']]
            self.assertAlmostEqual(linha['recompensa_total'], sum(x['recompensa'] for x in dados))
            contagem = sum(20 <= x['temperatura'] <= 26 and 50 <= x['umidade'] <= 70
                           and 600 <= x['luminosidade'] <= 900 for x in dados)
            self.assertAlmostEqual(linha['todas_ideais_pct'], contagem / 2)
            self.assertEqual(sum(linha[f'acao_{i}'] for i in range(8)), 200)
        esperado = sum(x['recompensa_total'] for x in linhas if x['estrategia'] == 'treinado') / 2
        self.assertAlmostEqual(resumo['estrategias']['treinado']['recompensa_total'], esperado)

    def test_04_reprodutibilidade(self):
        a = self.agente_fixo()
        self.assertEqual(avaliar(a, 2, seed=2026), avaliar(a, 2, seed=2026))

    def test_05_arquivos_e_preservacao_de_execucoes(self):
        dados = avaliar(self.agente_fixo(), 1)
        with tempfile.TemporaryDirectory() as base:
            p1 = salvar_avaliacao(*dados, base)
            p2 = salvar_avaliacao(*dados, base)
            self.assertNotEqual(p1, p2)
            with (p1 / 'episodios_avaliacao.csv').open(encoding='utf-8') as arquivo:
                self.assertEqual(len(list(csv.DictReader(arquivo))), 2)
            with (p1 / 'trajetorias_avaliacao.csv').open(encoding='utf-8') as arquivo:
                self.assertEqual(len(list(csv.DictReader(arquivo))), 400)
            self.assertEqual(json.loads((p1 / 'resumo_avaliacao.json').read_text(encoding='utf-8')), dados[2])

    def test_06_validacao_do_treino_e_integridade_da_origem(self):
        with tempfile.TemporaryDirectory() as base:
            pasta = Path(base)
            self.agente_fixo().salvar(pasta / 'q_table.json')
            conteudo = (pasta / 'q_table.json').read_bytes()
            parametros = {k: getattr(cfg, k) for k in dir(cfg) if k.isupper()}
            resumo = pasta / 'resumo_treinamento.json'
            resumo.write_text(json.dumps({'parametros': parametros}), encoding='utf-8')
            a, digest = carregar_treino(pasta)
            self.assertEqual(len(digest), 64)
            avaliar(a, 1)
            self.assertEqual((pasta / 'q_table.json').read_bytes(), conteudo)
            parametros['MAX_PASSOS'] = 10
            resumo.write_text(json.dumps({'parametros': parametros}), encoding='utf-8')
            with self.assertRaises(ValueError):
                carregar_treino(pasta)

    def test_07_rejeita_episodios_invalidos(self):
        for valor in (0, -1, True, 2.5):
            with self.assertRaises(ValueError):
                avaliar(self.agente_fixo(), valor)


if __name__ == '__main__':
    unittest.main(verbosity=2)
