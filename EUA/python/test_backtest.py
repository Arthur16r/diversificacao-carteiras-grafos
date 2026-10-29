"""Verifica a definição do Sharpe e o alinhamento temporal da referência."""
import unittest

import numpy as np
import pandas as pd

from backtest import calcular_metricas


class TestSharpe(unittest.TestCase):
    def setUp(self):
        self.datas = pd.bdate_range("2020-01-01", periods=4)
        self.valor = pd.Series([100., 110., 99., 108.9], index=self.datas)
        self.referencia = pd.Series([100., 101., 103.02, 106.1106], index=self.datas)

    def test_excessos_variaveis_e_medida_antiga(self):
        resultado = calcular_metricas(self.valor, .02, self.referencia)
        excessos = np.array([.09, -.12, .07])
        esperado = excessos.mean() / excessos.std(ddof=1) * np.sqrt(252)
        self.assertAlmostEqual(resultado["sharpe"], esperado)
        self.assertAlmostEqual(resultado["vol_anual"], np.std([.1, -.1, .1], ddof=1) * np.sqrt(252))
        self.assertAlmostEqual(resultado["razao_cagr_excedente_vol"],
                               (resultado["cagr"] - .02) / resultado["vol_anual"])

    def test_ordem_e_datas_extras_da_referencia(self):
        ref = pd.concat([self.referencia, pd.Series([80.], index=[pd.Timestamp("2019-12-31")])])
        esperado = calcular_metricas(self.valor, .02, self.referencia)["sharpe"]
        self.assertEqual(calcular_metricas(self.valor, .02, ref.iloc[::-1])["sharpe"], esperado)

    def test_referencia_incompleta_falha(self):
        with self.assertRaisesRegex(ValueError, "Referência"):
            calcular_metricas(self.valor, .02, self.referencia.drop(self.datas[1]))

    def test_excesso_sem_variacao_indefinido(self):
        self.assertTrue(np.isnan(calcular_metricas(self.valor, .02, self.valor)["sharpe"]))


if __name__ == "__main__":
    unittest.main()
