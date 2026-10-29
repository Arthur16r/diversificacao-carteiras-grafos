"""
Coleta preços históricos de ações e REITs americanos via yfinance.

Pool: 50 ações (líderes de mercado 1990-2010, por setor) + 20 REITs
(equivalente aos FIIs do projeto brasileiro).

Alguns tickers podem ter histórico incompleto dentro da janela de
construção (1990-2010) por IPO tardio, ou terem passado por fusões/
cisões complexas (ex: UTX->RTX, DOW/DD/AA pós-2016/2019) -- rodar
diagnosticar_acoes_fiis.py (adaptado) antes de confiar nos resultados,
igual fizemos no projeto brasileiro.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path

TICKERS = {
    # --- Tecnologia (6) ---
    "MSFT": {"tipo": "acao", "setor": "tecnologia"},
    "INTC": {"tipo": "acao", "setor": "tecnologia"},
    "IBM": {"tipo": "acao", "setor": "tecnologia"},
    "ORCL": {"tipo": "acao", "setor": "tecnologia"},
    "CSCO": {"tipo": "acao", "setor": "tecnologia"},
    "HPQ": {"tipo": "acao", "setor": "tecnologia"},

    # --- Telecom (2) ---
    "T": {"tipo": "acao", "setor": "telecom"},
    "VZ": {"tipo": "acao", "setor": "telecom"},

    # --- Consumo defensivo (6) ---
    "WMT": {"tipo": "acao", "setor": "consumo_defensivo"},
    "PG": {"tipo": "acao", "setor": "consumo_defensivo"},
    "KO": {"tipo": "acao", "setor": "consumo_defensivo"},
    "PEP": {"tipo": "acao", "setor": "consumo_defensivo"},
    "CL": {"tipo": "acao", "setor": "consumo_defensivo"},
    "MO": {"tipo": "acao", "setor": "consumo_defensivo"},

    # --- Industrial/Conglomerado (4) ---
    "GE": {"tipo": "acao", "setor": "industrial"},
    "HON": {"tipo": "acao", "setor": "industrial"},
    "MMM": {"tipo": "acao", "setor": "industrial"},
    "RTX": {"tipo": "acao", "setor": "industrial"},  # era UTX ate 2020; negocio ficou mais estreito (so aeroespacial/defesa) apos cisao de Carrier/Otis

    # --- Aeroespacial/Defesa (4) ---
    "BA": {"tipo": "acao", "setor": "aeroespacial_defesa"},
    "LMT": {"tipo": "acao", "setor": "aeroespacial_defesa"},
    "NOC": {"tipo": "acao", "setor": "aeroespacial_defesa"},
    "GD": {"tipo": "acao", "setor": "aeroespacial_defesa"},

    # --- Petróleo (3) ---
    "XOM": {"tipo": "acao", "setor": "petroleo"},
    "CVX": {"tipo": "acao", "setor": "petroleo"},
    "COP": {"tipo": "acao", "setor": "petroleo"},

    # --- Materiais/Mineração (3) ---
    "DD": {"tipo": "acao", "setor": "materiais"},   # reestruturacao 2016-2019
    "PPG": {"tipo": "acao", "setor": "materiais"},  # substitui DOW (empresa nova desde 2019, historico curto demais)
    "AA": {"tipo": "acao", "setor": "materiais"},   # cisao 2016

    # --- Bancos (5) ---
    "C": {"tipo": "acao", "setor": "banco"},      # reverse split 2011
    "BAC": {"tipo": "acao", "setor": "banco"},
    "JPM": {"tipo": "acao", "setor": "banco"},
    "WFC": {"tipo": "acao", "setor": "banco"},
    "USB": {"tipo": "acao", "setor": "banco"},

    # --- Seguros (3) ---
    "AIG": {"tipo": "acao", "setor": "seguros"},  # reverse split 2009
    "MET": {"tipo": "acao", "setor": "seguros"},
    "TRV": {"tipo": "acao", "setor": "seguros"},

    # --- Holding diversificada (1) ---
    "BRK-B": {"tipo": "acao", "setor": "holding_diversificada"},

    # --- Saúde/Farmacêutica (4) ---
    "JNJ": {"tipo": "acao", "setor": "saude"},
    "PFE": {"tipo": "acao", "setor": "saude"},
    "MRK": {"tipo": "acao", "setor": "saude"},
    "ABT": {"tipo": "acao", "setor": "saude"},

    # --- Consumo discricionário (3) ---
    "HD": {"tipo": "acao", "setor": "consumo_discricionario"},
    "MCD": {"tipo": "acao", "setor": "consumo_discricionario"},
    "DIS": {"tipo": "acao", "setor": "consumo_discricionario"},

    # --- Energia elétrica (4) ---
    "SO": {"tipo": "acao", "setor": "energia_eletrica"},
    "DUK": {"tipo": "acao", "setor": "energia_eletrica"},
    "AEP": {"tipo": "acao", "setor": "energia_eletrica"},
    "NEE": {"tipo": "acao", "setor": "energia_eletrica"},

    # --- Transporte (2) ---
    "UNP": {"tipo": "acao", "setor": "transporte"},
    "FDX": {"tipo": "acao", "setor": "transporte"},

    # --- REITs (20) ---
    "SPG": {"tipo": "reit", "segmento": "shopping"},
    "MAC": {"tipo": "reit", "segmento": "shopping"},
    "KIM": {"tipo": "reit", "segmento": "shopping"},
    "REG": {"tipo": "reit", "segmento": "shopping"},
    "BXP": {"tipo": "reit", "segmento": "escritorio"},
    "VNO": {"tipo": "reit", "segmento": "escritorio"},
    "SLG": {"tipo": "reit", "segmento": "escritorio"},
    "CPT": {"tipo": "reit", "segmento": "residencial"},  # substitui AVB (fundiu com EQR em ago/2026 -> VMRK)
    "MAA": {"tipo": "reit", "segmento": "residencial"},  # substitui EQR (fundiu com AVB em ago/2026 -> VMRK)
    "ESS": {"tipo": "reit", "segmento": "residencial"},
    "UDR": {"tipo": "reit", "segmento": "residencial"},
    "WELL": {"tipo": "reit", "segmento": "saude"},
    "VTR": {"tipo": "reit", "segmento": "saude"},
    "PSA": {"tipo": "reit", "segmento": "self_storage"},
    "ARE": {"tipo": "reit", "segmento": "laboratorios_life_science"},  # substitui EXR (IPO em 2004, so ~30% da janela de construcao)
    "HST": {"tipo": "reit", "segmento": "hotel"},
    "O": {"tipo": "reit", "segmento": "varejo_triple_net"},
    "FR": {"tipo": "reit", "segmento": "industrial_logistica"},
    "PLD": {"tipo": "reit", "segmento": "industrial_logistica"},
    "WPC": {"tipo": "reit", "segmento": "diversificado"},  # substitui DRE (comprada pela Prologis em 2022, deixou de existir)
}

START_DATE = "1990-01-01"
END_DATE = "2026-07-01"

OUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "precos_acoes_reits.csv"


def baixar_fechamento(ticker: str) -> pd.Series | None:
    """Baixa um ticker e devolve a série de fechamento ajustado, ou None
    se falhar. Lida com o formato de colunas mudar entre versões do
    yfinance (MultiIndex mesmo para um único ticker, em algumas versões)."""
    try:
        hist = yf.download(
            ticker, start=START_DATE, end=END_DATE, progress=False, auto_adjust=True
        )
    except Exception as e:
        print(f"  erro ao baixar {ticker}: {e}")
        return None

    if hist is None or hist.empty:
        print(f"  aviso: nenhum dado retornado para {ticker}")
        return None

    close = hist["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.rename(ticker)
    return close


def collect():
    frames = {}
    for ticker in TICKERS:
        print(f"Baixando {ticker}...")
        serie = baixar_fechamento(ticker)
        if serie is not None:
            frames[ticker] = serie
            primeiro_dia = serie.first_valid_index()
            print(f"  ok: {len(serie)} linhas, começa em {primeiro_dia.date() if primeiro_dia is not None else '?'}")

    if not frames:
        print("Nenhum ticker foi baixado com sucesso -- nada para salvar.")
        return

    df = pd.concat(frames.values(), axis=1)
    df.index.name = "data"
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH)
    print(f"\nSalvo em {OUT_PATH} ({df.shape[0]} linhas, {df.shape[1]} ativos)")

    esperados = set(TICKERS.keys())
    baixados = set(frames.keys())
    faltando = esperados - baixados
    if faltando:
        print(f"\nAVISO: {len(faltando)} ticker(s) não baixaram: {sorted(faltando)}")

    # alerta de historico curto (comeca bem depois de 1990) -- esperado
    # para alguns (IPO tardio), mas vale conferir
    print("\nAtivos com início de histórico depois de 1995 (histórico parcial):")
    for ticker, serie in frames.items():
        primeiro_dia = serie.first_valid_index()
        if primeiro_dia is not None and primeiro_dia.year > 1995:
            print(f"  {ticker}: começa em {primeiro_dia.date()}")


if __name__ == "__main__":
    collect()
