"""Casos pequenos com caminhos e seleção conhecidos, sem depender do CSV real."""
import unittest

import numpy as np
import pandas as pd

from mst_portfolios import calcular_distancias_mst, selecionar_carteira_mst


class TestMstPortfolios(unittest.TestCase):
    def setUp(self):
        # As duas ações se conectam por um REIT na árvore global.
        nomes = ["MSFT", "SPG", "INTC", "IBM"]
        self.dist = pd.DataFrame([
            [0, .6, .9, 1.2], [.6, 0, .8, 1.1],
            [.9, .8, 0, 1.0], [1.2, 1.1, 1.0, 0],
        ], index=nomes, columns=nomes)
        self.arestas = pd.DataFrame([
            ("MSFT", "SPG", .6), ("SPG", "INTC", .8), ("INTC", "IBM", 1.),
        ], columns=["de", "para", "distancia"])

    def test_soma_caminhos_globais(self):
        d = calcular_distancias_mst(self.dist, self.arestas)
        self.assertAlmostEqual(d.loc["MSFT", "INTC"], 1.4)
        self.assertAlmostEqual(d.loc["MSFT", "IBM"], 2.4)
        np.testing.assert_allclose(d, d.T)
        np.testing.assert_array_equal(np.diag(d), 0)
        self.assertEqual(selecionar_carteira_mst(d, {"acao": 2, "reit": 1}),
                         ["MSFT", "IBM", "SPG"])

    def test_pesos_originais_e_ordem_arestas(self):
        self.dist.loc["MSFT", "SPG"] = self.dist.loc["SPG", "MSFT"] = .600000123
        d = calcular_distancias_mst(self.dist, self.arestas.iloc[::-1])
        self.assertAlmostEqual(d.loc["MSFT", "IBM"], 2.400000123)

    def test_arvore_incompativel(self):
        with self.assertRaises(ValueError):
            calcular_distancias_mst(self.dist, self.arestas.iloc[:2])
        self.arestas.loc[2] = ["MSFT", "INTC", .9]  # ciclo e IBM isolado
        with self.assertRaises(ValueError):
            calcular_distancias_mst(self.dist, self.arestas)

    def test_cota_insuficiente(self):
        d = calcular_distancias_mst(self.dist, self.arestas)
        with self.assertRaises(ValueError):
            selecionar_carteira_mst(d, {"reit": 2})


if __name__ == "__main__":
    unittest.main()
