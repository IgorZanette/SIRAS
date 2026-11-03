# 0014 — Fórmulas informadas pelo usuário sempre no laudo, fora do ranking

- **Status:** aceito
- **Data:** 2026-11-02
- **Contexto:** piloto informal da avaliação de usabilidade, na versão publicada no
  Render, antes de qualquer participante da amostra
- **Revoga:** a D11 da [ADR 0009](0009-selecao-de-formula-por-pontos-de-quebra.md)
  ("a fórmula do usuário entra no ranking")
- **Afeta:** `siras/motor/formulacao.py`, `siras/dominio/laudo.py`
  (`ResultadoFormulacao.informadas` e `.informadas_sem_uso`),
  `siras/relatorio/apresentacao.py`, `templates/_parciais/laudo_anexo.html`,
  `templates/dados.html`, `static/js/formulas.js` (novo), `siras/web/formulario.py`
- **Não afeta:** calcário e doses de N, P₂O₅ e K₂O — nem, portanto, os 25 casos de
  validação, que conferem só essas saídas

## O que o piloto mostrou

Três problemas no campo "Fórmulas que a sua revenda tem":

1. **A fórmula informada sumia.** Pela D11 ela disputava as três vagas do catálogo com
   as 38 fórmulas cadastradas. Quando perdia, não aparecia. A pessoa informou 05-25-25 e
   18-18-18, viu o laudo indicar 05-20-20, e entendeu que o sistema tinha trocado a
   fórmula dela. O cálculo estava certo; a resposta não era a que ela procurava: quem
   diz "tenho 05-25-25" quer saber quanto aplicar DESSA.
2. **O formato era rígido.** "5 25 25", como a pessoa escreveu, era recusado; o hífen
   tinha de ser digitado.
3. **O erro aparecia tarde e com o conselho errado.** 40-50-60 (soma 150%) só era
   acusado depois do envio, travava o laudo inteiro por um campo opcional, e a mensagem
   terminava com "confira a unidade no laudo do laboratório" — conselho escrito para os
   teores da análise de solo.

## Decisões

| ID | Decisão |
|---|---|
| D14.1 | As fórmulas informadas são avaliadas pelo mesmo método (pontos de quebra, ADR 0009 D1) e aparecem **sempre, todas, na ordem escrita**, num bloco próprio do laudo. O catálogo passa a ranquear só as fórmulas do catálogo |
| D14.2 | Cada fórmula informada é comparada com a melhor do catálogo pelo mesmo custo que ordena o catálogo, e o laudo diz em palavras se ela atende tão bem quanto ou com mais sobra, falta ou complemento. O número do custo não aparece: ele não tem unidade |
| D14.3 | Fórmula informada sem o nutriente que a recomendação pede (ex.: 00-00-60 quando só há P) não some: é declarada como sem uso como adubo de base |
| D14.4 | O servidor aceita hífen, espaço, ponto ou barra como separador, e seis dígitos colados |
| D14.5 | Máscara no navegador (`formulas.js`): hífen automático, teclado numérico, conferência da soma ao sair do campo, envio barrado com fórmula inválida. A regra continua no servidor |
| D14.6 | Erro de fórmula não é erro de medida: não recebe o conselho sobre a unidade do laboratório |
| D14.7 | Na calculadora de custo, as fórmulas informadas entram antes das do catálogo |

## Por que a D11 parecia certa e não era

A D11 tratava a fórmula informada como "mais uma candidata", e do ponto de vista do
método isso é correto: ela é avaliada como qualquer outra. O erro foi de leitura do que
o usuário pergunta. Ele não pergunta "qual a melhor fórmula entre as que existem" — isso
o catálogo já responde —, e sim "serve a que eu tenho, e quanto ponho". A resposta mais
útil é justamente a do caso em que ela perde para o catálogo, e era nesse caso que ela
sumia.
