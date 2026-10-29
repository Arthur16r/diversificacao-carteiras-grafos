"""Comparação fora da amostra: MST, grafo completo e concentrada de referência."""
import hashlib

import pandas as pd

from backtest import avaliar, carregar_precos_periodo, curva_valor_buy_and_hold
from mst_portfolios import CARTEIRAS_MST_PATH, DIST_PATH, MST_PATH
from portfolio_metrics import (
    COTAS_DIVERSIFICADA_PADRAO,
    OUT_DIR,
    remover_classe,
    TAMANHO_PRINCIPAL,
    TETO_TESOURO_CONCENTRADA,
    construir_carteira_gulosa_com_classes,
    construir_carteira_por_classe,
)


def main():
    registro = pd.read_csv(CARTEIRAS_MST_PATH).iloc[0]
    for caminho, coluna in [(DIST_PATH, "sha256_matriz_origem"), (MST_PATH, "sha256_arestas_mst")]:
        if hashlib.sha256(caminho.read_bytes()).hexdigest() != registro[coluna]:
            raise ValueError("Carteira MST desatualizada: regenere a árvore e mst_portfolios.py")
    precos = carregar_precos_periodo()
    dist = remover_classe(pd.read_csv(DIST_PATH, index_col=0), "exterior")
    carteiras = {
        "diversificada_mst": registro["ativos"].split(";"),
        "diversificada_grafo_completo": construir_carteira_por_classe(dist, COTAS_DIVERSIFICADA_PADRAO),
        "concentrada_referencia": construir_carteira_gulosa_com_classes(
            dist, TAMANHO_PRINCIPAL, "concentrada", tetos={"tesouro": TETO_TESOURO_CONCENTRADA}),
    }
    curvas = {nome: curva_valor_buy_and_hold(precos, ativos) for nome, ativos in carteiras.items()}
    primeira = next(iter(curvas.values())).index
    if any(not curva.index.equals(primeira) for curva in curvas.values()):
        raise ValueError("As carteiras não possuem as mesmas datas de avaliação")
    resultados = []
    for nome, ativos in carteiras.items():
        # Todos os scores usam a matriz ORIGINAL: caminhos da MST não são correlações.
        m = avaliar(precos, dist, ativos, "comparacao_mst", nome, nome)
        m["multiplicador_final"] = curvas[nome].iloc[-1]
        resultados.append(m)
    df = pd.DataFrame(resultados)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "resultado_backtest_mst.csv", index=False)
    pd.DataFrame(curvas).rename_axis("data").to_csv(OUT_DIR / "curvas_backtest_mst.csv")
    print(df[["carteira", "cagr", "vol_anual", "sharpe", "max_drawdown", "score_geral",
              "score_intra_classe", "n_efetivo_final", "multiplicador_final"]].to_string(index=False))
    print(f"Período comum: {primeira[0].date()} a {primeira[-1].date()}, {len(primeira)} preços")
    mst, grafo = map(set, [carteiras["diversificada_mst"], carteiras["diversificada_grafo_completo"]])
    print("Ativos em comum:", sorted(mst & grafo))
    print("Entram na MST:", sorted(mst - grafo))
    print("Saem do grafo completo:", sorted(grafo - mst))
    for nome, ativos in carteiras.items():
        retornos = precos[ativos].iloc[-1] / precos[ativos].iloc[0]
        contribuicoes = ((retornos - 1) / len(ativos)).sort_values(ascending=False)
        print(f"Contribuição ao ganho acumulado (por ativo), {nome}:")
        print(contribuicoes.to_string())


if __name__ == "__main__":
    main()
