# Visualizações do projeto

## Geração pelo executor central

Na raiz, com o ambiente Python ativado:

```bash
python main.py --mercado ambos --etapa visualizacoes
python main.py --mercado brasil --etapa visualizacoes --figura grafos
python main.py --etapa visualizacoes --figura fluxograma
```

O padrão é `--figura todas`. `--listar` mostra os comandos e `--verificar`
confere os pré-requisitos sem gerar arquivos. `completo` também gera essas
visualizações depois dos experimentos. Não exige Gephi ou novos pacotes além
das dependências já listadas no projeto.

## Imagens automáticas da MST e do grafo completo

As matrizes, `cpp/mst_edges.csv` e `data/processed/carteiras_mst.csv` devem
estar disponíveis após a etapa principal. Não é necessário executar os
complementares nem o benchmark. O gerador verifica hashes da carteira,
simetria da matriz, conectividade e pesos da árvore antes de desenhar.

São gerados em `automaticas/EUA/` e `automaticas/BRASIL/`:

- `mst_eua.svg`, `.pdf`, `.png` (ou `mst_brasil`).
- `grafo_completo_eua.svg`, `.pdf`, `.png` (ou `grafo_completo_brasil`).
- `procedencia.json`, com hashes, ativos selecionados, contagens e posições.

Os arquivos dessa pasta são locais e ignorados pelo Git. Ambos os desenhos
usam as mesmas posições e todos os ativos do respectivo experimento principal:
74 nos EUA e 37 no Brasil, sem IVVB11. São 73/2.701 arestas, respectivamente,
para MST/grafo completo nos EUA, e 36/666 no Brasil. As cores representam
classes e os círculos maiores identificam a seleção **pela MST**, inclusive
no grafo completo; não representam a seleção pela matriz completa.

O layout radial usa o centro do diâmetro topológico da MST, divide os setores
pela quantidade de folhas e posiciona os nós por profundidade. Não usa pesos
das arestas nem resultados financeiros para posicionar os nós. Portanto,
comprimento visual e espessura não codificam distância de correlação.
O grafo completo mostra todas as conexões com baixa opacidade.

Essas figuras são uma alternativa automática. Os `.gephi`, SVGs exportados
manualmente, legendas existentes e a disposição feita no Gephi são preservados.
Para apresentação em uma página pequena, a exportação manual pode permitir
um acabamento mais fino dos rótulos.

Também é possível chamar o gerador diretamente:

```bash
python visualizacoes/gerar_grafos.py --mercado eua
python visualizacoes/gerar_grafos.py --mercado brasil --destino pasta_de_figuras
```

## Versão horizontal para o artigo IEEE

`python visualizacoes/gerar_fluxograma_horizontal.py` gera
`fluxograma_metodologia_horizontal.pdf`, `.svg` e `.png`.
A versão tem 17 × 10,4 cm, títulos de 9 pt e texto dos blocos de 8,5 pt,
com detalhes metodológicos transferidos para o texto do artigo. Deve ser
inserida proporcionalmente em duas colunas, sem esticar altura/largura.
A versão vertical original permanece preservada.

Exemplo no LaTeX (enviar o PDF horizontal para o Overleaf):

```latex
\begin{figure*}[t]
    \centering
    \includegraphics[width=\textwidth]{fluxograma_metodologia_horizontal.pdf}
    \caption{Fluxo de construção e avaliação das carteiras. Os dados de teste
    permanecem reservados até o backtest; as análises complementares não
    realimentam a seleção principal.}
    \label{fig:fluxograma}
\end{figure*}
```

## Versão vertical original

O fluxograma representa o pipeline atual dos EUA (principal) e do Brasil
(complementar). A seleção pelo grafo completo e a seleção pelos caminhos da
MST aparecem em ramos distintos. A janela de teste fica reservada até o
backtest. As análises complementares são experimentos separados, não passos
obrigatoriamente posteriores à avaliação nem entradas para selecionar ativos.

Arquivos gerados:

- `fluxograma_metodologia.png`: imagem para visualizar e compartilhar.
- `fluxograma_metodologia.svg`: imagem vetorial editável.
- `fluxograma_metodologia.pdf`: versão vetorial para inserir em documentos.

Para regenerar, na raiz do projeto, com matplotlib instalado:

```bash
python visualizacoes/gerar_fluxograma.py
```

O gerador só grava essas três figuras nesta pasta. Não executa experimentos
nem altera dados, carteiras ou resultados. As visualizações do grafo completo
e da MST dos EUA estão em `gephi/EUA/`; os procedimentos de importação e
acabamento estão em [gephi/README.md](gephi/README.md).
