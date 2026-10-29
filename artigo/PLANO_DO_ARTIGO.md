# Plano do artigo

Decisões confirmadas pelo autor: texto em português; foco na comparação entre
grafo completo e MST, incluindo risco, desempenho e custo computacional.
EUA como experimento principal; Brasil como estudo complementar.

## Título de trabalho

**Seleção de carteiras por grafos de correlação: comparação entre grafo completo
e árvore geradora mínima**

Título provisório, sem alegar que a MST otimiza retorno ou garante diversificação máxima.

## Pergunta central e contribuição

Como a seleção de ativos por distâncias no grafo completo se compara à seleção
por distâncias de caminhos na MST, sob as mesmas cotas por classe, em termos de
risco, desempenho fora da amostra e custo computacional da construção da árvore?

A contribuição é uma avaliação experimental reproduzível de duas representações
da dependência entre ativos, com seleção heurística e restrições por classe.
A MST é calculada por Prim em C++. Não se propõe um algoritmo novo de Prim nem
se prova uma seleção ótima de carteira. O custo medido é o da rotina Prim;
não é uma comparação de tempo de ponta a ponta entre as estratégias.

O comparador concentrado contextualiza a diversificação, mas tem composição
por classe diferente. A comparação entre as duas diversificadas e as aleatórias
com cotas iguais é mais adequada para investigar o efeito da seleção.
As cotas controlam a quantidade por classe, não todos os fatores econômicos
ou exposições setoriais, nem os pesos finais após a valorização dos ativos.

## Estrutura proposta no formato IEEE

1. **Resumo e palavras-chave.** Problema, método, desenho, principais resultados
   e limitação temporal. Escrever a versão definitiva por último.
2. **Introdução.** Motivação; uso de dependência entre retornos na seleção;
   pergunta central; contribuições e organização do artigo.
3. **Fundamentação e trabalhos relacionados.** Diversificação e correlação;
   distância entre ativos; MST; Prim; seleção gulosa/farthest-first;
   trabalhos financeiros que utilizam árvores de correlação. Inserir apenas
   referências verificadas e ligadas a afirmações específicas.
4. **Metodologia.** Fluxograma; dados e universo; tratamento; separação temporal;
   fórmulas; grafo e MST; heurísticas e cotas; backtest; aleatórias; estabilidade;
   robustez; protocolo do benchmark e ambiente.
5. **Resultados e discussão.** EUA principal; referência aleatória; sensibilidade
   temporal/estabilidade; custo do Prim; Brasil complementar; síntese dos limites.
6. **Conclusões e trabalhos futuros.** Responder à pergunta delimitando mercados,
   universos e janelas; apresentar extensões sem prometer superioridade.

A numeração final e a distribuição de páginas dependem do template e do limite
de páginas do enunciado, ainda a reconferir antes da diagramação. Autores e
afiliações devem ser confirmados; preservar a orientação de professor como
último autor previamente identificada no enunciado.

## Conteúdo metodológico que deve estar explícito

- EUA: universo de 74 ativos; construção até 2010; teste 2011-01-03 a 2026-06-30;
  N=10, diversificadas com 4 ações, 4 REITs e 2 Treasury.
- Brasil: 37 ativos no principal sem IVVB11; construção 2016–2022;
  teste 2023-01-02 a 2026-06-30; N=8 com 3 ações, 3 FIIs e 2 títulos.
  IVVB11 aparece em variantes complementares, com universo completo de 38.
- Datas iniciais individuais variam. A correlação principal usa observações
  disponíveis por par, não uma história comum completa para todos os ativos.
- Retorno simples diário: r(i,t) = P(i,t)/P(i,t−1) − 1.
  Distância: d(i,j) = sqrt(2(1−rho(i,j))).
- Seleção diversificada farthest-first por classe. Na MST, a distância de
  seleção é a soma das arestas do caminho único, podendo cruzar outras classes.
  Não converter essa soma em correlação nem afirmar otimalidade global.
- Buy-and-hold com pesos iniciais iguais, quantidades fracionárias e sem custos.
  Concentração pode crescer ao longo do teste; mostrar número efetivo
  N_eff = 1/sum(w_i²) e pesos finais.
- Sharpe: média dos excessos diários dividida pelo desvio amostral dos excessos,
  vezes sqrt(252). Não substituir por (CAGR−taxa anual)/volatilidade.
  Referências: Treasury de 3 meses nos EUA e índice sintético Selic no Brasil.
- Aleatórias: 5.000 carteiras distintas por mercado, mesma cota e N das
  diversificadas, pesos iguais, seed 42. Percentuais são descritivos, não p-valores.
- Robustez 2003–2010: muda somente a construção; o teste permanece 2011–2026.
  Portanto não é uma segunda janela de teste independente.
- Estabilidade: interseção das arestas dividida por V−1 entre 2003–2006 e
  2007–2010; comparar o mesmo universo de 74 ativos.
- Benchmark Ubuntu 24.04 via WSL2, g++ 13.3.0, C++17, -Wall -O2;
  cinco sementes e dez repetições por tamanho sintético. Dez medições para
  a única entrada real. Excluir geração/leitura do trecho cronometrado;
  informar aquecimento/lotes e o que a rotina inclui. CPU/RAM precisam ser
  registradas junto ao limite de memória disponível ao WSL, não só ao Windows.
- Tempo de Prim denso Θ(V²); armazenamento da matriz Θ(V²).
  Não confundir O(V) de estruturas auxiliares com memória total.
  Memória V² doubles é estimativa de dados, não pico de RAM medido.

## Evidências que precisam aparecer na discussão

| Evidência | Interpretação admissível |
|---|---|
| EUA principal: MST Sharpe 0,725; grafo 0,679 | Vantagem observada da MST nessa configuração |
| EUA construção comum: MST 0,542; grafo 0,620 | Ordenação sensível à janela de construção |
| Brasil: MST vol. 7,43%, drawdown −6,95%, Sharpe 0,194 | Perfil de menor risco, mas menor retorno ajustado à referência |
| EUA: 29/73 arestas preservadas | Estrutura muda entre os subperíodos; não estabelece causa econômica |
| Benchmark Ubuntu: expoente 2,048 de 50 a 3.200 vértices | Evidência empírica compatível com análise quadrática |
| De 10 mil para 20 mil: razão 5,025; expoente local 2,329 | Trecho com maior crescimento; duas escalas não redefinem a complexidade |

Resultados exatos e fontes: [resultados/RESUMO.md](resultados/RESUMO.md).

## Figuras e tabelas propostas

Priorizar no corpo, ajustando ao limite de páginas:

- Fluxograma metodológico já gerado.
- MST dos EUA com legenda por classe e destaque da seleção. Salvar `.gephi`
  e exportar SVG/PDF; a imagem final ainda requer acabamento.
- Curvas de patrimônio normalizadas dos três comparadores nos EUA.
- Benchmark mediana/IQR versus V, referência V² e memória teórica.
- Tabela do desenho: universos, datas, N, cotas, taxa de referência.
- Tabela das três carteiras por mercado (dados em `principal.csv`).
- Tabela/figura das referências aleatórias com cotas e da robustez temporal.

Brasil pode ter tabela ou painel menor. Não é obrigatório mostrar todas as
arestas do grafo completo: o desenho denso pode ser pouco informativo. Se usado,
deixar explícito qualquer filtro visual; não apresentar grafo filtrado como completo.

Suplemento/repositório: varreduras completas, todos os cenários de aportes,
pesos e ativos de cada carteira, medições brutas, ambiente e tratamento dos dados.
Aportes são um extra; evitar que ocupem o centro do artigo.

## Limitações e integridade da interpretação

- Universo fixo escolhido retrospectivamente: explicitar seleção e possível
  viés de sobrevivência; não apresentar como universo histórico investível
  livre de viés apenas por separar construção e teste.
- Cobertura desigual e correlações por pares podem gerar matriz de correlação
  que não seja semidefinida positiva. Prim usa os pesos do grafo; não afirmar
  propriedades geométricas adicionais sem demonstrá-las.
- TIPS começa em 2003; sua série nominal é uma aproximação com carry real,
  duração e inflação de referência. Treasury e títulos brasileiros são proxies,
  não ETFs ou carteiras de títulos exatamente replicáveis.
- Históricos de empresas têm alterações societárias; preservar limitações
  previamente reconhecidas (por exemplo RTX/UTX). Não atribuir resultados só
  ao algoritmo, ignorando os ativos escolhidos.
- XPML11 tem tratamento documentado com fonte B3 e rendimento; descrever
  a correção e disponibilizar sua procedência, sem alegar certificação de
  todo o histórico de preços.
- Separar retorno total ajustado de variação do preço da cota dos FIIs.
- Embraer termina com 37,64% na diversificada brasileira sem aportes;
  isso comprova concentração final, mas sua contribuição ao risco requer
  decomposição específica antes de atribuir causalidade.
- Bancos na concentrada brasileira e composição de REITs na americana são
  fatores de composição; explicações de desempenho setorial permanecem
  hipóteses até investigação específica.
- Não atribuir mudanças de correlação à crise de 2008 como causalidade provada.
- Uma janela de teste por mercado, períodos e moedas distintos, sem custos,
  quantidades fracionárias. Generalização limitada. Informar que há experimentos
  exploratórios; não alegar pré-registro nem ajustar janelas para favorecer um método.

## Decisões editoriais ainda abertas

1. Aprovar ou ajustar o título de trabalho.
2. Confirmar se os aportes ficam apenas no suplemento ou recebem um parágrafo.
   Recomendação: suplemento e uma menção breve no corpo.
3. Confirmar template IEEE exato, limite de páginas, autoria e afiliações.
   Esses dados são necessários antes da diagramação, não para organizar os resultados.

## Próxima sequência de redação

1. Aprovar o recorte acima e conferir o enunciado/template atualizado.
2. Redigir metodologia a partir do pipeline e inserir as tabelas consolidadas.
3. Escrever resultados e discussão juntos, incluindo os resultados desfavoráveis.
4. Verificar referências primárias; completar fundamentação e introdução.
5. Finalizar conclusão, resumo, figuras e diagramação IEEE.

Não existem referências bibliográficas validadas ou citações prontas neste plano.
Nomes de autores lembrados de conversas não devem virar referências sem verificação.
