"""Exporta grafo completo e complemento da MST, sem alterar entradas ou layout."""

import csv
import hashlib
import json
import math
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
PASTA = Path(__file__).resolve().parent / "gephi" / "EUA"


def main():
    matriz_path = RAIZ / "EUA/data/processed/distance_matrix.csv"
    mst_path = RAIZ / "EUA/cpp/mst_edges.csv"
    with matriz_path.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.reader(f))
    nomes = linhas[0][1:]
    if len(nomes) != 74 or len(set(nomes)) != 74 or [l[0] for l in linhas[1:]] != nomes:
        raise ValueError("Esperada matriz dos 74 ativos dos EUA com rótulos alinhados")
    if any(len(l) != 75 for l in linhas):
        raise ValueError("Matriz não quadrada")
    matriz = [list(map(float, l[1:])) for l in linhas[1:]]
    with mst_path.open(encoding="utf-8-sig", newline="") as f:
        mst = list(csv.DictReader(f))
    indice = {n: i for i, n in enumerate(nomes)}
    pares_mst, adj = set(), {n: set() for n in nomes}
    for e in mst:
        a, b = e["de"], e["para"]
        par = frozenset((a, b))
        if a not in indice or b not in indice or a == b or par in pares_mst:
            raise ValueError("Aresta inválida na MST")
        if not math.isclose(float(e["distancia"]), matriz[indice[a]][indice[b]], rel_tol=6e-6, abs_tol=6e-6):
            raise ValueError("MST incompatível com a matriz atual")
        pares_mst.add(par)
        adj[a].add(b)
        adj[b].add(a)
    visitados, pilha = set(), [nomes[0]]
    while pilha:
        n = pilha.pop()
        if n not in visitados:
            visitados.add(n)
            pilha.extend(adj[n] - visitados)
    if len(pares_mst) != 73 or len(visitados) != 74:
        raise ValueError("MST não é uma árvore abrangente de 74 ativos")
    completas, adicionais = [], []
    for i, a in enumerate(nomes):
        for j, b in enumerate(nomes):
            d = matriz[i][j]
            if not math.isfinite(d) or not 0 <= d <= 2 or not math.isclose(d, matriz[j][i], abs_tol=1e-12):
                raise ValueError("Distância inválida ou matriz assimétrica")
            if i == j and abs(d) > 1e-12:
                raise ValueError("Diagonal não nula")
            if j <= i:
                continue
            linha = (a, b, "Undirected", 1, d, 1-d*d/2)
            completas.append(linha)
            if frozenset((a, b)) not in pares_mst:
                adicionais.append(linha)
    if len(completas) != 2701 or len(adicionais) != 2628:
        raise ValueError("Contagem de arestas inesperada")
    PASTA.mkdir(parents=True, exist_ok=True)
    for nome, arestas in (("arestas_grafo_completo.csv", completas),
                           ("arestas_adicionais_para_completar_mst.csv", adicionais)):
        with (PASTA / nome).open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("Source", "Target", "Type", "Weight", "Distancia", "Correlacao"))
            writer.writerows(arestas)
        print(f"{nome}: {len(arestas)} arestas")
    (PASTA / "grafo_completo_procedencia.json").write_text(json.dumps({
        "vertices": 74, "arestas_completo": 2701, "arestas_mst": 73,
        "arestas_adicionais": 2628,
        "sha256_matriz": hashlib.sha256(matriz_path.read_bytes()).hexdigest(),
        "sha256_mst": hashlib.sha256(mst_path.read_bytes()).hexdigest(),
        "peso_visual": 1,
        "observacao": "Correlacao = 1 - Distancia²/2; sem filtro. Layout não é recalculado."
    }, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
