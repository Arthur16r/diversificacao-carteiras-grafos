# Validação do executor central — 19/11/2026

O executor `main.py` coordena os scripts existentes em processos separados,
com o mesmo interpretador Python e os diretórios de trabalho de cada mercado.
Não altera as regras financeiras, a seleção ou o Prim. Os comandos completos,
as consultas sem execução e os pré-requisitos estão no README da raiz.

## Verificações realizadas

- Windows: os 45 testes aprovados; pré-verificação
  financeira detectou corretamente a ausência de g++ e make no PATH e não
  iniciou nenhuma etapa.
- Ubuntu 24.04 via WSL2: oito testes do executor, 20 dos EUA e 17 do Brasil
  aprovados, totalizando **45 testes**. A execução ocorreu em cópia temporária
  de código, antes de copiar qualquer CSV de mercado.
- A etapa principal foi bloqueada corretamente nessa cópia sem dados.
- Após copiar somente as seis entradas brutas previstas no README, a etapa
  principal dos dois mercados foi executada na cópia isolada: reconstrução
  dos títulos, merge, grafos, seleções, backtest/varredura, compilação e execução
  de Prim, seleção pela MST e comparação principal.
- As três carteiras principais de cada mercado preservaram os ativos, pesos
  por ativo e indicadores comparados: CAGR, volatilidade, Sharpe, drawdown,
  número efetivo e multiplicador final. Tolerância relativa 1e-9 e absoluta
  1e-11, com comparação numérica dos pesos JSON.
- As pré-condições de complementares e benchmark foram aprovadas após a
  reconstrução principal. O plano completo com `--grandes` foi listado sem
  executar as medições grandes.
- As compilações forçadas com `make -B` dos alvos Prim e benchmark foram
  conferidas em outro diretório temporário do Ubuntu. A execução de Prim
  em uma matriz sintética de três vértices gerou as duas arestas esperadas
  e custo 2,5; não foram feitas novas medições de tempo.

Os testes do executor cobrem listagem sem dados/execução, bloqueio global por
pré-requisitos ausentes, interrupção após comando malsucedido, reconhecimento
de entradas produzidas por passos anteriores, CSV incompatível, combinação
inválida de `--grandes`, exclusão de medições grandes por padrão e dependências
entre Prim/seleção/backtest, incluindo a matriz doméstica do Brasil.

## Independência dos testes brasileiros

O caso de XPML11 em `BRASIL/python/test_dados.py` passou a substituir a leitura
do arquivo por uma tabela sintética em memória. Mantém as verificações de
retorno, provento, ancoragem, idempotência e preservação da entrada, sem exigir
o CSV de mercado excluído do repositório. O tratamento financeiro em
`limpar_precos.py` foi preservado.

## Limites

Foi usado um ambiente virtual existente no Ubuntu; não se repetiu a instalação
das dependências nem do sistema operacional. A validação limpa anterior desses
componentes permanece em [RELATORIO.md](RELATORIO.md).

Não foram recoletados dados, refeitos os experimentos de 5.000 aleatórias ou
aportes, nem medidas novas curvas de benchmark nesta validação do executor.
Suas rotinas são as já existentes; a pré-verificação e os planos foram conferidos.
Os dados e resultados da pasta de trabalho e as fontes consolidadas para o
artigo foram preservados. A cópia temporária foi encerrada após a comparação.
