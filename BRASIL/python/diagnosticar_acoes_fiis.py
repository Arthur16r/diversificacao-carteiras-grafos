"""
Procura dias com retorno diário suspeito (>15% ou <-15%) em ações/FIIs,
dentro do período do backtest (2023-2026) -- ajuda a achar dado ruim do
yfinance (ex: ajuste de proventos errado, ticker trocado sem migrar
histórico, etc.)
"""

import pandas as pd
from pathlib import Path

PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"

INICIO = "2023-01-01"
FIM = "2026-07-01"
LIMITE = 0.15  # 15% num dia e MUITO pra acao/FII normal


def main():
    df = pd.read_csv(PATH, index_col="data", parse_dates=True)
    df = df.loc[INICIO:FIM]
    retornos = df.pct_change()

    for ativo in retornos.columns:
        suspeitos = retornos[ativo][retornos[ativo].abs() > LIMITE].dropna()
        if not suspeitos.empty:
            print(f"\n=== {ativo}: {len(suspeitos)} dia(s) suspeito(s) ===")
            print(suspeitos.sort_values(key=abs, ascending=False).head(10))


if __name__ == "__main__":
    main()
