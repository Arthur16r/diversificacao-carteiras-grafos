"""Referência aleatória com N e cotas iguais; Sharpe é o critério principal.

Percentuais são posições descritivas numa amostra de carteiras, não p-valores
de superioridade geral: todas compartilham o mesmo histórico e muitos ativos.
"""
import hashlib
import json

import numpy as np
import pandas as pd

from backtest import avaliar, carregar_precos_periodo
from mst_portfolios import CARTEIRAS_MST_PATH, DIST_PATH, MST_PATH
from portfolio_metrics import (
    COTAS_DIVERSIFICADA_PADRAO, OUT_DIR, construir_carteira_por_classe, remover_classe,
    gerar_carteiras_aleatorias_com_cotas,
)

N_CARTEIRAS = 5000
SEED = 42


def main():
    registro = pd.read_csv(CARTEIRAS_MST_PATH).iloc[0]
    for caminho, coluna in [(DIST_PATH, "sha256_matriz_origem"), (MST_PATH, "sha256_arestas_mst")]:
        if hashlib.sha256(caminho.read_bytes()).hexdigest() != registro[coluna]:
            raise ValueError("Carteira MST desatualizada; regenere antes de comparar")
    dist = remover_classe(pd.read_csv(DIST_PATH, index_col=0), "exterior")
    precos = carregar_precos_periodo()
    # Mesmas datas para todos: não aceita descartar pregões de carteiras específicas.
    if precos[dist.index].isna().any().any():
        raise ValueError("Há preços ausentes no período de comparação")
    carteiras = gerar_carteiras_aleatorias_com_cotas(dist, COTAS_DIVERSIFICADA_PADRAO, N_CARTEIRAS, SEED)
    linhas = []
    for i, ativos in enumerate(carteiras):
        m = avaliar(precos, dist, ativos, "aleatoria_cotas", f"aleatoria_{i:04d}", "cotas_3_3_2")
        m["seed"] = SEED
        linhas.append(m)
        if (i + 1) % 1000 == 0:
            print(f"Avaliadas {i + 1}/{N_CARTEIRAS} carteiras", flush=True)
    aleatorias = pd.DataFrame(linhas)
    referencias = {
        "diversificada_mst": registro["ativos"].split(";"),
        "diversificada_grafo_completo": construir_carteira_por_classe(dist, COTAS_DIVERSIFICADA_PADRAO),
    }
    resultados_ref, resumo = [], []
    for nome, ativos in referencias.items():
        m = avaliar(precos, dist, ativos, "referencia_cotas", nome, "cotas_3_3_2")
        resultados_ref.append(m)
        for metrica in ["sharpe", "cagr", "vol_anual", "max_drawdown"]:
            valores = aleatorias[metrica].to_numpy()
            if not np.isfinite(valores).all() or not np.isfinite(m[metrica]):
                raise ValueError(f"Métrica não finita: {metrica}")
            # Drawdown menos negativo é melhor; só volatilidade é menor=melhor.
            diferencas = valores - m[metrica] if metrica == "vol_anual" else m[metrica] - valores
            inferiores = int((diferencas > 1e-12).sum())
            superiores = int((diferencas < -1e-12).sum())
            resumo.append({
                "carteira": nome, "metrica": metrica, "criterio_principal": metrica == "sharpe",
                "valor_referencia": m[metrica], "n_aleatorias": N_CARTEIRAS,
                "n_superadas": inferiores, "n_superiores": superiores,
                "n_empates": N_CARTEIRAS - inferiores - superiores,
                "percentual_superadas": 100 * inferiores / N_CARTEIRAS,
                "mediana_aleatorias": float(np.median(valores)),
                "q05_aleatorias": float(np.quantile(valores, .05)),
                "q95_aleatorias": float(np.quantile(valores, .95)),
            })
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    aleatorias.to_csv(OUT_DIR / "resultado_aleatorias_cotas.csv", index=False)
    pd.DataFrame(resultados_ref).to_csv(OUT_DIR / "referencias_aleatorias_cotas.csv", index=False)
    comparacao = pd.DataFrame(resumo)
    comparacao.to_csv(OUT_DIR / "comparacao_aleatorias_mst.csv", index=False)
    metadata = {
        "n_carteiras": N_CARTEIRAS, "seed": SEED, "cotas": COTAS_DIVERSIFICADA_PADRAO,
        "criterio_principal": "sharpe", "pesos_iniciais": "iguais", "rebalanceamento": False,
        "inicio_efetivo": linhas[0]["inicio_efetivo"], "fim_efetivo": linhas[0]["fim_efetivo"],
        "sha256_matriz": registro["sha256_matriz_origem"],
        "sha256_precos": hashlib.sha256((OUT_DIR / "precos_final.csv").read_bytes()).hexdigest(),
        "interpretacao": "Comparação descritiva de carteiras na mesma janela; não são testes temporais independentes",
    }
    (OUT_DIR / "experimento_aleatorias_cotas.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(comparacao.to_string(index=False))


if __name__ == "__main__":
    main()
