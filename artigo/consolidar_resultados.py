"""Consolida saídas existentes sem executar experimentos ou alterar suas fontes.

python -B artigo/consolidar_resultados.py --ubuntu
--ubuntu lê também a cópia WSL Ubuntu-24.04. Sem a opção, usa só a cópia local.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import platform
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = Path(__file__).resolve().parent / "resultados"
ARQUIVOS = [
    "resultado_backtest_mst.csv", "comparacao_aleatorias_mst.csv",
    "comparacao_aportes_completa.csv", "resultado_varredura_n.csv",
    "experimento_aleatorias_cotas.json", "experimento_aportes.json",
]
EXTRAS = ["EUA/data/processed/estabilidade_mst/resumo.json",
          "EUA/data/processed/robustez_janela_comum/comparacao_backtest.csv",
          "BRASIL/data/processed/resultado_varredura_exterior.csv"]
for pasta in ("benchmark_prim", "benchmark_prim_grandes"):
    for nome in ("resumo.csv", "medicoes.csv", "ambiente.json", "compilacao.txt"):
        EXTRAS.append(f"EUA/data/processed/{pasta}/{nome}")
CAMINHOS = [f"{m}/data/processed/{n}" for m in ("EUA", "BRASIL") for n in ARQUIVOS] + EXTRAS


def ler_csv(texto):
    return list(csv.DictReader(io.StringIO(texto.lstrip("\ufeff"))))


def escrever_csv(nome, linhas):
    with (SAIDA / nome).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(linhas[0]))
        writer.writeheader()
        writer.writerows(linhas)


def tabela(linhas, campos):
    cab = "| " + " | ".join(t for _, t, _ in campos) + " |"
    saida = [cab, "|" + "|".join("---" for _ in campos) + "|"]
    for linha in linhas:
        saida.append("| " + " | ".join(fmt(linha[k]) for k, _, fmt in campos) + " |")
    return "\n".join(saida)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ubuntu", action="store_true")
    args = parser.parse_args()
    origem_local = "local_windows" if platform.system() == "Windows" else "local_linux"
    fontes = {origem_local: {p: (RAIZ / p).read_text(encoding="utf-8-sig") for p in CAMINHOS}}
    if args.ubuntu:
        codigo = (
            "import pathlib,json; r=pathlib.Path('/home/arthur/projetos/diversificar-carteira'); "
            f"ps={CAMINHOS!r}; "
            "print(json.dumps({p:(r/p).read_text(encoding='utf-8-sig') for p in ps}))"
        )
        resultado = subprocess.run(["wsl", "--distribution", "Ubuntu-24.04", "--exec", "python3", "-c", codigo],
                                   capture_output=True, check=True, encoding="utf-8")
        fontes["ubuntu_wsl"] = json.loads(resultado.stdout)
    # Leitura e comparação antes de gravar a consolidação.
    comparacoes = []
    if args.ubuntu:
        for p in CAMINHOS:
            if not p.endswith(".csv") or "benchmark_prim" in p:
                continue
            a, b = ler_csv(fontes[origem_local][p]), ler_csv(fontes["ubuntu_wsl"][p])
            iguais = len(a) == len(b)
            if iguais:
                for la, lb in zip(a, b):
                    if la.keys() != lb.keys():
                        iguais = False
                        break
                    for chave in la:
                        try:
                            x, y = float(la[chave]), float(lb[chave])
                            igual = (math.isnan(x) and math.isnan(y)) or math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-12)
                        except ValueError:
                            igual = la[chave] == lb[chave]
                        iguais = iguais and igual
            comparacoes.append({"arquivo": p, "linhas_local": len(a), "linhas_ubuntu": len(b), "equivalentes": iguais})
    SAIDA.mkdir(parents=True, exist_ok=True)
    manifesto = []
    for origem, arquivos in fontes.items():
        for relativo, texto in arquivos.items():
            destino = SAIDA / "fontes" / origem / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(texto, encoding="utf-8")
            manifesto.append({"origem": origem, "arquivo": relativo,
                "sha256_texto_utf8_normalizado": hashlib.sha256(texto.encode("utf-8")).hexdigest()})
    (SAIDA / "manifesto.json").write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")
    if comparacoes:
        escrever_csv("conferencia_windows_ubuntu.csv", comparacoes)
    fonte = fontes.get("ubuntu_wsl", fontes[origem_local])
    principal, aleatorias, aportes, varredura = [], [], [], []
    for mercado in ("EUA", "BRASIL"):
        for nome, destino in (("resultado_backtest_mst.csv", principal),
                              ("comparacao_aleatorias_mst.csv", aleatorias),
                              ("comparacao_aportes_completa.csv", aportes),
                              ("resultado_varredura_n.csv", varredura)):
            destino.extend({"mercado": mercado, **r} for r in ler_csv(fonte[f"{mercado}/data/processed/{nome}"]))
    for nome, linhas in (("principal.csv", principal), ("aleatorias.csv", aleatorias),
                         ("aportes.csv", aportes), ("varredura_n.csv", varredura)):
        escrever_csv(nome, linhas)
    pct = lambda v: f"{100*float(v):.2f}%"
    numero = lambda v: f"{float(v):.3f}"
    identidade = str
    relatorio = ["# Consolidação dos resultados", "",
        "Gerada de saídas existentes. Não recalcula carteiras nem executa backtests.",
        f"Fonte das tabelas financeiras: {'Ubuntu WSL' if args.ubuntu else 'cópia local '+platform.system()}.", "",
        "## Experimento principal", "",
        "EUA: N=10, cotas 4 ações/4 REITs/2 Treasury, teste 2011-01-03 a 2026-06-30. "
        "Brasil: N=8, cotas 3 ações/3 FIIs/2 títulos, teste 2023-01-02 a 2026-06-30. "
        "As cotas se aplicam às duas diversificadas. A concentrada segue restrições próprias; "
        "compará-la não isola o efeito da topologia com composição fixa. "
        "Retornos nominais em moedas e janelas distintas não devem ser ranqueados entre países.", "",
        tabela(principal, [("mercado", "Mercado", identidade), ("carteira", "Carteira", identidade),
            ("cagr", "CAGR", pct), ("vol_anual", "Vol. anual", pct), ("sharpe", "Sharpe", numero),
            ("max_drawdown", "Drawdown", pct), ("n_efetivo_final", "N efetivo final", numero)]), "",
        "## Referência aleatória com cotas iguais", "",
        "5.000 carteiras distintas por mercado, seed 42; percentuais descritivos de carteiras superadas. "
        "Não representam p-valores nem 5.000 períodos independentes.", "",
        tabela(aleatorias, [("mercado", "Mercado", identidade), ("carteira", "Carteira", identidade),
            ("metrica", "Métrica", identidade), ("percentual_superadas", "% superadas", lambda v: f"{float(v):.2f}%")]), "",
        "## Robustez temporal — EUA", "",
        tabela(ler_csv(fonte[EXTRAS[1]]), [("janela_construcao", "Construção", identidade),
            ("carteira", "Carteira", identidade), ("cagr", "CAGR", pct), ("vol_anual", "Vol. anual", pct),
            ("sharpe", "Sharpe", numero), ("max_drawdown", "Drawdown", pct)]), ""]
    estabilidade = json.loads(fonte[EXTRAS[0]])
    relatorio += [f"Estabilidade estrutural: {estabilidade['arestas_comuns']}/{estabilidade['arestas_por_arvore']} "
        f"arestas preservadas ({100*estabilidade['fracao_preservada']:.2f}%) entre 2003–2006 e 2007–2010. "
        "Isso não identifica causalmente o efeito da crise de 2008 nem mede estabilidade do desempenho.", "",
        "## Custo de Prim", "",
        "Implementação densa: Θ(V²) em tempo; matriz Θ(V²) em memória. "
        "Benchmark sintético: cinco sementes e dez repetições por semente/tamanho; "
        "o grafo real tem dez medições de uma entrada. Mediana e quartis; geração e leitura fora do trecho cronometrado. "
        "Memória abaixo é apenas V² doubles, não pico de RAM medido.", ""]
    for ambiente, arquivos in fontes.items():
        relatorio += [f"### {ambiente}", ""]
        for pasta in ("benchmark_prim", "benchmark_prim_grandes"):
            prefixo = f"EUA/data/processed/{pasta}/"
            metadados = json.loads(arquivos[prefixo+"ambiente.json"])
            relatorio += [f"{pasta}: expoente log-log descritivo **{metadados['inclinacao_log_log_descritiva']:.3f}**. "
                f"Sistema: `{metadados['sistema']}`.", "",
                tabela(ler_csv(arquivos[prefixo+"resumo.csv"]), [("vertices", "V", identidade),
                    ("mediana_ms", "Mediana (ms)", numero), ("q25_ms", "Q25 (ms)", numero),
                    ("q75_ms", "Q75 (ms)", numero), ("matriz_dados_mib", "Matriz (MiB)", numero)]), ""]
    falhas = sum(not r["equivalentes"] for r in comparacoes)
    relatorio += ["## Conferência e arquivos auxiliares", "",
        f"Comparações Windows/Ubuntu: {len(comparacoes)} tabelas; divergências: {falhas}. "
        "A comparação usa tolerância numérica, preservando campos textuais. "
        "Hashes no manifesto referem-se ao texto UTF-8 normalizado da cópia, não aos bytes originais.", "",
        "`aportes.csv` separa cenários com/sem capital inicial e modos de compra. XIRR mede o retorno "
        "dos fluxos do investidor; Sharpe e risco vêm dos retornos ajustados pelos fluxos. "
        "`varredura_n.csv` preserva todos os N. A variante brasileira com IVVB11 permanece nas fontes, "
        "separada da varredura doméstica. Arquivos originais não foram sobrescritos.", "",
        f"As fontes completas selecionadas ficam em `fontes/{origem_local}` e, quando disponível, "
        "`fontes/ubuntu_wsl`. O benchmark Ubuntu é a referência para o artigo; Windows é suplementar. "
        "O Ubuntu dos experimentos anteriores foi executado via WSL2, não instalação Linux nativa.", ""]
    (SAIDA / "RESUMO.md").write_text("\n".join(relatorio), encoding="utf-8")
    print(f"Consolidação: {SAIDA}; tabelas comparadas: {len(comparacoes)}; divergências: {falhas}")


if __name__ == "__main__":
    main()
