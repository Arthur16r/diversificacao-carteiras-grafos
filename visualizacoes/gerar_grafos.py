"""Gera imagens locais da MST e do grafo completo, sem executar experimentos.

O layout radial é calculado pela topologia da MST, sem escala de distância.
Os projetos e as exportações manuais do Gephi permanecem preservados.
"""

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parent.parent
CORES = {"acao": "#3675cf", "reit": "#e47830", "fii": "#e47830", "tesouro": "#239b68"}
ROTULOS = {"acao": "Ações", "reit": "REITs", "fii": "FIIs", "tesouro": "Títulos públicos"}


def carregar(mercado):
    """Confere matriz, árvore e proveniência da carteira antes de desenhar."""
    base = RAIZ / mercado
    pasta = base / "data/processed"
    origem = pasta / "distance_matrix.csv"
    matriz_path = pasta / ("distance_matrix_sem_exterior.csv" if mercado == "BRASIL" else "distance_matrix.csv")
    mst_path = base / "cpp/mst_edges.csv"
    carteira_path = pasta / "carteiras_mst.csv"
    completa = pd.read_csv(origem, index_col=0)
    dist = pd.read_csv(matriz_path, index_col=0)
    nomes = list(dist.index)
    valores = dist.to_numpy(dtype=float)
    if (len(nomes) < 2 or not dist.index.is_unique or nomes != list(dist.columns)
            or not np.isfinite(valores).all() or np.any(valores < 0) or np.any(valores > 2)
            or not np.allclose(valores, valores.T, rtol=0, atol=1e-12)
            or not np.allclose(np.diag(valores), 0, rtol=0, atol=1e-12)):
        raise ValueError("Matriz de distâncias inválida")
    if (not completa.index.is_unique or list(completa.index) != list(completa.columns)
            or not set(nomes) <= set(completa.index)
            or not np.allclose(completa.loc[nomes, nomes].to_numpy(dtype=float), valores, rtol=0, atol=1e-12)):
        raise ValueError("Matriz doméstica incompatível com a matriz de origem")
    carteiras = pd.read_csv(carteira_path)
    if len(carteiras) != 1:
        raise ValueError("Esperada uma carteira MST principal")
    carteira = carteiras.iloc[0]
    for campo, arquivo in (("sha256_matriz_origem", origem), ("sha256_arestas_mst", mst_path)):
        if carteira[campo] != hashlib.sha256(arquivo.read_bytes()).hexdigest():
            raise ValueError("Carteira desatualizada: execute a etapa principal antes de gerar imagens")
    selecionados = set(carteira["ativos"].split(";"))
    if len(selecionados) != int(carteira["n_ativos"]) or not selecionados <= set(nomes):
        raise ValueError("Ativos selecionados incompatíveis com a matriz")
    adj = {n: [] for n in nomes}
    pares, arestas = set(), []
    tabela = pd.read_csv(mst_path)
    for a, b, peso in tabela[["de", "para", "distancia"]].itertuples(index=False, name=None):
        par = frozenset((a, b))
        if a not in adj or b not in adj or a == b or par in pares:
            raise ValueError("Aresta inválida ou duplicada na MST")
        if not np.isclose(float(peso), dist.loc[a, b], rtol=6e-6, atol=6e-6):
            raise ValueError("Pesos da MST incompatíveis com a matriz")
        pares.add(par)
        arestas.append((a, b))
        adj[a].append(b)
        adj[b].append(a)
    vistos, pilha = set(), [nomes[0]]
    while pilha:
        n = pilha.pop()
        if n not in vistos:
            vistos.add(n)
            pilha.extend(adj[n])
    if len(arestas) != len(nomes) - 1 or vistos != set(nomes):
        raise ValueError("As arestas não formam uma árvore abrangente")
    # Carrega somente as definições do módulo, sem executar seu main financeiro.
    spec = importlib.util.spec_from_file_location(f"metricas_visualizacao_{mercado}", base / "python/portfolio_metrics.py")
    metricas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metricas)
    classes = {n: metricas.classificar_tipo_ativo(n) for n in nomes}
    if not set(classes.values()) <= set(CORES):
        raise ValueError("Classe inesperada no universo principal")
    registro = {
        "mercado": mercado, "vertices": len(nomes), "arestas_mst": len(arestas),
        "arestas_grafo_completo": len(nomes) * (len(nomes) - 1) // 2,
        "selecionados_mst": sorted(selecionados), "fim_construcao": str(carteira["fim_construcao"]),
        "sha256_matriz_origem": carteira["sha256_matriz_origem"],
        "sha256_matriz_visualizada": hashlib.sha256(matriz_path.read_bytes()).hexdigest(),
        "sha256_arestas_mst": carteira["sha256_arestas_mst"],
        "sha256_carteira_mst": hashlib.sha256(carteira_path.read_bytes()).hexdigest(),
        "layout": "Radial pela topologia da MST; posições iguais nas duas figuras; sem escala de distância.",
    }
    return nomes, adj, arestas, selecionados, classes, registro


def layout_radial(adj):
    """Enraíza no centro do diâmetro e divide setores pela quantidade de folhas.

    Ordem dos vizinhos e desempates seguem a entrada. Não usa correlações,
    distâncias ou resultados do backtest para posicionar os nós.
    """
    def percurso(inicio):
        pais, ordem = {inicio: None}, [inicio]
        for n in ordem:
            for v in adj[n]:
                if v not in pais:
                    pais[v] = n
                    ordem.append(v)
        return ordem, pais

    extremo = percurso(next(iter(adj)))[0][-1]
    ordem, pais = percurso(extremo)
    diametro, n = [], ordem[-1]
    while n is not None:
        diametro.append(n)
        n = pais[n]
    raiz = diametro[len(diametro) // 2]
    ordem, pais = percurso(raiz)
    filhos = {n: [v for v in adj[n] if pais.get(v) == n] for n in ordem}
    folhas = {}
    for n in reversed(ordem):
        folhas[n] = sum(folhas[v] for v in filhos[n]) or 1
    posicoes = {raiz: (0.0, 0.0)}
    fila = deque([(raiz, 0, 0.0, 2 * np.pi)])
    while fila:
        n, nivel, inicio, fim = fila.popleft()
        angulo = inicio
        for v in filhos[n]:
            largura = (fim - inicio) * folhas[v] / folhas[n]
            meio = angulo + largura / 2
            posicoes[v] = ((nivel + 1) * np.cos(meio), (nivel + 1) * np.sin(meio))
            fila.append((v, nivel + 1, angulo, angulo + largura))
            angulo += largura
    return posicoes


def ajustar_rotulos(fig, rotulos, selecionados):
    """Escolhe deslocamentos curtos que reduzam colisões entre os textos."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ocupados = []
    ordem = sorted(rotulos, key=lambda n: (n not in selecionados, -len(n), n))
    candidatos = [(4, 5, "left", "bottom"), (4, -5, "left", "top"),
                  (-4, 5, "right", "bottom"), (-4, -5, "right", "top"),
                  (4, 16, "left", "bottom"), (4, -16, "left", "top"),
                  (-4, 16, "right", "bottom"), (-4, -16, "right", "top"),
                  (4, 28, "left", "bottom"), (-4, -28, "right", "top")]
    for nome in ordem:
        texto = rotulos[nome]
        melhor = None
        for dx, dy, ha, va in candidatos:
            texto.set_position((dx, dy))
            texto.set_ha(ha)
            texto.set_va(va)
            caixa = texto.get_window_extent(renderer).expanded(1.10, 1.15)
            custo = sum(max(0, min(caixa.x1, c.x1) - max(caixa.x0, c.x0))
                        * max(0, min(caixa.y1, c.y1) - max(caixa.y0, c.y0)) for c in ocupados)
            if melhor is None or custo < melhor[0]:
                melhor = (custo, dx, dy, ha, va)
            if custo == 0:
                break
        _, dx, dy, ha, va = melhor
        texto.set_position((dx, dy))
        texto.set_ha(ha)
        texto.set_va(va)
        ocupados.append(texto.get_window_extent(renderer).expanded(1.10, 1.15))


def gerar(mercado, destino=None):
    nomes, adj, mst, selecionados, classes, registro = carregar(mercado)
    posicoes = layout_radial(adj)
    destino = Path(destino) if destino is not None else RAIZ / "visualizacoes/automaticas" / mercado
    destino.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "pdf.fonttype": 42})
    coordenadas = np.array([posicoes[n] for n in nomes])
    for tipo in ("mst", "grafo_completo"):
        fig, ax = plt.subplots(figsize=(12, 12), facecolor="white")
        if tipo == "mst":
            arestas = mst
        else:
            arestas = [(a, b) for i, a in enumerate(nomes) for b in nomes[i + 1:]]
        segmentos = [[posicoes[a], posicoes[b]] for a, b in arestas]
        ax.add_collection(LineCollection(segmentos, colors="#667085",
                                        linewidths=0.9 if tipo == "mst" else 0.3,
                                        alpha=0.8 if tipo == "mst" else 0.10, zorder=1))
        ax.scatter(coordenadas[:, 0], coordenadas[:, 1],
                   s=[105 if n in selecionados else 28 for n in nomes],
                   c=[CORES[classes[n]] for n in nomes], edgecolors="white", linewidths=0.5, zorder=3)
        rotulos = {}
        for n in nomes:
            rotulos[n] = ax.annotate(n, posicoes[n], xytext=(4, 5), textcoords="offset points", fontsize=7,
                                     weight="bold" if n in selecionados else "normal", zorder=4,
                                     bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7, "pad": 0.3})
        titulo = "Árvore geradora mínima" if tipo == "mst" else "Grafo completo de distâncias"
        total_arestas = f"{len(arestas):,}".replace(",", ".")
        ax.set_title(f"{titulo} — {mercado}\n{len(nomes)} ativos · {total_arestas} arestas · construção até {registro['fim_construcao']}", fontsize=14, pad=20)
        legenda = [Line2D([], [], marker="o", linestyle="", color=CORES[c], label=ROTULOS[c], markersize=7)
                   for c in CORES if c in classes.values()]
        legenda.extend(Line2D([], [], marker="o", linestyle="", color="#667085", label=rotulo, markersize=tamanho)
                       for tamanho, rotulo in ((5, "Não selecionado"), (10, "Selecionado na carteira MST")))
        fig.legend(handles=legenda, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.05), frameon=False, fontsize=9)
        fig.text(0.5, 0.025, "Posições determinadas pela topologia da MST; comprimento visual sem escala de distância.\n"
                 "Tamanho indica seleção na carteira MST, inclusive no grafo completo; espessura não codifica distância.",
                 ha="center", fontsize=8, color="#475467")
        ax.margins(0.15)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.subplots_adjust(left=0.06, right=0.94, bottom=0.16, top=0.90)
        ajustar_rotulos(fig, rotulos, selecionados)
        for extensao in ("svg", "pdf", "png"):
            arquivo = destino / f"{tipo}_{mercado.lower()}.{extensao}"
            fig.savefig(arquivo, dpi=250, facecolor="white")
            print(arquivo)
        plt.close(fig)
    registro["posicoes"] = posicoes
    (destino / "procedencia.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mercado", choices=("eua", "brasil"), required=True)
    parser.add_argument("--destino", type=Path, help="Pasta alternativa para as seis imagens e o registro de procedência.")
    args = parser.parse_args()
    gerar(args.mercado.upper(), args.destino)
