# Diversificação de carteiras com grafos e árvores

Projeto de AEDS2 que investiga risco e desempenho de carteiras selecionadas
por grafos de correlação e árvores geradoras mínimas. EUA é o estudo principal;
Brasil é o complementar. O objetivo é investigar empiricamente os benefícios
e as limitações da diversificação por heurísticas de distância, sem implementar
otimização média-variância nem presumir superioridade em qualquer período.

## Organização

- `EUA/` e `BRASIL/`: `python/` para pipeline, experimentos e testes;
  `cpp/` para Prim e Makefile; `data/raw/` para entradas e `data/processed/`
  para matrizes, carteiras e resultados.
- `BRASIL/python/anterior/`: histórico fora do pipeline atual; não executar.
- `visualizacoes/`: fluxograma, imagens automáticas dos grafos e exportação para Gephi.
- `artigo/resultados/`: consolidação com fontes Windows e Ubuntu separadas.
- `main.py`: executor central dos testes e experimentos pelo terminal.

Catálogo: [ORGANIZACAO.md](ORGANIZACAO.md).
Resultados: [artigo/resultados/RESUMO.md](artigo/resultados/RESUMO.md).
Os materiais de redação e passagem para outras ferramentas são mantidos
localmente e não são necessários para executar o projeto.

## Preparação no Ubuntu 24.04

Na raiz do projeto:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip g++ make
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-ubuntu-validado.txt
```

`requirements-ubuntu-validado.txt` registra as versões completas do ambiente
novo de validação (Ubuntu 24.04, Python 3.12). `requirements.txt` permanece
como lista curta das dependências diretas, sem fixação, para outros ambientes.
As versões dos benchmarks anteriores estão nas fontes consolidadas.
A validação foi feita no Ubuntu 24.04 via WSL2, com 20 testes nos EUA e 17 no Brasil.
Relatório da reconstrução em ambiente novo: [validacao/RELATORIO.md](validacao/RELATORIO.md).

## Entradas necessárias para reconstruir sem recoleta

Os dados devem estar nos caminhos abaixo antes de executar o pipeline:

- `EUA/data/raw/precos_acoes_reits.csv`
- `EUA/data/raw/fred_taxas_brutas.csv`
- `EUA/data/raw/fred_cpi_mensal.csv`
- `BRASIL/data/raw/precos_acoes_fiis.csv`
- `BRASIL/data/raw/tesouro_bruto.csv`
- `BRASIL/data/raw/xpml11_b3_janeiro2026.csv`

As séries sintéticas de títulos e todos os arquivos de `data/processed/`
são gerados pelos comandos abaixo; não são pré-requisitos dessa reconstrução.
Há um **depósito parcial**, publicado em 06/11/2026:
[Dados de títulos públicos e benchmark de Prim — DOI 10.5281/zenodo.23751340](https://doi.org/10.5281/zenodo.23751340).
Inclui taxas/CPI e índices sintéticos dos EUA, dados e índices de títulos
brasileiros e as medições originais de Prim no Ubuntu. O ZIP preserva os
caminhos `EUA/data/raw/` e `BRASIL/data/raw/` para os dados de títulos; as
medições ficam em `BENCHMARK_UBUNTU/` dentro do pacote.

**O depósito não contém todas as entradas acima e não reproduz sozinho os
backtests completos.** Ficam excluídos preços Yahoo, fechamentos B3, tabelas
combinadas, matrizes e resultados financeiros. O Yahoo Finance respondeu à
consulta do autor informando que os dados fornecidos pelo serviço não devem
ser redistribuídos e não autorizou a coleta programática descrita no pedido.
Por isso, os históricos de preços não acompanham o código nem o depósito.
O esclarecimento sobre a publicação de resultados derivados ainda está pendente.
Os CSVs de preços e as saídas volumosas não são versionados no Git: clonar
somente o código não basta para executar os experimentos. Tabelas consolidadas,
figuras e fontes selecionadas estão preservadas no repositório do projeto.

Para nova coleta FRED, defina sua chave no terminal, sem inseri-la no código:

```bash
export FRED_API_KEY="sua_chave"
```

A reconstrução com os três CSVs locais dos EUA não precisa dessa chave.

**Como obter e preparar essas entradas:** consulte
[OBTENCAO_DADOS.md](OBTENCAO_DADOS.md). O roteiro mostra a extração do Zenodo,
as alternativas de coleta FRED/Tesouro e os formatos das entradas excluídas.
Ainda é necessária uma fonte com direitos de uso adequados para os históricos
de ações/fundos/ETF; não há uma substituição integral validada neste projeto.

## Executor central

Na raiz, com o ambiente ativado, `python main.py` mostra a ajuda. Os scripts
individuais abaixo continuam disponíveis. O executor usa o mesmo Python do
ambiente atual e chama cada script no diretório correspondente, interrompendo
a sequência no primeiro erro.

```bash
python main.py --mercado ambos --etapa testes
python main.py --mercado eua --etapa principal
python main.py --mercado brasil --etapa principal
python main.py --mercado ambos --etapa complementares
python main.py --mercado eua --etapa benchmark
python main.py --mercado ambos --etapa visualizacoes
```

| Etapa | Conteúdo e pré-requisitos |
|---|---|
| `testes` | Testes do executor e dos mercados escolhidos; usam dados sintéticos, sem arquivos de mercado |
| `principal` | Reconstrução local dos títulos, merge, grafo, seleções, backtest/varredura, compilação de Prim, MST e comparação principal; exige os brutos listados acima |
| `complementares` | 5.000 aleatórias e aportes; EUA também estabilidade/robustez, Brasil também IVVB11; exige `principal` concluído |
| `benchmark` | Compila e mede Prim e gera resumos; organizado em EUA/cpp e exige a matriz real já gerada |
| `visualizacoes` | Imagens automáticas da MST e do grafo completo dos mercados escolhidos, mais fluxograma horizontal; os grafos exigem `principal` concluído |
| `completo` | Testes, principal, complementares e visualizações dos mercados escolhidos; inclui benchmark padrão se EUA estiver selecionado |

Para executar essa sequência completa, com todas as entradas locais disponíveis:

```bash
python main.py --mercado ambos --etapa completo
```

Examine os comandos ou confira os pré-requisitos sem executar experimentos:

```bash
python main.py --mercado ambos --etapa completo --listar
python main.py --mercado ambos --etapa principal --verificar
```

`--listar` funciona sem dados e sem compilador. `--verificar` confere entradas,
cabeçalhos básicos e dependências antes de qualquer etapa. A execução normal
regenera as saídas locais selecionadas; os brutos existentes não são recoletados.
Nenhum coletor Yahoo é chamado pelo executor. Os projetos editados manualmente
no Gephi e a consolidação do artigo têm seus procedimentos próprios descritos abaixo.
As compilações usam `make -B` para reconstruir o executável com a configuração
atual, inclusive ao alternar entre ambientes. Validação do executor e seus
limites: [validacao/EXECUTOR.md](validacao/EXECUTOR.md).

O benchmark de 10 mil/20 mil vértices exige a opção explícita `--grandes`:

```bash
python main.py --mercado eua --etapa benchmark --grandes
```

Sem essa opção, `completo` inclui apenas o benchmark padrão. O benchmark fica
no estudo dos EUA; `--mercado brasil --etapa benchmark` não é uma combinação
válida. Em Windows sem g++/make no PATH, use o ambiente Ubuntu/WSL validado.

## Testes

Na raiz, com o ambiente ativado. Execute os mercados separadamente, pois
possuem módulos com os mesmos nomes:

```bash
cd EUA/python
python -B -m unittest discover -p 'test_*.py'
cd ../../BRASIL/python
python -B -m unittest discover -p 'test_*.py'
cd ../..
```

O comando central `python main.py --mercado ambos --etapa testes` coordena
esses dois processos e os testes do próprio executor. O teste brasileiro da
ponte XPML11 usa uma fonte sintética substituída em memória; não exige o CSV
B3. A validação anterior dos experimentos permanece documentada no relatório.

## EUA — execução com dados locais

Na raiz. Regenera resultados em `EUA/data/processed/` e a árvore em `EUA/cpp/`.
Não execute se pretende apenas consultar as saídas existentes.

```bash
cd EUA/python
python collect_tesouro_fred.py --usar-taxas-locais
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
python estabilidade_mst.py --executavel ../cpp/mst
python robustez_janela_comum.py --executavel ../cpp/mst
cd ../..
```

Pressupõe os dados locais já presentes. Se o CPI local estiver ausente, o
coletor tenta baixá-lo. Recoletar ações/taxas pela internet é uma etapa
separada e pode modificar o dataset. Diagnósticos são consultas manuais,
não filtros automáticos que excluem ativos.

## Brasil — execução com dados locais

Na raiz; também regenera saídas no respectivo mercado.

```bash
cd BRASIL/python
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

O merge usa `limpar_precos.py`, tratamento atual de XPML11 com fonte
documentada. A correção antiga por interpolação foi arquivada.

## Benchmark de Prim

Na raiz. Uma nova execução substitui as medições nos diretórios correspondentes.

```bash
cd EUA/cpp
make benchmark
cd ../python
python resumir_benchmark_prim.py
cd ../cpp
./benchmark_prim ../data/processed/benchmark_prim_grandes ../data/processed/distance_matrix.csv --grandes
cd ../python
python resumir_benchmark_prim.py --pasta ../data/processed/benchmark_prim_grandes
cd ../..
```

A extensão mede 10 mil e 20 mil vértices. A matriz de 20 mil contém cerca
de 3,2 GB de doubles, além dos outros custos do processo. Resultados Ubuntu
já preservados: `artigo/resultados/fontes/ubuntu_wsl/EUA/data/processed/`.

## Visualizações e consolidação

Na raiz, o executor pode gerar somente imagens, sem refazer backtests:

```bash
python main.py --mercado ambos --etapa visualizacoes
python main.py --mercado eua --etapa visualizacoes --figura grafos
python main.py --etapa visualizacoes --figura fluxograma
```

Sem `--figura`, gera grafos e fluxograma. Os grafos exigem as matrizes, a MST
e a carteira MST da etapa principal. `--figura fluxograma` funciona sem dados
de mercado. `--listar` e `--verificar` também funcionam nessa etapa.

As imagens automáticas ficam em `visualizacoes/automaticas/EUA/` e
`visualizacoes/automaticas/BRASIL/`, em SVG, PDF e PNG. Cada pasta recebe
um `procedencia.json` com hashes das entradas, seleção e posições dos nós.
Os arquivos são gerados localmente e excluídos do Git. O Brasil usa os
37 ativos do universo principal, sem IVVB11.

A MST e o grafo completo usam as mesmas posições, determinadas pela
topologia da árvore. As cores representam classes e o tamanho destaca
a carteira **MST**, inclusive no grafo completo. O comprimento visual e
a espessura não codificam distância. Não há filtragem das arestas completas.
As figuras do Gephi e sua disposição manual permanecem preservadas.

Os geradores individuais também continuam disponíveis:

```bash
python visualizacoes/gerar_fluxograma_horizontal.py
python visualizacoes/gerar_fluxograma.py
python visualizacoes/gerar_grafos.py --mercado eua
python visualizacoes/gerar_grafos.py --mercado brasil
python visualizacoes/exportar_mst_eua_gephi.py
```

O fluxograma horizontal para o artigo está em
[visualizacoes/fluxograma_metodologia_horizontal.pdf](visualizacoes/fluxograma_metodologia_horizontal.pdf),
com versões SVG e PNG. O gerador horizontal produz apenas essas figuras;
não executa backtests. A versão vertical original também foi preservada.
Instruções de uso no LaTeX: [visualizacoes/README.md](visualizacoes/README.md).

Importação: [visualizacoes/gephi/README.md](visualizacoes/gephi/README.md).
O exportador usa a MST existente, sem recalculá-la.
Para gerar as arestas do grafo completo, use
`python visualizacoes/exportar_grafo_completo_eua_gephi.py`.
As figuras finais com margens/legenda dependem dos SVGs previamente exportados
do Gephi, que preservam a disposição manual. Na raiz:

```bash
python visualizacoes/adicionar_legenda_mst_eua.py
python visualizacoes/adicionar_legenda_mst_eua.py --grafo-completo
```

`python artigo/consolidar_resultados.py` atualiza a consolidação local.
A opção `--ubuntu` destina-se ao Windows com WSL `Ubuntu-24.04` e cópia em
`/home/arthur/projetos/diversificar-carteira`; não é necessária para executar
os experimentos em Linux nativo. Preservar as cópias consolidadas antes de regenerá-las.
A consolidação requer previamente os dois pipelines, os experimentos de estabilidade
e robustez e **ambos os benchmarks** (padrão e grandes), incluindo seus resumos.
Para apenas consultar, abra `artigo/resultados/RESUMO.md`, sem executar o consolidador.

O uso de versões diferentes de bibliotecas pode alterar a ordem de ativos
em situações de empate numérico. Na validação limpa, XPLG11 e MXRF11 tiveram
a ordem invertida na carteira MST brasileira, sem alterar composição,
pesos por ativo ou métricas dentro da tolerância numérica da comparação.

## Entrada do programa e entregas

`main.py` organiza a execução pelo terminal; os scripts preservam seus pontos
de entrada próprios e os Makefiles compilam o C++. O enunciado `pratica (5).pdf`
exige Ubuntu 24.04 e instruções objetivas de execução. O executor central foi
incluído para facilitar o uso e a demonstração do projeto.

Código: [Arthur16r/diversificacao-carteiras-grafos](https://github.com/Arthur16r/diversificacao-carteiras-grafos),
disponível publicamente para consulta e avaliação.
O depósito parcial está disponível no [Zenodo](https://doi.org/10.5281/zenodo.23751340),
com atribuições e condições por componente. Os dados de origem Federal Reserve
Board/BLS mantêm a condição de domínio público; o componente Tesouro brasileiro
mantém ODbL 1.0 e as contribuições autorais indicadas usam CC BY 4.0.
O autor informou que o professor admite a indisponibilidade dos demais dados
caso não seja possível obter autorização.
Nenhum upload é feito pelos comandos do pipeline.
