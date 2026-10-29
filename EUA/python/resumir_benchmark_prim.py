"""Resumo e figuras do benchmark; executar após make benchmark em EUA/cpp."""
import hashlib
import argparse
import json
import os
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent.parent / "data" / "processed" / "benchmark_prim"


def main(pasta: Path = PASTA):
    global PASTA
    PASTA = pasta.resolve()
    df = pd.read_csv(PASTA / "medicoes.csv")
    if df.empty or df.tempo_ns.le(0).any() or df.duplicated(["origem", "vertices", "seed", "repeticao"]).any():
        raise ValueError("Medições incompletas ou tempos inválidos")
    if not df.groupby(["origem", "vertices", "seed"]).size().eq(10).all():
        raise ValueError("Esperadas dez repetições por entrada")
    for _, grupo in df[df.origem == "sintetico"].groupby("vertices"):
        if set(grupo.seed) != {42, 43, 44, 45, 46}:
            raise ValueError("Esperadas cinco sementes por tamanho sintético")
    registros = []
    for (origem, v), grupo in df.groupby(["origem", "vertices"], sort=True):
        mediana = grupo.tempo_ns.median()
        registros.append({"origem": origem, "vertices": v, "n_medicoes": len(grupo),
                          "n_seeds": grupo.seed.nunique(), "mediana_ms": mediana / 1e6,
                          "q25_ms": grupo.tempo_ns.quantile(.25) / 1e6,
                          "q75_ms": grupo.tempo_ns.quantile(.75) / 1e6,
                          "ns_por_v2": mediana / v**2,
                          "arestas": int(grupo.arestas.iloc[0]),
                          "visitas_teoricas_lacos": int(grupo.visitas_teoricas_lacos.iloc[0]),
                          "matriz_dados_mib": int(grupo.bytes_matriz_dados.iloc[0]) / 2**20})
    resumo = pd.DataFrame(registros)
    s = resumo[resumo.origem == "sintetico"].sort_values("vertices").copy()
    s["razao_tempo_dobrar_v"] = (s.mediana_ms / s.mediana_ms.shift(1)).where(s.vertices == 2 * s.vertices.shift(1))
    resumo = resumo.merge(s[["vertices", "origem", "razao_tempo_dobrar_v"]], on=["vertices", "origem"], how="left")
    resumo.to_csv(PASTA / "resumo.csv", index=False)
    df.groupby(["origem", "vertices", "seed"]).tempo_ns.median().rename("mediana_ns").to_csv(PASTA / "medianas_por_seed.csv")
    # Inclinação descritiva log-log; não substitui a demonstração dos laços.
    slope = float(np.polyfit(np.log(s.vertices), np.log(s.mediana_ms), 1)[0])
    cpp = Path(__file__).resolve().parent.parent / "cpp"
    executavel = cpp / ("benchmark_prim.exe" if (cpp / "benchmark_prim.exe").exists() else "benchmark_prim")
    ambiente = {"sistema": platform.platform(), "processador": platform.processor(),
                "processador_env": os.environ.get("PROCESSOR_IDENTIFIER"), "cpu_logicas": os.cpu_count(),
                "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                "matplotlib": matplotlib.__version__, "inclinacao_log_log_descritiva": slope,
                "sha256_prim": hashlib.sha256((cpp / "mst.cpp").read_bytes()).hexdigest(),
                "sha256_benchmark": hashlib.sha256((cpp / "benchmark_prim.cpp").read_bytes()).hexdigest(),
                "sha256_executavel": hashlib.sha256(executavel.read_bytes()).hexdigest(),
                "observacao": "Memória reportada é só V² doubles, sem overhead. Medições de lotes aquecidos incluem alocações, destruição e consumo O(1) do resultado."}
    (PASTA / "ambiente.json").write_text(json.dumps(ambiente, ensure_ascii=False, indent=2), encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    erros = np.vstack([s.mediana_ms - s.q25_ms, s.q75_ms - s.mediana_ms])
    axes[0].errorbar(s.vertices, s.mediana_ms, yerr=erros, fmt="o-", capsize=3, label="Mediana e intervalo interquartil")
    ancora = s.iloc[-1]
    axes[0].plot(s.vertices, ancora.mediana_ms * (s.vertices / ancora.vertices)**2, "--", label="Referência proporcional a V²")
    axes[0].set(xscale="log", yscale="log", xlabel="Número de vértices (V)", ylabel="Tempo por chamada (ms)")
    axes[0].legend(fontsize=8)
    axes[1].plot(s.vertices, s.ns_por_v2, "o-")
    axes[1].set(xscale="log", xlabel="Número de vértices (V)", ylabel="Tempo / V² (ns)")
    for ax in axes:
        ax.grid(True, alpha=.25)
    fig.suptitle("Prim com matriz de adjacência — grafos completos sintéticos")
    fig.tight_layout()
    fig.savefig(PASTA / "benchmark_prim.png", dpi=200)
    fig.savefig(PASTA / "benchmark_prim.pdf")
    plt.close(fig)
    print(resumo.to_string(index=False))
    print(f"Inclinação log-log descritiva: {slope:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pasta", type=Path, default=PASTA)
    main(parser.parse_args().pasta)
