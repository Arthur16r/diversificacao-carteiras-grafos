"""
Backtest das carteiras (buy-and-hold, sem rebalanceamento) no período
fora da amostra (2023-2026), calculando CAGR, volatilidade anualizada,
Sharpe (excesso sobre a Selic) e drawdown máximo.

Lê:
  - data/processed/precos_final.csv       (preços diários completos)
  - data/processed/carteiras_niveis.csv   (carteiras aleatórias já classificadas)
e recalcula as 2 carteiras de referência (guloso) com o mesmo N.
"""

import numpy as np
import pandas as pd
from pathlib import Path

from portfolio_metrics import (
    carregar_matriz_distancia,
    construir_carteira_gulosa,
    construir_carteira_gulosa_com_classes,
    construir_carteira_com_cotas,
    remover_classe,
    COTAS_DIVERSIFICADA_PADRAO,
    TAMANHO_CONCENTRADA_REALISTA,
    COTAS_DIVERSIFICADA_REALISTA,
    N_NIVEIS,
)

PRECOS_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"
NIVEIS_PATH = Path(__file__).parent.parent / "data" / "processed" / "carteiras_niveis.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "resultado_backtest.csv"

INICIO_TESTE = "2023-01-01"
FIM_TESTE = "2026-07-01"

TAMANHO_CARTEIRA = 8  # decidido: N=8


def carregar_precos_periodo() -> pd.DataFrame:
    precos = pd.read_csv(PRECOS_PATH, index_col="data", parse_dates=True)
    return precos.loc[INICIO_TESTE:FIM_TESTE]


def curva_valor_buy_and_hold(precos: pd.DataFrame, ativos: list[str]) -> pd.Series:
    """Valor da carteira ao longo do tempo, comprando pesos iguais no
    início e nunca rebalanceando (buy-and-hold)."""
    sub = precos[ativos].dropna()
    normalizado = sub / sub.iloc[0]
    peso_inicial = 1.0 / len(ativos)
    valor = (normalizado * peso_inicial).sum(axis=1)
    return valor


def calcular_metricas(valor: pd.Series, retorno_livre_risco_anual: float) -> dict:
    n_dias = len(valor)
    anos = n_dias / 252

    cagr = (valor.iloc[-1] / valor.iloc[0]) ** (1 / anos) - 1

    retornos_diarios = valor.pct_change().dropna()
    vol_anual = retornos_diarios.std() * np.sqrt(252)

    sharpe = (cagr - retorno_livre_risco_anual) / vol_anual if vol_anual > 0 else np.nan

    pico = valor.cummax()
    drawdown = (valor / pico) - 1
    max_drawdown = drawdown.min()

    return {
        "cagr": cagr,
        "vol_anual": vol_anual,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
    }


def taxa_livre_risco(precos: pd.DataFrame) -> float:
    """CAGR da Selic no período, usado como referência para o Sharpe."""
    selic = precos["selic"].dropna()
    anos = len(selic) / 252
    return (selic.iloc[-1] / selic.iloc[0]) ** (1 / anos) - 1


def main():
    precos = carregar_precos_periodo()
    rf = taxa_livre_risco(precos)
    print(f"Período de teste: {precos.index.min().date()} a {precos.index.max().date()}")
    print(f"Taxa livre de risco (CAGR Selic no período): {rf:.2%}\n")

    dist_completa = carregar_matriz_distancia()
    # experimento principal (N=8) NAO inclui a classe "exterior" -- o
    # IVVB11 so entra no experimento complementar N=18 (secao abaixo)
    dist = remover_classe(dist_completa, "exterior")

    # -- carteiras de referencia --
    # concentrada: garante minimo 1 por classe, resto livre (guloso puro)
    # diversificada: cotas fixas (3 acoes / 3 fiis / 2 tesouro)
    # tambem mantemos as versoes "originais" (sem nenhum controle de
    # classe) para comparacao, ja que documentam o resultado organico
    # do algoritmo antes da correcao
    resultados = []
    combinacoes = [
        ("original", "concentrada",
         construir_carteira_gulosa(dist, TAMANHO_CARTEIRA, "concentrada")),
        ("original", "diversificada",
         construir_carteira_gulosa(dist, TAMANHO_CARTEIRA, "diversificada")),
        ("corrigida", "concentrada",
         construir_carteira_gulosa_com_classes(dist, TAMANHO_CARTEIRA, "concentrada", tetos={"tesouro": 2})),
        ("corrigida", "diversificada",
         construir_carteira_com_cotas(dist, COTAS_DIVERSIFICADA_PADRAO)),
    ]
    for metodo_nome, modo, ativos in combinacoes:
        valor = curva_valor_buy_and_hold(precos, ativos)
        metricas = calcular_metricas(valor, rf)
        metricas["nivel"] = f"referencia_{modo}_{metodo_nome}"
        metricas["ativos"] = ";".join(ativos)
        resultados.append(metricas)
        print(f"[{metodo_nome}] {modo}: CAGR={metricas['cagr']:.2%}  "
              f"vol={metricas['vol_anual']:.2%}  Sharpe={metricas['sharpe']:.2f}  "
              f"maxDD={metricas['max_drawdown']:.2%}\n    ativos={ativos}")

    # -- carteiras aleatorias classificadas por nivel --
    df_niveis = pd.read_csv(NIVEIS_PATH)
    for _, linha in df_niveis.iterrows():
        ativos = linha["ativos"].split(";")
        valor = curva_valor_buy_and_hold(precos, ativos)
        if len(valor) < 30:  # protecao: ativo sem dado suficiente no periodo
            continue
        metricas = calcular_metricas(valor, rf)
        metricas["nivel"] = f"nivel_{linha['nivel']}"
        metricas["ativos"] = linha["ativos"]
        resultados.append(metricas)

    # -- experimento complementar "realista": tamanho variavel --
    # concentrada continua N=8, diversificada cresce para N=18 (mais
    # proxima de como um investidor real montaria as duas carteiras;
    # mistura efeito de N com efeito de correlacao, por isso e reportado
    # separado do experimento principal, nao substituindo ele)
    print("\n=== Experimento complementar: tamanho variavel "
          f"(concentrada N={TAMANHO_CONCENTRADA_REALISTA} vs diversificada N={sum(COTAS_DIVERSIFICADA_REALISTA.values())}) ===")
    concentrada_realista = construir_carteira_gulosa_com_classes(
        dist, TAMANHO_CONCENTRADA_REALISTA, "concentrada", tetos={"tesouro": 2}
    )
    diversificada_realista = construir_carteira_com_cotas(dist_completa, COTAS_DIVERSIFICADA_REALISTA)
    for nome, ativos in [("concentrada_N8", concentrada_realista),
                          ("diversificada_N18", diversificada_realista)]:
        valor = curva_valor_buy_and_hold(precos, ativos)
        metricas = calcular_metricas(valor, rf)
        metricas["nivel"] = f"realista_{nome}"
        metricas["ativos"] = ";".join(ativos)
        resultados.append(metricas)
        print(f"[realista] {nome}: CAGR={metricas['cagr']:.2%}  "
              f"vol={metricas['vol_anual']:.2%}  Sharpe={metricas['sharpe']:.2f}  "
              f"maxDD={metricas['max_drawdown']:.2%}\n    ativos={ativos}")

    df_resultado = pd.DataFrame(resultados)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_resultado.to_csv(OUT_PATH, index=False)
    print(f"\nResultados salvos em {OUT_PATH}")

    print("\n=== Média por nível (carteiras aleatórias) ===")
    resumo = (
        df_resultado[df_resultado["nivel"].str.startswith("nivel_")]
        .groupby("nivel")[["cagr", "vol_anual", "sharpe", "max_drawdown"]]
        .mean()
    )
    print(resumo)


if __name__ == "__main__":
    main()
