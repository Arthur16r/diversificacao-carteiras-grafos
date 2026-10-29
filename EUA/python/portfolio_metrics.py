"""
Métrica de diversificação de carteira + geração de carteiras para o
backtest, em cima da matriz de distância completa.

Lógica idêntica à do projeto brasileiro (já testada e corrigida lá),
só a classificação de ativos muda: aqui usamos uma lista EXPLÍCITA
(não heurística de sufixo de ticker), porque tickers americanos não
têm um padrão visual como o "11.SA" dos FIIs/units brasileiros que
pudesse ser usado (e que já nos gerou bug com TAEE11/IVVB11 no Brasil).
"""

import itertools
import math
import numpy as np
import pandas as pd
from pathlib import Path

DIST_PATH = Path(__file__).parent.parent / "data" / "processed" / "distance_matrix.csv"
OUT_DIR = Path(__file__).parent.parent / "data" / "processed"

N_NIVEIS = 5
N_CARTEIRAS_POR_NIVEL = 100

# -- classificacao explicita por lista (nao por heuristica de nome) --
ACOES = {
    "MSFT", "INTC", "IBM", "ORCL", "CSCO", "HPQ", "T", "VZ", "WMT", "PG",
    "KO", "PEP", "CL", "MO", "GE", "HON", "MMM", "RTX", "BA", "LMT",
    "NOC", "GD", "XOM", "CVX", "COP", "DD", "PPG", "AA", "C", "BAC",
    "JPM", "WFC", "USB", "AIG", "MET", "TRV", "BRK-B", "JNJ", "PFE",
    "MRK", "ABT", "HD", "MCD", "DIS", "SO", "DUK", "AEP", "NEE", "UNP",
    "FDX",
}
REITS = {
    "SPG", "MAC", "KIM", "REG", "BXP", "VNO", "SLG", "CPT", "MAA", "ESS",
    "UDR", "WELL", "VTR", "PSA", "ARE", "HST", "O", "FR", "PLD", "WPC",
}
TESOURO_USA = {"tesouro_curto", "tesouro_medio", "tesouro_longo", "tesouro_tips"}


def classificar_tipo_ativo(ativo: str) -> str:
    if ativo in ACOES:
        return "acao"
    if ativo in REITS:
        return "reit"
    if ativo in TESOURO_USA:
        return "tesouro"
    raise ValueError(f"Ativo não classificado: {ativo!r} -- adicione em ACOES/REITS/TESOURO_USA")


# --- tamanhos de carteira (decisao de DESENHO, tomada antes de ver resultados) ---
# N=10 principal: as cotas ficam 4 acoes / 4 REITs / 2 Treasury e o minimo
# de 1 ativo por classe pesa menos (30% da carteira, contra 37,5% em N=8).
# A varredura de sensibilidade inclui N=8 (tamanho do projeto brasileiro).
TAMANHO_PRINCIPAL = 10
NS_VARREDURA = [6, 8, 10, 12, 15, 18, 24]
TAMANHO_REALISTA_DIVERSIFICADA = 20   # experimento "realista": concentrada N=10 vs diversificada N=20
TETO_TESOURO_CONCENTRADA = 2          # so ha 4 series de Treasury e elas sao muito parecidas entre si


def cotas_para_n(n: int) -> dict[str, int]:
    """Cotas por classe para uma carteira diversificada de n ativos.
    Treasury: 2 (3 a partir de n~18, no maximo 4, que e o total disponivel);
    o restante e dividido entre acoes e REITs (acoes ficam com o ativo
    extra se for impar). Ex.: n=8 -> 3/3/2; n=10 -> 4/4/2; n=18 -> 8/7/3."""
    tesouro = min(4, max(2, int(0.15 * n + 0.5)))
    resto = n - tesouro
    return {"acao": (resto + 1) // 2, "reit": resto // 2, "tesouro": tesouro}


COTAS_DIVERSIFICADA_PADRAO = cotas_para_n(TAMANHO_PRINCIPAL)
COTAS_DIVERSIFICADA_REALISTA = cotas_para_n(TAMANHO_REALISTA_DIVERSIFICADA)


def carregar_matriz_distancia() -> pd.DataFrame:
    return pd.read_csv(DIST_PATH, index_col=0)


def metrica_diversificacao(dist: pd.DataFrame, ativos: list[str]) -> float:
    pares = itertools.combinations(ativos, 2)
    distancias = [dist.loc[a, b] for a, b in pares]
    return float(np.mean(distancias))


def construir_carteira_gulosa(
    dist: pd.DataFrame, tamanho: int, modo: str = "diversificada", inicio: str | None = None
) -> list[str]:
    ativos = list(dist.index)
    if inicio is None:
        inicio = dist.mean(axis=1).idxmin()

    escolhidos = [inicio]
    restantes = [a for a in ativos if a != inicio]

    while len(escolhidos) < tamanho and restantes:
        if modo == "diversificada":
            candidato = max(restantes, key=lambda c: min(dist.loc[c, e] for e in escolhidos))
        elif modo == "concentrada":
            candidato = min(restantes, key=lambda c: np.mean([dist.loc[c, e] for e in escolhidos]))
        else:
            raise ValueError("modo deve ser 'diversificada' ou 'concentrada'")

        escolhidos.append(candidato)
        restantes.remove(candidato)

    return escolhidos


def construir_carteira_gulosa_com_classes(
    dist: pd.DataFrame, tamanho: int, modo: str = "diversificada", tetos: dict[str, int] | None = None
) -> list[str]:
    ativos = list(dist.index)
    classes = {a: classificar_tipo_ativo(a) for a in ativos}
    tipos_presentes = sorted(set(classes.values()))

    escolhidos = []
    for tipo in tipos_presentes:
        candidatos_tipo = [a for a in ativos if classes[a] == tipo and a not in escolhidos]
        escolha = min(candidatos_tipo, key=lambda a: dist.loc[a].mean())
        escolhidos.append(escolha)

    contagem = {tipo: sum(1 for a in escolhidos if classes[a] == tipo) for tipo in tipos_presentes}

    restantes = [a for a in ativos if a not in escolhidos]
    while len(escolhidos) < tamanho and restantes:
        candidatos = restantes
        if tetos:
            candidatos = [
                a for a in candidatos
                if contagem.get(classes[a], 0) < tetos.get(classes[a], float("inf"))
            ]
        if not candidatos:
            break

        if modo == "diversificada":
            candidato = max(candidatos, key=lambda c: min(dist.loc[c, e] for e in escolhidos))
        elif modo == "concentrada":
            candidato = min(candidatos, key=lambda c: np.mean([dist.loc[c, e] for e in escolhidos]))
        else:
            raise ValueError("modo deve ser 'diversificada' ou 'concentrada'")

        escolhidos.append(candidato)
        contagem[classes[candidato]] = contagem.get(classes[candidato], 0) + 1
        restantes.remove(candidato)

    return escolhidos


def construir_carteira_com_cotas(dist: pd.DataFrame, cotas: dict[str, int]) -> list[str]:
    ativos = list(dist.index)
    classes = {a: classificar_tipo_ativo(a) for a in ativos}
    quota_restante = dict(cotas)
    tamanho = sum(cotas.values())

    classe_inicial = max(quota_restante, key=quota_restante.get)
    candidatos_iniciais = [a for a in ativos if classes[a] == classe_inicial]
    inicio = min(candidatos_iniciais, key=lambda a: dist.loc[a].mean())

    escolhidos = [inicio]
    quota_restante[classes[inicio]] -= 1
    restantes = [a for a in ativos if a != inicio]

    while len(escolhidos) < tamanho and restantes:
        candidatos = [a for a in restantes if quota_restante.get(classes[a], 0) > 0]
        if not candidatos:
            faltando = {c: q for c, q in quota_restante.items() if q > 0}
            print(f"aviso: cotas nao totalmente satisfeitas (sem ativos suficientes para "
                  f"{faltando}); completando com ativos de outras classes")
            candidatos = restantes

        candidato = max(candidatos, key=lambda c: min(dist.loc[c, e] for e in escolhidos))
        escolhidos.append(candidato)
        quota_restante[classes[candidato]] = quota_restante.get(classes[candidato], 0) - 1
        restantes.remove(candidato)

    return escolhidos


def construir_carteira_por_classe(dist: pd.DataFrame, cotas: dict[str, int]) -> list[str]:
    """Carteira diversificada: farthest-first DENTRO de cada classe,
    isoladamente, respeitando cotas fixas por classe.

    Por que dentro da classe: na versao global (construir_carteira_com_cotas)
    a distancia de um candidato era medida contra TODOS os ativos ja
    escolhidos; um ativo de outra classe, que esta perto do candidato por
    acaso, mascarava a redundancia entre dois ativos da MESMA classe (ex.:
    dois FIIs de logistica no projeto brasileiro). Aqui a diversidade
    dentro de cada classe e garantida pela propria regra, e a diversidade
    entre classes e medida no resultado (score_geral vs score_intra_classe).

    Ponto de partida de cada classe: o PAR mais distante da classe (e nao o
    ativo mais "central"), o que tambem evita que a diversificada e a
    concentrada partam do mesmo ativo pivo. Classe com cota 1: o ativo mais
    atipico (maior distancia media aos demais da classe)."""
    ativos = list(dist.index)
    classes = {a: classificar_tipo_ativo(a) for a in ativos}
    escolhidos: list[str] = []

    for classe, cota in cotas.items():
        membros = [a for a in ativos if classes[a] == classe]
        if cota <= 0:
            continue
        if len(membros) < cota:
            print(f"aviso: classe {classe!r} tem {len(membros)} ativos, cota pedida {cota}; usando todos")
            escolhidos.extend(membros)
            continue

        sub = dist.loc[membros, membros]
        if cota == 1:
            escolha = [sub.mean(axis=1).idxmax()]
        else:
            vals = np.nan_to_num(sub.values.astype(float), nan=-1.0)
            np.fill_diagonal(vals, -1.0)
            i, j = np.unravel_index(np.argmax(vals), vals.shape)
            escolha = [membros[i], membros[j]]
            restantes = [m for m in membros if m not in escolha]
            while len(escolha) < cota and restantes:
                cand = max(restantes, key=lambda c: min(sub.loc[c, e] for e in escolha))
                escolha.append(cand)
                restantes.remove(cand)
        escolhidos.extend(escolha)

    return escolhidos


def metrica_intra_classe(dist: pd.DataFrame, ativos: list[str]) -> float:
    """Distancia media entre pares da MESMA classe (diversidade dentro das
    classes). Complementa metrica_diversificacao (todos os pares)."""
    classes = {a: classificar_tipo_ativo(a) for a in ativos}
    pares = [(a, b) for a, b in itertools.combinations(ativos, 2) if classes[a] == classes[b]]
    if not pares:
        return float("nan")
    return float(np.mean([dist.loc[a, b] for a, b in pares]))


def numero_efetivo_ativos(pesos: dict[str, float]) -> float:
    """Numero efetivo de ativos = 1 / HHI. Em buy-and-hold os pesos derivam:
    um vencedor pode dominar a carteira e esse numero cai bem abaixo de N."""
    w = np.array(list(pesos.values()), dtype=float)
    w = w / w.sum()
    return float(1.0 / np.sum(w ** 2))


def remover_classe(dist: pd.DataFrame, classe: str) -> pd.DataFrame:
    ativos_da_classe = [a for a in dist.index if classificar_tipo_ativo(a) == classe]
    return dist.drop(index=ativos_da_classe, columns=ativos_da_classe)


def gerar_carteiras_aleatorias(
    dist: pd.DataFrame, tamanho: int, n_carteiras: int, seed: int = 42
) -> list[list[str]]:
    rng = np.random.default_rng(seed)
    ativos = list(dist.index)
    carteiras = []
    for _ in range(n_carteiras):
        escolha = rng.choice(ativos, size=tamanho, replace=False)
        carteiras.append(list(escolha))
    return carteiras


def gerar_carteiras_aleatorias_com_cotas(
    dist: pd.DataFrame, cotas: dict[str, int], n_carteiras: int, seed: int = 42
) -> list[list[str]]:
    """Amostra carteiras distintas uniformemente, com cotas exatas por classe.

    Não altera o gerador original nem usa preços ou resultados do backtest.
    Dentro de uma carteira não há repetição; amostras duplicadas são rejeitadas.
    """
    pools = {classe: [a for a in dist.index if classificar_tipo_ativo(a) == classe]
             for classe in cotas}
    if not dist.index.is_unique or not isinstance(n_carteiras, int) or n_carteiras < 0:
        raise ValueError("Universo ou quantidade de carteiras inválidos")
    possibilidades = 1
    for classe, cota in cotas.items():
        if not isinstance(cota, int) or cota < 0 or cota > len(pools[classe]):
            raise ValueError(f"Cota inválida: {classe}={cota}")
        possibilidades *= math.comb(len(pools[classe]), cota)
    if sum(cotas.values()) == 0 or n_carteiras > possibilidades:
        raise ValueError("Quantidade solicitada incompatível com as cotas")
    rng = np.random.default_rng(seed)
    carteiras, vistas = [], set()
    while len(carteiras) < n_carteiras:
        escolhidos = []
        for classe, cota in cotas.items():
            escolhidos.extend(sorted(rng.choice(pools[classe], size=cota, replace=False).tolist()))
        chave = tuple(sorted(escolhidos))
        if chave not in vistas:
            vistas.add(chave)
            carteiras.append(escolhidos)
    return carteiras


def classificar_por_nivel(
    carteiras: list[list[str]], dist: pd.DataFrame, n_niveis: int = N_NIVEIS
) -> pd.DataFrame:
    registros = []
    for i, carteira in enumerate(carteiras):
        score = metrica_diversificacao(dist, carteira)
        registros.append({"carteira_id": i, "ativos": ";".join(carteira), "score": score})

    df = pd.DataFrame(registros)
    try:
        df["nivel"] = pd.qcut(
            df["score"], q=n_niveis, labels=range(1, n_niveis + 1), duplicates="drop"
        )
    except ValueError:
        df["nivel"] = pd.cut(
            df["score"].rank(method="first"), bins=n_niveis, labels=range(1, n_niveis + 1)
        )
    return df.sort_values("score").reset_index(drop=True)


def main():
    dist_completa = carregar_matriz_distancia()
    n_ativos_disponiveis = len(dist_completa)
    print(f"Matriz carregada: {n_ativos_disponiveis} ativos disponíveis.\n")

    tamanho = min(TAMANHO_PRINCIPAL, n_ativos_disponiveis - 1)

    print(f"=== Carteiras de referência (N={tamanho}) ===")
    concentrada = construir_carteira_gulosa_com_classes(
        dist_completa, tamanho, "concentrada", tetos={"tesouro": TETO_TESOURO_CONCENTRADA}
    )
    diversificada = construir_carteira_por_classe(dist_completa, COTAS_DIVERSIFICADA_PADRAO)
    for nome, cart in [("Concentrada", concentrada), ("Diversificada (por classe)", diversificada)]:
        print(f"{nome}: {cart}")
        print(f"  score geral = {metrica_diversificacao(dist_completa, cart):.4f} | "
              f"score intra-classe = {metrica_intra_classe(dist_completa, cart):.4f}")
    print(f"Cotas da diversificada: {COTAS_DIVERSIFICADA_PADRAO}\n")

    print(f"=== Amostragem aleatória ({N_CARTEIRAS_POR_NIVEL * N_NIVEIS} carteiras de N={tamanho}) ===")
    carteiras_aleatorias = gerar_carteiras_aleatorias(
        dist_completa, tamanho, N_CARTEIRAS_POR_NIVEL * N_NIVEIS
    )
    df_niveis = classificar_por_nivel(carteiras_aleatorias, dist_completa)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "carteiras_niveis.csv"
    df_niveis.to_csv(out_path, index=False)
    print(f"Salvo em {out_path}")
    print(df_niveis.groupby("nivel", observed=True)["score"].agg(["count", "mean", "min", "max"]))


if __name__ == "__main__":
    main()
