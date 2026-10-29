"""Aportes igualitários e no pior retorno mensal, executados no pregão seguinte."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from backtest import calcular_metricas
from mst_portfolios import CARTEIRAS_MST_PATH, DIST_PATH, MST_PATH
from portfolio_metrics import (
    carregar_matriz_distancia, classificar_tipo_ativo, numero_efetivo_ativos,
    construir_carteira_gulosa_com_classes, construir_carteira_por_classe,
    TAMANHO_PRINCIPAL, TETO_TESOURO_CONCENTRADA,
    COTAS_DIVERSIFICADA_PADRAO, COTAS_DIVERSIFICADA_REALISTA,
)

PRECOS_PATH = Path(__file__).parent.parent / "data" / "processed" / "precos_final.csv"
OUT_DIR = PRECOS_PATH.parent
INICIO_TESTE = "2011-01-01"
FIM_TESTE = "2026-07-01"
VALOR_APORTE = 1000.0
CENARIOS_INICIAIS = [0.0, 100_000.0]


def carregar_precos_diarios():
    return pd.read_csv(PRECOS_PATH, index_col="data", parse_dates=True).sort_index().loc[INICIO_TESTE:FIM_TESTE]


def datas_de_aporte(precos):
    """Datas de SINAL: último pregão de cada mês, não datas de compra."""
    return pd.DatetimeIndex(precos.groupby(precos.index.to_period("M")).tail(1).index)


def metricas_da_serie(retornos, precos_referencia, inicio):
    """Base 1 na primeira aplicação: inclui o primeiro intervalo no TWR e DD."""
    curva = pd.concat([pd.Series([1.0], index=[inicio]), (1 + retornos).cumprod()])
    ref = precos_referencia.reindex(curva.index)
    if ref.isna().any():
        raise ValueError("Referência ausente nas datas da carteira")
    anos = (curva.index[-1] - inicio).days / 365.25
    rf = (ref.iloc[-1] / ref.iloc[0]) ** (1 / anos) - 1
    m = calcular_metricas(curva, rf, ref)
    return dict(retorno_twr_anual=m["cagr"], volatilidade_anual=m["vol_anual"],
                sharpe=m["sharpe"], max_drawdown=m["max_drawdown"],
                razao_twr_excedente_vol=m["razao_cagr_excedente_vol"],
                taxa_livre_risco_anual=rf)


def xirr(fluxos):
    d0 = fluxos[0][0]
    def vpl(taxa):
        return sum(valor / (1 + taxa) ** ((data - d0).days / 365.0) for data, valor in fluxos)
    return brentq(vpl, -0.99, 10.0)


def simular_aportes(precos_diarios, ativos, modo, aporte_inicial=0.0):
    """Sem filtros, sem limites e com repetição. Unidades fracionárias, sem custos.

    O primeiro sinal usa primeiro/último fechamento do primeiro mês disponível.
    Os demais usam os dois fechamentos mensais. Compra no fechamento seguinte.
    Empates seguem a ordem fixa dos ativos. Não elimina dias com dados ausentes.
    """
    if modo not in {"igualitario", "inteligente"}:
        raise ValueError("Modo inválido")
    if not ativos or len(set(ativos)) != len(ativos) or aporte_inicial < 0:
        raise ValueError("Ativos ou capital inicial inválidos")
    sub = precos_diarios[ativos].sort_index()
    if sub.index.has_duplicates or sub.isna().any().any() or (sub <= 0).any().any():
        raise ValueError("Preços ausentes, inválidos ou datas duplicadas")
    meses = datas_de_aporte(sub)
    if len(meses) < 3:
        raise ValueError("Poucos meses para simular")
    n = len(ativos)
    unidades, totais, mensais, max_pesos = [np.zeros(n) for _ in range(4)]
    escolhas, sequencias, max_sequencias = [np.zeros(n, dtype=int) for _ in range(3)]
    agenda, oportunidades = {}, []
    if aporte_inicial:
        agenda[sub.index[0]] = (None, None, None, np.full(n, aporte_inicial / n))
    for i, sinal in enumerate(meses):
        pos = sub.index.searchsorted(sinal, side="right")
        if pos == len(sub):
            continue  # não cria compra após o fim do teste
        base = sub.index[0] if i == 0 else meses[i - 1]
        sinal_ret = sub.loc[sinal].to_numpy() / sub.loc[base].to_numpy() - 1
        valores = np.full(n, VALOR_APORTE / n) if modo == "igualitario" else np.zeros(n)
        if modo == "inteligente":
            valores[int(np.argmin(sinal_ret))] = VALOR_APORTE
        agenda[sub.index[pos]] = (sinal, base, sinal_ret, valores)
        oportunidades.append(int((sinal_ret < 0).sum()))
    fluxos, operacoes, diario, retornos = [], [], [], []
    anterior, inicio = 0.0, None
    for data, linha in sub.iterrows():
        precos = linha.to_numpy()
        valores = unidades * precos
        antes = float(valores.sum())
        ret = antes / anterior - 1 if anterior > 0 else np.nan
        if anterior > 0:
            retornos.append((data, ret))
        if antes > 0:
            max_pesos = np.maximum(max_pesos, valores / antes)
        aporte = 0.0
        if data in agenda:
            sinal, base, sinal_ret, distribuicao = agenda[data]
            aporte = float(distribuicao.sum())
            unidades += distribuicao / precos
            totais += distribuicao
            if sinal is not None:
                mensais += distribuicao
                if modo == "inteligente":
                    selecionados = distribuicao > 0
                    escolhas += selecionados
                    sequencias = np.where(selecionados, sequencias + 1, 0)
                    max_sequencias = np.maximum(max_sequencias, sequencias)
            for j in np.flatnonzero(distribuicao):
                operacoes.append(dict(data_sinal=sinal, data_base_sinal=base, data_compra=data,
                                      tipo="inicial" if sinal is None else "mensal", ativo=ativos[j],
                                      valor_aportado=distribuicao[j], preco_compra=precos[j],
                                      unidades_compradas=distribuicao[j] / precos[j],
                                      retorno_sinal=np.nan if sinal is None else sinal_ret[j]))
            fluxos.append((data, -aporte))
            if inicio is None:
                inicio = data
        valores = unidades * precos
        anterior = float(valores.sum())
        if anterior > 0:
            max_pesos = np.maximum(max_pesos, valores / anterior)
            diario.append(dict(data=data, valor_antes_aporte=antes, aporte=aporte,
                               valor_depois_aporte=anterior, retorno_sem_fluxos=ret,
                               maior_peso=float((valores / anterior).max())))
    serie = pd.Series(dict(retornos), dtype=float)
    if serie.empty:
        raise ValueError("Sem retornos após a primeira aplicação")
    final = anterior
    fluxos.append((sub.index[-1], final))
    pesos = unidades * sub.iloc[-1].to_numpy() / final
    detalhes = [
        dict(ativo=a, classe=classificar_tipo_ativo(a), valor_final=unidades[j] * sub.iloc[-1, j],
             peso_final=pesos[j], percentual_final=100 * pesos[j], total_aportado_ativo=totais[j],
             aportes_mensais_ativo=mensais[j], percentual_aportes_mensais=100 * mensais[j] / mensais.sum(),
             vezes_escolhido=int(escolhas[j]), maior_sequencia_escolhas=int(max_sequencias[j]),
             maior_peso_observado=max_pesos[j])
        for j, a in enumerate(ativos)
    ]
    resultado = dict(
        xirr=xirr(fluxos), valor_final=final, total_aportado=float(totais.sum()),
        ganho_absoluto=final - totais.sum(), inicio_efetivo=inicio.date().isoformat(),
        fim_efetivo=sub.index[-1].date().isoformat(), observacoes=len(serie),
        n_aportes_mensais=len(oportunidades), aporte_mensal=VALOR_APORTE,
        meses_com_ativo_em_queda=sum(o > 0 for o in oportunidades),
        total_meses_avaliados=len(oportunidades),
        frequencia_oportunidade=float(np.mean(np.array(oportunidades) > 0)),
        media_ativos_em_queda_mes=float(np.mean(oportunidades)),
        maior_sequencia_mesmo_ativo=int(max_sequencias.max()),
        maior_peso_observado=float(max_pesos.max()), maior_peso_final=float(pesos.max()),
        n_efetivo_final=numero_efetivo_ativos(dict(zip(ativos, pesos))),
        pesos_finais=json.dumps(dict(zip(ativos, pesos)), sort_keys=True),
        vezes_escolhido=json.dumps(dict(zip(ativos, map(int, escolhas))), sort_keys=True),
        _detalhes=detalhes, _operacoes=operacoes, _diario=diario,
    )
    resultado.update(metricas_da_serie(serie, precos_diarios["tesouro_curto"], inicio))
    return resultado


def main():
    precos = carregar_precos_diarios()
    dist = carregar_matriz_distancia()
    registro = pd.read_csv(CARTEIRAS_MST_PATH).iloc[0]
    for caminho, coluna in [(DIST_PATH, "sha256_matriz_origem"), (MST_PATH, "sha256_arestas_mst")]:
        if hashlib.sha256(caminho.read_bytes()).hexdigest() != registro[coluna]:
            raise ValueError("Carteira MST desatualizada")
    carteiras = {
        "concentrada": construir_carteira_gulosa_com_classes(
            dist, TAMANHO_PRINCIPAL, "concentrada", tetos={"tesouro": TETO_TESOURO_CONCENTRADA}),
        "diversificada": construir_carteira_por_classe(dist, COTAS_DIVERSIFICADA_PADRAO),
        "diversificada_mst": registro["ativos"].split(";"),
        "diversificada_N20_realista": construir_carteira_por_classe(dist, COTAS_DIVERSIFICADA_REALISTA),
    }
    resultados, pesos, operacoes, diarios = [], [], [], []
    for inicial in CENARIOS_INICIAIS:
        for nome, ativos in carteiras.items():
            for modo in ["igualitario", "inteligente"]:
                r = simular_aportes(precos, ativos, modo, aporte_inicial=inicial)
                meta = dict(carteira=nome, modo=modo, aporte_inicial=inicial)
                det, ops, dia = [r.pop(k) for k in ["_detalhes", "_operacoes", "_diario"]]
                r.update(meta, n_ativos=len(ativos), ativos=";".join(ativos), experimento="aportes_mensais")
                resultados.append(r)
                pesos.extend(dict(meta, **d) for d in det)
                operacoes.extend(dict(meta, **o) for o in ops)
                diarios.extend(dict(meta, **d) for d in dia)
                print(f"\n{nome} | {modo} | inicial={inicial:,.0f} | XIRR={r['xirr']:.2%} | Sharpe={r['sharpe']:.3f} | maxDD={r['max_drawdown']:.2%}")
                print(pd.DataFrame(det).sort_values("peso_final", ascending=False)[[
                    "ativo", "classe", "valor_final", "percentual_final", "total_aportado_ativo", "percentual_aportes_mensais",
                    "vezes_escolhido", "maior_sequencia_escolhas", "maior_peso_observado"]].to_string(index=False))
    df = pd.DataFrame(resultados)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for inicial, sufixo in [(0, "sem_inicial"), (100_000, "com_inicial")]:
        df[df.aporte_inicial == inicial].to_csv(OUT_DIR / f"resultado_aportes_{sufixo}.csv", index=False)
    df.to_csv(OUT_DIR / "comparacao_aportes_completa.csv", index=False)
    pd.DataFrame(pesos).to_csv(OUT_DIR / "pesos_finais_aportes.csv", index=False)
    pd.DataFrame(operacoes).to_csv(OUT_DIR / "operacoes_aportes.csv", index=False)
    pd.DataFrame(diarios).to_csv(OUT_DIR / "diario_aportes.csv", index=False)
    configuracao = dict(
        cenarios_iniciais=CENARIOS_INICIAIS, aporte_mensal=VALOR_APORTE,
        sinal="Fechamento mensal; primeiro mês comparado ao primeiro pregão disponível",
        execucao="Fechamento do primeiro pregão após o sinal; sem compra após o fim dos dados",
        repeticao=True, filtros=False, unidades_fracionarias=True, custos=0,
        sha256_precos=hashlib.sha256(PRECOS_PATH.read_bytes()).hexdigest(),
        sha256_matriz=registro["sha256_matriz_origem"],
        sha256_mst=registro["sha256_arestas_mst"],
    )
    (OUT_DIR / "experimento_aportes.json").write_text(
        json.dumps(configuracao, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
