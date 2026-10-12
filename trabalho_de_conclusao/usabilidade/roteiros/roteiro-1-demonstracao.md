# Roteiro 1 — Demonstração conduzida

**Para o pesquisador.** O participante assiste; não digita.
Duração prevista: **~10 minutos**. Protocolo completo em [`protocolo`](../protocolo.md).

---

## Objetivo

Dar o primeiro contato. Ao fim deste roteiro o participante precisa saber **o que a
ferramenta entrega** e **por onde se anda nela** — o bastante para executar R2 sozinho.

Não se coleta métrica aqui. O que se anota são as reações espontâneas: onde a pessoa
franze a testa, o que ela pergunta, o que ela comenta sem ser perguntada.

## Antes de começar

- [ ] Código do participante dito em voz alta: `P___`
- [ ] SIRAS rodando em `localhost`, versão `congelamento-v1`, navegador em janela limpa
- [ ] Gravação de tela iniciada, **se** o participante concordar quando perguntado

> Sem termo assinado e sem ficha de papel: decisão do orientador em 10/10/2026. A
> caracterização do participante é a Seção 1 do próprio formulário.

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

**Gleba 3 do Anexo 1 do Manual** (Tab. A.1, p. 353), com **milho**. É uma análise de solo
real e publicada — não um caso montado —, e é o que resolve o problema que esta ficha teve
desde o começo: o formulário exige Al, Ca, Mg e V%, e os casos de calagem e de adubação não
os trazem, porque foram montados para verificar um módulo cada.

Escolhida por exercitar, num caso só, a interpretação de fósforo por classe de argila
(argila 12 % → classe 4), a de potássio por CTC (4,7 → CTC baixa), um solo arenoso que
aciona o fator de textura, e uma situação em que **a calagem não é indicada** — que costuma
ser a primeira pergunta de quem olha o laudo.

| Campo | Valor |
|---|---|
| Cultura | Milho |
| Sistema de manejo | Convencional |
| Cultivo | 1º |
| pH em água | 5,8 |
| Índice SMP | 5,9 |
| Argila | 12 % |
| Matéria orgânica | 1,9 % |
| P (Mehlich-1) | 12,5 mg/dm³ |
| K | 25 mg/dm³ |
| Ca trocável | 2,0 cmolc/dm³ |
| Mg trocável | 1,1 cmolc/dm³ |
| Al trocável | 0,0 cmolc/dm³ |
| CTC a pH 7,0 | 4,7 cmolc/dm³ |
| Saturação por bases (V%) | 67 % |
| PRNT do corretivo | 100 % |
| Profundidade de incorporação | 20 cm |

**Seleções no formulário**, para o pesquisador não hesitar na frente do participante:
*Cultura* = Milho · *Sistema de manejo* = Convencional · *Condição da área* = "todos os
casos" · *Cultivo* = 1º.

**Campos de cenário, à escolha do pesquisador** — não são análise de solo e não têm
referência: *cultura antecedente* (o formulário exige; define a dose de N junto com a MO) e
*expectativa de rendimento* (opcional; em branco, o laudo manda todo o nitrogênio para
cobertura, o que é comportamento documentado e não erro).

**Procedência de cada linha.** Os onze valores da análise são a transcrição da Gleba 3 da
Tab. A.1 (p. 353), em `testes/casos/entradas_aptidao.json`, caso `ANX-G3-MILH`. O V% de 67 %
é publicado na própria Tab. A.1, e `scripts/validar_anexo1.py` confere que ele fecha com Ca,
Mg, K e CTC da mesma linha. **Nenhum valor foi inventado.**

## Resultado esperado

Três níveis de referência, com procedências diferentes. O pesquisador precisa saber qual é
qual, porque só os dois primeiros são oráculo.

**1. Classes de P e K — oráculo externo, publicado no Manual** (Tab. A.2 e A.3; milho é
grupo 2 em P e em K). `scripts/validar_anexo1.py` verifica que o SIRAS reproduz as classes
publicadas, sem divergência:

- classe de P: **Baixo**
- classe de K: **Baixo**

**2. Aptidão edáfica — gabarito conferido pelo autor** em 09/09/2026
(`testes/casos/gabarito_aptidao.csv`, linha `ANX-G3-MILH`):

| | |
|---|---|
| V% / m% | 67,32 % / 0 % |
| Classe de argila / de CTC | 4 / baixa |
| F1 acidez | ligeiro |
| F2 fósforo | forte |
| F3 potássio | forte |
| F4 Ca e Mg | ligeiro |
| F5 CTC | moderado |
| F6 matéria orgânica | moderado |
| F7 textura | moderado |
| **Classe** | **Restrita** |
| **Fator determinante** | **F2 — fósforo** |

**3. Calagem — derivada do critério, não de gabarito.** Milho é grão: o disparo é
`pH < 5,5` (Tab. 5.3, p. 75), e aqui o pH é **5,8**. A calagem **não é indicada**, e a dose
sai **0,0 t/ha**. Note que isso não torna a acidez irrelevante — o gabarito acima dá F1 como
*ligeiro*, e é um bom momento da demonstração para mostrar que "sem calcário" e "sem
limitação" não são a mesma coisa.

**Conferido contra o sistema em 11/10/2026.** O motor foi executado com esta entrada e
devolveu exatamente o acima: calcário 0,0 t/ha com motivo `ph_acima_do_disparo` pelo
critério `graos_convencional`, P baixo, K baixo, e aptidão **Restrita** com determinante
**F2_fosforo**. A conferência é verificação, e não a fonte: o oráculo continua sendo o
Manual (classes) e o gabarito do autor (aptidão).

> **Doses de N, P₂O₅ e K₂O: `PREENCHER`.** Esta gleba não tem referência de adubação
> calculada à mão — as que existem (ADU-*) são de outros solos. Enquanto não houver, **o
> pesquisador não cobre acerto nas doses** durante a demonstração; percorre a tela
> normalmente e confere apenas as classes e a aptidão, que têm oráculo. Para fechar este
> item basta calcular à mão a adubação do milho para P Baixo e K Baixo, 1º cultivo, e
> registrar aqui com a memória de cálculo, como nos demais casos.

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

## O que anotar

> Não é formulário a preencher: é o que o pesquisador registra enquanto observa.

Participante: `P___`  ·  Data: ____/____/______  ·  Versão: `congelamento-v1`

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
