"""Ponte de retorno de XPML11 baseada em fechamentos oficiais da B3.

Não sobrescreve preços brutos. Mantém retornos fora da janela afetada e não
impõe retorno zero entre as duas pontas, como fazia o script antigo.
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data"
FONTE = BASE / "raw" / "xpml11_b3_janeiro2026.csv"


def corrigir_xpml(precos):
    precos = precos.copy()
    coluna = "XPML11.SA"
    if coluna not in precos or precos.index.max() < pd.Timestamp("2026-01-19"):
        return precos
    oficiais = pd.read_csv(FONTE, index_col="data", parse_dates=True)
    dias = oficiais.index
    original = precos.loc[dias, coluna].copy()
    if original.pct_change(fill_method=None).abs().max() < 1:
        return precos
    # Retorno total com reinvestimento do rendimento na data ex. Base posterior
    # é preservada; a escala histórica anterior é ajustada para ligar os retornos.
    retornos = (oficiais.fechamento + oficiais.provento_ex) / oficiais.fechamento.shift(1)
    fator_total = retornos.iloc[1:].prod()
    base = original.iloc[-1] / fator_total
    fator = base / original.iloc[0]
    precos.loc[:dias[0], coluna] *= fator
    for i in range(1, len(dias)):
        precos.loc[dias[i], coluna] = precos.loc[dias[i-1], coluna] * retornos.iloc[i]
    precos.attrs["correcao_xpml"] = dict(fator_historico=float(fator),
        fonte="COTAHIST B3; rendimento de R$0,92 do relatório XP Malls janeiro/2026",
        metodo="Retornos oficiais na ponte 13–19/01/2026; reinvestimento na data ex; sem interpolação")
    return precos
