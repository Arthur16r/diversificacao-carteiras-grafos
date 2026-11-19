"""Executor por terminal. Coordena os scripts existentes, sem recoletar dados."""

import argparse
import ast
import csv
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


RAIZ = Path(__file__).resolve().parent
ETAPAS = ("testes", "principal", "complementares", "benchmark", "visualizacoes", "completo")


@dataclass(frozen=True)
class Passo:
    nome: str
    pasta: Path
    comando: tuple[str, ...]
    entradas: tuple[Path, ...] = ()
    saidas: tuple[Path, ...] = ()


def executavel(nome):
    return nome + (".exe" if os.name == "nt" else "")


def plano(mercados, etapa, grandes=False, figura="todas"):
    passos = []
    if etapa in ("testes", "completo"):
        passos.append(Passo("Testes do executor", Path("."),
                            (sys.executable, "-B", "-m", "unittest", "test_main", "visualizacoes.test_gerar_grafos")))
        for mercado in mercados:
            passos.append(Passo(f"{mercado}: testes automatizados", Path(mercado) / "python",
                                (sys.executable, "-B", "-m", "unittest", "discover", "-p", "test_*.py")))
    for mercado in mercados:
        base = Path(mercado)
        py, cpp, raw, processed = (base / p for p in ("python", "cpp", "data/raw", "data/processed"))
        matriz = processed / "distance_matrix.csv"
        matriz_prim = processed / ("distance_matrix_sem_exterior.csv" if mercado == "BRASIL" else "distance_matrix.csv")
        precos = processed / "precos_final.csv"
        arestas = cpp / "mst_edges.csv"
        carteira = processed / "carteiras_mst.csv"
        prim = cpp / executavel("mst")

        def script(arquivo, args=(), entradas=(), saidas=()):
            passos.append(Passo(f"{mercado}: {arquivo}", py,
                                (sys.executable, "-B", arquivo, *map(str, args)),
                                (py / arquivo, *entradas), tuple(saidas)))

        if etapa in ("principal", "completo"):
            if mercado == "EUA":
                titulos = raw / "tesouro_retornos.csv"
                script("collect_tesouro_fred.py", ("--usar-taxas-locais",),
                       (raw / "fred_taxas_brutas.csv", raw / "fred_cpi_mensal.csv"), (titulos,))
                entradas_merge = (raw / "precos_acoes_reits.csv", titulos)
            else:
                titulos = raw / "tesouro_series_rolling.csv"
                script("collect_tesouro.py", ("--usar-bruto-local",),
                       (raw / "tesouro_bruto.csv",), (titulos,))
                entradas_merge = (raw / "precos_acoes_fiis.csv", raw / "xpml11_b3_janeiro2026.csv", titulos)
            script("merge_sources.py", entradas=entradas_merge, saidas=(precos,))
            script("build_graph.py", entradas=(precos,), saidas=tuple(dict.fromkeys((matriz, matriz_prim))))
            script("portfolio_metrics.py", entradas=(matriz,), saidas=(processed / "carteiras_niveis.csv",))
            script("backtest.py", entradas=(precos, matriz, processed / "carteiras_niveis.csv"),
                   saidas=(processed / "resultado_backtest.csv", processed / "resultado_varredura_n.csv"))
            passos.append(Passo(f"{mercado}: compilar Prim", cpp, ("make", "-B", "mst"),
                                (cpp / "Makefile", cpp / "mst.cpp"), (prim,)))
            passos.append(Passo(f"{mercado}: executar Prim", cpp,
                                (str(RAIZ / prim), str(RAIZ / matriz_prim)),
                                (prim, matriz_prim), (arestas,)))
            script("mst_portfolios.py", entradas=(matriz, arestas),
                   saidas=(carteira, processed / "distance_matrix_mst.csv"))
            script("backtest_mst.py", entradas=(precos, matriz, carteira, arestas),
                   saidas=(processed / "resultado_backtest_mst.csv", processed / "curvas_backtest_mst.csv"))
        if etapa in ("complementares", "completo"):
            dependencias = (precos, matriz, carteira, arestas)
            script("comparar_aleatorias_mst.py", entradas=dependencias)
            script("aportes_mensais.py", entradas=dependencias)
            if mercado == "EUA":
                script("estabilidade_mst.py", ("--executavel", RAIZ / prim), (precos, matriz, prim))
                script("robustez_janela_comum.py", ("--executavel", RAIZ / prim),
                       (*dependencias, prim, processed / "resultado_backtest_mst.csv"))
            else:
                script("varredura_exterior.py", entradas=(precos, matriz))
    if "EUA" in mercados and etapa in ("benchmark", "completo"):
        cpp = Path("EUA/cpp")
        processed = Path("EUA/data/processed")
        programa = cpp / executavel("benchmark_prim")
        matriz = processed / "distance_matrix.csv"
        passos.append(Passo("EUA: compilar benchmark", cpp, ("make", "-B", "benchmark_prim"),
                            (cpp / "Makefile", cpp / "benchmark_prim.cpp", cpp / "mst.cpp"), (programa,)))
        for pasta, argumentos in [("benchmark_prim", ())] + ([("benchmark_prim_grandes", ("--grandes",))] if grandes else []):
            destino = processed / pasta
            passos.append(Passo(f"EUA: medir {pasta}", cpp,
                                (str(RAIZ / programa), str(RAIZ / destino), str(RAIZ / matriz), *argumentos),
                                (programa, matriz), (destino / "medicoes.csv",)))
            passos.append(Passo(f"EUA: resumir {pasta}", Path("EUA/python"),
                                (sys.executable, "-B", "resumir_benchmark_prim.py", "--pasta", str(RAIZ / destino)),
                                (Path("EUA/python/resumir_benchmark_prim.py"), destino / "medicoes.csv")))
    if etapa in ("visualizacoes", "completo"):
        pasta = Path("visualizacoes")
        if figura in ("fluxograma", "todas"):
            gerador = pasta / "gerar_fluxograma_horizontal.py"
            passos.append(Passo("Fluxograma horizontal", Path("."),
                                (sys.executable, "-B", str(gerador)), (gerador,)))
        if figura in ("grafos", "todas"):
            gerador = pasta / "gerar_grafos.py"
            for mercado in mercados:
                base = Path(mercado)
                processed = base / "data/processed"
                matriz = processed / ("distance_matrix_sem_exterior.csv" if mercado == "BRASIL" else "distance_matrix.csv")
                entradas = (gerador, base / "python/portfolio_metrics.py", matriz,
                            processed / "distance_matrix.csv", processed / "carteiras_mst.csv",
                            base / "cpp/mst_edges.csv")
                passos.append(Passo(f"{mercado}: imagens do grafo e da MST", Path("."),
                                    (sys.executable, "-B", str(gerador), "--mercado", mercado.lower()),
                                    tuple(dict.fromkeys(entradas))))
    return passos


def colunas_entrada(caminho):
    nome = caminho.name
    if nome.startswith("precos_acoes_"):
        script = "collect_stocks_reits.py" if caminho.parts[0] == "EUA" else "collect_stocks_fiis.py"
        arvore = ast.parse((RAIZ / caminho.parts[0] / "python" / script).read_text(encoding="utf-8"))
        for no in arvore.body:
            if isinstance(no, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TICKERS" for t in no.targets):
                return {"data", *ast.literal_eval(no.value)}
        raise ValueError("Lista TICKERS ausente no coletor")
    return {
        "fred_taxas_brutas.csv": {"data", "DGS3MO", "DGS5", "DGS10", "DFII10"},
        "fred_cpi_mensal.csv": {"data", "CPIAUCNS"},
        "tesouro_bruto.csv": {"Tipo Titulo", "Data Vencimento", "Data Base", "PU Compra Manha"},
        "xpml11_b3_janeiro2026.csv": {"data", "fechamento", "provento_ex"},
    }.get(nome)


def conferir(passos, mercados, etapa):
    erros, produzidos, conferidos = [], set(), set()
    modulos = {"numpy", "pandas"} if etapa != "visualizacoes" else {"matplotlib"}
    if any("gerar_grafos.py" in p.comando[2] for p in passos if len(p.comando) > 2):
        modulos.update(("numpy", "pandas"))
    if etapa in ("testes", "complementares", "completo"):
        modulos.add("scipy")
    if "EUA" in mercados and etapa in ("testes", "principal", "completo"):
        modulos.add("requests")
    if etapa in ("testes", "completo") or ("EUA" in mercados and etapa == "benchmark"):
        modulos.add("matplotlib")
    for modulo in sorted(modulos):
        if importlib.util.find_spec(modulo) is None:
            erros.append(f"Dependência ausente neste Python: {modulo}. Consulte a instalação no README.")
    if any(p.comando[0] == "make" for p in passos):
        for ferramenta in ("make", "g++"):
            if shutil.which(ferramenta) is None:
                erros.append(f"Ferramenta ausente no PATH: {ferramenta}. No Ubuntu: sudo apt install g++ make.")
    for passo in passos:
        if not (RAIZ / passo.pasta).is_dir():
            erros.append(f"Diretório ausente: {passo.pasta}")
        for entrada in passo.entradas:
            if entrada in produzidos or entrada in conferidos:
                continue
            conferidos.add(entrada)
            absoluto = RAIZ / entrada
            if not absoluto.is_file() or absoluto.stat().st_size == 0:
                erros.append(f"Arquivo ausente ou vazio: {entrada}")
                continue
            campos = colunas_entrada(entrada)
            if campos:
                try:
                    with absoluto.open(encoding="utf-8-sig", newline="") as arquivo:
                        leitor = csv.reader(arquivo)
                        cabecalho = next(leitor)
                        if len(cabecalho) != len(set(cabecalho)):
                            erros.append(f"Colunas duplicadas: {entrada}")
                        faltas = campos - set(cabecalho)
                        if faltas:
                            erros.append(f"Colunas ausentes em {entrada}: {', '.join(sorted(faltas))}")
                        if not any(leitor):
                            erros.append(f"CSV sem linhas de dados: {entrada}")
                except (OSError, UnicodeError, csv.Error, StopIteration) as exc:
                    erros.append(f"CSV ilegível: {entrada} ({type(exc).__name__})")
        produzidos.update(passo.saidas)
    return erros


def executar(passos):
    ambiente = os.environ.copy()
    ambiente.update(PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg", PYTHONUNBUFFERED="1")
    for i, passo in enumerate(passos, 1):
        print(f"\n[{i}/{len(passos)}] {passo.nome}", flush=True)
        resultado = subprocess.run(passo.comando, cwd=RAIZ / passo.pasta, env=ambiente, check=False)
        if resultado.returncode:
            print(f"Execução interrompida: {passo.nome} (código {resultado.returncode}).", file=sys.stderr)
            return resultado.returncode if resultado.returncode > 0 else 1
    print("\nTodas as etapas selecionadas foram concluídas.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mercado", choices=("eua", "brasil", "ambos"), default="ambos")
    parser.add_argument("--etapa", choices=ETAPAS, required=True)
    parser.add_argument("--grandes", action="store_true", help="Inclui benchmark de 10 mil e 20 mil vértices; somente com EUA e benchmark/completo.")
    parser.add_argument("--figura", choices=("grafos", "fluxograma", "todas"),
                        help="Somente em visualizacoes; padrão: todas. Grafos usam as matrizes e a MST locais.")
    consulta = parser.add_mutually_exclusive_group()
    consulta.add_argument("--listar", action="store_true", help="Mostra os comandos e diretórios, sem executar nem exigir dados.")
    consulta.add_argument("--verificar", action="store_true", help="Confere entradas e ferramentas, sem executar etapas.")
    args_lista = sys.argv[1:] if argv is None else argv
    if not args_lista:
        parser.print_help()
        return 0
    args = parser.parse_args(args_lista)
    mercados = ("EUA", "BRASIL") if args.mercado == "ambos" else (args.mercado.upper(),)
    tem_benchmark = "EUA" in mercados and args.etapa in ("benchmark", "completo")
    if args.etapa == "benchmark" and "EUA" not in mercados:
        parser.error("O benchmark está organizado em EUA/cpp; use --mercado eua ou ambos.")
    if args.grandes and not tem_benchmark:
        parser.error("--grandes exige EUA e --etapa benchmark ou completo.")
    if args.figura and args.etapa != "visualizacoes":
        parser.error("--figura exige --etapa visualizacoes.")
    passos = plano(mercados, args.etapa, args.grandes, args.figura or "todas")
    if args.listar:
        for i, passo in enumerate(passos, 1):
            comando = subprocess.list2cmdline(passo.comando) if os.name == "nt" else shlex.join(passo.comando)
            print(f"{i:02}. {passo.nome}\n    diretório: {passo.pasta}\n    {comando}")
        print("\nPlano apenas listado; nenhum comando foi executado.")
        return 0
    erros = conferir(passos, mercados, args.etapa)
    if erros:
        print("Pré-requisitos incompletos; nenhuma etapa foi executada:", file=sys.stderr)
        for erro in erros:
            print(f"- {erro}", file=sys.stderr)
        print("Consulte OBTENCAO_DADOS.md. Complementares, benchmark e imagens dos grafos exigem a etapa principal concluída.", file=sys.stderr)
        return 2
    if args.verificar:
        print(f"Pré-requisitos conferidos para {len(passos)} etapas. Nenhum comando foi executado.")
        return 0
    try:
        return executar(passos)
    except OSError as exc:
        print(f"Não foi possível iniciar um comando: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
