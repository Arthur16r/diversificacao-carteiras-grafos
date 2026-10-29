"""
Junta as fontes de dados (ações/REITs + Tesouro americano via FRED) numa
única tabela de preços/índices alinhada por data.
"""

import numpy as np
import pandas as pd
from pathlib import Path

ACOES_REITS_PATH = Path(__file__).parent.parent / "data" / "raw" / "precos_acoes_reits.csv"
TESOURO_PATH = Path(__file__).parent.parent / "data" / "raw" / "tesouro_retornos.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"

# Regras de limpeza documentadas: ativos cujo historico ANTES de uma data
# pertence a outro negocio (nao e a mesma serie economica) e deve ser
# descartado. Cada entrada precisa de justificativa verificavel.
#   VTR: ate 30/04/1998 o ticker era a Vencor Inc., operadora de hospitais e
#        casas de repouso. Em 01/05/1998 ela virou a Ventas (REIT de saude) e
#        as operacoes foram para uma empresa nova (SEC Form 8-K, 30/04/1998).
LIMPEZAS_INICIO = {
    "VTR": "1998-05-01",
}


def juntar_fontes() -> pd.DataFrame:
    acoes_reits = pd.read_csv(ACOES_REITS_PATH, index_col="data", parse_dates=True)
    tesouro = pd.read_csv(TESOURO_PATH, index_col="data", parse_dates=True)

    # calendario de referencia = dias de pregao americanos (indice de
    # acoes/REITs), que e o mais restrito dos dois (FRED publica taxa em
    # mais dias uteis, incluindo alguns que a bolsa nao abre)
    calendario = acoes_reits.index
    tesouro_alinhado = tesouro.reindex(calendario, method="ffill")

    precos = pd.concat([acoes_reits, tesouro_alinhado], axis=1)
    precos.index.name = "data"

    for ticker, data_inicio in LIMPEZAS_INICIO.items():
        if ticker in precos.columns:
            n = int((precos.index < data_inicio).sum() - precos.loc[precos.index < data_inicio, ticker].isna().sum())
            precos.loc[precos.index < data_inicio, ticker] = np.nan
            print(f"Limpeza: {ticker} descartado antes de {data_inicio} ({n} dias removidos)")
    return precos


def main():
    precos = juntar_fontes()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    precos.to_csv(OUT_PATH)
    print(f"Tabela final salva em {OUT_PATH}")
    print(f"{precos.shape[0]} dias, {precos.shape[1]} ativos")

    faltando = precos.isna().sum()
    faltando = faltando[faltando > 0].sort_values(ascending=False)
    if not faltando.empty:
        print("\nAtivos com dados faltando em algum trecho do período:")
        print(faltando)


if __name__ == "__main__":
    main()
