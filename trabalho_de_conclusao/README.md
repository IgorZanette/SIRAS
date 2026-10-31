# Trabalho de Conclusão de Curso

Esta pasta guarda o **trabalho sobre o sistema**: o que foi prometido, como a avaliação
foi desenhada, o que ela mediu e o texto que vai à banca. A implementação do SIRAS está
em [`../siras/`](../siras/), separada desta.

A regra do corte, feita em 11/10/2026 antes do congelamento: se o documento descreve o
sistema, está em `siras/docs/`; se descreve o trabalho sobre o sistema, está aqui.

| Pasta | O que é |
|---|---|
| [`proposta/`](proposta/) | A proposta aprovada, em LaTeX. É o que foi prometido, e o parâmetro contra o qual o resultado se mede |
| [`artigo_final/`](artigo_final/) | O artigo final, na classe oficial do curso (`CC-EC_TF-TC`) |
| [`figuras/`](figuras/) | As figuras do artigo, feitas no Figma e exportadas em PDF, e a especificação de cada uma |
| [`validacao/`](validacao/) | O protocolo de validação (Seção 4.4 da proposta) e como o oráculo de cada caso é calculado à mão |
| [`usabilidade/`](usabilidade/) | O protocolo do teste com usuários e o questionário pelas dez heurísticas de Nielsen |
| [`processo/`](processo/) | Roadmap com o estado de cada etapa, o plano do front-end e as convenções de trabalho |

## O que cruza a fronteira, e por quê

Dois pontos, ambos deliberados e todos de código que produz ou confere material do
trabalho:

- `siras/scripts/consolidar_heuristicas.py` lê o instrumento de `usabilidade/`
- `siras/testes/unidade/test_estado_do_projeto.py` **confere** que a seção de estado da
  tela inicial não divergiu de `processo/roadmap.md` — escrita no template, divergiria
  na primeira semana

Fora esses, as duas metades são independentes: a implementação roda sem esta pasta, e os
documentos daqui se leem sem o código.
