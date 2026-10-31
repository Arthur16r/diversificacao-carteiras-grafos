# Fluxograma da metodologia

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
