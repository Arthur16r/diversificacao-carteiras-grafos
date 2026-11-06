# Entradas locais — EUA

Antes de executar os comandos do README da raiz, coloque nesta pasta:

- `precos_acoes_reits.csv`
- `fred_taxas_brutas.csv`
- `fred_cpi_mensal.csv`

Os dados existentes no computador não foram removidos, mas ficam fora do Git.
As taxas e o CPI, junto dos índices sintéticos de títulos, estão no
[depósito parcial do Zenodo](https://doi.org/10.5281/zenodo.23751340).
Os preços do Yahoo Finance não têm autorização de redistribuição e ficam
excluídos; o pacote não basta para reproduzir todos os backtests. Consulte o
README da raiz para a situação dos dados. A partir das três entradas acima,
o pipeline reconstrói `tesouro_retornos.csv`
e as saídas processadas.
Não substituir os dados por uma nova coleta ao tentar reproduzir o experimento
congelado: provedores podem revisar históricos.
