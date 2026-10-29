import unittest
from collections import Counter

import pandas as pd

from portfolio_metrics import classificar_tipo_ativo, gerar_carteiras_aleatorias_com_cotas


class TestAleatoriasCotas(unittest.TestCase):
    def setUp(self):
        self.dist = pd.DataFrame(index=["MSFT", "IBM", "INTC", "SPG", "FR", "tesouro_curto", "tesouro_longo"])
        self.cotas = {"acao": 2, "reit": 1, "tesouro": 1}

    def test_cotas_unicidade_e_reproducibilidade(self):
        a = gerar_carteiras_aleatorias_com_cotas(self.dist, self.cotas, 12)
        self.assertEqual(a, gerar_carteiras_aleatorias_com_cotas(self.dist, self.cotas, 12))
        self.assertEqual(len({tuple(sorted(c)) for c in a}), 12)
        for c in a:
            self.assertEqual(len(c), len(set(c)))
            self.assertEqual(Counter(map(classificar_tipo_ativo, c)), self.cotas)

    def test_quantidade_impossivel(self):
        with self.assertRaises(ValueError):
            gerar_carteiras_aleatorias_com_cotas(self.dist, self.cotas, 13)


if __name__ == "__main__":
    unittest.main()
