"""
Mostra os preços do XPML11 numa janela ao redor da data suspeita, para
confirmar o problema e decidir como corrigir.
"""

import pandas as pd
from pathlib import Path

PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"


def main():
    df = pd.read_csv(PATH, index_col="data", parse_dates=True)
    janela = df.loc["2026-01-05":"2026-01-25", ["XPML11.SA"]]
    print(janela.to_string())


if __name__ == "__main__":
    main()
