"""
Junta as fontes de dados (ações/FIIs + Tesouro Direto) numa única tabela de
preços alinhada por data, pronta para calcular retornos/correlação.
"""

import pandas as pd
from limpar_precos import corrigir_xpml
from pathlib import Path

ACOES_FIIS_PATH = Path(__file__).parent.parent / "data" / "raw" / "precos_acoes_fiis.csv"
TESOURO_PATH = Path(__file__).parent.parent / "data" / "raw" / "tesouro_series_rolling.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"


def juntar_fontes() -> pd.DataFrame:
    acoes_fiis = pd.read_csv(ACOES_FIIS_PATH, index_col="data", parse_dates=True)
    acoes_fiis = corrigir_xpml(acoes_fiis)
    # Cotação faltante confirmada no COTAHIST oficial, sem interpolação.
    # https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_D24102025.ZIP
    data_ivvb = pd.Timestamp("2025-10-24")
    if data_ivvb in acoes_fiis.index and pd.isna(acoes_fiis.loc[data_ivvb, "IVVB11.SA"]):
        acoes_fiis.loc[data_ivvb, "IVVB11.SA"] = 411.68
    tesouro = pd.read_csv(TESOURO_PATH, index_col="data", parse_dates=True)

    # calendario de referencia = dias de pregao da B3 (indice de acoes/FIIs),
    # que e o mais restrito dos dois (Tesouro tem preco em mais dias uteis)
    calendario = acoes_fiis.index

    # Tesouro tem preco quase todo dia util, mas nem sempre exatamente nos
    # mesmos dias de pregao da B3 (feriados podem diferir) -- reindexa para
    # o calendario da B3 e "carrega para frente" o ultimo preco conhecido
    tesouro_alinhado = tesouro.reindex(calendario, method="ffill")

    precos = pd.concat([acoes_fiis, tesouro_alinhado], axis=1)
    precos.index.name = "data"
    return precos


def main():
    precos = juntar_fontes()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    precos.to_csv(OUT_PATH)
    print(f"Tabela final salva em {OUT_PATH}")
    print(f"{precos.shape[0]} dias, {precos.shape[1]} ativos")

    faltando = precos.isna().sum()
    faltando = faltando[faltando > 0].sort_values(ascending=False)
    if not faltando.empty:
        print("\nAtivos com dados faltando em algum trecho do período")
        print("(normal: ativo criado depois do início do período, ou faixa")
        print("de Tesouro sem título disponível naqueles dias):")
        print(faltando)


if __name__ == "__main__":
    main()
