"""
Confere se existem pares de ativos com correlação negativa real no pool,
olhando a matriz de distância completa (distância > sqrt(2) implica
correlação negativa, já que d = sqrt(2*(1-rho))).
"""

import pandas as pd
from pathlib import Path

DIST_PATH = Path(__file__).parent.parent / "data" / "processed" / "distance_matrix.csv"


def main():
    dist = pd.read_csv(DIST_PATH, index_col=0)

    pares = []
    for i in dist.index:
        for j in dist.columns:
            if i < j:  # evita duplicar par e a diagonal
                pares.append((i, j, dist.loc[i, j]))

    pares.sort(key=lambda x: -x[2])

    print("Top 10 pares mais distantes (potencialmente correlação negativa):")
    for a, b, d in pares[:10]:
        rho = 1 - (d ** 2) / 2
        print(f"{a} -- {b}: distancia={d:.3f}, correlacao={rho:.3f}")

    negativos = [(a, b, d) for a, b, d in pares if (1 - (d ** 2) / 2) < 0]
    print(f"\nTotal de pares com correlação negativa: {len(negativos)} de {len(pares)}")


if __name__ == "__main__":
    main()
