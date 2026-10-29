"""
Coleta preços históricos de ações e FIIs via yfinance.

Pool final: 16 ações + 14 FIIs, cobrindo os setores/segmentos definidos.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path

TICKERS = {
    # --- Ações (16) ---
    "ITUB4.SA": {"tipo": "acao", "setor": "banco"},
    "BBAS3.SA": {"tipo": "acao", "setor": "banco"},
    "BBDC4.SA": {"tipo": "acao", "setor": "banco"},
    "ABCB4.SA": {"tipo": "acao", "setor": "banco_atacado_pj"},
    "WEGE3.SA": {"tipo": "acao", "setor": "industrial"},
    "EMBJ3.SA": {"tipo": "acao", "setor": "aeroespacial"},
    "PETR4.SA": {"tipo": "acao", "setor": "petroleo"},
    "VALE3.SA": {"tipo": "acao", "setor": "mineracao"},
    "TAEE11.SA": {"tipo": "acao", "setor": "energia_transmissao"},
    "CPFE3.SA": {"tipo": "acao", "setor": "energia_geracao_distribuicao"},
    "BBSE3.SA": {"tipo": "acao", "setor": "seguros"},
    "PSSA3.SA": {"tipo": "acao", "setor": "seguros"},
    "SAPR4.SA": {"tipo": "acao", "setor": "saneamento"},
    "SBSP3.SA": {"tipo": "acao", "setor": "saneamento"},
    "VIVT3.SA": {"tipo": "acao", "setor": "telecom"},
    "ABEV3.SA": {"tipo": "acao", "setor": "consumo_defensivo"},

    # --- FIIs (14) ---
    "HGLG11.SA": {"tipo": "fii", "segmento": "logistica"},
    "BTLG11.SA": {"tipo": "fii", "segmento": "logistica"},
    "XPLG11.SA": {"tipo": "fii", "segmento": "logistica"},
    "XPML11.SA": {"tipo": "fii", "segmento": "shopping"},
    "VISC11.SA": {"tipo": "fii", "segmento": "shopping"},
    "ALZR11.SA": {"tipo": "fii", "segmento": "renda_urbana_triple_net"},
    "KNRI11.SA": {"tipo": "fii", "segmento": "hibrido_lajes_logistica"},
    "BRCR11.SA": {"tipo": "fii", "segmento": "lajes_corporativas"},
    "KNCR11.SA": {"tipo": "fii", "segmento": "papel_cdi"},
    "VGIR11.SA": {"tipo": "fii", "segmento": "papel_cdi"},
    "MXRF11.SA": {"tipo": "fii", "segmento": "papel_diversificado"},
    "PORD11.SA": {"tipo": "fii", "segmento": "papel_diversificado"},
    "CPTS11.SA": {"tipo": "fii", "segmento": "papel_diversificado"},
    "RBRR11.SA": {"tipo": "fii", "segmento": "papel_ipca"},

    # --- Exterior (1) ---
    "IVVB11.SA": {"tipo": "exterior", "segmento": "sp500_brl"},
}

START_DATE = "2016-01-01"
END_DATE = "2026-07-01"

OUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "precos_acoes_fiis.csv"


def baixar_fechamento(ticker: str) -> pd.Series | None:
    """Baixa um ticker e devolve a série de fechamento ajustado, ou None
    se falhar. Lida com o formato de colunas mudar entre versões do
    yfinance (às vezes vem MultiIndex mesmo para um único ticker)."""
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
            print(f"  ok: {len(serie)} linhas")

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


if __name__ == "__main__":
    collect()
