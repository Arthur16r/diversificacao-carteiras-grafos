"""Validação isolada: executar com Python do Ubuntu, passando --origem e --relatorio.

Não modifica fontes nem resultados existentes. Copia fontes e entradas brutas
para ~/projetos/validacoes_aeds2, cria venv e reconstrói saídas.
Logs ficam no diretório informado.
"""
import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origem", type=Path, required=True)
    parser.add_argument("--relatorio", type=Path, required=True)
    parser.add_argument("--retomar", action="store_true", help="Retoma a cópia isolada registrada, sem repetir passos aprovados")
    args = parser.parse_args()
    origem = args.origem.resolve()
    relatorio = args.relatorio.resolve()
    relatorio.mkdir(parents=True, exist_ok=True)
    anterior = json.loads((relatorio / "resultado.json").read_text(encoding="utf-8")) if args.retomar else None
    base_copias = Path.home() / "projetos" / "validacoes_aeds2"
    base_copias.mkdir(parents=True, exist_ok=True)
    copia = Path(anterior["copia_isolada"]) if anterior else Path(tempfile.mkdtemp(prefix="readme_", dir=base_copias))
    passos = [p for p in anterior["passos"] if p["exit_code"] == 0] if anterior else []
    comparacoes = []
    ambiente = os.environ.copy()
    ambiente.update(MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1", PIP_DISABLE_PIP_VERSION_CHECK="1")

    def salvar():
        (relatorio / "resultado.json").write_text(json.dumps({
            "origem": str(origem), "copia_isolada": str(copia),
            "passos": passos, "comparacoes": comparacoes,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    def executar(nome, cmd, cwd=copia):
        if any(p["nome"] == nome and p["exit_code"] == 0 for p in passos):
            print(f"JA APROVADO {nome}", flush=True)
            return
        print(f"INICIO {nome}", flush=True)
        inicio = time.monotonic()
        with (relatorio / f"{nome}.log").open("w", encoding="utf-8") as f:
            resultado = subprocess.run(cmd, cwd=cwd, env=ambiente, stdout=f, stderr=subprocess.STDOUT)
        passos.append({"nome": nome, "comando": cmd, "cwd": str(cwd.relative_to(copia)),
                        "exit_code": resultado.returncode, "segundos": round(time.monotonic()-inicio, 3)})
        salvar()
        print(f"FIM {nome}: exit={resultado.returncode}", flush=True)
        if resultado.returncode:
            print((relatorio / f"{nome}.log").read_text(encoding="utf-8")[-6000:], flush=True)
            raise SystemExit(resultado.returncode)

    # Nenhum processed, binário, cache ou venv anterior é transportado.
    for mercado in (() if args.retomar else ("EUA", "BRASIL")):
        for sub in ("python", "cpp"):
            shutil.copytree(origem / mercado / sub, copia / mercado / sub,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.exe", "mst", "benchmark_prim", "mst_edges.csv", "anterior"))
        bruto = copia / mercado / "data/raw"
        bruto.mkdir(parents=True)
        entradas = (["precos_acoes_reits.csv", "fred_taxas_brutas.csv", "fred_cpi_mensal.csv"] if mercado == "EUA"
                    else ["precos_acoes_fiis.csv", "tesouro_bruto.csv", "xpml11_b3_janeiro2026.csv"])
        for nome in entradas:
            shutil.copy2(origem / mercado / "data/raw" / nome, bruto / nome)
    if not args.retomar:
        shutil.copy2(origem / "requirements.txt", copia / "requirements.txt")
        if (origem / "requirements-ubuntu-validado.txt").exists():
            shutil.copy2(origem / "requirements-ubuntu-validado.txt", copia / "requirements-ubuntu-validado.txt")
        shutil.copytree(origem / "visualizacoes", copia / "visualizacoes", ignore=shutil.ignore_patterns("__pycache__", "*.gephi", "*.png", "*.pdf"))
        shutil.copytree(origem / "artigo", copia / "artigo", ignore=shutil.ignore_patterns("resultados", "__pycache__"))
    executar("01_venv", [sys.executable, "-m", "venv", ".venv"])
    python = str(copia / ".venv/bin/python")
    requisitos = "requirements-ubuntu-validado.txt" if (copia / "requirements-ubuntu-validado.txt").exists() else "requirements.txt"
    executar("02_dependencias", [python, "-m", "pip", "install", "-r", requisitos])
    executar("03_versoes", [python, "-m", "pip", "freeze"])
    executar("04_compilador", ["g++", "--version"])
    contador = 5
    for mercado in ("EUA", "BRASIL"):
        py = copia / mercado / "python"
        cpp = copia / mercado / "cpp"
        executar(f"{contador:02}_{mercado}_testes", [python, "-B", "-m", "unittest", "discover", "-p", "test_*.py"], py)
        contador += 1
        coleta = (["collect_tesouro_fred.py", "--usar-taxas-locais"] if mercado == "EUA"
                  else ["collect_tesouro.py", "--usar-bruto-local"])
        etapas = [(python, *coleta), (python, "merge_sources.py"), (python, "build_graph.py"),
                  (python, "portfolio_metrics.py"), (python, "backtest.py")]
        for cmd in etapas:
            executar(f"{contador:02}_{mercado}_{Path(cmd[1]).stem}", list(cmd), py)
            contador += 1
        executar(f"{contador:02}_{mercado}_prim", ["make", "run"], cpp)
        contador += 1
        for script in ("mst_portfolios.py", "backtest_mst.py", "comparar_aleatorias_mst.py", "aportes_mensais.py"):
            executar(f"{contador:02}_{mercado}_{Path(script).stem}", [python, script], py)
            contador += 1
        adicionais = (["estabilidade_mst.py", "robustez_janela_comum.py"] if mercado == "EUA" else ["varredura_exterior.py"])
        for script in adicionais:
            cmd = [python, script] + (["--executavel", "../cpp/mst"] if mercado == "EUA" else [])
            executar(f"{contador:02}_{mercado}_{Path(script).stem}", cmd, py)
            contador += 1
        for nome in ("resultado_backtest_mst.csv", "comparacao_aleatorias_mst.csv", "comparacao_aportes_completa.csv", "resultado_varredura_n.csv"):
            def ler(base):
                return list(csv.DictReader(io.StringIO((base / mercado / "data/processed" / nome).read_text(encoding="utf-8-sig"))))
            esperado, atual = ler(origem), ler(copia)
            iguais = len(esperado) == len(atual)
            def equivalentes(a, b):
                if isinstance(a, dict) and isinstance(b, dict):
                    return a.keys() == b.keys() and all(equivalentes(a[k], b[k]) for k in a)
                if isinstance(a, list) and isinstance(b, list):
                    return len(a) == len(b) and all(equivalentes(x, y) for x, y in zip(a, b))
                try:
                    x, y = float(a), float(b)
                    return (math.isnan(x) and math.isnan(y)) or math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-11)
                except (ValueError, TypeError):
                    if isinstance(a, str) and isinstance(b, str) and a.startswith(("{", "[")) and b.startswith(("{", "[")):
                        return equivalentes(json.loads(a), json.loads(b))
                    return a == b
            diferencas = []
            for linha, (a, b) in enumerate(zip(esperado, atual), 1):
                iguais = iguais and a.keys() == b.keys()
                for chave in a.keys() & b.keys():
                    igual = equivalentes(a[chave], b[chave])
                    if not igual:
                        diferencas.append({"linha": linha, "campo": chave, "original": a[chave], "regenerado": b[chave]})
                    iguais = iguais and igual
            mesma_carteira_metricas = len(esperado) == len(atual) and all(
                d["campo"] == "ativos" and sorted(d["original"].split(";")) == sorted(d["regenerado"].split(";"))
                for d in diferencas)
            comparacoes.append({"mercado": mercado, "arquivo": nome, "equivalente": iguais,
                "mesma_carteira_e_metricas": mesma_carteira_metricas, "diferencas": diferencas})
            salvar()
    executar("benchmark_padrao", ["make", "benchmark"], copia / "EUA/cpp")
    executar("resumo_benchmark", [python, "resumir_benchmark_prim.py"], copia / "EUA/python")
    executar("benchmark_grandes", ["./benchmark_prim", "../data/processed/benchmark_prim_grandes",
             "../data/processed/distance_matrix.csv", "--grandes"], copia / "EUA/cpp")
    executar("resumo_benchmark_grandes", [python, "resumir_benchmark_prim.py", "--pasta",
             "../data/processed/benchmark_prim_grandes"], copia / "EUA/python")
    for script in ("gerar_fluxograma.py", "exportar_mst_eua_gephi.py", "exportar_grafo_completo_eua_gephi.py",
                   "adicionar_legenda_mst_eua.py"):
        executar(Path(script).stem, [python, "visualizacoes/"+script])
    executar("legenda_grafo", [python, "visualizacoes/adicionar_legenda_mst_eua.py", "--grafo-completo"])
    executar("consolidacao_local", [python, "artigo/consolidar_resultados.py"])
    salvar()
    print(f"FINALIZADO: {relatorio}; cópia preservada em {copia}", flush=True)


if __name__ == "__main__":
    main()
