# Fluxograma da metodologia

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
nem altera dados, carteiras ou resultados. A visualização dos grafos e das
MSTs será uma tarefa separada.
