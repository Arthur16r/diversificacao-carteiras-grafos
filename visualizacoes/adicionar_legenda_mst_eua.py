"""Acrescenta legenda e margens à exportação do Gephi, preservando o original."""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


PASTA = Path(__file__).resolve().parent / "gephi" / "EUA"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def tag(nome):
    return f"{{{NS}}}{nome}"


def main(grafo_completo=False):
    nome = "grafo_completo_eua" if grafo_completo else "mst_eua_carteira_destacada"
    origem = PASTA / f"{nome}.svg"
    destino = PASTA / f"{nome}_com_legenda.svg"
    raiz = ET.parse(origem).getroot()
    x, y, largura, altura = map(float, raiz.attrib["viewBox"].split())
    # Coordenadas da árvore permanecem intactas. Apenas a área externa aumenta.
    margem, cabecalho, rodape = 70, 75, 300 if grafo_completo else 220
    novo_x, novo_y = x - margem, y - margem - cabecalho
    nova_largura = largura + 2 * margem
    nova_altura = altura + 2 * margem + cabecalho + rodape
    raiz.set("viewBox", f"{novo_x} {novo_y} {nova_largura} {nova_altura}")
    raiz.set("width", str(nova_largura))
    raiz.set("height", str(nova_altura))
    raiz.insert(0, ET.Element(tag("rect"), {
        "x": str(novo_x), "y": str(novo_y), "width": str(nova_largura),
        "height": str(nova_altura), "fill": "white", "id": "fundo_branco",
    }))
    decoracao = ET.SubElement(raiz, tag("g"), {"id": "legenda_e_titulo", "font-family": "Arial, sans-serif", "fill": "#172b45"})

    def texto(tx, ty, valor, tamanho=24, negrito=False):
        atributos = {"x": str(tx), "y": str(ty), "font-size": str(tamanho)}
        if negrito:
            atributos["font-weight"] = "bold"
        ET.SubElement(decoracao, tag("text"), atributos).text = valor

    titulo = "Grafo completo de correlações — EUA" if grafo_completo else "Árvore geradora mínima — EUA"
    subtitulo = ("74 ativos · 2.701 arestas · construção até 2010 · sem filtro de conexões"
                 if grafo_completo else "74 ativos · 73 arestas · construção até 2010 · carteira MST com 10 ativos")
    texto(x, y - 77, titulo, 32, True)
    texto(x, y - 40, subtitulo, 22)
    grupo_arestas = raiz.find(f"{tag('g')}[@id='edges']")
    esperado = 2701 if grafo_completo else 73
    if grupo_arestas is None or len(grupo_arestas.findall(tag("path"))) != esperado:
        raise ValueError(f"Esperadas {esperado} arestas na exportação")
    inicio_y = y + altura + 60
    ET.SubElement(decoracao, tag("line"), {
        "x1": str(x), "x2": str(x + largura), "y1": str(inicio_y-25),
        "y2": str(inicio_y-25), "stroke": "#cbd5e1", "stroke-width": "1.5",
    })
    texto(x, inicio_y + 10, "Classes de ativos", 24, True)
    nos = raiz.find(f"{tag('g')}[@id='nodes']")
    if nos is None:
        raise ValueError("Grupo de nós não encontrado na exportação")
    circulos = list(nos.findall(tag("circle")))
    if len(circulos) != 74:
        raise ValueError("Esperados 74 nós na MST dos EUA")
    por_nome = {c.attrib["class"]: c for c in circulos}
    for deslocamento, classe, exemplo in ((0, "Ações", "id_MSFT"), (260, "REITs", "id_FR"), (520, "Treasury", "id_tesouro_curto")):
        ET.SubElement(decoracao, tag("circle"), {
            "cx": str(x + deslocamento + 12), "cy": str(inicio_y+48), "r": "10",
            "fill": por_nome[exemplo].attrib["fill"],
        })
        texto(x+deslocamento+35, inicio_y+56, classe)
    pequeno = float(por_nome["id_MSFT"].attrib["r"])
    grande = float(por_nome["id_ORCL"].attrib["r"])
    for deslocamento, raio, label in ((0, pequeno, "Não selecionado"), (350, grande, "Selecionado na carteira MST")):
        ET.SubElement(decoracao, tag("circle"), {
            "cx": str(x+deslocamento+15), "cy": str(inicio_y+105), "r": str(raio),
            "fill": "#64748b", "stroke": "#334155", "stroke-width": "1",
        })
        texto(x+deslocamento+43, inicio_y+113, label)
    texto(x, inicio_y+163, "A posição e o comprimento visual das arestas não representam uma escala exata", 22)
    texto(x, inicio_y+194, "das distâncias. O tamanho dos nós indica seleção, não grau ou importância.", 22)
    if grafo_completo:
        texto(x, inicio_y+232, "Posições mantidas da MST; destaque da carteira selecionada pela MST.", 22)
        texto(x, inicio_y+267, "Arestas cinza: todas as conexões, suavizadas apenas para facilitar a leitura.", 22)
    ET.ElementTree(raiz).write(destino, encoding="utf-8", xml_declaration=True)
    print(destino)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grafo-completo", action="store_true")
    main(parser.parse_args().grafo_completo)
