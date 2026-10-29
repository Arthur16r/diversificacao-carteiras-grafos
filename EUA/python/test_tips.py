"""Verificações da indexação nominal e da cobertura histórica do TIPS."""
import unittest

import pandas as pd

from collect_tesouro_fred import construir_indices, cpi_referencia_tips


class TestTips(unittest.TestCase):
    def setUp(self):
        self.datas = pd.to_datetime(["2003-01-01", "2003-01-02", "2003-01-03", "2003-01-06"])
        self.taxas = pd.DataFrame({
            "DGS3MO": 2.0, "DGS5": 3.0, "DGS10": 4.0,
            "DFII10": [float("nan"), 0.0, 0.0, 0.0],
        }, index=self.datas)
        self.cpi = pd.Series([100.0, 103.1], index=pd.to_datetime(["2002-10-01", "2002-11-01"]))

    def test_defasagem_e_interpolacao(self):
        ref = cpi_referencia_tips(self.cpi, self.datas)
        self.assertAlmostEqual(ref.iloc[0], 100.0)
        self.assertAlmostEqual(ref.iloc[1], 100.1)
        self.assertAlmostEqual(ref.iloc[-1], 100.5)

    def test_ausencia_inicial_e_retorno_nominal(self):
        tips = construir_indices(self.taxas, self.cpi)["tesouro_tips"]
        self.assertTrue(pd.isna(tips.iloc[0]))
        self.assertEqual(tips.iloc[1], 100.0)
        self.assertAlmostEqual(tips.iloc[-1], 100 * 100.5 / 100.1)

    def test_carrego_real_inclui_fim_de_semana(self):
        self.taxas["DFII10"] = [float("nan"), 2.0, 2.0, 2.0]
        cpi = self.cpi * 0 + 100
        tips = construir_indices(self.taxas, cpi)["tesouro_tips"]
        self.assertAlmostEqual(tips.iloc[-1] / tips.iloc[-2] - 1, 0.02 * 3 / 365.25)

    def test_cpi_incompleto_nao_vira_retorno_zero(self):
        with self.assertRaisesRegex(ValueError, "CPI"):
            construir_indices(self.taxas, self.cpi.iloc[:1])

    def test_contingencia_oficial_outubro_2025(self):
        cpi = pd.Series([324.800, float("nan"), 324.122],
                        index=pd.to_datetime(["2025-09-01", "2025-10-01", "2025-11-01"]))
        ref = cpi_referencia_tips(cpi, pd.to_datetime(["2026-01-01"]))
        self.assertAlmostEqual(ref.iloc[0], 325.604)
        self.assertTrue(pd.isna(cpi.iloc[1]))  # preserva o dado bruto


if __name__ == "__main__":
    unittest.main()
