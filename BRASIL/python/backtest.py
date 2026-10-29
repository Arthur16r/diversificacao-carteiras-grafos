"""
Backtest das carteiras (buy-and-hold, sem rebalanceamento) no período
fora da amostra (2023-2026): CAGR, volatilidade anualizada, Sharpe (excesso
sobre o índice Selic), drawdown máximo, e métricas estruturais
(score geral, score intra-classe, número efetivo de ativos no fim).

Três blocos:
  1. Experimento principal (N = TAMANHO_PRINCIPAL): concentrada vs
     diversificada, mais variantes de comparação e carteiras aleatórias
     por nível de diversificação.
  2. Experimento "realista": concentrada N=10 vs diversificada N=20.
  3. Varredura de sensibilidade ao N (NS_VARREDURA): mostra se a conclusão
     depende do tamanho de carteira escolhido.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

from portfolio_metrics import (
    carregar_matriz_distancia,
    remover_classe,
    construir_carteira_gulosa,
    construir_carteira_gulosa_com_classes,
    construir_carteira_com_cotas,
    construir_carteira_por_classe,
    metrica_diversificacao,
    metrica_intra_classe,
    numero_efetivo_ativos,
    cotas_para_n,
    TAMANHO_PRINCIPAL,
    NS_VARREDURA,
    TAMANHO_REALISTA_DIVERSIFICADA,
    TETO_TESOURO_CONCENTRADA,
    COTAS_DIVERSIFICADA_PADRAO,
    COTAS_DIVERSIFICADA_REALISTA,
)

PRECOS_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"
NIVEIS_PATH = Path(__file__).parent.parent / "data" / "processed" / "carteiras_niveis.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "resultado_backtest.csv"
OUT_VARREDURA_PATH = Path(__file__).parent.parent / "data" / "processed" / "resultado_varredura_n.csv"

INICIO_TESTE = "2023-01-01"
FIM_TESTE = "2026-06-30"


def carregar_precos_periodo() -> pd.DataFrame:
    precos = pd.read_csv(PRECOS_PATH, index_col="data", parse_dates=True)
    return precos.sort_index().loc[INICIO_TESTE:FIM_TESTE]


def curva_valor_buy_and_hold(precos: pd.DataFrame, ativos: list[str]) -> pd.Series:
    sub = precos[ativos].dropna()
    normalizado = sub / sub.iloc[0]
    peso_inicial = 1.0 / len(ativos)
    return (normalizado * peso_inicial).sum(axis=1)


def pesos_finais_buy_and_hold(precos: pd.DataFrame, ativos: list[str]) -> dict[str, float]:
    sub = precos[ativos].dropna(how="any")
    relativos = sub.iloc[-1] / sub.iloc[0]
    return (relativos / relativos.sum()).to_dict()


def calcular_metricas(
    valor: pd.Series, retorno_livre_risco_anual: float, precos_referencia: pd.Series
) -> dict:
    """Sharpe dos excessos diários; medida antiga mantida separadamente.

    A referência deve cobrir todas as datas da carteira. Ambos os retornos
    usam os mesmos intervalos, sem preencher preços ou descartar ausências.
    """
    referencia = precos_referencia.reindex(valor.index)
    if referencia.isna().any() or (referencia <= 0).any():
        raise ValueError("Referência do Sharpe ausente ou inválida nas datas da carteira")
    anos = (valor.index[-1] - valor.index[0]).days / 365.25
    cagr = (valor.iloc[-1] / valor.iloc[0]) ** (1 / anos) - 1

    retornos_diarios = valor.pct_change(fill_method=None).iloc[1:]
    vol_anual = retornos_diarios.std() * np.sqrt(252)
    excessos = retornos_diarios - referencia.pct_change(fill_method=None).iloc[1:]
    desvio_excessos = excessos.std(ddof=1)
    sharpe = excessos.mean() / desvio_excessos * np.sqrt(252) if desvio_excessos > 0 else np.nan
    razao_cagr_excedente_vol = (
        (cagr - retorno_livre_risco_anual) / vol_anual if vol_anual > 0 else np.nan
    )
    max_drawdown = ((valor / valor.cummax()) - 1).min()

    return {
        "cagr": cagr,
        "vol_anual": vol_anual,
        "sharpe": sharpe,
        "razao_cagr_excedente_vol": razao_cagr_excedente_vol,
        "max_drawdown": max_drawdown,
        "inicio_efetivo": valor.index[0].date().isoformat(),
        "fim_efetivo": valor.index[-1].date().isoformat(),
        "observacoes": len(valor),
    }


def taxa_livre_risco(precos: pd.DataFrame) -> float:
    """CAGR do indice sintetico 'selic' (índice Selic) no periodo."""
    curto = precos["selic"].dropna()
    anos = (curto.index[-1] - curto.index[0]).days / 365.25
    return (curto.iloc[-1] / curto.iloc[0]) ** (1 / anos) - 1


def avaliar(precos, dist, ativos, grupo, carteira, nivel) -> dict:
    """Roda o backtest de uma carteira e anexa metadados e métricas estruturais."""
    valor = curva_valor_buy_and_hold(precos, ativos)
    rf = taxa_livre_risco(precos.loc[valor.index[0]:valor.index[-1]])
    m = calcular_metricas(valor, rf, precos["selic"])
    pesos = pesos_finais_buy_and_hold(precos, ativos)
    m.update({
        "experimento": "backtest_buy_and_hold",
        "grupo": grupo,
        "carteira": carteira,
        "nivel": nivel,
        "n_ativos": len(ativos),
        "taxa_livre_risco_anual": rf,
        "score_geral": metrica_diversificacao(dist, ativos),
        "score_intra_classe": metrica_intra_classe(dist, ativos),
        "n_efetivo_final": numero_efetivo_ativos(pesos),
        "ativos": ";".join(ativos),
        "pesos_finais": json.dumps(pesos, sort_keys=True),
    })
    return m


def imprimir(rotulo: str, m: dict, mostrar_ativos: bool = True):
    print(f"[{rotulo}] CAGR={m['cagr']:.2%}  vol={m['vol_anual']:.2%}  Sharpe={m['sharpe']:.2f}  "
          f"maxDD={m['max_drawdown']:.2%}  N_efetivo_final={m['n_efetivo_final']:.1f}  "
          f"score_geral={m['score_geral']:.3f}  score_intra={m['score_intra_classe']:.3f}")
    if mostrar_ativos:
        print(f"    ativos={m['ativos'].split(';')}")


def main():
    precos = carregar_precos_periodo()
    rf = taxa_livre_risco(precos)
    print(f"Período de teste: {precos.index.min().date()} a {precos.index.max().date()}")
    print(f"Taxa livre de risco (CAGR índice Selic no período): {rf:.2%}\n")

    dist_completa = carregar_matriz_distancia()
    dist = remover_classe(dist_completa, "exterior")
    N = TAMANHO_PRINCIPAL
    resultados = []

    # ---------- 1. experimento principal ----------
    print(f"=== Experimento principal (N={N}) ===")
    concentrada = construir_carteira_gulosa_com_classes(
        dist, N, "concentrada", tetos={"tesouro": TETO_TESOURO_CONCENTRADA})
    combinacoes = [
        ("original", "concentrada", construir_carteira_gulosa(dist, N, "concentrada")),
        ("original", "diversificada", construir_carteira_gulosa(dist, N, "diversificada")),
        ("classes", "concentrada", concentrada),
        ("cotas_global", "diversificada", construir_carteira_com_cotas(dist, COTAS_DIVERSIFICADA_PADRAO)),
        ("por_classe", "diversificada", construir_carteira_por_classe(dist, COTAS_DIVERSIFICADA_PADRAO)),
    ]
    for metodo, modo, ativos in combinacoes:
        m = avaliar(precos, dist, ativos, metodo, modo, f"referencia_{modo}_{metodo}")
        resultados.append(m)
        imprimir(f"{metodo}] [{modo}", m)

    df_niveis = pd.read_csv(NIVEIS_PATH)
    for _, linha in df_niveis.iterrows():
        ativos = linha["ativos"].split(";")
        if len(precos[ativos].dropna()) < 30:
            continue
        resultados.append(avaliar(precos, dist, ativos, "aleatoria", str(linha["nivel"]),
                                  f"nivel_{linha['nivel']}"))

    # ---------- 2. experimento realista ----------
    N2 = TAMANHO_REALISTA_DIVERSIFICADA
    print(f"\n=== Experimento realista (concentrada N={N} vs diversificada N={N2}, cotas {COTAS_DIVERSIFICADA_REALISTA}) ===")
    div_realista = construir_carteira_por_classe(dist_completa, COTAS_DIVERSIFICADA_REALISTA)
    m = avaliar(precos, dist_completa, div_realista, "realista", f"diversificada_N{N2}", f"realista_diversificada_N{N2}")
    resultados.append(m)
    imprimir(f"realista] [diversificada_N{N2}", m)
    print(f"    (a concentrada N={N} desse experimento é a mesma do bloco principal)")

    df_resultado = pd.DataFrame(resultados)
    inicio = ["experimento", "grupo", "carteira", "nivel", "n_ativos", "cagr", "vol_anual", "sharpe",
              "max_drawdown", "n_efetivo_final", "score_geral", "score_intra_classe",
              "taxa_livre_risco_anual", "inicio_efetivo", "fim_efetivo", "observacoes", "ativos", "pesos_finais"]
    resto = [c for c in df_resultado.columns if c not in inicio]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_resultado[inicio + resto].to_csv(OUT_PATH, index=False)
    print(f"\nResultados salvos em {OUT_PATH}")

    print("\n=== Média por nível (carteiras aleatórias) ===")
    resumo = (df_resultado[df_resultado["nivel"].str.startswith("nivel_")]
              .groupby("nivel")[["cagr", "vol_anual", "sharpe", "max_drawdown"]].mean())
    print(resumo)

    # ---------- 3. varredura de sensibilidade ao N ----------
    print("\n=== Varredura de sensibilidade ao N (concentrada vs diversificada por classe) ===")
    linhas = []
    for n in NS_VARREDURA:
        if n >= len(dist):
            continue
        conc = construir_carteira_gulosa_com_classes(
            dist, n, "concentrada", tetos={"tesouro": TETO_TESOURO_CONCENTRADA})
        div = construir_carteira_por_classe(dist, cotas_para_n(n))
        for nome, ativos in [("concentrada", conc), ("diversificada", div)]:
            m = avaliar(precos, dist, ativos, "varredura_n", nome, f"varredura_N{n}_{nome}")
            m["N"] = n
            linhas.append(m)

    df_v = pd.DataFrame(linhas)
    colunas = ["N", "carteira", "cagr", "vol_anual", "sharpe", "razao_cagr_excedente_vol", "max_drawdown",
               "n_efetivo_final", "score_geral", "score_intra_classe", "ativos", "pesos_finais"]
    OUT_VARREDURA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_v[colunas].to_csv(OUT_VARREDURA_PATH, index=False)

    print(f"{'N':>3} | {'conc vol':>8} {'div vol':>8} {'razão':>6} | {'conc Sharpe':>11} {'div Sharpe':>10} | "
          f"{'conc CAGR':>9} {'div CAGR':>8} | {'N_ef conc':>9} {'N_ef div':>8}")
    for n in sorted(df_v["N"].unique()):
        c = df_v[(df_v["N"] == n) & (df_v["carteira"] == "concentrada")].iloc[0]
        d = df_v[(df_v["N"] == n) & (df_v["carteira"] == "diversificada")].iloc[0]
        print(f"{n:>3} | {c['vol_anual']:>8.2%} {d['vol_anual']:>8.2%} {d['vol_anual'] / c['vol_anual']:>6.2f} | "
              f"{c['sharpe']:>11.2f} {d['sharpe']:>10.2f} | {c['cagr']:>9.2%} {d['cagr']:>8.2%} | "
              f"{c['n_efetivo_final']:>9.1f} {d['n_efetivo_final']:>8.1f}")
    print(f"\nVarredura salva em {OUT_VARREDURA_PATH}")


if __name__ == "__main__":
    main()
