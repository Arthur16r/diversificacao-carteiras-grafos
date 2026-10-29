# MST dos EUA no Gephi

Na raiz do projeto: `python visualizacoes/exportar_mst_eua_gephi.py`.
O exportador usa apenas a biblioteca padrão e não recalcula a árvore nem
altera resultados. Confere os hashes da carteira, a conectividade e os pesos.
As classes vêm das listas do módulo original, sem importar/executar o pipeline.

1. Crie um projeto no Gephi Desktop.
2. Importe `EUA/nos_mst.csv` como tabela de nós, delimitador vírgula, UTF-8.
3. Importe `EUA/arestas_mst.csv` como tabela de arestas no mesmo workspace.
4. Use grafo não direcionado. Confira 74 nós e 73 arestas.
5. Em Appearance/Aparência, nós, cor, Partition/Partição: selecione `Classe`.
6. Para tamanho dos nós, use Ranking por `Grau_MST` (coluna numérica).
7. Organize os nós com ForceAtlas 2; mantenha influência do peso das arestas
   em zero. Pare o layout quando a disposição ficar legível. Ative rótulos.

`Carteira_MST` identifica os dez ativos selecionados para destaque posterior.
`Distancia` contém o peso financeiro da matriz original, com precisão completa;
`Weight` é 1 para todas as arestas, evitando interpretar distância maior como
ligação mais forte. A disposição visual não representa uma escala exata de
distâncias nem os comprimentos dos caminhos usados na seleção.

Ao salvar, guarde o projeto `.gephi`, além das imagens exportadas. Os CSVs não
armazenam a disposição manual, as cores e os ajustes feitos na interface.

## Legenda na figura exportada

Após exportar `EUA/mst_eua_carteira_destacada.svg` pelo Gephi, execute na raiz:
`python visualizacoes/adicionar_legenda_mst_eua.py`.
Gera `EUA/mst_eua_carteira_destacada_com_legenda.svg`, com margens, título,
legenda por classe e explicação dos tamanhos. Não altera o original nem o
projeto `.gephi`; mantém as posições, arestas, cores e rótulos exportados.

## Grafo completo na mesma disposição

Na raiz: `python visualizacoes/exportar_grafo_completo_eua_gephi.py`.
Gera a lista completa de 2.701 arestas e, separadamente, as 2.628 que não
estão na MST, com distância original e correlação derivada. Nenhum filtro.

Para preservar a disposição manual: abra o projeto MST com 74 nós e 73
arestas e use **Salvar como** `grafo_completo_eua.gephi` antes de editar.
Nessa nova cópia, importe somente
`EUA/arestas_adicionais_para_completar_mst.csv` como tabela de arestas,
não direcionadas, anexando ao mesmo espaço de trabalho. Não reimporte nós.
Confira 74 nós e 2.701 arestas. Não execute layout novamente.

`arestas_grafo_completo.csv` destina-se a importação em grafo sem arestas;
não o importe por cima da MST, pois poderia duplicar conexões.
Para a figura, usar arestas cinza finas, opacidade de aproximadamente 5–10%,
sem rótulos de aresta, preservando cores e tamanhos dos nós. O destaque
continua sendo da carteira selecionada pela MST, não da carteira selecionada
pelo grafo completo. `Grau_MST` continua sendo grau na árvore, não no completo.

Após exportar `EUA/grafo_completo_eua.svg`, acrescente margens e legenda com
`python visualizacoes/adicionar_legenda_mst_eua.py --grafo-completo` na raiz.
A saída é `EUA/grafo_completo_eua_com_legenda.svg`; o original é preservado.
