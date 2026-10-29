"""
A partir de preços históricos, calcula:
  1. retornos diários
  2. matriz de correlação
  3. matriz de distância: d_ij = sqrt(2 * (1 - rho_ij))

Se existir data/processed/precos_final.csv (gerado pelo merge_sources.py
com dados reais), usa ele. Caso contrário, usa dados sintéticos de
exemplo só para testar o pipeline.
"""

import numpy as np
import pandas as pd
from pathlib import Path

PRECOS_FINAIS_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "distance_matrix.csv"

# a MST/matriz de correlacao deve ser construida SO com dados in-sample
# (2016-2022) -- o periodo depois disso e reservado para o backtest
# fora da amostra (ver INICIO_TESTE em backtest.py). Sem esse filtro, a
# matriz "vazava" informacao do periodo de teste.
FIM_CONSTRUCAO = "2022-12-31"


def gerar_precos_exemplo(n_dias=500, seed=42):
    rng = np.random.default_rng(seed)
    ativos = ["Banco", "FII_papel", "FII_tijolo", "Tesouro", "Acao_EUA"]
    n = len(ativos)
    retornos = rng.normal(0, 0.01, size=(n_dias, n))
    retornos[:, 1] -= 0.5 * retornos[:, 0]
    retornos[:, 2] += 0.3 * retornos[:, 0]
    precos = 100 * np.cumprod(1 + retornos, axis=0)
    return pd.DataFrame(precos, columns=ativos)


def calcular_matriz_distancia(precos: pd.DataFrame) -> pd.DataFrame:
    # NAO usar .dropna() aqui: isso descartaria o dia INTEIRO (para todos
    # os ativos) se qualquer um deles tivesse um unico dado faltando --
    # distorce a correlacao de todo mundo por causa de 1 ativo com mais
    # "buracos" (ex: um ETF com padrao de negociacao diferente). O
    # .corr() do pandas ja calcula cada par usando so os dias em que
    # AQUELE par especifico tem dado (pairwise), que e o correto aqui.
    retornos = precos.pct_change(fill_method=None)
    corr = retornos.corr()
    dist = np.sqrt(2 * (1 - corr))
    return dist


def main():
    if PRECOS_FINAIS_PATH.exists():
        print(f"Usando dados reais de {PRECOS_FINAIS_PATH} (in-sample até {FIM_CONSTRUCAO})")
        precos = pd.read_csv(PRECOS_FINAIS_PATH, index_col="data", parse_dates=True)
        precos = precos.loc[:FIM_CONSTRUCAO]
    else:
        print("precos_final.csv não encontrado -- usando dados de exemplo")
        precos = gerar_precos_exemplo()

    dist = calcular_matriz_distancia(precos)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dist.to_csv(OUT_PATH)
    # A comparação N=8 não admite exterior nem nos caminhos da MST global.
    from portfolio_metrics import remover_classe
    remover_classe(dist, "exterior").to_csv(OUT_PATH.parent / "distance_matrix_sem_exterior.csv")
    print(f"Matriz de distância salva em {OUT_PATH}")
    print(dist.round(3))


if __name__ == "__main__":
    main()
