# Obtenção e preparação das entradas

Este roteiro distingue a reconstrução com os arquivos usados no estudo de
uma nova coleta. O [depósito parcial](https://doi.org/10.5281/zenodo.23751340)
não contém todos os dados necessários aos backtests. Uma nova coleta pode
incorporar revisões históricas e produzir resultados diferentes dos publicados.

## 1. Recuperar os dados disponíveis no Zenodo

Abra o registro e baixe **dataset_parcial_titulos_prim_v1.0.0.zip**.
Extraia em uma pasta separada. O pacote contém os caminhos abaixo:

| Arquivo dentro do ZIP | Destino no repositório | Uso |
|---|---|---|
| `EUA/data/raw/fred_taxas_brutas.csv` | Mesmo caminho | Taxas de Treasury e TIPS |
| `EUA/data/raw/fred_cpi_mensal.csv` | Mesmo caminho | CPI mensal para TIPS |
| `BRASIL/data/raw/tesouro_bruto.csv` | Mesmo caminho | PUs, taxas e vencimentos brasileiros |

Copie esses três arquivos para os destinos indicados. Não substitua uma cópia
de trabalho que deseja preservar. O ZIP também oferece os índices sintéticos
já calculados e as medições originais em `BENCHMARK_UBUNTU/`; o executor
reconstrói os índices a partir dos brutos e mede novos benchmarks somente
quando essa etapa for solicitada.

Exemplo no Ubuntu, na raiz do repositório, supondo que o ZIP esteja na pasta
Downloads da sua conta Linux:

```bash
python -m zipfile -e "$HOME/Downloads/dataset_parcial_titulos_prim_v1.0.0.zip" dados_zenodo
mkdir -p EUA/data/raw BRASIL/data/raw
cp -n dados_zenodo/EUA/data/raw/fred_taxas_brutas.csv EUA/data/raw/
cp -n dados_zenodo/EUA/data/raw/fred_cpi_mensal.csv EUA/data/raw/
cp -n dados_zenodo/BRASIL/data/raw/tesouro_bruto.csv BRASIL/data/raw/
```

Ajuste o caminho do ZIP ao local em que foi salvo; no WSL, Downloads do Windows
e Downloads do Linux são pastas diferentes. `cp -n` preserva arquivos já existentes.
A pasta `dados_zenodo/` é local e não é versionada.

## 2. Entender o que continua faltando

| Mercado | Entrada não incluída no depósito | Formato esperado |
|---|---|---|
| EUA | `EUA/data/raw/precos_acoes_reits.csv` | `data` + 50 ações e 20 REITs |
| Brasil | `BRASIL/data/raw/precos_acoes_fiis.csv` | `data` + 16 ações, 14 FIIs e IVVB11 |
| Brasil | `BRASIL/data/raw/xpml11_b3_janeiro2026.csv` | Datas, fechamentos e proventos da ponte de XPML11 |

Os preços usados no estudo foram obtidos do Yahoo Finance via yfinance.
Em resposta ao pedido do autor, o Yahoo não autorizou a redistribuição e
informou não autorizar a recuperação programática descrita. Por esse motivo,
este roteiro não apresenta a execução dos coletores Yahoo como um procedimento
autorizado de obtenção dos dados faltantes. Os scripts `collect_stocks_reits.py`
e `collect_stocks_fiis.py` preservam o procedimento original e a relação de
tickers; não são executados pelo `main.py`.

Para executar os backtests, é necessário dispor de uma cópia obtida com
direitos de uso adequados ou obter históricos de um fornecedor que autorize
o uso pretendido e convertê-los ao formato abaixo. Não foi validada neste
projeto uma fonte alternativa que substitua integralmente esses históricos.
Disponibilidade para consulta e licença de uma biblioteca não equivalem a
permissão de coleta ou redistribuição dos dados.

### Formato dos preços de ações, fundos e ETF

- CSV em UTF-8, aceitando BOM; separador vírgula e decimal ponto.
- Primeira coluna chamada `data`, no formato `AAAA-MM-DD`, com datas únicas
  e em ordem crescente. As demais colunas são os identificadores dos ativos.
- EUA: os 70 tickers definidos em `EUA/python/collect_stocks_reits.py`, na
  ordem do dicionário `TICKERS`. Brasil: os 31 definidos em
  `BRASIL/python/collect_stocks_fiis.py`, também na ordem de `TICKERS`.
- Valores são fechamentos ajustados pelos eventos e distribuições considerados
  pelo provedor. Não misturar fechamentos brutos com séries ajustadas nem somar
  dividendos novamente às séries ajustadas usadas pelo modelo.
- Ausências anteriores ao início do histórico devem permanecer vazias.
  Não criar preços retroativos ou preencher indiscriminadamente os retornos.
- Janelas: EUA, construção 1990–2010 e teste 2011–junho/2026; Brasil,
  construção 2016–2022 e teste 2023–junho/2026. O histórico efetivo varia
  por ativo. Para a comparação publicada, os ativos devem cobrir o teste.

Um CSV de outra fonte pode atender ao esquema sem reproduzir os resultados:
é preciso conferir ajustes, calendários, tickers, eventos corporativos e
ausências. O merge aplica os tratamentos documentados nos READMEs dos mercados.

### Tabela de apoio XPML11

O arquivo local tem cabeçalho `data,fechamento,provento_ex,url_cotahist`.
O tratamento lê as três primeiras colunas; a última registra procedência.
As datas da ponte são 13, 14, 15, 16 e 19/01/2026; `provento_ex` representa
o rendimento por cota na data ex, com zero nos dias sem esse evento.

A fonte histórica de fechamentos é o
[COTAHIST da B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/).
O rendimento e seu relatório de origem estão documentados no
[README brasileiro](BRASIL/README.md). Essa tabela não foi incluída no depósito;
obtenção e eventual redistribuição devem respeitar as condições das fontes.
Não substituir suas observações por interpolação ou inventar valores para
contornar a ausência do arquivo.

## 3. Nova coleta das fontes de títulos

Estas etapas são alternativas aos brutos congelados do Zenodo e gravam os
respectivos arquivos locais. Antes de usá-las, preserve as cópias do estudo.
O executor central usa somente os modos de reconstrução com dados locais.

### FRED — Estados Unidos

Solicite sua própria chave conforme a
[documentação oficial do FRED](https://fred.stlouisfed.org/docs/api/api_key.html).
Com o ambiente ativado, na raiz, execute no terminal Linux:

```bash
export FRED_API_KEY="sua_chave"
python EUA/python/collect_tesouro_fred.py
```

O coletor consulta DGS3MO, DGS5, DGS10, DFII10 e CPIAUCNS e salva as taxas,
o CPI e os índices sintéticos em `EUA/data/raw/`. Não coloque a chave no código
ou no repositório. A reconstrução com os dois brutos do Zenodo dispensa a chave.

### Tesouro Transparente — Brasil

O conjunto oficial é
[Taxas dos Títulos Ofertados pelo Tesouro Direto](https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3),
disponibilizado sob ODbL. Na raiz, com o ambiente ativado:

```bash
python BRASIL/python/collect_tesouro.py
```

O coletor baixa o CSV oficial, converte o formato da fonte e filtra os tipos
usados no projeto. Grava `tesouro_bruto.csv`, `tesouro_series_rolling.csv` e
o registro de faltas de PU em `BRASIL/data/raw/`. O CSV baixado diretamente
do portal usa outro separador/formato; não basta renomeá-lo e colocá-lo como
`tesouro_bruto.csv` sem a conversão e os filtros do coletor.

## 4. Conferir antes de executar

Na raiz, com o ambiente ativado:

```bash
python main.py --mercado ambos --etapa principal --verificar
```

O comando confere existência das entradas, cabeçalhos obrigatórios, ferramentas
e dependências antes de iniciar qualquer etapa. Não certifica a qualidade
econômica da série nem equivalência com o provedor original. Para ver apenas
a sequência de comandos, inclusive sem dados disponíveis:

```bash
python main.py --mercado ambos --etapa completo --listar
```

Os testes automatizados usam dados sintéticos e podem ser executados sem os
CSVs de mercado. Isso verifica as rotinas, mas não equivale a reproduzir os
backtests financeiros. Instruções de instalação e execução no [README](README.md).
