# Brasil — estudo complementar

O experimento principal do projeto é o americano. O Brasil é um estudo
complementar com histórico disponível mais curto; não se comparam retornos
nominais em BRL e USD como se fossem a mesma oportunidade de investimento.

## Universo e fontes

O universo completo tem **38 ativos/séries**: 16 ações, 14 FIIs, sete séries
sintéticas de títulos públicos e o ETF IVVB11. O experimento principal usa
apenas os **37 domésticos**; IVVB11 entra em cenários complementares específicos.
Os tickers estão em `python/collect_stocks_fiis.py`; a classificação está em
`python/portfolio_metrics.py`, incluindo TAEE11 como ação e IVVB11 como exterior.

Os preços ajustados de ações, FIIs e ETF são coletados via yfinance. As séries
de títulos usam PUs do Tesouro Direto: Selic, prefixados curto/médio/longo e
IPCA curto/médio/longo. Esses nomes representam as regras de seleção dos
vencimentos descritas abaixo, não sete títulos fixos durante todo o histórico.
O universo delimitado não elimina vieses de seleção e sobrevivência.

## Desenho dos experimentos

- Construção: 2016–2022; teste com preços de 2023-01-02 a 2026-06-30
  (871 observações de preços na avaliação principal).
- N=8: 3 ações / 3 FIIs / 2 séries de títulos na diversificada.
- Concentrada: mínimo de um ativo por classe, máximo de dois títulos.
- N=18 complementar: 6 ações / 7 FIIs / 4 títulos / 1 exterior (IVVB11).
- Varredura doméstica: N = 6, 8, 10, 12, 15, 18 e 24, comparando
  concentrada e diversificada pelo grafo completo, sem varredura MST.
- N=8 exclui exterior tanto na seleção quanto nos caminhos da MST.
- Referência: índice sintético de Tesouro Selic já existente no projeto.
- Buy-and-hold fracionário, pesos iniciais iguais, sem custos ou rebalanceamento.

Na varredura, a cota de títulos é `t = min(7, max(2, round(N/4)))`, usando
o arredondamento do Python (empates para o inteiro par). O restante é dividido
entre ações e FIIs, com a posição extra em ações quando ímpar. Assim, N=18
doméstico usa 7/7/4; difere do complementar com IVVB11, que usa 6/7/4/1.
As cotas determinam quantidades de ativos por classe, não os pesos finais.

## Grafo e regras de seleção

`build_graph.py` calcula retornos simples diários com
`pct_change(fill_method=None)`, correlações de Pearson por pares disponíveis
e distâncias `d(i,j) = sqrt(2 * (1 - rho(i,j)))`. Usa apenas a janela de
construção; os preços posteriores ficam reservados ao backtest.
Os pares podem utilizar históricos de comprimentos diferentes.

Cada ativo/série é um vértice e cada par é uma aresta. A matriz completa de
38 ativos é `distance_matrix.csv`. O estudo principal remove exterior antes
da seleção e da MST, usando `distance_matrix_sem_exterior.csv`: 37 vértices,
666 arestas no grafo completo e 36 arestas na MST.

- **Concentrada:** começa com um representante de cada classe, escolhido
  pela menor distância média ao universo. Completa a carteira com o candidato
  de menor distância média aos já selecionados, respeitando o teto de dois
  títulos. Sua composição por classe pode diferir da diversificada.
- **Diversificada pelo grafo completo:** preenche cada cota separadamente.
  Começa pelo par mais distante da classe e adiciona o candidato com a maior
  distância mínima aos já selecionados dessa classe. Quando a cota é um,
  escolhe a maior distância média dentro da classe. Essa heurística
  farthest-first não garante ótimo global nem mínima variância financeira.
- **Diversificada pela MST:** Prim em C++ calcula a árvore dos 37 ativos.
  A seleção usa a mesma heurística por classe e cotas 3/3/2, substituindo
  a distância direta pela soma dos pesos do caminho único na árvore.
  O caminho pode passar por outras classes domésticas; IVVB11 fica excluído.
  As distâncias de caminho podem superar 2 e não são convertidas em correlações.

Os scores das carteiras principais são medidos na mesma matriz doméstica
original. O backtest também conserva variantes de seleção em seus resultados;
a comparação das três estratégias principais fica em `resultado_backtest_mst.csv`.

## Tratamento dos dados

`collect_tesouro.py` mantém os PUs individuais antes de filtrar as faixas,
para consultar o PU anterior do mesmo título quando muda sua posição no ranking.
Curto/médio/longo são primeiro/segundo/terceiro
vencimentos, não limites fixos em anos nem necessariamente o último disponível.
Quando não existe PU anterior, a implementação usa retorno zero. As
séries são proxies rolling por PU de compra; não se deve afirmar que reproduzem
perfeitamente cupons, custos de negociação ou uma carteira investível exata.

`limpar_precos.py`, usado pelo merge, trata XPML11 entre 13 e 19/01/2026
com fechamentos COTAHIST da B3 e o rendimento de R$0,92 na data ex de 19/01,
usando o fator `(preço + rendimento)/preço_anterior`. Dados e URLs estão em
`data/raw/xpml11_b3_janeiro2026.csv`; o rendimento foi conferido no
[relatório da gestão de janeiro/2026](https://filemanager-cdn.mziq.com/published/8071264f-09a1-481e-9c5e-25e5b370cd63/da7ca28f-af1c-4f72-8b9e-735de0083900_28757546000100-REL12022026V01-001111679.pdf).
O tratamento reancora a escala anterior à posterior, preserva retornos fora
da ponte e não interpola preços nem altera o arquivo bruto.

A ausência de IVVB11 em 24/10/2025 é preenchida com R$411,68, fechamento
confirmado no COTAHIST_D24102025.ZIP, sem forward-fill ou interpolação. Os
preços brutos e as demais colunas permanecem preservados.
Layout dos fechamentos: [B3](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf).

## Módulos principais

| Script | Função |
|---|---|
| `python/collect_stocks_fiis.py` | Coleta de preços ajustados de ações, FIIs e ETF |
| `python/collect_tesouro.py` | Construção das séries rolling de títulos |
| `python/limpar_precos.py`, `python/merge_sources.py` | Tratamento e alinhamento das fontes |
| `python/build_graph.py` | Matrizes de distância completa e doméstica |
| `python/portfolio_metrics.py` | Classes, cotas, seleções, scores e amostragem por níveis |
| `python/backtest.py` | Buy-and-hold, cenário N=18 e varredura doméstica |
| `cpp/mst.cpp`, `cpp/Makefile` | Compilação e execução de Prim |
| `python/mst_portfolios.py`, `python/backtest_mst.py` | Seleção pela árvore e comparação das três carteiras principais |
| `python/comparar_aleatorias_mst.py` | Comparação com 5.000 carteiras de mesmas cotas |
| `python/varredura_exterior.py` | Varredura adicional com IVVB11 |
| `python/aportes_mensais.py` | Modalidades de aportes e composição final |
| `python/test_*.py` | Testes automatizados |

O catálogo dos diagnósticos e módulos de apoio está em
[`../ORGANIZACAO.md`](../ORGANIZACAO.md).

## Execução com dados locais

Prepare o ambiente e as entradas conforme o [README da raiz](../README.md),
validado no Ubuntu 24.04. Obtenção e formatos estão em
[OBTENCAO_DADOS.md](../OBTENCAO_DADOS.md). O executor central pode rodar este
mercado, a partir da raiz:

```bash
python main.py --mercado brasil --etapa principal
python main.py --mercado brasil --etapa complementares
```

São necessárias as entradas em `BRASIL/data/raw/`:

- `precos_acoes_fiis.csv`;
- `tesouro_bruto.csv`;
- `xpml11_b3_janeiro2026.csv`.

O bruto e os índices de títulos estão no
[depósito parcial do Zenodo](https://doi.org/10.5281/zenodo.23751340), sob ODbL 1.0.
Os históricos de ações/FIIs/ETF e a tabela de fechamentos B3 ficam excluídos:
o depósito não basta para reconstruir os backtests completos.
O coletor reconstrói `tesouro_series_rolling.csv` a partir do bruto local.
Não é necessário ter arquivos processados ou binários anteriores.

A partir da **raiz do repositório**, com o ambiente ativado:

```bash
cd BRASIL/python
python -B -m unittest discover -p 'test_*.py'
python collect_tesouro.py --usar-bruto-local
python merge_sources.py
python build_graph.py
python portfolio_metrics.py
python backtest.py
cd ../cpp
make run
cd ../python
python mst_portfolios.py
python backtest_mst.py
python comparar_aleatorias_mst.py
python aportes_mensais.py
python varredura_exterior.py
cd ../..
```

Os comandos regeneram saídas locais. Compile e execute Prim antes de gerar a
carteira MST; ela é pré-requisito dos experimentos seguintes. Execute o merge
antes de `build_graph.py`: seu modo de exemplo, sem `precos_final.csv`, não
reproduz o experimento financeiro.

A compilação e a execução foram reproduzidas no Ubuntu 24.04 via WSL2,
incluindo 17 testes aprovados. As métricas e os pesos conferidos coincidiram
com Windows dentro da tolerância documentada; a ordem textual de XPLG11 e
MXRF11 na MST pode variar sem mudar a composição. Evidências e limites:
[relatório de validação](../validacao/RELATORIO.md).

## Métricas

Sharpe: média/desvio amostral dos excessos diários sobre a Selic × sqrt(252).
`razao_cagr_excedente_vol` preserva a medida anterior com nome distinto.
CAGR usa anos de 365,25 dias; volatilidade anual usa desvio amostral dos
retornos diários × `sqrt(252)`; drawdown máximo é o mínimo de
`patrimonio / maximo_acumulado - 1`. O número efetivo de ativos é
`1 / sum(peso_final**2)`.
`score_geral` considera a distância média de todos os pares da carteira;
`score_intra_classe` considera apenas pares da mesma classe.
O backtest exporta datas efetivas, pesos, número efetivo de ativos e scores
geral/intra-classe. A separação temporal não torna a avaliação um teste de
superioridade em múltiplas janelas independentes.

## Experimentos complementares

### Varredura com exterior

Variante adicional: `python3 varredura_exterior.py`. Mantém N=6 e N=8 sem
exterior e, para N=10,12,15,18,24, compara as diversificadas sem/com uma posição
em IVVB11. A cota exterior substitui uma ação, mantendo N e as cotas de FIIs e
títulos. Em N=18 resulta em 6/7/4/1, igual ao cenário complementar existente.
A concentrada permanece doméstica como referência contextual. Saída separada:
`resultado_varredura_exterior.csv`. Não substitui o experimento principal N=8
nem a varredura original. A comparação mede uma troca de exposição acionária,
não o efeito isolado de adicionar um ativo sem alterar a composição.

### Carteiras aleatórias com as mesmas cotas

`comparar_aleatorias_mst.py` avalia 5.000 carteiras distintas, seed 42, com
as mesmas cotas 3/3/2 e pesos iguais. Sharpe é o critério principal; percentuais
são posições descritivas na amostra, não p-valores nem replicações temporais.
Todas usam o mesmo universo doméstico, janela de teste e regras de execução
das diversificadas N=8. A amostra de 500 carteiras por cinco níveis de score,
gerada em `portfolio_metrics.py` e avaliada em `backtest.py`, é outro experimento.

### Aportes mensais

Aportes: R$0 ou R$100 mil iniciais e R$1.000 mensais. A compra ocorre no
fechamento do pregão seguinte ao sinal mensal. A variante `inteligente` compra
o menor retorno, mesmo se positivo, sem filtros ou limites e com repetição.
No primeiro mês a base é o primeiro preço do teste. Com capital inicial a
simulação começa no primeiro pregão; sem capital começa na primeira compra
mensal. TWR e drawdown incluem a base inicial; aportes não contam como retorno.
XIRR usa datas reais. Tabelas detalham pesos, valores, aportes, sequências e
maiores pesos observados nos fechamentos.

São quatro carteiras: concentrada N=8, grafo completo N=8, MST N=8 e
diversificada N=18 com IVVB11. Cada uma combina duas modalidades (igualitária
e menor retorno mensal anterior) e dois capitais iniciais, totalizando 16
cenários. O capital inicial é dividido igualmente; o aporte direcionado é
integralmente destinado a um único ativo. Sem capital inicial, a primeira
compra direcionada concentra 100% do patrimônio nesse ativo. As cotas do
universo selecionado não garantem pesos por classe durante a simulação.
Não há custos, impostos, rebalanceamento ou restrição a compras fracionárias.
XIRR mede o retorno dos fluxos de caixa; TWR, volatilidade, Sharpe e drawdown
descontam o efeito mecânico da entrada dos aportes.

## Onde consultar as saídas

Os caminhos abaixo são relativos a `BRASIL/data/processed/`, exceto a
exportação C++ indicada. Taxas e pesos financeiros estão em forma decimal
(por exemplo, `0.12` significa 12%); Sharpe e scores não são percentuais.

| Arquivo ou diretório | Conteúdo |
|---|---|
| `precos_final.csv` | Preços ajustados e índices de títulos alinhados |
| `distance_matrix.csv`, `distance_matrix_sem_exterior.csv` | Matrizes completa (38) e doméstica (37), calculadas na construção |
| `BRASIL/cpp/mst_edges.csv` (caminho desde a raiz) | As 36 arestas da MST doméstica exportadas por Prim |
| `distance_matrix_mst.csv`, `carteiras_mst.csv` | Caminhos domésticos na MST, seleção, pesos iniciais e procedência |
| `resultado_backtest_mst.csv`, `curvas_backtest_mst.csv` | Três carteiras principais N=8, métricas, ativos, pesos finais e evolução normalizada |
| `resultado_backtest.csv` | Variantes de seleção, cenário N=18 com exterior e resultados das 500 aleatórias por níveis |
| `carteiras_niveis.csv` | Amostra de 500 carteiras por cinco níveis de score; distinta das 5.000 com cotas |
| `resultado_varredura_n.csv` | Concentrada e diversificada doméstica nos sete valores de N |
| `resultado_varredura_exterior.csv` | Comparação adicional das diversificadas com e sem IVVB11 |
| `resultado_aleatorias_cotas.csv` | Métricas individuais das 5.000 referências com cotas 3/3/2 |
| `comparacao_aleatorias_mst.csv`, `referencias_aleatorias_cotas.csv` | Percentuais superados e métricas das duas diversificadas de referência |
| `experimento_aleatorias_cotas.json` | Regras e hashes da comparação aleatória |
| `comparacao_aportes_completa.csv` | Indicadores e patrimônio dos 16 cenários com aportes |
| `resultado_aportes_sem_inicial.csv`, `resultado_aportes_com_inicial.csv` | Resultados separados por capital inicial zero ou R$100 mil |
| `pesos_finais_aportes.csv` | Valores e pesos finais por ativo, aportes e sequências de escolhas |
| `operacoes_aportes.csv`, `diario_aportes.csv`, `experimento_aportes.json` | Sinais, compras, evolução diária e regras dos aportes |

Resultados consolidados dos dois países:
[`../artigo/resultados/RESUMO.md`](../artigo/resultados/RESUMO.md).
O benchmark de Prim está documentado no [estudo dos EUA](../EUA/README.md).
Os testes de estabilidade da MST e robustez temporal foram realizados apenas
para o universo norte-americano.

`python/anterior/`, eventuais arquivos de `data/archive/` e
`data/processed/resultado_aportes.csv` são legados e não integram o pipeline
acima. Seus resultados não devem ser misturados com os experimentos atuais.
