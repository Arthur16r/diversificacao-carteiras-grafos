"""Casos controlados de execução, fluxos externos e concentração."""
import unittest

import numpy as np
import pandas as pd

from aportes_mensais import metricas_da_serie, simular_aportes


class TestAportes(unittest.TestCase):
    def setUp(self):
        datas = pd.to_datetime(["2020-01-02", "2020-01-31", "2020-02-03", "2020-02-28",
                                "2020-03-02", "2020-03-31", "2020-04-01", "2020-04-02"])
        self.p = pd.DataFrame({"ITUB4.SA": [100, 90, 90, 81, 81, 72.9, 72.9, 72.9],
                               "PETR4.SA": 100., "selic": 100.}, index=datas)

    def test_compra_seguinte_repeticao_e_contabilidade(self):
        r = simular_aportes(self.p, ["ITUB4.SA", "PETR4.SA"], "inteligente")
        ops = pd.DataFrame(r["_operacoes"])
        self.assertEqual(list(ops.ativo), ["ITUB4.SA"] * 3)
        self.assertTrue((ops.data_compra > ops.data_sinal).all())
        self.assertEqual(list(ops.data_compra), list(self.p.index[[2, 4, 6]]))
        self.assertEqual(r["maior_sequencia_mesmo_ativo"], 3)
        self.assertAlmostEqual(r["total_aportado"], 3000)
        self.assertAlmostEqual(r["valor_final"], 2710)
        self.assertAlmostEqual(r["maior_peso_final"], 1)
        self.assertAlmostEqual(sum(d["peso_final"] for d in r["_detalhes"]), 1)

    def test_nao_usa_preco_da_compra_para_escolher(self):
        self.p.loc["2020-02-03", "ITUB4.SA"] = 150
        r = simular_aportes(self.p, ["ITUB4.SA", "PETR4.SA"], "inteligente")
        primeira = r["_operacoes"][0]
        self.assertEqual(primeira["ativo"], "ITUB4.SA")
        self.assertAlmostEqual(primeira["unidades_compradas"], 1000 / 150)
        self.assertAlmostEqual(primeira["retorno_sinal"], -.1)

    def test_fluxos_nao_viram_rentabilidade(self):
        self.p.loc[:, :] = 100.
        for inicial in [0, 100_000]:
            r = simular_aportes(self.p, ["ITUB4.SA", "PETR4.SA"], "igualitario", inicial)
            self.assertAlmostEqual(r["valor_final"], inicial + 3000)
            self.assertAlmostEqual(r["retorno_twr_anual"], 0)
            self.assertAlmostEqual(r["xirr"], 0, places=8)
            self.assertEqual(r["max_drawdown"], 0)
            for d in r["_detalhes"]:
                self.assertAlmostEqual(d["percentual_final"], 50)
                self.assertAlmostEqual(d["percentual_aportes_mensais"], 50)

    def test_primeira_perda_e_periodo_twr(self):
        datas = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"])
        retornos = pd.Series([-.1, 0.], index=datas[1:])
        ref = pd.Series(100., index=datas)
        m = metricas_da_serie(retornos, ref, datas[0])
        self.assertAlmostEqual(m["max_drawdown"], -.1)
        self.assertAlmostEqual(m["retorno_twr_anual"], .9 ** (365.25 / 4) - 1)

    def test_sem_dados_nao_descarta_pregao(self):
        self.p.loc["2020-02-03", "ITUB4.SA"] = np.nan
        with self.assertRaises(ValueError):
            simular_aportes(self.p, ["ITUB4.SA", "PETR4.SA"], "inteligente")


if __name__ == "__main__":
    unittest.main()
