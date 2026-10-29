"""
Procura dias com retorno diário suspeito em TODO o histórico (construção
1990-2010 e teste 2011-2026), porque aqui o risco de dado quebrado
(desdobramento mal ajustado, fusão, ticker reaproveitado) existe nas
duas janelas -- diferente do Brasil, onde só conferimos o período de teste.

Limites:
  - ações/REITs: |retorno diário| > 25% (acima disso, só evento raro real
    ou erro de dado -- conferir caso a caso)
  - Treasury (índice sintético): |retorno diário| > 3%

Também mostra a primeira data com dado de cada ativo, para identificar
histórico parcial.
"""

import pandas as pd
from pathlib import Path

PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"

LIMITE_ACAO_REIT = 0.25
LIMITE_TESOURO = 0.03


def main():
    df = pd.read_csv(PATH, index_col="data", parse_dates=True)
    retornos = df.pct_change(fill_method=None)

    print("=== Saltos suspeitos ===")
    achou = False
    for ativo in retornos.columns:
        limite = LIMITE_TESOURO if ativo.startswith("tesouro_") else LIMITE_ACAO_REIT
        suspeitos = retornos[ativo][retornos[ativo].abs() > limite].dropna()
        if not suspeitos.empty:
            achou = True
            print(f"\n{ativo}: {len(suspeitos)} dia(s) acima de {limite:.0%}")
            print(suspeitos.sort_values(key=abs, ascending=False).head(5).to_string())
    if not achou:
        print("Nenhum salto acima dos limites.")

    print("\n=== Início do histórico de cada ativo (depois de 1992) ===")
    for ativo in df.columns:
        primeiro = df[ativo].first_valid_index()
        if primeiro is not None and primeiro.year > 1992:
            print(f"{ativo}: {primeiro.date()}")


if __name__ == "__main__":
    main()
