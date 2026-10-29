# Diversificação de carteiras com grafos e árvores

Projeto de AEDS2 que investiga risco e desempenho de carteiras selecionadas
por grafos de correlação e árvores geradoras mínimas. EUA é o estudo principal;
Brasil é o complementar. A redação do artigo está pausada.

## Organização

- `EUA/` e `BRASIL/`: `python/` para pipeline, experimentos e testes;
  `cpp/` para Prim e Makefile; `data/raw/` para entradas e `data/processed/`
  para matrizes, carteiras e resultados.
- `BRASIL/python/anterior/`: histórico fora do pipeline atual; não executar.
- `visualizacoes/`: fluxograma e exportação para Gephi.
- `artigo/resultados/`: consolidação com fontes Windows e Ubuntu separadas.

Catálogo: [ORGANIZACAO.md](ORGANIZACAO.md).
Resultados: [artigo/resultados/RESUMO.md](artigo/resultados/RESUMO.md).
O plano do artigo é provisório; a motivação central é investigar benefícios
da diversificação usando grafos e árvores como instrumentos.

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
Quando o dataset for publicado, estas entradas precisarão ser extraídas para
os mesmos caminhos. O link do depósito ainda não está disponível.
Os CSVs de preços e as saídas volumosas não são versionados no Git: clonar
somente o código não basta para executar os experimentos. Tabelas consolidadas,
figuras e fontes selecionadas continuam disponíveis para consulta no repositório.

Para nova coleta FRED, defina sua chave no terminal, sem inseri-la no código:

```bash
export FRED_API_KEY="sua_chave"
```

A reconstrução com os três CSVs locais dos EUA não precisa dessa chave.

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

Na raiz:

```bash
python visualizacoes/gerar_fluxograma.py
python visualizacoes/exportar_mst_eua_gephi.py
```

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

Não há `main.py` central. Os scripts têm pontos de entrada próprios;
os Makefiles compilam e executam o C++. O enunciado `pratica (5).pdf` exige
Ubuntu 24.04, execução via terminal e instruções objetivas, sem exigir
menu ou arquivo Python central.

Código: [Arthur16r/diversificacao-carteiras-grafos](https://github.com/Arthur16r/diversificacao-carteiras-grafos),
mantido privado nesta etapa. O depósito do dataset tratado no Zenodo ou
Mendeley Data ainda está pendente. Nenhum upload é feito pelos comandos do pipeline.
