# Consolidação dos resultados

Gerada de saídas existentes. Não recalcula carteiras nem executa backtests.
Fonte das tabelas financeiras: Ubuntu WSL.

## Experimento principal

EUA: N=10, cotas 4 ações/4 REITs/2 Treasury, teste 2011-01-03 a 2026-06-30. Brasil: N=8, cotas 3 ações/3 FIIs/2 títulos, teste 2023-01-02 a 2026-06-30. As cotas se aplicam às duas diversificadas. A concentrada segue restrições próprias; compará-la não isola o efeito da topologia com composição fixa. Retornos nominais em moedas e janelas distintas não devem ser ranqueados entre países.

| Mercado | Carteira | CAGR | Vol. anual | Sharpe | Drawdown | N efetivo final |
|---|---|---|---|---|---|---|
| EUA | diversificada_mst | 12.18% | 15.33% | 0.725 | -35.25% | 7.642 |
| EUA | diversificada_grafo_completo | 11.38% | 15.29% | 0.679 | -36.73% | 7.455 |
| EUA | concentrada_referencia | 7.32% | 20.81% | 0.368 | -44.29% | 7.546 |
| BRASIL | diversificada_mst | 14.27% | 7.43% | 0.194 | -6.95% | 7.365 |
| BRASIL | diversificada_grafo_completo | 20.64% | 13.32% | 0.566 | -15.12% | 5.042 |
| BRASIL | concentrada_referencia | 19.52% | 12.03% | 0.535 | -12.33% | 7.362 |

## Referência aleatória com cotas iguais

5.000 carteiras distintas por mercado, seed 42; percentuais descritivos de carteiras superadas. Não representam p-valores nem 5.000 períodos independentes.

| Mercado | Carteira | Métrica | % superadas |
|---|---|---|---|
| EUA | diversificada_mst | sharpe | 98.64% |
| EUA | diversificada_mst | cagr | 98.04% |
| EUA | diversificada_mst | vol_anual | 67.06% |
| EUA | diversificada_mst | max_drawdown | 51.18% |
| EUA | diversificada_grafo_completo | sharpe | 94.28% |
| EUA | diversificada_grafo_completo | cagr | 91.96% |
| EUA | diversificada_grafo_completo | vol_anual | 68.48% |
| EUA | diversificada_grafo_completo | max_drawdown | 33.48% |
| BRASIL | diversificada_mst | sharpe | 32.08% |
| BRASIL | diversificada_mst | cagr | 31.02% |
| BRASIL | diversificada_mst | vol_anual | 87.42% |
| BRASIL | diversificada_mst | max_drawdown | 92.94% |
| BRASIL | diversificada_grafo_completo | sharpe | 70.40% |
| BRASIL | diversificada_grafo_completo | cagr | 80.22% |
| BRASIL | diversificada_grafo_completo | vol_anual | 4.56% |
| BRASIL | diversificada_grafo_completo | max_drawdown | 9.12% |

## Robustez temporal — EUA

| Construção | Carteira | CAGR | Vol. anual | Sharpe | Drawdown |
|---|---|---|---|---|---|
| principal_1990_2010 | grafo_completo | 11.38% | 15.29% | 0.679 | -36.73% |
| principal_1990_2010 | mst | 12.18% | 15.33% | 0.725 | -35.25% |
| comum_2003_2010 | grafo_completo | 10.40% | 15.34% | 0.620 | -37.44% |
| comum_2003_2010 | mst | 9.23% | 15.70% | 0.542 | -38.41% |

Estabilidade estrutural: 29/73 arestas preservadas (39.73%) entre 2003–2006 e 2007–2010. Isso não identifica causalmente o efeito da crise de 2008 nem mede estabilidade do desempenho.

## Custo de Prim

Implementação densa: Θ(V²) em tempo; matriz Θ(V²) em memória. Benchmark sintético: cinco sementes e dez repetições por semente/tamanho; o grafo real tem dez medições de uma entrada. Mediana e quartis; geração e leitura fora do trecho cronometrado. Memória abaixo é apenas V² doubles, não pico de RAM medido.

### local_windows

benchmark_prim: expoente log-log descritivo **2.040**. Sistema: `Windows-11-10.0.26200-SP0`.

| V | Mediana (ms) | Q25 (ms) | Q75 (ms) | Matriz (MiB) |
|---|---|---|---|---|
| 74 | 0.012 | 0.012 | 0.013 | 0.042 |
| 50 | 0.005 | 0.005 | 0.005 | 0.019 |
| 100 | 0.021 | 0.020 | 0.022 | 0.076 |
| 200 | 0.111 | 0.107 | 0.116 | 0.305 |
| 400 | 0.461 | 0.444 | 0.474 | 1.221 |
| 800 | 1.641 | 1.610 | 1.720 | 4.883 |
| 1600 | 6.629 | 6.503 | 6.798 | 19.531 |
| 3200 | 25.446 | 25.055 | 26.148 | 78.125 |

benchmark_prim_grandes: expoente log-log descritivo **2.296**. Sistema: `Windows-11-10.0.26200-SP0`.

| V | Mediana (ms) | Q25 (ms) | Q75 (ms) | Matriz (MiB) |
|---|---|---|---|---|
| 10000 | 416.330 | 409.467 | 424.917 | 762.939 |
| 20000 | 2044.531 | 2032.684 | 2077.699 | 3051.758 |

### ubuntu_wsl

benchmark_prim: expoente log-log descritivo **2.048**. Sistema: `Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39`.

| V | Mediana (ms) | Q25 (ms) | Q75 (ms) | Matriz (MiB) |
|---|---|---|---|---|
| 74 | 0.011 | 0.011 | 0.011 | 0.042 |
| 50 | 0.005 | 0.005 | 0.005 | 0.019 |
| 100 | 0.020 | 0.019 | 0.021 | 0.076 |
| 200 | 0.109 | 0.107 | 0.117 | 0.305 |
| 400 | 0.454 | 0.442 | 0.479 | 1.221 |
| 800 | 1.603 | 1.565 | 1.700 | 4.883 |
| 1600 | 6.220 | 6.090 | 6.543 | 19.531 |
| 3200 | 24.780 | 24.181 | 25.474 | 78.125 |

benchmark_prim_grandes: expoente log-log descritivo **2.329**. Sistema: `Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39`.

| V | Mediana (ms) | Q25 (ms) | Q75 (ms) | Matriz (MiB) |
|---|---|---|---|---|
| 10000 | 391.396 | 382.666 | 398.274 | 762.939 |
| 20000 | 1966.635 | 1947.020 | 2031.728 | 3051.758 |

## Conferência e arquivos auxiliares

Comparações Windows/Ubuntu: 10 tabelas; divergências: 0. A comparação usa tolerância numérica, preservando campos textuais. Hashes no manifesto referem-se ao texto UTF-8 normalizado da cópia, não aos bytes originais.

`aportes.csv` separa cenários com/sem capital inicial e modos de compra. XIRR mede o retorno dos fluxos do investidor; Sharpe e risco vêm dos retornos ajustados pelos fluxos. `varredura_n.csv` preserva todos os N. A variante brasileira com IVVB11 permanece nas fontes, separada da varredura doméstica. Arquivos originais não foram sobrescritos.

As fontes completas selecionadas ficam em `fontes/local_windows` e, quando disponível, `fontes/ubuntu_wsl`. O benchmark Ubuntu é a referência para o artigo; Windows é suplementar. Ubuntu foi executado via WSL2, não instalação Linux nativa.
