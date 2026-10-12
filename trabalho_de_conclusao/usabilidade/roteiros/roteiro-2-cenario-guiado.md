# Roteiro 2 — Cenário guiado, executado pelo participante

**Para o pesquisador**, com uma ficha a imprimir e entregar.
Duração prevista: **~15 minutos**. Protocolo completo em [`protocolo`](../protocolo.md).

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
> implantar **milho em plantio direto já consolidado**, numa área **sem restrições na
> camada de 10 a 20 cm**. O calcário disponível na região tem **PRNT 75 %**.
>
> Acabou de chegar o resultado da análise de solo do talhão. O produtor quer saber
> **quanto de calcário aplicar**.
>
> ### Análise de solo — Talhão 1
>
> | Determinação | Resultado |
> |---|---|
> | pH em água | 5,3 |
> | Índice SMP | 5,4 |
> | Argila | 27 % |
> | Matéria orgânica | 2,1 % |
> | P (Mehlich-1) | 13,1 mg/dm³ |
> | K | 44 mg/dm³ |
> | Ca trocável | 2,5 cmolc/dm³ |
> | Mg trocável | 1,3 cmolc/dm³ |
> | Al trocável | 1,1 cmolc/dm³ |
> | CTC a pH 7,0 | 12,7 cmolc/dm³ |
> | Saturação por bases (V%) | 31 % |
> | Saturação por alumínio (m%) | 22 % |
>
> ### Tarefa
>
> Gere um laudo no SIRAS para essa situação e me diga, ao final:
>
> 1. **quanto de calcário** o sistema recomenda, em t/ha;
> 2. **por que** essa quantidade, e não outra;
> 3. se o solo está **apto** para a cultura hoje.

> **Procedência da análise — para o pesquisador, não vai na ficha.** É a **Gleba 4 do
> Anexo 1 do Manual** (Tab. A.1, p. 353), com milho: análise real e publicada, completa nos
> doze campos que o formulário exige. Substituiu o CAL-02, que era um caso de calagem e por
> isso não trazia P, K, Ca, Mg e Al — e esses cinco não podiam ser inventados, porque
> valores incoerentes entre si são notados de imediato por um agrônomo e a sessão vira uma
> discussão sobre a análise em vez de sobre a interface.
>
> **A troca não custou a referência de calcário**, e é por isso que esta gleba foi a
> escolhida entre as quatro: a Gleba 4 tem **índice SMP 5,4, o mesmo do CAL-02**, e sob o
> mesmo cenário (plantio direto consolidado, sem restrições, PRNT 75) **todos os insumos do
> cálculo coincidem** — o disparo, o fator, a entrada da Tab. 5.2 e a conversão por PRNT. A
> memória conferida à mão pelo autor em 22/08/2026 se aplica inteira.

## Resultado esperado

**Seleções que a situação implica**, para o pesquisador conferir se o participante chegou
ao mesmo lugar: *Cultura* = Milho · *Sistema de manejo* = Plantio direto · *Condição da
área* = "consolidado, sem restrições na camada 10-20 cm" · *PRNT* = 75. Escolher a
condição de área errada muda a dose, e **isso é achado de usabilidade, não erro do
participante** — anote se acontecer.

As três perguntas da tarefa têm resposta com oráculo. Procedências distintas:

**1. Calcário: 2,3 t/ha** — memória conferida pelo autor em 22/08/2026 (caso CAL-02,
`testes/casos/casos_recomendacao.json`), aplicável aqui porque os insumos do cálculo são os
mesmos.

Memória, se o participante perguntar: Tab. 5.3, p. 75, linha de plantio direto consolidado
— disparo em pH < 5,5, alvo pH 6,0, fator 1/4, aplicação superficial. O pH 5,3 dispara. A
exceção da nota (1) exige V ≥ 65 % **e** Al < 10 %; com V = 31 % ela não se aplica.
Tab. 5.2: SMP 5,4 para pH 6,0 dá 6,8 t/ha; × 1/4 = 1,7; PRNT 75: 1,7 × 100/75 = 2,27 →
**2,3 t/ha**.

**2. Por que essa quantidade** — a resposta certa do participante menciona, em alguma
ordem: o plantio direto consolidado reduz a dose a um quarto, e o PRNT 75 do calcário
disponível a aumenta na mesma proporção em que o corretivo é mais fraco. Não se espera que
ele cite as tabelas; espera-se que ele **ache essa explicação no laudo**, que é o que está
sendo avaliado.

**3. Aptidão** — gabarito conferido pelo autor em 09/09/2026
(`testes/casos/gabarito_aptidao.csv`, linha `ANX-G4-MILH`):

| | |
|---|---|
| V% / m% | 30,81 % / 21,94 % |
| Classe de argila / de CTC | 3 / média |
| F1 acidez | moderado |
| F2 fósforo | moderado |
| F3 potássio | forte |
| F4 Ca e Mg | ligeiro |
| F5 CTC | ligeiro |
| F6 matéria orgânica | moderado |
| F7 textura | ligeiro |
| **Classe** | **Restrita** |
| **Fator determinante** | **F3 — potássio** |

Classes de P e K, oráculo externo publicado no Manual (Tab. A.2 e A.3, milho é grupo 2 em
ambos; verificadas por `scripts/validar_anexo1.py`): **P médio** e **K baixo**.

**Conferido contra o sistema em 11/10/2026.** O motor foi executado com esta entrada e
devolveu exatamente o acima: 2,3 t/ha pelo critério `graos_pd_consolidado`, P médio, K
baixo, e aptidão **Restrita** com determinante **F3_potassio**. Vale como verificação de
que a transferência da memória do CAL-02 está correta — o oráculo continua sendo o cálculo
à mão do autor, não a saída do sistema.

> **Doses de N, P₂O₅ e K₂O: `PREENCHER`.** Esta gleba não tem referência de adubação
> calculada à mão. Não afeta a tarefa — ela pergunta por calcário e por aptidão, e as duas
> têm oráculo —, mas **não cobre acerto nas doses** se o participante comentá-las.

## O que anotar

> Não é formulário a preencher: é o que o pesquisador registra enquanto observa.

Participante: `P___`  ·  Data: ____/____/______  ·  Versão: `congelamento-v1`

**Conclusão da tarefa**

- [ ] Concluída sozinho
- [ ] Concluída com ajuda — o que travou: ______________________________
- [ ] Não concluída — onde parou: ______________________________

Tempo total: ______ min *(anotado, não conclusivo — ver o protocolo, §7)*

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
