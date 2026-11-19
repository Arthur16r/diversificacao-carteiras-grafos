"""Confere a procedência e o universo das figuras com entradas sintéticas."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from visualizacoes import gerar_grafos


class TestDadosFiguras(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.raiz = Path(self.temporario.name)
        self.pasta = self.raiz / "BRASIL/data/processed"
        self.pasta.mkdir(parents=True)
        cpp = self.raiz / "BRASIL/cpp"
        cpp.mkdir()
        py = self.raiz / "BRASIL/python"
        py.mkdir()
        (py / "portfolio_metrics.py").write_text(
            "def classificar_tipo_ativo(n):\n"
            "    return {'A': 'acao', 'F': 'fii', 'T': 'tesouro', 'IVVB11.SA': 'exterior'}[n]\n",
            encoding="utf-8")
        nomes = ["A", "F", "T", "IVVB11.SA"]
        self.matriz = pd.DataFrame([[0, 1, 1.5, 1.4], [1, 0, 0.5, 1.3],
                                   [1.5, 0.5, 0, 1.2], [1.4, 1.3, 1.2, 0]], index=nomes, columns=nomes)
        self.matriz.to_csv(self.pasta / "distance_matrix.csv")
        self.matriz.iloc[:3, :3].to_csv(self.pasta / "distance_matrix_sem_exterior.csv")
        self.mst = cpp / "mst_edges.csv"
        self.mst.write_text("de,para,distancia\nA,F,1\nF,T,0.5\n", encoding="utf-8")
        self.carteira = pd.DataFrame([{
            "ativos": "A;T", "n_ativos": 2, "fim_construcao": "2022-12-31",
            "sha256_matriz_origem": hashlib.sha256((self.pasta / "distance_matrix.csv").read_bytes()).hexdigest(),
            "sha256_arestas_mst": hashlib.sha256(self.mst.read_bytes()).hexdigest(),
        }])
        self.carteira.to_csv(self.pasta / "carteiras_mst.csv", index=False)
        self.substituicao = patch.object(gerar_grafos, "RAIZ", self.raiz)
        self.substituicao.start()
        self.addCleanup(self.substituicao.stop)

    def test_brasil_principal_exclui_exterior_mantendo_procedencia_completa(self):
        nomes, adj, _, selecionados, classes, registro = gerar_grafos.carregar("BRASIL")
        self.assertEqual(nomes, ["A", "F", "T"])
        self.assertEqual(selecionados, {"A", "T"})
        self.assertEqual(set(classes.values()), {"acao", "fii", "tesouro"})
        self.assertEqual(registro["arestas_grafo_completo"], 3)
        posicoes = gerar_grafos.layout_radial(adj)
        self.assertEqual(set(posicoes), set(nomes))
        self.assertEqual(len(set(posicoes.values())), 3)

    def test_carteira_antiga_e_rejeitada_antes_de_gerar_imagem(self):
        with self.mst.open("a", encoding="utf-8") as f:
            f.write("A,T,1.5\n")
        with self.assertRaisesRegex(ValueError, "Carteira desatualizada"):
            gerar_grafos.carregar("BRASIL")

    def test_matriz_domestica_diferente_da_origem_e_rejeitada(self):
        domestica = self.matriz.iloc[:3, :3].copy()
        domestica.loc["A", "F"] = domestica.loc["F", "A"] = 0.9
        domestica.to_csv(self.pasta / "distance_matrix_sem_exterior.csv")
        with self.assertRaisesRegex(ValueError, "Matriz doméstica incompatível"):
            gerar_grafos.carregar("BRASIL")


if __name__ == "__main__":
    unittest.main()
