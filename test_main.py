"""Verifica orquestração e pré-requisitos sem executar experimentos."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import main


class TestExecutor(unittest.TestCase):
    def test_listar_funciona_sem_dados_e_nao_executa(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(main, "RAIZ", Path(pasta)), \
                patch.object(main, "conferir") as conferir, patch.object(main.subprocess, "run") as rodar, \
                redirect_stdout(io.StringIO()):
            self.assertEqual(main.main(["--etapa", "completo", "--listar"]), 0)
        conferir.assert_not_called()
        rodar.assert_not_called()

    def test_falha_interrompe_os_comandos_seguinte(self):
        passos = [main.Passo("primeiro", Path("."), ("primeiro",)),
                  main.Passo("segundo", Path("."), ("segundo",))]
        with patch.object(main.subprocess, "run", return_value=subprocess.CompletedProcess([], 7)) as rodar, \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main.executar(passos), 7)
        self.assertEqual(rodar.call_count, 1)

    def test_falta_no_segundo_mercado_bloqueia_todo_plano(self):
        with patch.object(main, "conferir", return_value=["Arquivo ausente BRASIL/entrada.csv"]), \
                patch.object(main, "executar") as rodar, redirect_stderr(io.StringIO()):
            self.assertEqual(main.main(["--etapa", "principal", "--mercado", "ambos"]), 2)
        rodar.assert_not_called()

    def test_entrada_gerada_nao_precisa_existir_antes(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(main, "RAIZ", Path(pasta)), \
                patch.object(main.importlib.util, "find_spec", return_value=object()):
            passos = [main.Passo("gerar", Path("."), ("gerar",), saidas=(Path("gerado.csv"),)),
                      main.Passo("usar", Path("."), ("usar",), entradas=(Path("gerado.csv"),))]
            self.assertEqual(main.conferir(passos, ("BRASIL",), "principal"), [])

    def test_csv_incompativel_e_identificado_sem_rodar(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(main, "RAIZ", Path(pasta)), \
                patch.object(main.importlib.util, "find_spec", return_value=object()):
            arquivo = Path(pasta) / "fred_taxas_brutas.csv"
            arquivo.write_text("data,DGS3MO\n2000-01-01,1\n", encoding="utf-8")
            passos = [main.Passo("ler", Path("."), ("ler",), entradas=(Path(arquivo.name),))]
            erros = main.conferir(passos, ("EUA",), "principal")
            self.assertTrue(any("DFII10" in erro for erro in erros))

    def test_grandes_exige_benchmark_norte_americano(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as erro:
            main.main(["--etapa", "completo", "--mercado", "brasil", "--grandes"])
        self.assertEqual(erro.exception.code, 2)

    def test_benchmark_grande_nao_entra_por_padrao(self):
        padrao = main.plano(("EUA",), "completo")
        ampliado = main.plano(("EUA",), "completo", grandes=True)
        self.assertFalse(any("--grandes" in p.comando for p in padrao))
        self.assertEqual(sum("--grandes" in p.comando for p in ampliado), 1)

    def test_principal_compila_prim_antes_de_usar_mst(self):
        passos = main.plano(("EUA", "BRASIL"), "principal")
        for mercado in ("EUA", "BRASIL"):
            itens = [p for p in passos if p.nome.startswith(mercado + ":")]
            nomes = [p.nome for p in itens]
            self.assertLess(nomes.index(mercado + ": executar Prim"), nomes.index(mercado + ": mst_portfolios.py"))
            self.assertLess(nomes.index(mercado + ": mst_portfolios.py"), nomes.index(mercado + ": backtest_mst.py"))
        brasil = next(p for p in passos if p.nome == "BRASIL: executar Prim")
        self.assertIn("distance_matrix_sem_exterior.csv", brasil.comando[-1])


if __name__ == "__main__":
    unittest.main()
