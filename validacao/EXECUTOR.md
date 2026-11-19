# Validação do executor central — 19/11/2026

O executor `main.py` coordena os scripts existentes em processos separados,
com o mesmo interpretador Python e os diretórios de trabalho de cada mercado.
Não altera as regras financeiras, a seleção ou o Prim. Os comandos completos,
as consultas sem execução e os pré-requisitos estão no README da raiz.

## Ampliação para visualizações — 19/11/2026

A etapa `visualizacoes` gera imagens automáticas da MST e do grafo completo
dos mercados escolhidos, além do fluxograma horizontal. `--figura grafos`
ou `--figura fluxograma` restringe a geração; `completo` inclui as imagens
depois dos experimentos. As figuras automáticas ficam em uma pasta local
ignorada pelo Git, separada dos projetos manuais do Gephi.

- **51 testes aprovados no Windows e no Ubuntu:** 11 do executor, três de
  procedência/universo das figuras, 20 dos EUA e 17 do Brasil.
- Execução real da etapa de grafos pelo `main.py` no Windows: seis imagens
  por mercado (dois desenhos em SVG/PDF/PNG), com registro de procedência.
- Ubuntu/WSL: em cópia temporária, testes do executor/figuras, fluxograma sem
  dados de mercado, bloqueio da geração de grafos sem entradas, e execução
  completa de `visualizacoes` após copiar somente as matrizes, árvores,
  carteiras e módulo de classificação de cada mercado.
- Contagens conferidas: EUA 74 nós, 73 arestas na MST e 2.701 no grafo
  completo; Brasil 37 nós, 36/666 arestas, preservando a exclusão de IVVB11
  do experimento principal. Destaque de 10/8 ativos das carteiras MST.
- Os testes rejeitam carteira com hash desatualizado e matriz doméstica
  incompatível com a matriz de origem. O gerador também confere conectividade,
  duplicatas, pesos e simetria antes de desenhar.
- Inspeção visual de figuras dos dois mercados; redução automática de
  colisões entre rótulos, com posições dos nós iguais entre os dois desenhos.
- O título do bloco do fluxograma foi encurtado para “Prim e seleção na MST”
  porque a renderização no Ubuntu excedia a largura por cerca de dois pixels.
  As figuras horizontais foram regeneradas com esse ajuste textual.

Nenhum backtest, seleção financeira ou medição de benchmark foi refeito
para essa ampliação. Não foram alterados os arquivos ou layouts do Gephi.
As verificações da implementação inicial do executor estão registradas abaixo.

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
