"""Variante da varredura com IVVB11 para N>8; preserva a varredura original."""
import json

import pandas as pd

from backtest import avaliar, carregar_precos_periodo
from portfolio_metrics import (
    carregar_matriz_distancia, remover_classe, cotas_para_n, NS_VARREDURA, OUT_DIR,
    construir_carteira_por_classe, construir_carteira_gulosa_com_classes,
)


def cotas_com_exterior(n):
    cotas = cotas_para_n(n)
    if n > 8:
        cotas["acao"] -= 1
        cotas["exterior"] = 1
    return cotas


def main():
    completa = carregar_matriz_distancia()
    domestica = remover_classe(completa, "exterior")
    precos = carregar_precos_periodo()
    linhas = []
    for n in NS_VARREDURA:
        conc = construir_carteira_gulosa_com_classes(domestica, n, "concentrada", tetos={"tesouro": 2})
        combinacoes = [("concentrada", "sem_exterior", domestica, conc, None)]
        for exterior in [False, True] if n > 8 else [False]:
            matriz = completa if exterior else domestica
            cotas = cotas_com_exterior(n) if exterior else cotas_para_n(n)
            ativos = construir_carteira_por_classe(matriz, cotas)
            combinacoes.append(("diversificada", "com_exterior" if exterior else "sem_exterior", matriz, ativos, cotas))
        for carteira, variante, matriz, ativos, cotas in combinacoes:
            m = avaliar(precos, matriz, ativos, "varredura_exterior", carteira, f"N{n}_{variante}")
            m.update(N=n, variante=variante, cotas=json.dumps(cotas, sort_keys=True))
            linhas.append(m)
    df = pd.DataFrame(linhas)
    df.to_csv(OUT_DIR / "resultado_varredura_exterior.csv", index=False)
    print(df[["N", "carteira", "variante", "cagr", "vol_anual", "sharpe", "max_drawdown"]].to_string(index=False))


if __name__ == "__main__":
    main()
