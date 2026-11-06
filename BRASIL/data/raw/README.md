# Entradas locais — Brasil

Antes de executar o README da raiz, coloque nesta pasta:

- `precos_acoes_fiis.csv`
- `tesouro_bruto.csv`
- `xpml11_b3_janeiro2026.csv`

Os arquivos existentes não foram removidos, mas ficam fora do Git. O bruto e
os índices de títulos estão no
[depósito parcial do Zenodo](https://doi.org/10.5281/zenodo.23751340), sob ODbL 1.0.
Os preços do Yahoo Finance não têm autorização de redistribuição e ficam
excluídos, assim como a tabela B3. Consulte o README da raiz para a situação
dos dados; o pacote não basta para reconstruir todos os backtests.
O pipeline reconstrói as séries
rolling de títulos e as saídas processadas. A tabela B3 participa do tratamento
atual de XPML11 e é necessária à reconstrução local.
