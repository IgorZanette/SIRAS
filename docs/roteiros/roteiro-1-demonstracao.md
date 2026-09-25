# Roteiro 1 — Demonstração conduzida

**Para o pesquisador.** O participante assiste; não digita.
Duração prevista: **~10 minutos**. Protocolo completo em [`../USABILIDADE.md`](../USABILIDADE.md).

---

## Objetivo

Dar o primeiro contato. Ao fim deste roteiro o participante precisa saber **o que a
ferramenta entrega** e **por onde se anda nela** — o bastante para executar R2 sozinho.

Não se coleta métrica aqui. O que se anota são as reações espontâneas: onde a pessoa
franze a testa, o que ela pergunta, o que ela comenta sem ser perguntada.

## Antes de começar

- [ ] TCLE lido e assinado
- [ ] Ficha do participante preenchida
- [ ] Código do participante entregue: `P___`
- [ ] SIRAS rodando em `localhost`, versão `usabilidade-v1`, navegador em janela limpa
- [ ] Gravação de tela iniciada, **se** consentida no TCLE

## Texto de abertura — ler, não improvisar

> "Obrigado por participar. Vou te mostrar uma ferramenta que interpreta análise de solo e
> gera recomendação de calagem e adubação, seguindo o Manual de Calagem e Adubação do RS e
> de SC. Eu desenvolvi essa ferramenta, e é exatamente por isso que preciso da tua opinião
> honesta: **o que eu preciso ouvir é o que está ruim.** Elogio não me ajuda a corrigir
> nada.
>
> Primeiro eu mostro como funciona, com um caso pronto. Depois eu te passo uma ficha e tu
> fazes sozinho. Por último tu escolhes o que quiser e geras um laudo do teu jeito.
>
> Em nenhum momento é o teu conhecimento que está sendo testado. Quem está sendo testado é
> o sistema. Se em algum ponto ficar confuso, o problema é dele, não teu — e é isso que eu
> quero descobrir. Pode interromper e perguntar quando quiser."

## Caso da demonstração

Entrada do caso **ADU-01**, de `testes/casos/casos_recomendacao.json` — soja, primeiro
cultivo, com o resultado já conferido à mão pelo autor em 22/08/2026. Escolhido por
exercitar, num caso só, a interpretação de fósforo por classe de argila, a de potássio por
CTC, uma cultura leguminosa que não recebe nitrogênio e uma situação em que **a calagem
não é indicada** — que costuma ser a primeira pergunta de quem olha o laudo.

| Campo | Valor |
|---|---|
| Cultura | Soja |
| Sistema de manejo | Convencional |
| Cultivo | 1º |
| Expectativa de rendimento | 3,0 t/ha |
| pH em água | 6,0 |
| Índice SMP | 6,2 |
| Argila | 32 % |
| Matéria orgânica | 3,0 % |
| P (Mehlich-1) | 6,0 mg/dm³ |
| K | 80 mg/dm³ |
| CTC a pH 7,0 | 9,5 cmolc/dm³ |
| PRNT do corretivo | 100 % |
| Profundidade de incorporação | 20 cm |
| Al trocável | `PREENCHER` |
| Ca trocável | `PREENCHER` |
| Mg trocável | `PREENCHER` |
| Saturação por bases (V%) | `PREENCHER` |

> **Nota sobre os quatro campos em branco.** Os valores acima vêm do caso ADU-01, que foi
> montado para verificar calagem e adubação e não traz Al, Ca, Mg e V%. Esses quatro são
> exigidos pelo formulário porque alimentam a aptidão edáfica. Não foram preenchidos por
> antecipação de propósito: teor inventado sai facilmente incoerente com a CTC e a
> saturação, e um agrônomo percebe isso em dois segundos — o que arruinaria a credibilidade
> da sessão logo no primeiro contato. **Preencher com um laudo real anonimizado**, que é a
> mesma fonte que `VALIDACAO.md` já indica para reduzir a circularidade de H1.1.

**Resultado esperado** (referência conferida do ADU-01, para o pesquisador saber se a tela
está certa durante a demonstração):

- calcário: **0,0 t/ha** — pH acima do disparo
- classe de P: **muito baixo**; classe de K: **médio**
- N: **0 kg/ha** (leguminosa, fixação biológica)
- P₂O₅: **155 kg/ha**; K₂O: **105 kg/ha**

## Passo a passo da demonstração

Vá narrando o que faz. Não pule telas para ganhar tempo — a navegação é parte do que se
está mostrando.

1. **Tela inicial.** Diga em uma frase o que o sistema faz e siga adiante. Não venda.
2. **Escolha da cultura.** Mostre os seis grupos e as 61 culturas. Escolha soja.
3. **Formulário.** Preencha campo a campo, em voz alta. Chame atenção para:
   - a **leitura ao vivo**: a classe do teor aparece enquanto se digita;
   - os campos marcados como **opcionais**, e o motivo de preenchê-los;
   - que o sistema de manejo muda o critério de calagem aplicado.
4. **Gerar o laudo.** Deixe a tela de espera rodar; não a pule. Ela mostra o que o sistema
   consulta em cada passo.
5. **Laudo — percorrer nesta ordem:**
   1. os **quatro números** do veredito, e por que o calcário deu zero;
   2. a **interpretação dos atributos**, com a régua e a posição do teor na classe;
   3. **qual adubo comprar** — a formulação indicada, se houver catálogo cadastrado;
   4. **como aplicar** — o que o Manual publica junto da dose;
   5. **aptidão edáfica** — os dois cenários lado a lado, e o que separa um do outro;
   6. **de onde vem cada número** — a trilha, regra por regra, com tabela e página.
6. **Calculadora "Quanto vai custar".** Mostre que ela está fora do documento, e diga por
   quê: preço é negócio de quem compra, e o laudo é peça técnica.
7. **Versão impressa.** Abra e feche, só para mostrar que existe.

## Folha de observação

Participante: `P___`  ·  Data: ____/____/______  ·  Versão: `usabilidade-v1`

| # | O que observar | Anotação |
|---|---|---|
| 1 | Perguntas feitas durante a demonstração (cada uma é um ponto em que a tela não se explicou) | |
| 2 | Termos que o participante não reconheceu ou pediu para repetir | |
| 3 | Reação ao laudo: o que olhou primeiro, o que ignorou | |
| 4 | Comentários espontâneos sobre a recomendação em si (separar dos comentários sobre a tela) | |
| 5 | Momento em que demonstrou entender o propósito da ferramenta | |

## Encerramento

> "Alguma dúvida antes de tu fazeres sozinho?"

Responda à dúvida. Depois passe a **ficha do R2** e não toque mais no teclado.
