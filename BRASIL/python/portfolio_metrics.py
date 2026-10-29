"""
Métrica de diversificação de carteira + geração de carteiras para o
backtest, em cima da matriz de distância completa (todos os pares, não
só as arestas da MST).

Duas formas de montar carteira:
  - construir_carteira_gulosa(): determinística, "farthest-first" (mais
    diversificada) ou "nearest-neighbor" (mais concentrada) -- vira a
    carteira de referência de cada nível, boa para ilustrar no artigo.
  - gerar_carteiras_aleatorias(): amostragem aleatória, usada em massa
    (~30 por nível) para dar robustez estatística ao backtest.

Depois de gerar várias carteiras aleatórias, classificar_por_nivel()
separa elas em 5 faixas de diversificação (baseado em quantis da
métrica), para alimentar o backtest por nível.
"""

import itertools
import math
import numpy as np
import pandas as pd
from pathlib import Path

DIST_PATH = Path(__file__).parent.parent / "data" / "processed" / "distance_matrix.csv"
OUT_DIR = Path(__file__).parent.parent / "data" / "processed"

TAMANHO_PRINCIPAL = 8
TAMANHO_REALISTA_DIVERSIFICADA = 18
TETO_TESOURO_CONCENTRADA = 2
NS_VARREDURA = [6, 8, 10, 12, 15, 18, 24]


def cotas_para_n(n: int) -> dict[str, int]:
    tesouro = min(7, max(2, round(n / 4)))
    resto = n - tesouro
    return {"acao": (resto + 1) // 2, "fii": resto // 2, "tesouro": tesouro}


N_NIVEIS = 5
N_CARTEIRAS_POR_NIVEL = 100

# cotas fixas da carteira diversificada (decisao: concentrada so garante
# minimo de 1 por classe e completa livre; diversificada usa cotas
# fixas para isolar o efeito de correlacao de forma mais controlada)
# N=8 e o experimento PRINCIPAL e NAO inclui a classe exterior (decisao:
# ETFs de exterior so entram quando N for expandido, para nao tirar
# espaco de acao/fii/tesouro no experimento ja validado)
COTAS_DIVERSIFICADA_PADRAO = {"acao": 3, "fii": 3, "tesouro": 2}

# experimento complementar "realista": tamanho variavel (concentrada
# continua N=8 SEM exterior, diversificada cresce para N=18 e AQUI SIM
# inclui o IVVB11) -- ajuste as cotas abaixo se quiser outra proporcao
# (soma tem que dar 18)
TAMANHO_CONCENTRADA_REALISTA = 8
COTAS_DIVERSIFICADA_REALISTA = {"acao": 6, "fii": 7, "tesouro": 4, "exterior": 1}

# excecoes ao heuristico de sufixo "11.SA" (normalmente indica FII, mas
# alguns "units" de acoes tambem usam esse sufixo -- ex: TAEE11 e a
# Taesa, uma acao/unit de energia, nao um fundo imobiliario; IVVB11 e um
# ETF de exterior (replica o S&P 500 em reais), nao um FII)
EXCECOES_TIPO = {
    "TAEE11.SA": "acao",
    "IVVB11.SA": "exterior",
}


def carregar_matriz_distancia() -> pd.DataFrame:
    return pd.read_csv(DIST_PATH, index_col=0)


def metrica_diversificacao(dist: pd.DataFrame, ativos: list[str]) -> float:
    """Distância média par a par entre os ativos da carteira (usa a
    matriz completa, não só as arestas da MST)."""
    pares = itertools.combinations(ativos, 2)
    distancias = [dist.loc[a, b] for a, b in pares]
    return float(np.mean(distancias))


def construir_carteira_gulosa(
    dist: pd.DataFrame, tamanho: int, modo: str = "diversificada", inicio: str | None = None
) -> list[str]:
    """Constrói uma carteira de forma determinística e gulosa.

    modo="diversificada": a cada passo, adiciona o ativo que MAXIMIZA a
        menor distância até os já escolhidos (farthest-first traversal)
        -- espalha os ativos o máximo possível.
    modo="concentrada": a cada passo, adiciona o ativo mais PRÓXIMO (em
        média) dos já escolhidos -- agrupa ativos parecidos.
    """
    ativos = list(dist.index)
    if inicio is None:
        # começa pelo ativo mais "central" (menor distância média a todo mundo)
        inicio = dist.mean(axis=1).idxmin()

    escolhidos = [inicio]
    restantes = [a for a in ativos if a != inicio]

    while len(escolhidos) < tamanho and restantes:
        if modo == "diversificada":
            # para cada candidato, pega a distancia minima ate o grupo ja
            # escolhido; escolhe o candidato que MAXIMIZA essa distancia minima
            candidato = max(
                restantes,
                key=lambda c: min(dist.loc[c, e] for e in escolhidos),
            )
        elif modo == "concentrada":
            # escolhe o candidato com menor distancia MEDIA ate o grupo
            candidato = min(
                restantes,
                key=lambda c: np.mean([dist.loc[c, e] for e in escolhidos]),
            )
        else:
            raise ValueError("modo deve ser 'diversificada' ou 'concentrada'")

        escolhidos.append(candidato)
        restantes.remove(candidato)

    return escolhidos


def classificar_tipo_ativo(ativo: str) -> str:
    """Classifica um ativo em 'acao', 'fii' ou 'tesouro' pelo nome/ticker."""
    if ativo in EXCECOES_TIPO:
        return EXCECOES_TIPO[ativo]
    if ativo == "selic" or ativo.startswith("prefixado_") or ativo.startswith("ipca_"):
        return "tesouro"
    if ativo.endswith("11.SA"):
        return "fii"
    return "acao"


def construir_carteira_gulosa_com_classes(
    dist: pd.DataFrame, tamanho: int, modo: str = "diversificada", tetos: dict[str, int] | None = None
) -> list[str]:
    """Igual a construir_carteira_gulosa, mas garante pelo menos 1 ativo
    de cada classe (acao, fii, tesouro) antes de completar o resto pela
    regra gulosa normal -- evita que a carteira "concentrada" vire 100%
    de uma classe só. `tetos` (opcional) limita o NÚMERO MÁXIMO de
    ativos de uma classe (ex: {"tesouro": 2}), útil porque títulos de
    Tesouro do mesmo tipo tendem a ser MUITO parecidos entre si, mais
    até que ações do mesmo setor."""
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
            break  # todas as classes restantes bateram no teto

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
    """Constrói uma carteira diversificada (farthest-first) respeitando
    cotas FIXAS por classe de ativo (ex: {'acao': 3, 'fii': 3, 'tesouro': 2}).
    Diferente de construir_carteira_gulosa_com_classes (que só garante um
    MÍNIMO de 1 por classe e deixa o resto livre), aqui a composição final
    de cada classe é exatamente a informada em `cotas`."""
    ativos = list(dist.index)
    classes = {a: classificar_tipo_ativo(a) for a in ativos}
    quota_restante = dict(cotas)
    tamanho = sum(cotas.values())

    # comeca pelo ativo mais central dentro da classe de maior cota
    # (ponto de partida neutro, mesma logica das outras construções)
    classe_inicial = max(quota_restante, key=quota_restante.get)
    candidatos_iniciais = [a for a in ativos if classes[a] == classe_inicial]
    inicio = min(candidatos_iniciais, key=lambda a: dist.loc[a].mean())

    escolhidos = [inicio]
    quota_restante[classes[inicio]] -= 1
    restantes = [a for a in ativos if a != inicio]

    while len(escolhidos) < tamanho and restantes:
        candidatos = [a for a in restantes if quota_restante.get(classes[a], 0) > 0]
        if not candidatos:
            # nao ha mais candidatos dentro das cotas pedidas -- a(s)
            # classe(s) que ainda precisavam de mais ativos esgotaram o
            # pool disponivel. Completa o restante com qualquer ativo
            # disponivel (relaxa a cota), avisando o motivo.
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
    """Remove todos os ativos de uma classe da matriz de distância --
    usado para manter o experimento principal N=8 sem ativos de
    exterior (o IVVB11 so entra no experimento N=18)."""
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
    """Calcula a métrica de cada carteira e classifica em N_NIVEIS faixas
    (quantis), do menos ao mais diversificado."""
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
        # matriz muito pequena / poucos scores distintos -- cai para
        # divisao por rank simples, sempre funciona
        df["nivel"] = pd.cut(
            df["score"].rank(method="first"), bins=n_niveis, labels=range(1, n_niveis + 1)
        )
    return df.sort_values("score").reset_index(drop=True)


def main():
    dist_completa = carregar_matriz_distancia()
    dist = remover_classe(dist_completa, "exterior")
    n_ativos_disponiveis = len(dist)
    print(f"Matriz carregada: {n_ativos_disponiveis} ativos disponíveis.\n")

    # tamanho da carteira principal (experimento controlado, N fixo)
    # ajuste TAMANHO_FIXO conforme o pool real (sugestão: 10, quando
    # tiver os 37 ativos completos -- aqui cai automaticamente para o
    # que couber, útil para rodar com a matriz de teste menor)
    tamanho_fixo = min(8, n_ativos_disponiveis - 1)

    print(f"=== Carteiras de referência (método guloso, N={tamanho_fixo}) ===")
    carteira_diversificada = construir_carteira_gulosa(dist, tamanho_fixo, "diversificada")
    carteira_concentrada = construir_carteira_gulosa(dist, tamanho_fixo, "concentrada")
    print(f"[original] Mais diversificada: {carteira_diversificada}")
    print(f"  score = {metrica_diversificacao(dist, carteira_diversificada):.4f}")
    print(f"[original] Mais concentrada:   {carteira_concentrada}")
    print(f"  score = {metrica_diversificacao(dist, carteira_concentrada):.4f}\n")

    carteira_concentrada_corrigida = construir_carteira_gulosa_com_classes(
        dist, tamanho_fixo, "concentrada", tetos={"tesouro": 2}
    )
    carteira_diversificada_cotas = construir_carteira_por_classe(
        dist, COTAS_DIVERSIFICADA_PADRAO
    )
    print(f"[corrigida] Concentrada (min 1/classe + livre): {carteira_concentrada_corrigida}")
    print(f"  score = {metrica_diversificacao(dist, carteira_concentrada_corrigida):.4f}")
    print(f"[corrigida] Diversificada (cotas {COTAS_DIVERSIFICADA_PADRAO}): {carteira_diversificada_cotas}")
    print(f"  score = {metrica_diversificacao(dist, carteira_diversificada_cotas):.4f}\n")

    print(f"=== Amostragem aleatória (N={tamanho_fixo}, {N_CARTEIRAS_POR_NIVEL * N_NIVEIS} carteiras) ===")
    carteiras_aleatorias = gerar_carteiras_aleatorias(
        dist, tamanho_fixo, N_CARTEIRAS_POR_NIVEL * N_NIVEIS
    )
    df_niveis = classificar_por_nivel(carteiras_aleatorias, dist)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "carteiras_niveis.csv"
    df_niveis.to_csv(out_path, index=False)
    print(f"Salvo em {out_path}")
    print(df_niveis.groupby("nivel", observed=True)["score"].agg(["count", "mean", "min", "max"]))


if __name__ == "__main__":
    main()
