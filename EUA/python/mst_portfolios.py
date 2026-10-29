"""Seleciona a diversificada por caminhos na MST global produzida pelo C++.

Não executa backtest. A árvore é construída pelo Prim com a matriz in-sample;
a seleção reaproveita farthest-first por classe, com as mesmas cotas.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_graph import FIM_CONSTRUCAO
from portfolio_metrics import (
    COTAS_DIVERSIFICADA_PADRAO,
    DIST_PATH,
    OUT_DIR,
    classificar_tipo_ativo,
    construir_carteira_por_classe,
)

MST_PATH = Path(__file__).parent.parent / "cpp" / "mst_edges.csv"
DIST_MST_PATH = OUT_DIR / "distance_matrix_mst.csv"
CARTEIRAS_MST_PATH = OUT_DIR / "carteiras_mst.csv"


def calcular_distancias_mst(dist: pd.DataFrame, arestas: pd.DataFrame) -> pd.DataFrame:
    """Soma os pesos do caminho único entre todos os pares em O(V²).

    Os extremos vêm do Prim em C++. Usamos os pesos da matriz original,
    pois o CSV do C++ os exporta com precisão reduzida. Os caminhos podem
    atravessar ativos de qualquer classe. Não converte caminhos em correlação.
    """
    nomes = list(dist.index)
    if len(nomes) < 2 or nomes != list(dist.columns) or not dist.index.is_unique:
        raise ValueError("Matriz de origem com rótulos inválidos")
    if len(arestas) != len(nomes) - 1:
        raise ValueError("A MST deve conter V-1 arestas")
    adj = {a: [] for a in nomes}
    vistos = set()
    for de, para, peso_csv in arestas[["de", "para", "distancia"]].itertuples(index=False, name=None):
        if de not in adj or para not in adj or de == para:
            raise ValueError("Aresta com extremos inválidos")
        par = frozenset((de, para))
        if par in vistos:
            raise ValueError("Aresta duplicada")
        vistos.add(par)
        peso = float(dist.loc[de, para])
        if not np.isfinite(peso) or peso < 0 or not np.isclose(float(peso_csv), peso, rtol=6e-6, atol=6e-6):
            raise ValueError("Pesos incompatíveis: regenere a MST a partir da matriz atual")
        adj[de].append((para, peso))
        adj[para].append((de, peso))

    resultado = pd.DataFrame(0.0, index=dist.index, columns=dist.columns)
    for origem in nomes:
        visitados = set()
        pilha = [(origem, None, 0.0)]
        while pilha:
            atual, anterior, acumulado = pilha.pop()
            if atual in visitados:
                raise ValueError("As arestas contêm ciclo")
            visitados.add(atual)
            resultado.loc[origem, atual] = acumulado
            for vizinho, peso in adj[atual]:
                if vizinho != anterior:
                    pilha.append((vizinho, atual, acumulado + peso))
        if len(visitados) != len(nomes):
            raise ValueError("A árvore não conecta todos os ativos")
    return resultado


def selecionar_carteira_mst(dist_mst: pd.DataFrame, cotas: dict[str, int]) -> list[str]:
    """Mesma seleção por classe do grafo completo, com cotas exatas.

    Empates seguem a ordem dos ativos na matriz original, como no método atual.
    """
    for classe, cota in cotas.items():
        disponiveis = sum(classificar_tipo_ativo(a) == classe for a in dist_mst.index)
        if not isinstance(cota, int) or cota < 0 or cota > disponiveis:
            raise ValueError(f"Cota inválida para {classe}: {cota}")
    return construir_carteira_por_classe(dist_mst, cotas)


def main():
    dist = pd.read_csv(DIST_PATH, index_col=0)
    if not MST_PATH.exists():
        raise FileNotFoundError("mst_edges.csv ausente: execute make run em EUA/cpp primeiro")
    arestas = pd.read_csv(MST_PATH)
    dist_mst = calcular_distancias_mst(dist, arestas)
    ativos = selecionar_carteira_mst(dist_mst, COTAS_DIVERSIFICADA_PADRAO)
    registro = {
        "carteira": "diversificada_mst_N10",
        "metodo": "mst_caminhos_por_classe",
        "n_ativos": len(ativos),
        "cotas": json.dumps(COTAS_DIVERSIFICADA_PADRAO, sort_keys=True),
        "fim_construcao": FIM_CONSTRUCAO,
        "ativos": ";".join(ativos),
        "pesos_iniciais": json.dumps({a: 1 / len(ativos) for a in ativos}, sort_keys=True),
        "sha256_matriz_origem": hashlib.sha256(DIST_PATH.read_bytes()).hexdigest(),
        "sha256_arestas_mst": hashlib.sha256(MST_PATH.read_bytes()).hexdigest(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dist_mst.to_csv(DIST_MST_PATH)
    pd.DataFrame([registro]).to_csv(CARTEIRAS_MST_PATH, index=False)
    print(f"MST global: {len(dist)} ativos, {len(arestas)} arestas")
    print(f"Carteira diversificada por MST: {ativos}")
    print(f"Cotas: {COTAS_DIVERSIFICADA_PADRAO}; pesos iniciais iguais")
    print(f"Salvos: {DIST_MST_PATH.name} e {CARTEIRAS_MST_PATH.name}")


if __name__ == "__main__":
    main()
