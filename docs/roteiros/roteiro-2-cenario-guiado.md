# Roteiro 2 — Cenário guiado, executado pelo participante

**Para o pesquisador**, com uma ficha a imprimir e entregar.
Duração prevista: **~15 minutos**. Protocolo completo em [`../USABILIDADE.md`](../USABILIDADE.md).

---

## Objetivo

É o roteiro que mais informa. O participante recebe uma situação fechada, em papel, e
opera o sistema **sozinho** — sem ajuda, sem sugestão, sem o pesquisador apontando para a
tela.

Mede-se: se ele conclui, onde trava, o que tenta antes de acertar, e se o laudo que sai
responde à pergunta que ele foi encarregado de responder.

## Regra de condução — a mais importante deste roteiro

**Não ajude.** Diante de "é aqui?", devolva a pergunta:

> "O que tu farias se eu não estivesse aqui?"

Ajuda prestada é dado perdido: cada vez que o pesquisador aponta para o botão certo, um
problema de usabilidade deixa de ser registrado.

Só intervenha quando:

- o participante pedir para desistir da tarefa — registre **não concluída** e prossiga;
- passarem **3 minutos** no mesmo obstáculo — registre **concluída com ajuda**, diga o
  mínimo para destravar, e anote exatamente o que travou;
- o sistema apresentar defeito que impeça continuar — registre o defeito e a tela.

Pedir para **pensar em voz alta** é encorajado, e não conta como ajuda:

> "Vai me dizendo o que tu estás procurando."

## A ficha — imprimir e entregar

> ### Situação
>
> Tu és o responsável técnico de uma propriedade em **Passo Fundo, RS**. O produtor vai
> implantar **soja em plantio direto já consolidado**, numa área **sem restrições na camada
> de 10 a 20 cm**. O calcário disponível na região tem **PRNT 75 %**.
>
> Acabou de chegar o resultado da análise de solo do talhão. O produtor quer saber
> **quanto de calcário aplicar**.
>
> ### Análise de solo — Talhão 1
>
> | Determinação | Resultado |
> |---|---|
> | pH em água | 5,1 |
> | Índice SMP | 5,4 |
> | Argila | 45 % |
> | Matéria orgânica | 3,2 % |
> | CTC a pH 7,0 | 9,5 cmolc/dm³ |
> | Saturação por bases (V%) | 50 % |
> | Saturação por alumínio | 15 % |
> | P (Mehlich-1) | `PREENCHER` mg/dm³ |
> | K | `PREENCHER` mg/dm³ |
> | Ca trocável | `PREENCHER` cmolc/dm³ |
> | Mg trocável | `PREENCHER` cmolc/dm³ |
> | Al trocável | `PREENCHER` cmolc/dm³ |
>
> ### Tarefa
>
> Gere um laudo no SIRAS para essa situação e me diga, ao final:
>
> 1. **quanto de calcário** o sistema recomenda, em t/ha;
> 2. **por que** essa quantidade, e não outra;
> 3. se o solo está **apto** para a cultura hoje.

> **Nota sobre os campos em branco — para o pesquisador, não vai na ficha.** Os valores
> preenchidos vêm da entrada do caso **CAL-02** (`testes/casos/casos_recomendacao.json`),
> conferido à mão pelo autor em 22/08/2026. O CAL-02 foi montado para verificar calagem e
> por isso não traz teores de P, K, Ca, Mg e Al. Esses cinco não foram inventados de
> propósito: valores incoerentes entre si — K alto com CTC baixa, Ca e Mg que não fecham
> com a saturação declarada — seriam notados de imediato por um agrônomo, e a pessoa
> passaria a sessão discutindo a análise em vez de a interface. **Completar com um laudo
> real anonimizado.**

## Resultado esperado

Referência do CAL-02, conferida à mão pelo autor:

- **calcário: 2,3 t/ha**

Memória de cálculo, se o participante perguntar: Tab. 5.3, p. 75, linha de plantio direto
consolidado — disparo em pH < 5,5, alvo pH 6,0, fator 1/4, aplicação superficial. A exceção
da nota (1) exige V ≥ 65 % **e** Al < 10 %; com V = 50 % ela não se aplica. Tab. 5.2: SMP
5,4 para pH 6,0 dá 6,8 t/ha; × 1/4 = 1,7; PRNT 75: 1,7 × 100/75 = 2,27 → **2,3 t/ha**.

As doses de adubação dependerão dos teores de P e K que forem preenchidos na ficha, e não
têm referência calculada — **não cobre acerto nelas.**

## O que anotar

> Não é formulário a preencher: é o que o pesquisador registra enquanto observa.

Participante: `P___`  ·  Data: ____/____/______  ·  Versão: `congelamento-v1`

**Conclusão da tarefa**

- [ ] Concluída sozinho
- [ ] Concluída com ajuda — o que travou: ______________________________
- [ ] Não concluída — onde parou: ______________________________

Tempo total: ______ min *(anotado, não conclusivo — ver `USABILIDADE.md` §7)*

**Marcos — anote o que aconteceu em cada um**

| # | Marco | Sozinho? | O que observei |
|---|---|---|---|
| 1 | Encontrou a soja entre os grupos e culturas | | |
| 2 | Escolheu **plantio direto consolidado, sem restrições** | | |
| 3 | Achou onde informar o **PRNT 75** | | |
| 4 | Transcreveu a análise sem trocar campo | | |
| 5 | Entendeu a leitura ao vivo enquanto digitava | | |
| 6 | Gerou o laudo | | |
| 7 | Localizou a dose de calcário no laudo | | |
| 8 | Explicou **por que** aquela dose (usou a trilha? a observação do cartão?) | | |
| 9 | Localizou e interpretou a aptidão edáfica | | |

**Respostas dadas pelo participante**

1. Calcário recomendado: ______ t/ha  ·  bate com 2,3? ☐ sim ☐ não
2. Justificativa que deu: ______________________________________________
3. Aptidão hoje: ______________________________  ·  ☐ leu certo ☐ leu errado

**Erros, hesitações e voltas**

| Passo | O que fez | O que a tela respondeu |
|---|---|---|
| | | |

**Perguntas feitas ao pesquisador** — cada uma é uma tela que não se explicou sozinha

1. ______________________________________________________________
2. ______________________________________________________________

## Encerramento

> "O que mais te incomodou nessa parte?"

Deixe responder. Não defenda o sistema, não explique a intenção do desenho, não diga "é que
ali eu quis fazer...". Anote e siga para o R3.
