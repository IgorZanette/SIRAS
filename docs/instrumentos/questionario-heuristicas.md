# Questionário pós-teste — as dez heurísticas de Nielsen

**Para colar no Google Forms.** Cada bloco numerado abaixo é uma **seção** do formulário.
Texto em citação (`>`) é o que o participante lê; o resto são instruções para o autor.

Protocolo em [`../USABILIDADE.md`](../USABILIDADE.md). O enunciado de cada heurística está
em linguagem de agrônomo e adaptado ao SIRAS, seguindo a orientação do orientador — não é
a redação genérica de Nielsen, e sim a pergunta que o público-alvo consegue responder sobre
**este** sistema.

---

## Configuração do formulário

| Ajuste | Valor | Por quê |
|---|---|---|
| Coletar endereços de e-mail | **Desligado** | O TCLE já foi assinado em papel, e o código do participante identifica a resposta. Guardar e-mail acumularia dado pessoal sem necessidade |
| Permitir edição de resposta | **Ligado** | São dez seções; a pessoa precisa poder pausar e retomar |
| Limitar a uma resposta | **Desligado** | Exigiria login e, com ele, a conta Google do participante |
| Ordem embaralhada | **Desligado** | As heurísticas têm ordem canônica e devem sair na mesma ordem para todos |
| Barra de progresso | **Ligada** | Dez seções sem barra parecem não acabar, e a taxa de abandono sobe |

---

## Seção 1 — Abertura e identificação

**Título:** `Avaliação de usabilidade do SIRAS`

**Descrição:**

> Obrigado por participar. Este formulário tem dez blocos, um para cada aspecto de
> usabilidade, e quatro perguntas abertas no final. Leva cerca de quinze minutos, e tu
> podes pausar e retomar depois — a resposta fica salva.
>
> Responde pensando **no que tu viveste** durante a sessão: a demonstração, o cenário que
> tu preencheste sozinho e o laudo que tu geraste livremente.
>
> **O que me serve é a crítica.** Nota baixa não me magoa; nota alta que esconde um
> problema me faz entregar um sistema pior. Se alguma coisa te irritou, escreve.
>
> Tu não precisas te identificar. Usa o código que eu te entreguei na sessão.
>
> ---
>
> **A escala de 0 a 4**, a mesma em todos os blocos:
>
> - **0** — Não é um problema.
> - **1** — Problema estético: incomoda, mas não atrapalha o uso.
> - **2** — Problema leve: atrapalha pouco, dá para contornar.
> - **3** — Problema grave: atrapalha muito e atrasa o trabalho.
> - **4** — Catástrofe: impede de usar, ou faz sair informação errada.

**Pergunta 1.1** — *Resposta curta, obrigatória*

> Teu código de participante (está na folha que eu te entreguei — P1, P2, ...)

**Pergunta 1.2** — *Múltipla escolha, obrigatória*

> Qual a tua formação/atuação?

- Engenheiro(a) agrônomo(a)
- Técnico(a) agrícola
- Estudante de agronomia
- Outra

**Pergunta 1.3** — *Múltipla escolha, obrigatória*

> Como tu usaste o sistema na sessão?

- Presencialmente, no computador do pesquisador
- Remotamente, com controle da tela

---

## Seções 2 a 11 — as dez heurísticas

**Estrutura idêntica em todas as dez.** Substitua apenas o título, a descrição e o
enunciado da pergunta A.

- **Pergunta A** — *Escala linear de 0 a 4, obrigatória*
  Rótulo do 0: `Não é problema` · Rótulo do 4: `Catástrofe`
  Enunciado: `Qual a gravidade dos problemas que tu encontraste neste aspecto?`
- **Pergunta B** — *Parágrafo, opcional*
  `Descreve o que deu errado e em que tela aconteceu.`
- **Pergunta C** — *Parágrafo, opcional*
  `O que tu farias diferente?`

> **Sobre "opcional" em B e C.** Vale para as notas 0 e 1. Configure **B como obrigatória
> quando a nota for 3 ou 4** — no Google Forms isso se faz com uma pergunta separada,
> visível por ramificação de seção, ou com um lembrete na descrição. Nota alta sem
> descrição é o pior resultado possível: sabe-se que há um problema grave e não se sabe
> qual. Se preferir não ramificar, use este texto na descrição de cada seção:
> *"Se tu deste 3 ou 4, por favor descreve na pergunta seguinte — sem a descrição eu não
> consigo corrigir."*

### Seção 2 — Heurística 1: Visibilidade do status do sistema

> O sistema te deixa saber o que está acontecendo? Por exemplo: enquanto o laudo é gerado,
> fica claro que ele está sendo processado e o que está sendo consultado? Quando tu digitas
> um teor, dá para perceber na hora em que classe ele caiu? Quando uma ação dá certo, o
> sistema avisa?

### Seção 3 — Heurística 2: Correspondência com o mundo real

> Os termos, as unidades e os nomes de cultura são os que tu usas no teu trabalho? O
> sistema fala a língua da agronomia — pH, SMP, PRNT, CTC, cmolc/dm³ — ou aparecem palavras
> de computador que não dizem nada para quem é do campo? A sequência de telas segue a ordem
> em que tu efetivamente farias a coisa?

### Seção 4 — Heurística 3: Controle e liberdade do usuário

> Quando tu erras — escolhe a cultura errada, digita o teor no campo trocado —, é fácil
> voltar atrás? Dá para editar a análise depois de gerar o laudo sem ter de preencher tudo
> de novo? Tu te sentiste preso em alguma tela, sem saída visível?

### Seção 5 — Heurística 4: Consistência e padrões

> As telas se parecem entre si? Botões parecidos fazem coisas parecidas, as cores querem
> dizer sempre a mesma coisa, e as informações ficam sempre no mesmo lugar? O laudo na tela
> e a versão impressa dizem a mesma coisa?

### Seção 6 — Heurística 5: Prevenção de erros

> O sistema te impede de errar por distração? Por exemplo: avisa quando falta um campo
> obrigatório, antes de deixar tu gerares um laudo incompleto; impede valor impossível numa
> análise de solo; deixa claro quando uma variável é exigida para aquela cultura
> específica?

### Seção 7 — Heurística 6: Reconhecimento em vez de memorização

> Tu precisaste decorar alguma coisa de uma tela para usar na seguinte? As informações de
> que tu precisavas para decidir estavam à vista, ou tu tiveste de lembrar o que havia
> preenchido antes? As opções de cultura, manejo e fase estavam visíveis, ou era preciso
> saber de antemão qual escolher?

### Seção 8 — Heurística 7: Flexibilidade e eficiência de uso

> Pensando em usar isso **toda semana**, e não uma vez só: o sistema tem atalhos? Lançar
> vários talhões de uma vez funciona bem? Falta alguma facilidade que te pouparia tempo —
> repetir uma análise anterior, salvar um manejo que tu sempre usas, importar dados do
> laboratório?

### Seção 9 — Heurística 8: Estética e design minimalista

> As telas mostram o que interessa, ou há excesso de texto e de informação competindo pela
> tua atenção? O laudo tem coisa demais? Tem coisa de menos? Alguma seção tu simplesmente
> não usaria?

### Seção 10 — Heurística 9: Ajuda para reconhecer e corrigir erros

> Quando algo deu errado — campo faltando, valor recusado, combinação que o sistema não
> cobre —, a mensagem explicou o problema em português claro e disse o que fazer? Ou
> apareceu um texto técnico que não ajudava?

### Seção 11 — Heurística 10: Ajuda e documentação

> Se te desse uma dúvida sobre como usar alguma função, dava para achar ajuda dentro do
> próprio sistema? As explicações que existem — as notas dos campos, as tabelas do Manual,
> a trilha de onde vem cada número — foram suficientes?

---

## Seção 12 — Perguntas abertas finais

**Título:** `Para fechar`

**Descrição:**

> Quatro perguntas abertas. São as mais importantes do formulário — responde com o que te
> vier, sem filtrar.

**Pergunta 12.1** — *Parágrafo, obrigatória*

> Se tu pudesses mudar **uma coisa só** no SIRAS, qual seria?

**Pergunta 12.2** — *Parágrafo, obrigatória*

> Tu usarias essa ferramenta no teu trabalho? Por quê — ou por que não?

**Pergunta 12.3** — *Parágrafo, obrigatória*

> Duas perguntas diferentes, e eu preciso das duas separadas:
> **(a)** sobre a **ferramenta** — ela é confiável, clara, útil?
> **(b)** sobre a **recomendação agronômica** que ela gerou — tu concordarias com ela, e
> assinarias um laudo desses?

**Pergunta 12.4** — *Parágrafo, obrigatória*

> Falta alguma coisa no sistema para que ele servisse à tua rotina de verdade? O que?

---

## Depois da coleta

Exporte as respostas em CSV pela aba **Respostas** e rode:

```
python scripts/consolidar_heuristicas.py respostas.csv --saida docs/figuras/
```

O script produz, por heurística, média, mediana, mínimo, máximo e contagem; o ranking de
prioridade; e todos os relatos agrupados, identificados pelo código do participante. Saída
em Markdown e CSV, prontos para a monografia.
