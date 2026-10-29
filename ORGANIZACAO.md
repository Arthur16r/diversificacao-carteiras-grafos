# Catálogo dos códigos

Revisão em 26/10/2026. Não foram alteradas fórmulas, seleção, algoritmos ou resultados.

## Pipeline dos dois mercados

Os módulos homônimos em `EUA/python/` e `BRASIL/python/` são distintos,
adaptados a cada mercado. Execute no diretório correspondente.

| Script | Função |
|---|---|
| `collect_stocks_reits.py` / `collect_stocks_fiis.py` | Coleta de preços de ações e fundos |
| `collect_tesouro_fred.py` / `collect_tesouro.py` | Construção das séries sintéticas de títulos |
| `merge_sources.py` | Alinhamento e tratamento das fontes |
| `build_graph.py` | Matriz de distâncias por correlações na construção |
| `portfolio_metrics.py` | Métricas, restrições, seleção e amostragem |
| `backtest.py` | Buy-and-hold, níveis aleatórios e varredura de N |
| `mst_portfolios.py` | Seleção por caminhos na árvore do C++ |
| `backtest_mst.py` | Comparação MST, grafo completo e concentrada |
| `comparar_aleatorias_mst.py` | Referência de 5.000 aleatórias com cotas |
| `aportes_mensais.py` | Experimento complementar de aportes |
| `test_*.py` | Testes automatizados |

`portfolio_metrics.py` contém mais que métricas: `selecao_carteiras.py` seria
uma alternativa de nome, mas não foi renomeado. É importado por vários
módulos e os comandos atuais já foram validados. A mistura de português e
inglês não justifica trocar todos os nomes na etapa final.

## Específicos dos EUA

| Script | Função |
|---|---|
| `diagnosticar_saltos.py` | Inspeção de retornos extremos e cobertura |
| `estabilidade_mst.py` | Sobreposição de arestas e validação estrutural |
| `robustez_janela_comum.py` | Sensibilidade à construção 2003–2010 |
| `resumir_benchmark_prim.py` | Tabelas, ambiente e figuras do benchmark |

## Específicos do Brasil

| Script | Função |
|---|---|
| `limpar_precos.py` | Tratamento atual de XPML11, usado pelo merge e testes |
| `diagnosticar_acoes_fiis.py` | Inspeção de saltos no teste |
| `diagnosticar_tesouro.py` | Inspeção de saltos nas séries de títulos |
| `inspecionar_xpml11.py` | Consulta da janela de janeiro/2026 processada |
| `checar_correlacao_negativa.py` | Consulta de pares com correlação negativa |
| `varredura_exterior.py` | Variante de N com IVVB11 |

Diagnósticos são úteis para rastrear dados. Seus limiares indicam pontos para
inspeção, não prova de erro ou impossibilidade financeira. Não integram a seleção.

## Histórico

`BRASIL/python/anterior/` guarda versões antigas de `backtest.py`,
`portfolio_metrics.py` e `aportes_mensais.py`, fora do pipeline final.

O antigo `BRASIL/python/corrigir_xpml11.py` foi movido sem modificar seu conteúdo
para `BRASIL/python/anterior/corrigir_xpml11.py.txt`. Interpolava dados e
sobrescrevia o bruto; foi substituído por `limpar_precos.py`. A extensão
`.txt` identifica código histórico fora da execução. Nada foi excluído.
Os arquivos antigos têm caminhos/imports antigos e não constituem uma
reprodução autônoma do experimento anterior.

## Apoio

| Script | Função |
|---|---|
| `visualizacoes/gerar_fluxograma.py` | Fluxograma SVG/PDF/PNG |
| `visualizacoes/exportar_mst_eua_gephi.py` | Exportação validada para Gephi |
| `artigo/consolidar_resultados.py` | Consolidação e comparação Windows/Ubuntu |

Não foi criado menu ou `main.py` central. A sequência está no README da raiz;
uma interface unificada seria conveniência, não requisito do enunciado.
