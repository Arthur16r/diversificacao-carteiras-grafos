# Brasil — estudo complementar

O experimento principal do projeto é o americano. O Brasil é um estudo
complementar com histórico disponível mais curto; não se comparam retornos
nominais em BRL e USD como se fossem a mesma oportunidade de investimento.

## Desenho preservado

- Construção: 2016–2022; teste: 2023-01-01 a 2026-06-30.
- N=8: 3 ações / 3 FIIs / 2 séries de títulos na diversificada.
- Concentrada: mínimo de um ativo por classe, máximo de dois títulos.
- N=18 complementar: 6 ações / 7 FIIs / 4 títulos / 1 exterior (IVVB11).
- N=8 exclui exterior tanto na seleção quanto nos caminhos da MST.
- Referência: índice sintético de Tesouro Selic já existente no projeto.
- Buy-and-hold fracionário, pesos iniciais iguais, sem custos ou rebalanceamento.

O pipeline atualizado usa farthest-first dentro de cada classe; a variante
global com cotas permanece como comparação. A MST N=8 é calculada por Prim
em C++, sobre 37 ativos. A seleção pela árvore usa soma dos pesos do caminho
único, que pode passar por outras classes do mesmo universo. Não converte
distâncias de caminhos em correlações. Scores das duas carteiras são medidos
na mesma matriz de correlação/distância original, sem exterior.

## Correções e procedência dos dados

`collect_tesouro.py` agora mantém todos os PUs individuais antes de filtrar
as faixas. Assim um título que entra na terceira faixa pode usar seu preço
anterior, mesmo se antes era o quarto vencimento disponível. A escolha continua
sendo por posição no ranking: curto/médio/longo são primeiro/segundo/terceiro
vencimentos, não limites fixos em anos nem necessariamente o último disponível.
Quando não existe PU anterior, o método legado ainda usa retorno zero. As
séries são proxies rolling por PU de compra; não se deve afirmar que reproduzem
perfeitamente cupons, custos de negociação ou uma carteira investível exata.

O CSV bruto de ações foi preservado. `limpar_precos.py`, usado pelo merge,
reconstrói a ponte de XPML11 de 13 a 19/01/2026 com fechamentos COTAHIST da B3:
110,13; 110,40; 110,51; 110,00; 109,60. Os dados e URLs estão em
`data/raw/xpml11_b3_janeiro2026.csv`. O rendimento de R$0,92 na data ex de
19/01 é considerado via `(preço + rendimento)/preço_anterior`. A data ex foi
conferida na fonte de eventos e na marcação ER da B3; o valor foi confirmado
no [relatório da gestão de janeiro/2026](https://filemanager-cdn.mziq.com/published/8071264f-09a1-481e-9c5e-25e5b370cd63/da7ca28f-af1c-4f72-8b9e-735de0083900_28757546000100-REL12022026V01-001111679.pdf).

A escala anterior é reancorada à série posterior, preservando retornos antes
e depois da ponte. Não se força igualdade dos preços nas pontas nem se interpola.
Essa correção documentada não equivale a certificar todo o histórico do provedor.
A reparação automática `repair=True` foi investigada, mas não resolveu a quebra.
O script antigo foi arquivado em `python/anterior/corrigir_xpml11.py.txt`;
não participa do pipeline atualizado. A extensão `.txt` é intencional.

A ausência de IVVB11 em 24/10/2025 é preenchida com R$411,68, fechamento
confirmado no COTAHIST_D24102025.ZIP, sem forward-fill ou interpolação. Os
preços brutos e as demais colunas permanecem preservados.
Layout dos fechamentos: [B3](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf).

## Execução com dados locais

Instale pandas, numpy, scipy e yfinance; g++/make para C++. Em `BRASIL/python`:

```bash
python3 -B -m unittest test_dados test_backtest test_mst_portfolios test_aleatorias_cotas test_aportes_mensais
python3 collect_tesouro.py --usar-bruto-local
python3 merge_sources.py
python3 build_graph.py
python3 portfolio_metrics.py
python3 backtest.py
cd ../cpp
make run
cd ../python
python3 mst_portfolios.py
python3 backtest_mst.py
python3 comparar_aleatorias_mst.py
python3 aportes_mensais.py
```

O estudo N=8 usa `distance_matrix_sem_exterior.csv`; a matriz completa de 38
ativos é mantida para o cenário N=18. A compilação e a execução foram reproduzidas
no Ubuntu 24.04 via WSL2, incluindo 17 testes e os experimentos. As tabelas
financeiras conferidas coincidiram com Windows: `../artigo/resultados/RESUMO.md`.

## Métricas e saídas

Sharpe: média/desvio amostral dos excessos diários sobre a Selic × sqrt(252).
`razao_cagr_excedente_vol` preserva a medida anterior com nome distinto.
O backtest exporta datas efetivas, pesos, número efetivo de ativos e scores
geral/intra-classe. A varredura de N usa cotas derivadas por N, sem exterior;
o cenário N=18 com exterior é separado. Não misturar essas duas configurações.

Variante adicional: `python3 varredura_exterior.py`. Mantém N=6 e N=8 sem
exterior e, para N=10,12,15,18,24, compara as diversificadas sem/com uma posição
em IVVB11. A cota exterior substitui uma ação, mantendo N e as cotas de FIIs e
títulos. Em N=18 resulta em 6/7/4/1, igual ao cenário complementar existente.
A concentrada permanece doméstica como referência contextual. Saída separada:
`resultado_varredura_exterior.csv`. Não substitui o experimento principal N=8
nem a varredura original. A comparação mede uma troca de exposição acionária,
não o efeito isolado de adicionar um ativo sem alterar a composição.

`comparar_aleatorias_mst.py` avalia 5.000 carteiras distintas, seed 42, com
as mesmas cotas 3/3/2 e pesos iguais. Sharpe é o critério principal; percentuais
são posições descritivas na amostra, não p-valores nem replicações temporais.

Aportes: R$0 ou R$100 mil iniciais e R$1.000 mensais. A compra ocorre no
fechamento do pregão seguinte ao sinal mensal. A variante `inteligente` compra
o menor retorno, mesmo se positivo, sem filtros ou limites e com repetição.
No primeiro mês a base é o primeiro preço do teste. Com capital inicial a
simulação começa no primeiro pregão; sem capital começa na primeira compra
mensal. TWR e drawdown incluem a base inicial; aportes não contam como retorno.
XIRR usa datas reais. Tabelas detalham pesos, valores, aportes, sequências e
maiores pesos observados nos fechamentos. Saídas seguem os nomes usados nos EUA.

Resultados anteriores estão preservados em `data/archive/pre_atualizacao_20261021/`.
Não usar os números antigos juntamente com os novos. `python/anterior/` e
`data/processed/resultado_aportes.csv` são legados e não entram nas execuções atuais.
