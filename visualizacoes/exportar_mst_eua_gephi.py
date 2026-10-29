"""Exporta a MST existente dos EUA para CSVs do Gephi (somente stdlib)."""

import ast
import csv
import hashlib
import math
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent


def main():
    dados = RAIZ / "EUA" / "data" / "processed"
    matriz_path = dados / "distance_matrix.csv"
    arestas_path = RAIZ / "EUA" / "cpp" / "mst_edges.csv"
    with matriz_path.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.reader(arquivo))
    nomes = linhas[0][1:]
    if [linha[0] for linha in linhas[1:]] != nomes or len(set(nomes)) != len(nomes):
        raise ValueError("Rótulos incompatíveis na matriz")
    matriz = {linha[0]: dict(zip(nomes, map(float, linha[1:]))) for linha in linhas[1:]}
    with arestas_path.open(encoding="utf-8-sig", newline="") as arquivo:
        arestas = list(csv.DictReader(arquivo))
    with (dados / "carteiras_mst.csv").open(encoding="utf-8-sig", newline="") as arquivo:
        carteiras = list(csv.DictReader(arquivo))
    if len(carteiras) != 1:
        raise ValueError("Esperada uma carteira MST de referência")
    carteira = carteiras[0]
    for campo, caminho in (("sha256_matriz_origem", matriz_path), ("sha256_arestas_mst", arestas_path)):
        if carteira[campo] != hashlib.sha256(caminho.read_bytes()).hexdigest():
            raise ValueError("Carteira desatualizada: regenere mst_portfolios.py antes da exportação")
    selecionados = set(carteira["ativos"].split(";"))
    classes = {}
    fonte = ast.parse((RAIZ / "EUA" / "python" / "portfolio_metrics.py").read_text(encoding="utf-8-sig"))
    grupos = {"ACOES": "Acao", "REITS": "REIT", "TESOURO_USA": "Treasury"}
    for comando in fonte.body:
        if isinstance(comando, ast.Assign):
            for alvo in comando.targets:
                if isinstance(alvo, ast.Name) and alvo.id in grupos:
                    for ativo in ast.literal_eval(comando.value):
                        classes[ativo] = grupos[alvo.id]
    adj = {nome: set() for nome in nomes}
    exportadas = []
    for aresta in arestas:
        a, b = aresta["de"], aresta["para"]
        if a not in adj or b not in adj or a == b or b in adj[a]:
            raise ValueError("Aresta inválida ou duplicada")
        peso = matriz[a][b]
        if not math.isfinite(peso) or not math.isclose(peso, float(aresta["distancia"]), rel_tol=6e-6, abs_tol=6e-6):
            raise ValueError("MST incompatível com a matriz")
        adj[a].add(b)
        adj[b].add(a)
        # Peso visual constante: a distância não representa força de atração.
        exportadas.append((a, b, "Undirected", 1, peso))
    vistos, pilha = set(), [nomes[0]]
    while pilha:
        atual = pilha.pop()
        if atual not in vistos:
            vistos.add(atual)
            pilha.extend(adj[atual] - vistos)
    if len(arestas) != len(nomes)-1 or vistos != set(nomes):
        raise ValueError("As arestas não formam uma árvore abrangente")
    if not selecionados <= set(nomes) or any(nome not in classes for nome in nomes):
        raise ValueError("Classificação ou seleção incompatível")
    destino = RAIZ / "visualizacoes" / "gephi" / "EUA"
    destino.mkdir(parents=True, exist_ok=True)
    with (destino / "nos_mst.csv").open("w", encoding="utf-8-sig", newline="") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(("Id", "Label", "Classe", "Carteira_MST", "Grau_MST"))
        writer.writerows((n, n, classes[n], "Selecionado" if n in selecionados else "Nao selecionado", len(adj[n])) for n in nomes)
    with (destino / "arestas_mst.csv").open("w", encoding="utf-8-sig", newline="") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(("Source", "Target", "Type", "Weight", "Distancia"))
        writer.writerows(exportadas)
    print(f"Exportados {len(nomes)} nós, {len(arestas)} arestas e {len(selecionados)} selecionados em {destino}")


if __name__ == "__main__":
    main()
