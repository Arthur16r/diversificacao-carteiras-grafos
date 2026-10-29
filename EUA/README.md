# Diversificação via MST — Mercado Americano

Experimento principal do projeto. O projeto brasileiro (mesma metodologia,
já testada e corrigida) passa a ser o estudo complementar/réplica num
mercado emergente.

## Janelas de tempo

- **Construção do grafo/MST (in-sample)**: 1990-01-01 a 2010-12-31
- **Backtest (fora da amostra)**: 2011-01-01 a 2026-07-01

## Pool de ativos (74)

- **50 ações**: líderes de mercado por setor entre 1990-2010 (baseado na
  composição histórica do S&P 500, não nas maiores empresas de hoje)
- **20 REITs**: equivalente aos FIIs brasileiros
- **4 séries de Treasury (FRED, não fundos)**: curto (3 meses), médio
  (5 anos), longo (10 anos) e TIPS (10 anos reais, histórico só desde ~2003)

Substituições feitas por eventos corporativos reais (documentadas):
DRE→WPC (Duke Realty comprada pela Prologis, 2022), UTX→RTX (fusão
UTC/Raytheon, 2020; o negócio ficou mais estreito após a saída de Carrier e
Otis), DOW→PPG (a "DOW" atual é uma empresa nova, cindida em 2019),
AVB→CPT e EQR→MAA (AvalonBay e Equity Residential se fundiram em
ago/2026, virando VMRK), EXR→ARE (EXR abriu capital só em 2004; regra:
cobertura mínima de ~50% da janela de construção).

Regra de limpeza (merge_sources.py): VTR é descartado antes de 01/05/1998,
quando era a Vencor Inc. (operadora de hospitais), antes de virar REIT.

## Série nominal aproximada de TIPS

`tesouro_tips` permanece ausente antes da primeira taxa DFII10 disponível;
nessa primeira data o índice começa em 100. Dados ausentes não são retornos zero.
O CPI-U mensal sem ajuste sazonal (`CPIAUCNS`) é salvo separadamente em
`data/raw/fred_cpi_mensal.csv`. O CPI de referência diário segue:

```
RefCPI(t) = CPI(m-3) + (dia-1)/dias_no_mes * [CPI(m-2) - CPI(m-3)]
r_real(t) ≈ y_real(t-1) * dias_corridos/365.25 - 8.5 * Δy_real(t)
1 + r_nominal(t) = (1 + r_real(t)) * RefCPI(t)/RefCPI(t-1)
```

Taxas `y` estão em decimal. A interpolação considera dias corridos, incluindo
fins de semana entre observações. Não há arredondamento do RefCPI nesta
aproximação. A metodologia usa duration constante: não reproduz cupons,
convexidade, rollover ou piso de resgate de um título específico.
Exceção documentada: outubro/2025 está ausente no CPI do FRED; para indexar
TIPS usa-se o valor de contingência oficial 325.604, sem alterar o CSV bruto
([tabela do Treasury](https://www.treasurydirect.gov/instit/annceresult/tipscpi/2025/CPI_20251218.pdf)).
Referência da indexação: [TreasuryDirect — Appendix B](https://www.treasurydirect.gov/files/laws-and-regulations/auction-regulations-uoc/auct-reg-gsr-31-cfr-356.pdf).

Para reconstruir usando as taxas já salvas, execute em `python/`:

```bash
python3 -B -m unittest test_tips
python3 collect_tesouro_fred.py --usar-taxas-locais
python3 merge_sources.py
python3 diagnosticar_saltos.py
python3 build_graph.py
python3 portfolio_metrics.py
python3 backtest.py
python3 aportes_mensais.py
```

O CPI é baixado se ainda não existir. Resultados anteriores à reconstrução
não refletem esta correção; a mudança no grafo também pode mudar carteiras.

## Tamanhos de carteira (decisão de desenho, tomada antes de ver resultados)

- **Experimento principal: N=10.** Concentrada: mínimo 1 ativo por classe,
  resto livre, no máximo 2 Treasury. Diversificada: cotas fixas
  4 ações / 4 REITs / 2 Treasury, escolha por classe (ver abaixo).
- **Experimento "realista"**: concentrada N=10 vs diversificada N=20.
- **Varredura de sensibilidade**: N = 6, 8, 10, 12, 15, 18, 24. O N=8 está
  incluído para permitir comparação com o Brasil.

## Seleção da carteira diversificada: farthest-first por classe

A distância é medida **dentro de cada classe**, isoladamente, começando pelo
par mais distante da classe. Isso evita que um ativo de outra classe,
próximo por acaso, esconda a redundância entre dois ativos da mesma classe,
e evita que concentrada e diversificada partam do mesmo ativo pivô.
O resultado é avaliado por duas métricas: `score_geral` (todos os pares) e
`score_intra_classe` (só pares da mesma classe). O `backtest.py` também roda
as variantes antigas (`original`, `cotas_global`) para comparação.

## Estrutura

```
data/raw/        precos_acoes_reits.csv, fred_taxas_brutas.csv, tesouro_retornos.csv
data/processed/  precos_final.csv, distance_matrix.csv, carteiras_niveis.csv,
                 resultado_backtest.csv, resultado_varredura_n.csv, resultados de aportes
python/
  collect_stocks_reits.py   ações/REITs via yfinance
  collect_tesouro_fred.py   taxas do FRED -> índice sintético por duration
  merge_sources.py          junta as fontes + regras de limpeza documentadas
  diagnosticar_saltos.py    procura saltos suspeitos em todo o histórico
  build_graph.py            matriz de correlação (pairwise) e distância, só in-sample
  portfolio_metrics.py      métricas e construção das carteiras
  backtest.py               backtest buy-and-hold + varredura de N
  aportes_mensais.py        aportes mensais (igualitário vs inteligente), XIRR e TWR
cpp/
  mst.cpp                   grafo (matriz de adjacência) + MST via Prim, O(V^2)
  Makefile
```

## Como rodar (Linux / Ubuntu 24.04)

```bash
pip install pandas numpy scipy yfinance requests
cd python
python3 collect_stocks_reits.py
python3 collect_tesouro_fred.py      # precisa de chave FRED em FRED_API_KEY
python3 merge_sources.py
python3 diagnosticar_saltos.py       # conferir antes de seguir
python3 build_graph.py
python3 portfolio_metrics.py
python3 backtest.py
python3 aportes_mensais.py

cd ../cpp
make && make run
```

## Decisões herdadas do projeto brasileiro

- Correlação *pairwise* (nunca `.dropna()` geral antes de `.corr()`).
- O grafo é construído só com dados in-sample; o backtest usa só o período seguinte.
- Classificação de ativos por lista explícita, não por heurística de nome.
- Buy-and-hold sem rebalanceamento; os pesos derivam, e o número efetivo de
  ativos no fim (1/HHI) mostra o quanto.
- O experimento principal usa o grafo completo. O módulo adicional
  `mst_portfolios.py` seleciona uma diversificada usando caminhos na MST.

## Seleção adicional pela MST

Depois de gerar `distance_matrix.csv`, execute a partir de `EUA/`:

```bash
cd cpp
make run
cd ../python
python3 -B -m unittest test_mst_portfolios
python3 mst_portfolios.py
```

A árvore global do Prim contém os 74 ativos. A distância entre dois ativos é
a soma dos pesos no caminho único da árvore, que pode atravessar outras classes.
Usam-se os pesos originais de `distance_matrix.csv` para evitar o arredondamento
da exportação C++. Essas distâncias podem superar 2 e não são correlações.
A seleção por classe começa pelo par mais distante e continua por farthest-first,
como no método principal; empates seguem a ordem original da matriz. Cotas:
4 ações, 4 REITs e 2 Treasury, com pesos iniciais iguais de 10%.

Saídas adicionais em `data/processed/`: `distance_matrix_mst.csv` e
`carteiras_mst.csv`. A carteira registra as cotas, ativos, pesos e hashes das
entradas. O módulo não lê preços de teste e não executa comparações de desempenho.
Sempre regenere as arestas com `make run` após alterar a matriz original.

Para avaliar a carteira MST, execute `python3 backtest_mst.py` em `python/`.
O script compara MST e grafo completo com N=10 e cotas 4/4/2; inclui a
concentrada como referência contextual, cuja composição por classe é diferente.
Usa o mesmo período de teste, pesos iniciais iguais e nenhum rebalanceamento.
Os scores estruturais são medidos na matriz original em todas as carteiras.
Salva `resultado_backtest_mst.csv` e `curvas_backtest_mst.csv` sem substituir
o backtest principal. A interpretação é descritiva de uma janela histórica;
a robustez temporal foi executada e consolidada (ver README da raiz).

### Referência aleatória com as mesmas cotas

Em `python/`, execute `python3 comparar_aleatorias_mst.py`. O gerador adicional
`gerar_carteiras_aleatorias_com_cotas` sorteia 5.000 carteiras distintas com
4 ações, 4 REITs e 2 Treasury (seed 42), sem usar desempenho para selecionar.
Mantém o universo, datas, pesos iguais e ausência de rebalanceamento das duas
diversificadas. O gerador original sem cotas continua disponível e inalterado.
Sharpe é o critério principal; CAGR, volatilidade e drawdown são complementares.
`percentual_superadas` conta resultados estritamente piores, com tolerância
numérica de 1e-12; empates são registrados separadamente. Menor volatilidade
e drawdown menos negativo são considerados melhores nas respectivas métricas.

Saídas em `data/processed/`: `resultado_aleatorias_cotas.csv`,
`referencias_aleatorias_cotas.csv`, `comparacao_aleatorias_mst.csv` e
`experimento_aleatorias_cotas.json` (configuração e hashes das entradas).
Os percentuais descrevem a posição entre carteiras na janela histórica usada;
não são p-valores nem evidência de superioridade em janelas independentes.

## Experimentos complementares

### Robustez da janela de construção comum

Em `python/`, execute `python3 robustez_janela_comum.py` após compilar o Prim
(opcional `--executavel /caminho/para/mst`). Reconstrói grafo e MST com os mesmos
74 ativos em 2003–2010, exigindo cobertura completa e sem retornos anteriores à
janela. Seleciona as diversificadas N=10, cotas 4/4/2, e mantém exatamente o
backtest de 2011–junho/2026. Compara com as seleções principais, recalculadas
pelas mesmas funções e no mesmo período, sem alterar seus arquivos.
Saídas em `data/processed/robustez_janela_comum/`: matriz, MST, caminhos,
carteiras, métricas, curvas e configuração. Scores estruturais nesta tabela são
específicos de cada matriz de construção; não usam uma régua comum entre janelas.
É uma análise de sensibilidade da seleção, não um teste temporal independente
nem uma nova escolha do experimento principal baseada no resultado.

### Benchmark de Prim

Em `cpp/`, execute `make benchmark`. O executável reutiliza a função `primMST`
de `mst.cpp`; a macro `PRIM_SEM_MAIN` exclui apenas a interface de linha de comando.
O relógio `std::chrono::steady_clock` mede lotes de chamadas, incluindo alocações
e destruição internas e consumo O(1) do resultado para impedir otimização indevida.
Ficam fora do tempo: leitura, geração de grafos, validação e escrita de CSV.

Entradas: matriz real de 74 ativos e grafos completos sintéticos de 50, 100,
200, 400, 800, 1600 e 3200 vértices, com cinco sementes (42–46) por tamanho.
Pesos sintéticos simétricos em [0.1, 2), sem pretensão de representar correlações.
Há aquecimento, calibração para lotes de pelo menos aproximadamente 20 ms e dez
medições por entrada; não se mede desempenho de uma chamada fria isolada.
Os tamanhos são processados em ordem crescente, portanto condições térmicas e
outros processos podem influenciar os tempos. Não se usa tempo para validar correção.

Em `python/`, execute `python3 resumir_benchmark_prim.py` (requer matplotlib).
Resultados em `data/processed/benchmark_prim/`: medições individuais, medianas por
semente, resumo com quartis, razão ao dobrar V, gráfico PNG/PDF e ambiente da execução.
A figura compara tempo com uma referência V² e mostra tempo/V². Os dados reais
aparecem no resumo, separados da série sintética. A execução Ubuntu 24.04 via
WSL2 já foi validada; as fontes estão preservadas na consolidação da raiz.

Extensão para 10 mil e 20 mil vértices (mesmo protocolo, arquivos separados),
em `cpp/`: `./benchmark_prim ../data/processed/benchmark_prim_grandes ../data/processed/distance_matrix.csv --grandes`.
Depois, em `python/`: `python3 resumir_benchmark_prim.py --pasta ../data/processed/benchmark_prim_grandes`.
Há um único grafo grande alocado por vez, com cinco sementes e dez medições por
semente. A matriz de 10 mil exige 800.000.000 bytes (0,8 GB ou 0,745 GiB);
a de 20 mil exige 3.200.000.000 bytes (3,2 GB ou 2,980 GiB), sem overhead.

Decisão para a consolidação do artigo: discutir explicitamente o limite de
memória da representação densa, pois o grafo financeiro é COMPLETO. Só os pesos
de 100 mil vértices exigiriam 80 GB; um milhão exigiria 8 TB. Esses valores são
cálculos analíticos, não medições nem tentativas de alocação. Não extrapolar
tempos medidos em memória para situações com paginação em disco.
A compilação e a execução foram validadas no Ubuntu 24.04 via WSL2.
As medições abaixo são Windows; não confundir com o benchmark Ubuntu
preservado em `../artigo/resultados/fontes/ubuntu_wsl/`.
Na extensão executada, as medianas foram 416,33 ms (10 mil) e 2044,53 ms
(20 mil), razão de 4,91 ao dobrar V. Cada mediana agrega 50 medições
(cinco sementes, dez repetições). Esses dois pontos não demonstram uma nova
complexidade: Θ(V²) continua sendo a análise dos laços; efeitos de memória,
cache e ambiente são hipóteses para os desvios, sem isolamento causal neste teste.

Análise teórica: V iterações completas de duas varreduras de V posições dão
2V² visitas aos corpos dos laços, independentemente dos pesos de um grafo completo.
As operações internas não têm todas o mesmo custo. Tempo Θ(V²), matriz Θ(V²),
memória auxiliar Θ(V), E=V(V−1)/2. `visitas_teoricas_lacos` é uma contagem analítica,
não uma instrumentação. A memória indicada é somente V²*sizeof(double), sem
overhead dos vetores e sem medição de pico do processo. A inclinação log-log é
descritiva e não substitui a análise da complexidade.

### Estabilidade das arestas da MST

Depois de compilar Prim, execute em `python/`: `python3 estabilidade_mst.py`
(opcional: `--executavel /caminho/para/mst`). Compara as janelas fixas
2003–2006 e 2007–2010 com os mesmos 74 ativos e cobertura completa.
Cada janela recalcula os retornos dentro de suas fronteiras e executa o C++
em diretório separado. Confere árvores conexas, sem ciclos, com V−1 arestas,
e compara custos com Kruskal independente. Métrica principal: arestas não
orientadas em comum / 73. Jaccard usa outro denominador: união das arestas.
Não há limiar automático de aprovação nem busca de janelas que melhorem o resultado.
Saídas em `data/processed/estabilidade_mst/`: matrizes e arestas por janela,
comparação das conexões, graus, cobertura e resumo com hashes das entradas.
O teste não modifica a árvore principal nem avalia retorno de carteiras.

O backtest buy-and-hold usa `sharpe = média(r_carteira - r_tesouro_curto) /
desvio_padrão(r_carteira - r_tesouro_curto) * sqrt(252)`, com retornos simples
diários nas mesmas datas e desvio amostral (`ddof=1`). A anualização pressupõe
ausência de autocorrelação relevante. `tesouro_curto` é a referência sintética
aproximada já descrita no coletor. A antiga medida `(CAGR - CAGR_referência) /
volatilidade_anual` permanece como `razao_cagr_excedente_vol` nos dois CSVs do
backtest, para comparação. Os aportes mensais também usam excessos diários no
Sharpe; a comparação com buy-and-hold deve considerar fluxos e datas efetivas.

### Aportes mensais revisados

Execute `python3 aportes_mensais.py` em `python/`. Cenários de US$0 e US$100 mil
iniciais, com US$1.000 mensais. Carteiras: concentrada N=10, diversificada pelo
grafo N=10, diversificada pela MST N=10 e N=20 complementar. O capital inicial
é dividido igualmente no primeiro fechamento do teste. Os aportes seguintes
são igualitários ou vão integralmente para o pior retorno do mês anterior
(rótulo legado `inteligente`), mesmo se todos subirem; repetições são permitidas.

O sinal usa o último fechamento mensal, comparado ao anterior. No primeiro
mês usa o primeiro fechamento disponível como base, sem buscar dados anteriores
ao teste. A compra ocorre no fechamento do primeiro pregão seguinte; se não
houver esse pregão no período, o sinal não gera fluxo. Empates seguem a ordem
dos ativos. Não há rebalanceamento, taxas, impostos nem restrição a frações.

Sem capital inicial, a rentabilidade começa na primeira compra mensal; com
capital inicial começa no primeiro pregão. As datas efetivas são exportadas.
Os aportes são adicionados após medir o retorno das posições já existentes.
TWR anualizado e drawdown incluem a base 1 da primeira compra; Sharpe usa
excessos diários sobre o Treasury curto nos mesmos intervalos. XIRR usa datas
reais dos fluxos e base de 365 dias; TWR usa anos de 365,25 dias, como o backtest.

O terminal mostra os percentuais finais de todos os ativos. Saídas adicionais:
`comparacao_aportes_completa.csv`, `pesos_finais_aportes.csv` (classe, valor e
peso final, total aplicado, participação nos aportes MENSAIS, escolhas e maior
sequência de escolhas), `operacoes_aportes.csv` (sinal e execução),
`diario_aportes.csv` e `experimento_aportes.json` (regras e hashes). Os CSVs
`resultado_aportes_sem_inicial.csv` e `resultado_aportes_com_inicial.csv` são
atualizados; o último agora corresponde a US$100 mil, não US$1 milhão.
O maior peso observado considera fechamentos antes e depois dos aportes, não
máximas intradiárias. No cenário sem capital inicial, a primeira compra da
estratégia de pior retorno necessariamente concentra 100% num ativo; isso é
parte da regra. A sequência de escolhas conta somente aportes mensais dessa
estratégia, não a alocação inicial nem as compras igualitárias.

- Conferir com `inspecionar_datas.py`: ORCL (1992, 1997, 1999), USB 1992,
  HD 2000-10-12, HST 1991, RTX 2001-09-17.
- Estabilidade da MST entre subperíodos (arestas em comum / (V-1)).
- Benchmark de tempo do Prim conforme V cresce (exigido pelo enunciado).
