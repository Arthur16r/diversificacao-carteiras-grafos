"""Sensibilidade à construção em 2003–2010, mantendo o backtest original."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from backtest import avaliar, carregar_precos_periodo, curva_valor_buy_and_hold
from build_graph import PRECOS_FINAIS_PATH, calcular_matriz_distancia
from estabilidade_mst import CPP_DIR, conjunto_arestas, custo_kruskal
from mst_portfolios import MST_PATH, calcular_distancias_mst, selecionar_carteira_mst
from portfolio_metrics import COTAS_DIVERSIFICADA_PADRAO, DIST_PATH, OUT_DIR, construir_carteira_por_classe

SAIDA = OUT_DIR / "robustez_janela_comum"


def main(executavel):
    executavel = executavel.resolve()
    # Guardamos os hashes dos resultados principais para verificar preservação.
    protegidos = [DIST_PATH, MST_PATH, OUT_DIR / "resultado_backtest_mst.csv"]
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protegidos}
    original = pd.read_csv(DIST_PATH, index_col=0)
    precos = pd.read_csv(PRECOS_FINAIS_PATH, index_col="data", parse_dates=True).sort_index()
    sub = precos.loc["2003-01-01":"2010-12-31", original.index]
    if sub.isna().any().any():
        raise ValueError("A janela comum deve ter cobertura completa dos 74 ativos")
    dist = calcular_matriz_distancia(sub)
    if not np.isfinite(dist.to_numpy()).all():
        raise ValueError("Matriz com valores inválidos")
    SAIDA.mkdir(parents=True, exist_ok=True)
    entrada = SAIDA / "distance_matrix.csv"
    dist.to_csv(entrada)
    processo = subprocess.run([str(executavel), str(entrada.resolve())], cwd=SAIDA,
                              check=True, text=True, capture_output=True)
    (SAIDA / "prim_stdout.txt").write_text(processo.stdout, encoding="utf-8")
    arestas = pd.read_csv(SAIDA / "mst_edges.csv")
    caminhos = calcular_distancias_mst(dist, arestas)
    custo = sum(dist.loc[a, b] for a, b in conjunto_arestas(arestas))
    if not np.isclose(custo, custo_kruskal(dist), rtol=1e-12, atol=1e-12):
        raise ValueError("Custo da MST diverge de Kruskal")
    caminhos.to_csv(SAIDA / "distance_matrix_mst.csv")
    dist_orig_mst = calcular_distancias_mst(original, pd.read_csv(MST_PATH))
    teste = carregar_precos_periodo()
    linhas, curvas, selecoes = [], {}, []
    for janela, matriz, arvore in [("principal_1990_2010", original, dist_orig_mst),
                                    ("comum_2003_2010", dist, caminhos)]:
        for metodo, ativos in [
            ("grafo_completo", construir_carteira_por_classe(matriz, COTAS_DIVERSIFICADA_PADRAO)),
            ("mst", selecionar_carteira_mst(arvore, COTAS_DIVERSIFICADA_PADRAO)),
        ]:
            nome = f"{janela}_{metodo}"
            curva = curva_valor_buy_and_hold(teste, ativos)
            if len(curva) != len(teste):
                raise ValueError("Backtest perdeu pregões")
            curvas[nome] = curva
            m = avaliar(teste, matriz, ativos, janela, metodo, nome)
            m["multiplicador_final"] = curva.iloc[-1]
            # Scores são específicos de cada matriz de construção, não da mesma régua.
            m["janela_construcao"] = janela
            linhas.append(m)
            selecoes.append(dict(janela=janela, metodo=metodo, ativos=";".join(ativos),
                                  cotas=json.dumps(COTAS_DIVERSIFICADA_PADRAO)))
    df = pd.DataFrame(linhas)
    df.to_csv(SAIDA / "comparacao_backtest.csv", index=False)
    pd.DataFrame(curvas).rename_axis("data").to_csv(SAIDA / "curvas.csv")
    pd.DataFrame(selecoes).to_csv(SAIDA / "carteiras.csv", index=False)
    comuns = len(conjunto_arestas(arestas) & conjunto_arestas(pd.read_csv(MST_PATH)))
    metadata = dict(inicio_construcao=str(sub.index[0].date()), fim_construcao=str(sub.index[-1].date()),
                    n_precos_construcao=len(sub), retornos_por_par=len(sub) - 1,
                    n_ativos=len(dist), n_arestas=len(arestas), arestas_comuns_principal=comuns,
                    inicio_teste=str(teste.index[0].date()), fim_teste=str(teste.index[-1].date()),
                    cotas=COTAS_DIVERSIFICADA_PADRAO, custo_mst=float(custo),
                    sha256_precos=hashlib.sha256(PRECOS_FINAIS_PATH.read_bytes()).hexdigest(),
                    sha256_matriz_principal=hashes[DIST_PATH],
                    interpretacao="Sensibilidade à janela de construção; mesmo período de teste, sem validação temporal independente")
    (SAIDA / "experimento.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    for p, hash_antes in hashes.items():
        if hashlib.sha256(p.read_bytes()).hexdigest() != hash_antes:
            raise RuntimeError(f"Arquivo principal alterado: {p}")
    print(df[["janela_construcao", "carteira", "cagr", "vol_anual", "sharpe", "max_drawdown", "multiplicador_final", "ativos"]].to_string(index=False))
    print(f"Construção: {len(sub)-1} retornos por par; arestas comuns: {comuns}/73")
    print("Resultados principais preservados; saídas em", SAIDA)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--executavel", type=Path, default=CPP_DIR / ("mst.exe" if (CPP_DIR / "mst.exe").exists() else "mst"))
    main(parser.parse_args().executavel)
