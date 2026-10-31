"""Fluxograma compacto para duas colunas IEEE: 17 × 10,4 cm, PDF/SVG/PNG."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PASTA = Path(__file__).resolve().parent


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(17 / 2.54, 10.4 / 2.54), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 17), ylim=(0, 10.4))
    ax.axis("off")
    textos = []
    cores = {"dados": "#f1f4f8", "construcao": "#e9f2fb", "teste": "#edf6ef", "extra": "#fff4e3"}

    def caixa(x, y, w, h, titulo, corpo, grupo="dados"):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.025,rounding_size=0.09",
            facecolor=cores[grupo], edgecolor="#65758a", linewidth=0.75, zorder=3)
        ax.add_patch(patch)
        t1 = ax.text(x+w/2, y+h-0.18, titulo, ha="center", va="top", fontsize=9,
                    weight="bold", color="#182d46", zorder=4)
        t2 = ax.text(x+w/2, y+h-0.60, corpo, ha="center", va="top", fontsize=8.5,
                    linespacing=1.3, color="#26384a", zorder=4)
        textos.extend([(patch, t1), (patch, t2)])

    def caminho(pontos, tracejado=False):
        estilo = "--" if tracejado else "-"
        for a, b in zip(pontos[:-2], pontos[1:-1]):
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#53677d", linewidth=0.85,
                    linestyle=estilo, zorder=1)
        ax.add_patch(FancyArrowPatch(pontos[-2], pontos[-1], arrowstyle="-|>",
            mutation_scale=9, linewidth=0.85, color="#53677d", linestyle=estilo,
            shrinkA=0, shrinkB=2, zorder=1))

    ax.text(0.45, 10.08, "Metodologia: construção e avaliação fora da amostra",
            fontsize=10, weight="bold", color="#182d46")
    ax.text(0.45, 9.67, "EUA: estudo principal  •  Brasil: estudo complementar",
            fontsize=8.5, color="#52647a")

    caixa(0.45, 8.0, 3.8, 1.45, "Dados e tratamento", "Preços ajustados\ne séries de títulos")
    caixa(5.10, 8.0, 4.5, 1.45, "Separação temporal", "Janela de construção\nJanela de teste")
    caixa(10.50, 8.0, 6.0, 1.45, "Dados de teste", "Preços e referência livre de risco\nReservados até o backtest", "teste")
    caminho([(4.275, 8.81), (5.075, 8.81)])
    caminho([(9.625, 8.81), (10.475, 8.81)])

    caixa(0.45, 5.30, 3.8, 1.85, "Construção do grafo", "Retornos diários\nCorrelações por pares\nGrafo completo", "construcao")
    caminho([(6.2, 7.975), (6.2, 7.85), (2.35, 7.85), (2.35, 7.175)])
    caixa(5.10, 6.30, 4.5, 1.40, "Seleção pelo grafo", "Concentrada e diversificada\nDistâncias do grafo", "construcao")
    caixa(5.10, 4.45, 4.5, 1.45, "Prim e seleção pela MST", "Distâncias dos caminhos\nDiversificada: mesmas cotas", "construcao")
    caminho([(4.275, 6.22), (4.65, 6.22), (4.65, 7.05), (5.075, 7.05)])
    caminho([(4.65, 6.22), (4.65, 5.175), (5.075, 5.175)])

    caixa(10.50, 5.30, 6.0, 1.65, "Backtest fora da amostra", "Pesos iniciais iguais\nBuy-and-hold, sem rebalanceamento", "teste")
    caminho([(13.5, 7.975), (13.5, 6.975)])
    caminho([(9.625, 7.05), (10.0, 7.05), (10.0, 6.5), (10.475, 6.5)])
    caminho([(9.625, 5.175), (10.0, 5.175), (10.0, 5.75), (10.475, 5.75)])
    caixa(10.50, 3.0, 6.0, 1.45, "Avaliação e comparação", "CAGR, volatilidade e Sharpe\nDrawdown, pesos e N efetivo", "teste")
    caminho([(13.5, 5.275), (13.5, 4.475)])

    ax.text(0.55, 3.88, "Controle metodológico", fontsize=9, weight="bold", color="#182d46")
    ax.text(0.55, 3.48, "Seleção usa somente a construção.\nHeurísticas não garantem ótimo global.",
            fontsize=8.5, va="top", linespacing=1.4, color="#52647a")
    caixa(0.45, 0.70, 16.05, 1.42, "Experimentos complementares — análises separadas do pipeline",
          "Aleatórias com cotas • varredura de N • aportes mensais\nEstabilidade da MST • janela comum de construção • custo de Prim", "extra")
    caminho([(13.5, 2.975), (13.5, 2.145)], tracejado=True)
    ax.text(0.45, 0.20, "Azul: construção e seleção. Verde: teste. Amarelo: análises complementares, sem realimentar a seleção.",
            fontsize=7.5, color="#52647a")

    # Verifica que os textos dos blocos cabem no tamanho físico de exportação.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for patch, texto in textos:
        caixa_bbox = patch.get_window_extent(renderer)
        texto_bbox = texto.get_window_extent(renderer)
        if not (caixa_bbox.x0 <= texto_bbox.x0 and texto_bbox.x1 <= caixa_bbox.x1
                and caixa_bbox.y0 <= texto_bbox.y0 and texto_bbox.y1 <= caixa_bbox.y1):
            raise ValueError(f"Texto excede o bloco: {texto.get_text()}")
    for extensao in ("pdf", "svg", "png"):
        destino = PASTA / f"fluxograma_metodologia_horizontal.{extensao}"
        fig.savefig(destino, dpi=300, facecolor="white")
        print(destino)
    plt.close(fig)


if __name__ == "__main__":
    main()
