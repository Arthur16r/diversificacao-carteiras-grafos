"""Gera o fluxograma metodológico, sem ler nem modificar dados experimentais.

Uso na raiz do projeto: python visualizacoes/gerar_fluxograma.py
Dependência: matplotlib. Saídas: SVG, PDF e PNG nesta pasta.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PASTA = Path(__file__).resolve().parent


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(12, 16))
    fig.patch.set_facecolor("white")
    ax.set(xlim=(0, 12), ylim=(0, 16))
    ax.axis("off")
    cores = {"dados": "#edf2f7", "construcao": "#e7f1fc", "teste": "#e8f4ed", "extra": "#fff3df"}

    def caixa(x, y, w, h, titulo, corpo, grupo="dados"):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.025,rounding_size=0.10",
            linewidth=1.2, edgecolor="#62748a", facecolor=cores[grupo], zorder=2,
        ))
        ax.text(x+w/2, y+h-0.18, titulo, ha="center", va="top", fontsize=11,
                weight="bold", color="#172b45", zorder=3)
        ax.text(x+w/2, y+h-0.49, corpo, ha="center", va="top", fontsize=9.5,
                linespacing=1.45, color="#26384b", zorder=3)

    def seta(a, b, tracejada=False):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13,
            linewidth=1.25, color="#53677e", linestyle="--" if tracejada else "-",
            connectionstyle="arc3", zorder=1))

    ax.text(6, 15.75, "Metodologia do experimento", ha="center", fontsize=21,
            weight="bold", color="#172b45")
    ax.text(6, 15.38, "EUA: estudo principal  •  Brasil: estudo complementar",
            ha="center", fontsize=11, color="#53677e")

    caixa(2.1, 13.95, 7.8, 1.05, "1 · Dados e tratamento",
          "Preços ajustados e séries de títulos; alinhamento das datas,\ntratamento de inconsistências e preservação das ausências históricas.")
    caixa(2.1, 12.45, 7.8, 1.08, "2 · Separação temporal",
          "Construção: EUA 1990–2010 | Brasil 2016–2022\nTeste: EUA 2011–30/06/2026 | Brasil 2023–30/06/2026")
    seta((6, 13.95), (6, 13.53))
    caixa(0.4, 10.86, 7.1, 1.15, "3 · Construção do grafo",
          "Retornos diários → correlação de Pearson por pares disponíveis\nDistância dᵢⱼ = √[2(1 − ρᵢⱼ)] → grafo completo ponderado\nEUA: 74 ativos | Brasil: 37 no principal; 38 com IVVB11", "construcao")
    caixa(8.0, 10.86, 3.6, 1.15, "Dados de teste reservados",
          "Preços e taxa livre de risco\nUsados após a seleção\nSem selecionar pelo retorno futuro", "teste")
    seta((5, 12.45), (4, 12.01))
    seta((8.5, 12.45), (9.8, 12.01))

    caixa(0.4, 9.0, 3.3, 1.38, "4A · Matriz completa",
          "Seleção gulosa da concentrada\ne farthest-first por classe\npara a diversificada\nRestrições e cotas predefinidas", "construcao")
    caixa(4.2, 9.0, 3.3, 1.38, "4B · Árvore mínima",
          "Prim em C++: Θ(V²)\nMST global com V − 1 arestas\nDistâncias: soma no caminho\núnico entre os ativos", "construcao")
    seta((2, 10.86), (2, 10.38))
    seta((5.8, 10.86), (5.8, 10.38))
    caixa(4.2, 7.65, 3.3, 0.96, "5 · Carteira pela MST",
          "Farthest-first por classe\nMesmas cotas da diversificada", "construcao")
    seta((5.8, 9.0), (5.8, 8.61))

    caixa(1.0, 5.94, 10.0, 1.18, "6 · Backtest fora da amostra",
          "Carteiras selecionadas na construção + preços da janela de teste\nPesos iniciais iguais; buy-and-hold, sem rebalanceamento\nSem custos de negociação; quantidades fracionárias", "teste")
    seta((2, 9.0), (2, 7.12))
    seta((5.8, 7.65), (5.8, 7.12))
    seta((9.8, 10.86), (9.8, 7.12))
    caixa(1.0, 4.38, 10.0, 1.12, "7 · Avaliação e comparação",
          "CAGR, volatilidade, Sharpe com excessos diários e drawdown máximo\nPesos finais e número efetivo de ativos; referência livre de risco:\nTreasury de 3 meses (EUA) | índice sintético Selic (Brasil)", "teste")
    seta((6, 5.94), (6, 5.50))

    caixa(0.4, 2.25, 5.4, 1.55, "Análises complementares · carteiras",
          "5.000 aleatórias com o mesmo N e as mesmas cotas\nVarredura de N e cenário com mais ativos\nAportes mensais: igualitário e menor retorno anterior\nBrasil: variante com IVVB11", "extra")
    caixa(6.2, 2.25, 5.4, 1.55, "Análises complementares · estrutura",
          "EUA: estabilidade das arestas entre subperíodos\nEUA: robustez com construção comum 2003–2010\nBenchmark de Prim: grafos completos sintéticos\nTempo por V; memória da matriz; execução Ubuntu", "extra")
    seta((3, 4.38), (3, 3.80), True)
    seta((9, 4.38), (9, 3.80), True)
    ax.text(6, 1.75, "Leitura do fluxograma", ha="center", fontsize=11, weight="bold", color="#172b45")
    ax.text(6, 1.30,
        "Azul: estimação e seleção na construção. Verde: teste fora da amostra.\n"
        "Amarelo: experimentos separados que usam etapas do pipeline; não são etapas de seleção.\n"
        "Farthest-first é uma heurística: não garante a carteira globalmente mais diversificada.\n"
        "As janelas indicam os limites do experimento; alguns ativos começam depois do início.",
        ha="center", va="center", fontsize=9.5, linespacing=1.6, color="#53677e")
    fig.subplots_adjust(left=0.015, right=0.985, bottom=0.015, top=0.985)
    for extensao in ("svg", "pdf", "png"):
        destino = PASTA / f"fluxograma_metodologia.{extensao}"
        fig.savefig(destino, dpi=220, facecolor="white")
        print(destino)
    plt.close(fig)


if __name__ == "__main__":
    main()
