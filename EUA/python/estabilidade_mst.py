"""Estabilidade de arestas: duas janelas fixas, mesmos ativos, Prim em C++.

Não altera a árvore principal nem utiliza o período de backtest. Cada execução
do C++ tem diretório próprio, pois ele escreve mst_edges.csv no diretório atual.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from build_graph import PRECOS_FINAIS_PATH, calcular_matriz_distancia
from mst_portfolios import calcular_distancias_mst
from portfolio_metrics import DIST_PATH, OUT_DIR, classificar_tipo_ativo

JANELAS = [("2003_2006", "2003-01-01", "2006-12-31"),
           ("2007_2010", "2007-01-01", "2010-12-31")]
SAIDA = OUT_DIR / "estabilidade_mst"
CPP_DIR = Path(__file__).resolve().parent.parent / "cpp"


def conjunto_arestas(arestas: pd.DataFrame) -> set[tuple[str, str]]:
    return {tuple(sorted((de, para))) for de, para in arestas[["de", "para"]].itertuples(index=False, name=None)}


def custo_kruskal(dist: pd.DataFrame) -> float:
    """Verificação independente do custo mínimo, em precisão original."""
    n = len(dist)
    pais = list(range(n))

    def raiz(i):
        while pais[i] != i:
            pais[i] = pais[pais[i]]
            i = pais[i]
        return i

    total = 0.0
    for peso, i, j in sorted((dist.iloc[i, j], i, j) for i in range(n) for j in range(i + 1, n)):
        a, b = raiz(i), raiz(j)
        if a != b:
            pais[a] = b
            total += peso
    return float(total)


def main(executavel: Path):
    executavel = executavel.resolve()
    if not executavel.is_file():
        raise FileNotFoundError("Compile mst.cpp primeiro (make em EUA/cpp)")
    precos = pd.read_csv(PRECOS_FINAIS_PATH, index_col="data", parse_dates=True).sort_index()
    ativos = list(pd.read_csv(DIST_PATH, index_col=0).index)
    arvores, matrizes, detalhes = {}, {}, []
    for nome, inicio, fim in JANELAS:
        sub = precos.loc[inicio:fim, ativos]
        if len(sub) < 2 or sub.isna().any().any():
            raise ValueError(f"Janela {nome} sem cobertura completa dos mesmos ativos")
        # O primeiro preço de cada janela é a base; nenhum retorno cruza a fronteira.
        retornos = sub.pct_change(fill_method=None).iloc[1:]
        contagens = retornos.notna().astype(int).T @ retornos.notna().astype(int)
        dist = calcular_matriz_distancia(sub)
        if not np.isfinite(dist.to_numpy()).all() or not np.allclose(dist, dist.T):
            raise ValueError(f"Matriz inválida em {nome}")
        pasta = SAIDA / nome
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / "distance_matrix.csv"
        dist.to_csv(caminho)
        processo = subprocess.run([str(executavel), str(caminho.resolve())], cwd=pasta,
                                  capture_output=True, text=True, check=True)
        (pasta / "prim_stdout.txt").write_text(processo.stdout, encoding="utf-8")
        arestas = pd.read_csv(pasta / "mst_edges.csv")
        calcular_distancias_mst(dist, arestas)  # V-1, conectividade, ciclos e pesos
        custo = sum(float(dist.loc[a, b]) for a, b in conjunto_arestas(arestas))
        independente = custo_kruskal(dist)
        if not np.isclose(custo, independente, rtol=1e-12, atol=1e-12):
            raise ValueError(f"Prim e Kruskal divergem em {nome}")
        arvores[nome] = conjunto_arestas(arestas)
        matrizes[nome] = dist
        detalhes.append({"janela": nome, "inicio_solicitado": inicio, "fim_solicitado": fim,
                         "inicio_efetivo": str(sub.index[0].date()), "fim_efetivo": str(sub.index[-1].date()),
                         "n_ativos": len(ativos), "n_precos": len(sub), "n_retornos": len(retornos),
                         "min_observacoes_par": int(contagens.to_numpy().min()),
                         "n_arestas": len(arestas), "custo_prim": custo, "custo_kruskal": independente})
    nome_a, nome_b = [j[0] for j in JANELAS]
    a, b = arvores[nome_a], arvores[nome_b]
    comuns = a & b
    linhas = []
    for de, para in sorted(a | b):
        linhas.append({"de": de, "para": para,
                       "classe_de": classificar_tipo_ativo(de), "classe_para": classificar_tipo_ativo(para),
                       "status": "preservada" if (de, para) in comuns else f"somente_{nome_a if (de, para) in a else nome_b}",
                       f"peso_{nome_a}": matrizes[nome_a].loc[de, para],
                       f"peso_{nome_b}": matrizes[nome_b].loc[de, para]})
    pd.DataFrame(linhas).to_csv(SAIDA / "comparacao_arestas.csv", index=False)
    pd.DataFrame(detalhes).to_csv(SAIDA / "janelas.csv", index=False)
    graus = []
    for ativo in ativos:
        graus.append({"ativo": ativo, "classe": classificar_tipo_ativo(ativo),
                      **{f"grau_{nome}": sum(ativo in par for par in arestas) for nome, arestas in arvores.items()}})
    pd.DataFrame(graus).to_csv(SAIDA / "graus.csv", index=False)
    resumo = {"janelas": JANELAS, "n_ativos": len(ativos), "arestas_por_arvore": len(a),
              "arestas_comuns": len(comuns), "arestas_substituidas_por_arvore": len(a - b),
              "fracao_preservada": len(comuns) / (len(ativos) - 1),
              "jaccard": len(comuns) / len(a | b),
              "sha256_precos": hashlib.sha256(PRECOS_FINAIS_PATH.read_bytes()).hexdigest(),
              "sha256_executavel": hashlib.sha256(executavel.read_bytes()).hexdigest(),
              "sha256_cpp": hashlib.sha256((CPP_DIR / "mst.cpp").read_bytes()).hexdigest(),
              "interpretacao": "Comparação descritiva de duas janelas; não mede estabilidade do desempenho nem significância estatística"}
    (SAIDA / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(pd.DataFrame(detalhes).to_string(index=False))
    print(f"Arestas preservadas: {len(comuns)}/{len(a)} ({100 * resumo['fracao_preservada']:.2f}%)")
    print(f"Jaccard: {resumo['jaccard']:.4f}; substituídas por árvore: {len(a - b)}")
    for nome in arvores:
        print(f"Maiores graus {nome}:")
        print(pd.DataFrame(graus).nlargest(6, f"grau_{nome}").to_string(index=False))
    print(f"Resultados em {SAIDA}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--executavel", type=Path, default=CPP_DIR / ("mst.exe" if (CPP_DIR / "mst.exe").exists() else "mst"))
    main(parser.parse_args().executavel)
