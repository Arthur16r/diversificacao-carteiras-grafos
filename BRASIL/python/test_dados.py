import unittest
import pandas as pd

from collect_tesouro import montar_series_rolling
from limpar_precos import corrigir_xpml


class TestDados(unittest.TestCase):
    def test_rollover_preserva_pu_do_quarto_titulo(self):
        rows = []
        for dia in ['01/01/2020', '03/01/2020']:
            for venc in ['02/01/2020', '01/01/2021', '01/01/2022', '01/01/2023']:
                rows.append({'Tipo Titulo': 'Tesouro Prefixado', 'Data Base': dia,
                             'Data Vencimento': venc,
                             'PU Compra Manha': 103. if dia=='03/01/2020' and venc=='01/01/2023' else 100.})
        s = montar_series_rolling(pd.DataFrame(rows))
        self.assertAlmostEqual(s.loc['2020-01-03', 'prefixado_longo'], 103.)

    def test_xpml_ponte_preserva_retornos_reais_e_idempotencia(self):
        datas = pd.to_datetime(['2026-01-12','2026-01-13','2026-01-14','2026-01-15','2026-01-16','2026-01-19','2026-01-20'])
        p = pd.DataFrame({'XPML11.SA': [14.,14.1,.13,.14,.13,103.,104.]}, index=datas)
        c = corrigir_xpml(p)
        self.assertAlmostEqual(c.loc['2026-01-19','XPML11.SA'],103.)
        self.assertAlmostEqual(c.loc['2026-01-14','XPML11.SA']/c.loc['2026-01-13','XPML11.SA'],110.40/110.13)
        self.assertAlmostEqual(c.loc['2026-01-19','XPML11.SA']/c.loc['2026-01-16','XPML11.SA'],110.52/110.)
        self.assertAlmostEqual(c.iloc[1,0]/c.iloc[0,0],14.1/14.)
        pd.testing.assert_frame_equal(c,corrigir_xpml(c))
        self.assertEqual(p.iloc[2,0],.13)


if __name__ == '__main__':
    unittest.main()
