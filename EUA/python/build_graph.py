"""
A partir de preços históricos, calcula:
  1. retornos diários
  2. matriz de correlação (PAIRWISE -- cada par usa so os dias em que
     AQUELE par tem dado, sem exigir que todos os ativos tenham dado no
     mesmo dia -- ver nota abaixo)
  3. matriz de distância: d_ij = sqrt(2 * (1 - rho_ij))

Usa só dados in-sample (1990-2010) para a construção da MST -- o
período de 2011-2026 é reservado para o backtest fora da amostra.
"""

import numpy as np
import pandas as pd
from pathlib import Path

PRECOS_FINAIS_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "distance_matrix.csv"

FIM_CONSTRUCAO = "2010-12-31"


def calcular_matriz_distancia(precos: pd.DataFrame) -> pd.DataFrame:
    # NAO usar .dropna() aqui: isso descartaria o dia INTEIRO (para
    # todos os ativos) se qualquer um deles tivesse um unico dado
    # faltando -- distorce a correlacao de todo mundo por causa de 1
    # ativo com mais "buracos" (ex: IPO tardio, like NVDA/GOOGL aqui).
    # O .corr() do pandas ja calcula cada par usando so os dias em que
    # AQUELE par especifico tem dado (pairwise), que e o correto.
    retornos = precos.pct_change(fill_method=None)
    corr = retornos.corr()
    dist = np.sqrt(2 * (1 - corr))
    return dist


def main():
    if not PRECOS_FINAIS_PATH.exists():
        raise FileNotFoundError(
            f"{PRECOS_FINAIS_PATH} não encontrado -- rode merge_sources.py primeiro"
        )

    print(f"Usando dados reais de {PRECOS_FINAIS_PATH} (in-sample até {FIM_CONSTRUCAO})")
    precos = pd.read_csv(PRECOS_FINAIS_PATH, index_col="data", parse_dates=True)
    precos = precos.loc[:FIM_CONSTRUCAO]

    dist = calcular_matriz_distancia(precos)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dist.to_csv(OUT_PATH)
    print(f"Matriz de distância salva em {OUT_PATH} ({dist.shape[0]} ativos)")


if __name__ == "__main__":
    main()
