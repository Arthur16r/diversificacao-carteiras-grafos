# Validação do README em cópia limpa — 28/10/2026

Resultado: **39 etapas executadas, todas com código de saída zero**, em
Ubuntu 24.04 via WSL2, com Python 3.12 e ambiente virtual novo.

Fontes e seis entradas brutas foram copiadas para diretório isolado em
`/home/arthur/projetos/validacoes_aeds2/readme_x853xk5p`. Não foram copiadas
matrizes, carteiras, resultados financeiros, binários ou ambientes virtuais
anteriores. As saídas foram reconstruídas. Para a etapa gráfica foram
transportados os SVGs exportados manualmente do Gephi, pois são entradas
do acabamento com legendas, não resultados do pipeline financeiro.

## O que foi executado

- Criação de venv, instalação das dependências e registro das versões.
- Testes dos EUA: **20 aprovados**. Brasil: **17 aprovados**.
- Reconstrução das séries de títulos com dados locais, merge, construção
  do grafo, seleção e backtests dos dois mercados.
- Compilação e execução do Prim dos dois mercados.
- Carteiras MST, referências de 5.000 aleatórias, aportes, varreduras,
  estabilidade e robustez conforme os comandos do README.
- Benchmark padrão e extensão de 10 mil/20 mil vértices, com geração dos
  dois resumos. São medições de validação, não substituem os benchmarks
  anteriormente consolidados para o artigo.
- Fluxograma, exportações Gephi, acabamento dos SVGs e consolidação local.
- Conferência adicional `pip check`: sem dependências quebradas.
- Conferência offline do arquivo de versões fixadas com `pip install
  --dry-run --no-index`: todas as versões já presentes, sem instalação.

## Conferência dos resultados

Oito tabelas foram comparadas: backtest MST, aleatórias com cotas, aportes
e varredura de N, em cada mercado. Todas preservaram os mesmos ativos,
pesos por ativo e métricas, dentro de tolerância relativa 1e-9 e absoluta
1e-11. Campos JSON numéricos foram comparados como números, não como texto.

Há diferença de ordem textual em duas tabelas brasileiras: XPLG11 e MXRF11
trocaram de posição na lista da carteira MST. Não houve troca de ativos
nem alteração material do desempenho. Por isso não se afirma identidade
literal de todos os CSVs. Versões diferentes e empates numéricos podem
afetar a ordem de seleção/apresentação. Não foi alterada a heurística.

Evidências:

- `execucao_20261028/resultado.json`: comandos, diretórios, duração e exit codes;
  inclui a comparação estrita e os campos diferentes.
- `execucao_20261028/conferencia_resultados.json`: distingue ordem textual
  de composição e métricas.
- `execucao_20261028/*.log`: saídas individuais; `03_versoes.log` registra
  todas as versões do ambiente.

## Ajustes efetuados

- README passou a listar as seis entradas brutas e seus caminhos exatos.
- Foram explicitados os pré-requisitos da consolidação, incluindo os
  benchmarks padrão e grandes e seus resumos.
- `requirements-ubuntu-validado.txt` passou a registrar as versões completas
  usadas no ambiente novo. O README recomenda esse arquivo no Ubuntu/Python
  3.12; `requirements.txt` continua como lista direta sem fixação.
- Foram adicionados os comandos de exportação do grafo completo e de
  acabamento das figuras, com seus pré-requisitos de exportação manual.
- O consolidador foi corrigido para identificar execução local Linux
  como `local_linux`, em vez de sempre registrar `local_windows`.

## Limites da validação

Não foi reinstalado o sistema operacional ou repetido `apt install`:
Python, venv, g++ e make já estavam disponíveis no Ubuntu. O isolamento
testado foi de diretório de trabalho, entradas, binários e pacotes Python.
A instalação inicial dos pacotes Python usou rede/cache; a reconstrução
financeira usou os CSVs locais, sem recoleta de mercado.

Não foram publicados código/dataset, testadas APIs de recoleta nem refeitos
os ajustes manuais na interface do Gephi. Os resultados, figuras e projetos
originais da pasta de trabalho foram preservados; a consolidação de teste
foi executada somente na cópia isolada.

A primeira tentativa ficou em `execucao_20261027/`: a consolidação parou
antes de gerar os benchmarks grandes nessa cópia. O roteiro de validação
foi completado e a execução final acima passou por todos os passos.
