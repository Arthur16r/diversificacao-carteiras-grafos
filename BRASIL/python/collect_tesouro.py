"""
Coleta preços (PU Compra Manha, marcação a mercado) do Tesouro Direto via
Tesouro Transparente, e monta séries "rolling" por faixa de vencimento
RELATIVA (curto/médio/longo = vencimento mais próximo/do meio/mais distante
dentre os títulos disponíveis naquele dia, não um corte fixo em anos).

IMPORTANTE: quando a série troca de título especifico (ex: o titulo que
era "curto" venceu ou saiu da faixa, e outro titulo assume a posicao),
NAO usamos o nivel de preco (PU) bruto do titulo novo diretamente -- isso
criaria um "salto" artificial na serie, porque titulos diferentes tem
niveis de preco (PU) diferentes entre si, mesmo se comportando de forma
parecida. Em vez disso, encadeamos os RETORNOS: no dia da troca, usamos
a variacao percentual do titulo NOVO (comparado ao proprio preco dele no
dia anterior), nao o salto entre o preco antigo e o novo. Isso produz um
indice sintetico continuo, sem saltos de nivel de preco.

Fonte: https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3
"""

import argparse
import pandas as pd
from pathlib import Path

TESOURO_CSV_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"
)

TESOURO_TIPOS = {
    "Tesouro Selic": "selic",
    "Tesouro Prefixado": "prefixado",
    "Tesouro IPCA+": "ipca",
}

ROTULOS_FAIXA = {1: "curto", 2: "medio", 3: "longo"}

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "tesouro_bruto.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "tesouro_series_rolling.csv"


def baixar_bruto() -> pd.DataFrame:
    print("Baixando histórico completo do Tesouro Transparente...")
    df = pd.read_csv(TESOURO_CSV_URL, sep=";", decimal=",", encoding="latin1")
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Tipo Titulo"].isin(TESOURO_TIPOS.keys())].copy()

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_PATH, index=False)
    print(f"Bruto salvo em {RAW_PATH} ({df.shape[0]} linhas)")
    return df


def montar_series_rolling(df: pd.DataFrame) -> pd.DataFrame:
    """Recebe o CSV bruto e devolve uma tabela larga (data x serie) com um
    INDICE SINTETICO continuo por serie (base 100 no primeiro dia
    disponivel), sem saltos de preco nas trocas de titulo."""
    df = df.copy()
    df["Data Vencimento"] = pd.to_datetime(df["Data Vencimento"], dayfirst=True)
    df["Data Base"] = pd.to_datetime(df["Data Base"], dayfirst=True)
    df = df[df["Data Vencimento"] >= df["Data Base"]]

    # Preserva todos os títulos ANTES do filtro de faixas. O novo título
    # pode não pertencer à faixa no dia anterior, mas seu PU é necessário.
    df["titulo_id"] = df["Tipo Titulo"] + "|" + df["Data Vencimento"].dt.strftime("%Y-%m-%d")
    precos_por_titulo = df.pivot_table(
        index="Data Base", columns="titulo_id", values="PU Compra Manha", aggfunc="first"
    ).sort_index()
    df["rank_prazo"] = (
        df.groupby(["Data Base", "Tipo Titulo"])["Data Vencimento"]
        .rank(method="first", ascending=True)
        .astype(int)
    )
    df["faixa"] = df["rank_prazo"].map(ROTULOS_FAIXA)
    df = df[df["faixa"].notna()]

    df["serie"] = df["Tipo Titulo"].map(TESOURO_TIPOS) + "_" + df["faixa"]

    eh_selic = df["serie"].str.startswith("selic")
    df = df[~eh_selic | (df["faixa"] == "curto")]
    df.loc[df["serie"].str.startswith("selic"), "serie"] = "selic"

    # identificador unico de cada titulo especifico (tipo + vencimento
    # exato) -- usado para saber, no rollover, qual e o preco "de ontem"
    # do titulo NOVO (nao do titulo antigo que estava sendo usado)
    df["titulo_id"] = df["Tipo Titulo"] + "|" + df["Data Vencimento"].dt.strftime("%Y-%m-%d")

    # tabela larga: preco de CADA titulo especifico, por dia
    # qual titulo especifico esta "ativo" em cada serie, por dia
    ativo_por_serie = df.pivot_table(
        index="Data Base", columns="serie", values="titulo_id", aggfunc="first"
    ).sort_index()

    resultado = pd.DataFrame(index=ativo_por_serie.index, columns=ativo_por_serie.columns, dtype=float)
    faltas_pu = []

    for serie in ativo_por_serie.columns:
        dias_validos = ativo_por_serie[serie].dropna().index
        if len(dias_validos) == 0:
            continue

        primeiro_dia = dias_validos[0]
        resultado.loc[primeiro_dia, serie] = 100.0

        for i in range(1, len(dias_validos)):
            dia = dias_validos[i]
            dia_anterior = dias_validos[i - 1]
            titulo_hoje = ativo_por_serie.loc[dia, serie]

            preco_hoje = precos_por_titulo.loc[dia, titulo_hoje]
            preco_ontem = (
                precos_por_titulo.loc[dia_anterior, titulo_hoje]
                if titulo_hoje in precos_por_titulo.columns
                and dia_anterior in precos_por_titulo.index
                else None
            )

            if pd.notna(preco_ontem) and preco_ontem > 0 and pd.notna(preco_hoje):
                retorno = preco_hoje / preco_ontem - 1
            else:
                # titulo novo sem preco no dia anterior (raro) -- nao
                # aplica retorno nesse dia, evita salto artificial
                retorno = 0.0
                faltas_pu.append({"serie": serie, "data": dia, "data_anterior": dia_anterior,
                                  "titulo": titulo_hoje, "retorno_imputado": 0.0})

            resultado.loc[dia, serie] = resultado.loc[dia_anterior, serie] * (1 + retorno)

    resultado.index.name = "data"
    resultado.attrs["retornos_zero_sem_pu_anterior"] = faltas_pu
    return resultado


def collect(usar_bruto_local=False):
    df = pd.read_csv(RAW_PATH) if usar_bruto_local else baixar_bruto()
    series = montar_series_rolling(df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    series.to_csv(OUT_PATH)
    pd.DataFrame(series.attrs["retornos_zero_sem_pu_anterior"], columns=[
        "serie", "data", "data_anterior", "titulo", "retorno_imputado"
    ]).to_csv(OUT_PATH.parent / "tesouro_faltas_pu_anterior.csv", index=False)
    print(f"Séries rolling salvas em {OUT_PATH}")
    print(series.tail())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--usar-bruto-local", action="store_true")
    collect(parser.parse_args().usar_bruto_local)
