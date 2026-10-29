"""
Coleta taxas de juros de títulos públicos americanos via FRED (Federal
Reserve Economic Data) e converte em uma série de RETORNO aproximado
(não é um preço de fundo -- é a própria taxa, convertida via fórmula de
duration, método padrão em finanças para reconstruir retorno de título
a partir de taxa).

  retorno_t ≈ taxa_(t-1) / periodos_por_ano - duration * (taxa_t - taxa_(t-1))

Séries usadas (código FRED):
  DGS3MO  - Treasury 3 meses (equivalente "curto"/Selic)
  DGS5    - Treasury 5 anos (equivalente "médio")
  DGS10   - Treasury 10 anos (equivalente "longo")
  DFII10  - Treasury 10 anos indexado à inflação / TIPS (equivalente IPCA+,
            histórico mais curto, só a partir de ~2003)
"""

import argparse
import os
import pandas as pd
import requests
from pathlib import Path

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "DGS3MO": {"nome": "tesouro_curto", "duration": 0.25},
    "DGS5": {"nome": "tesouro_medio", "duration": 4.5},
    "DGS10": {"nome": "tesouro_longo", "duration": 8.5},
    "DFII10": {"nome": "tesouro_tips", "duration": 8.5},
}

START_DATE = "1990-01-01"
END_DATE = "2026-07-01"

OUT_RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "fred_taxas_brutas.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "tesouro_retornos.csv"
CPI_PATH = OUT_PATH.parent / "fred_cpi_mensal.csv"


def baixar_serie_fred(codigo: str) -> pd.Series:
    if not FRED_API_KEY:
        raise ValueError("Defina FRED_API_KEY no ambiente para coletar dados do FRED; com os CSVs locais, use --usar-taxas-locais.")
    params = {
        "series_id": codigo,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": START_DATE,
        "observation_end": END_DATE,
    }
    resp = requests.get(FRED_BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    dados = resp.json()["observations"]

    df = pd.DataFrame(dados)
    df["date"] = pd.to_datetime(df["date"])
    # FRED usa "." para dia sem dado (feriado, etc.) -- vira NaN
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    serie = df.set_index("date")["value"]
    serie.name = codigo
    return serie


def taxa_para_retorno(taxa: pd.Series, duration: float, periodos_por_ano: int = 252) -> pd.Series:
    """Converte uma serie de TAXA (em %, ex: 4.25 = 4.25% a.a.) em uma
    serie de RETORNO diario aproximado, via formula de duration."""
    taxa_decimal = taxa / 100.0
    carrego = taxa_decimal.shift(1) / periodos_por_ano
    variacao_preco = -duration * taxa_decimal.diff()
    retorno = carrego + variacao_preco
    return retorno


def cpi_referencia_tips(cpi: pd.Series, datas: pd.DatetimeIndex) -> pd.Series:
    """Ref CPI sem arredondamento: CPI-U NSA com defasagem e interpolação.

    Ref(t) = CPI(m-3) + (dia-1)/dias_no_mes * [CPI(m-2)-CPI(m-3)].
    Fonte: TreasuryDirect, 31 CFR 356, Appendix B. Não usa CPI futuro.
    """
    mensal = cpi.copy()
    mensal.index = mensal.index.to_period("M")
    if mensal.index.has_duplicates:
        raise ValueError("CPI mensal com meses duplicados")
    # Outubro/2025 não foi publicado pelo BLS. Para TIPS o Treasury fixou
    # 325.604 pela cláusula de contingência; não é uma estimativa nossa.
    # https://www.treasurydirect.gov/instit/annceresult/tipscpi/2025/CPI_20251218.pdf
    outubro = pd.Period("2025-10", freq="M")
    if outubro in mensal.index and pd.isna(mensal.loc[outubro]):
        mensal.loc[outubro] = 325.604
    meses = datas.to_period("M")
    anterior = mensal.reindex(meses - 3).to_numpy()
    seguinte = mensal.reindex(meses - 2).to_numpy()
    fracao = (datas.day - 1) / datas.days_in_month
    return pd.Series(anterior + fracao * (seguinte - anterior), index=datas)


def construir_indices(taxas: pd.DataFrame, cpi: pd.Series) -> pd.DataFrame:
    """Índices aproximados; preserva ausências anteriores à primeira taxa.

    TIPS: (1+r_nominal) = (1+r_real_aproximado) * RefCPI(t)/RefCPI(t-1).
    Carrego real ACT/365.25 e variação de preço por duration constante.
    Não reproduz um título específico, cupons exatos, convexidade ou piso.
    """
    taxas = taxas.sort_index()
    if taxas.index.has_duplicates:
        raise ValueError("Taxas com datas duplicadas")
    indices = {}
    for codigo, info in SERIES.items():
        taxa = taxas[codigo].ffill().dropna()
        if len(taxa) < 2:
            raise ValueError(f"Histórico insuficiente: {codigo}")
        if codigo == "DFII10":
            ref = cpi_referencia_tips(cpi, taxa.index)
            if ref.isna().any() or (ref <= 0).any():
                raise ValueError("CPI ausente ou inválido no período do TIPS")
            dias = taxa.index.to_series().diff().dt.days
            real = taxa.shift(1) / 100 * dias / 365.25 - info["duration"] * (taxa / 100).diff()
            ret = (1 + real) * (ref / ref.shift(1)) - 1
        else:
            # Preserva a aproximação existente dos Treasury nominais.
            ret = taxa_para_retorno(taxa, info["duration"])
        ret.iloc[0] = 0.0  # base 100 somente na primeira taxa disponível
        if ret.isna().any() or (ret <= -1).any():
            raise ValueError(f"Retorno ausente ou inválido: {codigo}")
        indices[info["nome"]] = 100 * (1 + ret).cumprod()
    resultado = pd.DataFrame(indices).reindex(taxas.index)
    resultado.index.name = "data"
    return resultado


def collect(usar_taxas_locais: bool = False):
    # CPI separado: frequência mensal, sem preencher meses ausentes.
    if CPI_PATH.exists() and usar_taxas_locais:
        cpi = pd.read_csv(CPI_PATH, index_col="data", parse_dates=True)["CPIAUCNS"]
    else:
        cpi = baixar_serie_fred("CPIAUCNS")
        CPI_PATH.parent.mkdir(parents=True, exist_ok=True)
        cpi.rename_axis("data").to_csv(CPI_PATH)
    if usar_taxas_locais:
        taxas = pd.read_csv(OUT_RAW_PATH, index_col="data", parse_dates=True)
        construir_indices(taxas, cpi).to_csv(OUT_PATH)
        print(f"Índices reconstruídos a partir das taxas locais: {OUT_PATH}")
        return
    taxas_brutas = {}

    for codigo, info in SERIES.items():
        print(f"Baixando {codigo} ({info['nome']}) do FRED...")
        taxa = baixar_serie_fred(codigo)
        taxa = taxa.ffill()  # fins de semana/feriados: carrega ultima taxa valida
        taxas_brutas[codigo] = taxa

        print(f"  ok: {taxa.notna().sum()} observações válidas, "
              f"de {taxa.first_valid_index().date()} a {taxa.last_valid_index().date()}")

    df_taxas = pd.DataFrame(taxas_brutas)
    df_taxas.index.name = "data"
    OUT_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_taxas.to_csv(OUT_RAW_PATH)
    print(f"\nTaxas brutas salvas em {OUT_RAW_PATH}")

    # Índices base 100 a partir da primeira taxa disponível de cada série.
    df_indices = construir_indices(df_taxas, cpi)
    df_indices.to_csv(OUT_PATH)
    print(f"Índices sintéticos (base 100) salvos em {OUT_PATH}")
    print(df_indices.tail())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--usar-taxas-locais", action="store_true",
                        help="Reconstrói sem baixar novamente as taxas; baixa CPI se necessário")
    collect(parser.parse_args().usar_taxas_locais)
