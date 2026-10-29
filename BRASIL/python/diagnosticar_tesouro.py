"""
Diagnóstico: procura dias com retorno diário suspeito (>5% ou <-5%) em
cada série de Tesouro -- isso não deveria acontecer nunca, já que
Tesouro tem baixíssima volatilidade diária. Se aparecer algo aqui, ainda
tem salto de preço não resolvido.
"""

import pandas as pd
from pathlib import Path

PATH = Path(__file__).parent.parent / "data" / "raw" / "tesouro_series_rolling.csv"


def main():
    df = pd.read_csv(PATH, index_col="data", parse_dates=True)
    retornos = df.pct_change()

    LIMITE = 0.03  # 3% num dia so ja e MUITO pra tesouro

    for serie in retornos.columns:
        suspeitos = retornos[serie][retornos[serie].abs() > LIMITE].dropna()
        if not suspeitos.empty:
            print(f"\n=== {serie}: {len(suspeitos)} dia(s) suspeito(s) ===")
            print(suspeitos.sort_values(key=abs, ascending=False).head(10))
        else:
            print(f"{serie}: ok, nenhum salto > {LIMITE:.0%}")


if __name__ == "__main__":
    main()
