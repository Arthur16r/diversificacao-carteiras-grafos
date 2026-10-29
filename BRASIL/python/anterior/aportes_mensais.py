"""
Simula aportes mensais numa carteira, comparando duas estratégias:

  - "inteligente": todo mês, o aporte inteiro vai para o ativo que MAIS
    CAIU naquele mês (dentro da carteira) -- testa se correlação negativa
    gera oportunidades reais de comprar barato.
  - "igualitario": todo mês, o aporte é dividido igualmente entre todos
    os ativos da carteira (baseline de comparação).

Sem repetir o mesmo ativo do mês anterior é opcional (Arthur cogitou,
mas recomendamos testar sem essa restrição primeiro -- ver discussão
anterior). Por padrão, evitar_repeticao=False.

Como os aportes acontecem em datas diferentes (fluxo de caixa
periódico), a métrica de retorno correta não é CAGR simples, é XIRR
(taxa interna de retorno considerando as datas exatas dos fluxos).
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import brentq

from portfolio_metrics import (
    carregar_matriz_distancia,
    construir_carteira_gulosa_com_classes,
    construir_carteira_com_cotas,
    remover_classe,
    COTAS_DIVERSIFICADA_PADRAO,
    TAMANHO_CONCENTRADA_REALISTA,
    COTAS_DIVERSIFICADA_REALISTA,
)

PRECOS_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "resultado_aportes.csv"

INICIO_TESTE = "2023-01-01"
FIM_TESTE = "2026-07-01"
TAMANHO_CARTEIRA = 8
VALOR_APORTE = 1000.0  # valor arbitrario, so a taxa (XIRR) importa


def carregar_precos_mensais() -> pd.DataFrame:
    precos = pd.read_csv(PRECOS_PATH, index_col="data", parse_dates=True)
    precos = precos.loc[INICIO_TESTE:FIM_TESTE]
    # pega o ultimo preco disponivel de cada mes
    mensal = precos.resample("ME").last()
    return mensal


def xirr(fluxos: list[tuple[pd.Timestamp, float]]) -> float:
    """Taxa interna de retorno anualizada, dado uma lista de (data, valor).
    Valores negativos = saida de caixa (aporte), positivo = entrada
    (resgate/valor final)."""
    d0 = fluxos[0][0]

    def vpl(taxa):
        return sum(
            valor / (1 + taxa) ** ((data - d0).days / 365.0) for data, valor in fluxos
        )

    return brentq(vpl, -0.99, 10.0)


def simular_aportes(
    precos_mensais: pd.DataFrame,
    ativos: list[str],
    modo: str,
    evitar_repeticao: bool = False,
    aporte_inicial: float = 0.0,
    k_piores: int = 1,
) -> dict:
    sub = precos_mensais[ativos].dropna()
    if len(sub) < 3:
        raise ValueError("poucos meses disponiveis para simular aportes")

    unidades = {a: 0.0 for a in ativos}
    fluxos = []
    ultimos_escolhidos: list[str] = []

    if aporte_inicial > 0:
        peso_inicial = aporte_inicial / len(ativos)
        for a in ativos:
            unidades[a] += peso_inicial / sub.iloc[0][a]
        fluxos.append((sub.index[0], -aporte_inicial))

    # primeiro mes: soh estabelece o preco de referencia (n/ tem retorno do
    # mes anterior ainda), aporte comeca a partir do segundo mes
    for i in range(1, len(sub)):
        data_i = sub.index[i]
        retornos_mes = sub.iloc[i] / sub.iloc[i - 1] - 1

        if modo == "inteligente":
            candidatos = ativos
            if evitar_repeticao and ultimos_escolhidos:
                candidatos = [a for a in ativos if a not in ultimos_escolhidos]
            # pega os k_piores ativos que mais cairam no mes, divide o aporte entre eles
            piores = retornos_mes[candidatos].nsmallest(k_piores).index.tolist()
            aporte_por_ativo = VALOR_APORTE / len(piores)
            for a in piores:
                unidades[a] += aporte_por_ativo / sub.iloc[i][a]
            ultimos_escolhidos = piores

        elif modo == "igualitario":
            aporte_por_ativo = VALOR_APORTE / len(ativos)
            for a in ativos:
                unidades[a] += aporte_por_ativo / sub.iloc[i][a]

        else:
            raise ValueError("modo deve ser 'inteligente' ou 'igualitario'")

        fluxos.append((data_i, -VALOR_APORTE))

    valor_final = sum(unidades[a] * sub.iloc[-1][a] for a in ativos)
    fluxos.append((sub.index[-1], valor_final))

    total_aportado = aporte_inicial + VALOR_APORTE * (len(sub) - 1)
    return {
        "xirr": xirr(fluxos),
        "valor_final": valor_final,
        "total_aportado": total_aportado,
        "ganho_absoluto": valor_final - total_aportado,
    }


def main():
    precos_mensais = carregar_precos_mensais()
    dist_completa = carregar_matriz_distancia()
    dist = remover_classe(dist_completa, "exterior")

    carteiras = {
        "concentrada": construir_carteira_gulosa_com_classes(dist, TAMANHO_CARTEIRA, "concentrada", tetos={"tesouro": 2}),
        "diversificada": construir_carteira_com_cotas(dist, COTAS_DIVERSIFICADA_PADRAO),
        "concentrada_N8_realista": construir_carteira_gulosa_com_classes(
            dist, TAMANHO_CONCENTRADA_REALISTA, "concentrada", tetos={"tesouro": 2}
        ),
        "diversificada_N18_realista": construir_carteira_com_cotas(dist_completa, COTAS_DIVERSIFICADA_REALISTA),
    }

    for aporte_inicial, label in [(0.0, "SEM aporte inicial (so aportes mensais)"),
                                   (1_000_000.0, "COM aporte inicial de R$1.000.000")]:
        print(f"\n=== {label} ===")
        resultados = []
        for nome, ativos in carteiras.items():
            for modo in ["igualitario", "inteligente"]:
                r = simular_aportes(precos_mensais, ativos, modo, aporte_inicial=aporte_inicial)
                r["carteira"] = nome
                r["modo"] = modo
                r["aporte_inicial"] = aporte_inicial
                resultados.append(r)
                print(
                    f"{nome:15s} | {modo:12s} | XIRR={r['xirr']:.2%}  "
                    f"valor_final={r['valor_final']:.2f}  "
                    f"aportado={r['total_aportado']:.2f}  "
                    f"ganho={r['ganho_absoluto']:.2f}"
                )

        df = pd.DataFrame(resultados)
        sufixo = "com_inicial" if aporte_inicial > 0 else "sem_inicial"
        out_path = OUT_PATH.parent / f"resultado_aportes_{sufixo}.csv"
        df.to_csv(out_path, index=False)
        print(f"Salvo em {out_path}")


if __name__ == "__main__":
    main()
