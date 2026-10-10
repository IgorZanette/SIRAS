# 0007 — Indicação de formulação do adubo a partir de catálogo de mercado

- **Status:** aceito, com os itens 5 e 6 **revogados** pela [ADR 0008](0008-escolha-de-formula-pelo-metodo-do-manual.md) em 10/10/2026
- **Data:** 2026-09-24
- **Contexto:** pedido do orientador na reunião de acompanhamento de 24/09/2026, 19:30 —
  "finalizar indicação de formulação do adubo correta"
- **Complementa:** 0004 (normalização de doses e variáveis condicionais); nenhuma revogada

## Contexto

O laudo entrega a recomendação em **nutriente**: tantos kg/ha de N, de P₂O₅ e de K₂O. Isso
é o que o Manual publica, e é o que a norma técnica exige. Mas não é o que se compra: a
revenda vende **adubo formulado**, rotulado por três garantias percentuais, e quem sai do
laudo para a loja precisa converter a recomendação em produto e quantidade.

Até 24/09/2026 o SIRAS deixava essa conversão inteiramente com o usuário. A calculadora
"Quanto vai custar" (13/09/2026) fazia a aritmética, mas só depois de a pessoa **digitar**
até três fórmulas — a interface não sugeria nenhuma, por decisão registrada em
`templates/laudo.html`: sugerir um teor "típico" seria afirmação agronômica da interface.

O orientador pediu que o sistema fechasse essa lacuna.

## Problema

Indicar uma formulação exige um dado que **o Manual não tem**. O CQFS publica critérios de
interpretação e doses de nutriente; não publica, e não teria por que publicar, a lista de
formulações que a indústria oferece. Qualquer indicação depende, portanto, de uma fonte
externa ao Manual — e o repositório inteiro está construído sobre a regra de que
`dados/` é transcrição conferida do Manual e nada mais.

Três riscos concretos:

1. **contaminar a fonte normativa** — pôr formulações comerciais junto das tabelas do
   Manual apagaria, no próprio repositório, a distinção que a monografia precisa declarar;
2. **inventar dado** — completar o catálogo com formulações "comuns na região" seria
   exatamente a fabricação de dados que o `CLAUDE.md` proíbe;
3. **travar o sistema** — se a indicação virar parte obrigatória do laudo, o SIRAS deixa
   de funcionar enquanto o catálogo não existir.

## Alternativas consideradas

| # | Alternativa | Por que não |
|---|---|---|
| A | Só a relação N:P₂O₅:K₂O da recomendação, sem catálogo | Aritmética pura, sem dado novo, mas não responde à pergunta do orientador: continua sem dizer **qual** adubo comprar |
| B | Fontes simples do Cap. 8 do Manual (ureia, superfosfato, cloreto de potássio) | Fonte normativa impecável, mas responde a outra pergunta — quem compra formulado não quer três produtos separados. Fica como extensão possível |
| C | **Catálogo de formulações comerciais, com fonte por entrada** | **Escolhida** |
| D | Catálogo embutido no código | Repetiria o erro que o B-6 do CCAE expôs: dado agronômico fora da base, invisível à validação |

## Decisão

**1. O catálogo vive fora de `dados/comum/`.** Fica em `dados/mercado/formulacoes.json`,
diretório novo cuja única razão de existir é separar dado de mercado de transcrição do
Manual. O arquivo declara isso no próprio campo `aviso`, e
`testes/integracao/test_laudo_formulacao.py` falha se esse aviso sumir.

**2. Cada entrada declara a própria fonte.** O campo `_fonte` é obrigatório no schema. É o
que separa dado conferido de número digitado de memória, e é o que a banca vai pedir.

**3. O arquivo nasce vazio.** O autor o preenche (pendência P7 do `docs/ROADMAP.md`).
Nenhuma formulação foi escrita por antecipação, nem como exemplo.

**4. Catálogo vazio não é erro.** `indicar_formulacao()` devolve `indicada = None` com
`motivo_sem_indicacao` preenchido; o cartão some do laudo e a calculadora volta ao
comportamento anterior, com as três vagas em branco. O laudo segue completo. O sistema não
pode ficar refém de um dado que depende de terceiros.

**5. Critério de dose** ~~(já em uso na calculadora desde 13/09/2026): a dose da formulação
é a **maior** entre a quantidade que cobre o P₂O₅ e a que cobre o K₂O.~~ **REVOGADO pela
ADR 0008.** O levantamento de 10/10/2026 localizou o procedimento publicado no Manual
(§8.3, p. 311): a dose se ancora no nutriente **mais deficiente no solo**. A regra deixou
de ser escolha do autor e passou a ser transcrição de método.

**6. Critério de escolha** ~~(decisão do autor, 24/09/2026): vence a de menor excesso total
de P₂O₅ + K₂O; empate pela menor falta de N.~~ **REVOGADO pela ADR 0008:** vence a de menor
**desvio relativo** (faltas + excessos sobre o alvo), com desempate pela fórmula mais
concentrada — como o Manual observa na p. 310.

*Por que o excesso, e não o custo:* o custo depende de preço, que é do comprador e não do
sistema — e escolher por preço faria a indicação mudar conforme o que a pessoa digitasse.
O excesso é propriedade da formulação frente à recomendação, e é determinístico. O custo
continua sendo comparado, com preços da pessoa, na calculadora.

*Por que o N fica fora do critério de dose:* é o nutriente que se completa com fonte à
parte, e amarrar a dose a ele faria a formulação sobrar em P e K para acertar o N. A falta
e o excesso de N ficam declarados — N a mais tem custo e efeito agronômico próprios.

**7. A indicação fica DENTRO do laudo; o preço, fora.** Dizer qual fonte de nutriente
aplicar é recomendação técnica, e o documento é assinado por quem responde por ela. Preço
é matéria comercial e continua na calculadora, fora do documento e da impressão — a mesma
linha que o comentário de `templates/laudo.html` já traçava.

**8. A indicação entra pré-preenchida na calculadora** (pedido do autor, 24/09/2026): quem
não encontrar o adubo indicado na revenda compara o que tem disponível contra o que o
SIRAS indicou, sem digitar os dois. Campo já preenchido pela pessoa nunca é sobrescrito.

**9. A dose sai do motor sem arredondamento.** A comparação entre formulações roda sobre o
valor cheio; quem arredonda é a apresentação. Arredondar no motor repetiria o defeito
**B-8** do CCAE, em que um valor arredondado cedo passou a decidir um corte.

## Consequências

- O laudo ganha a seção "Qual adubo comprar", que **imprime**, com a ressalva de
  procedência no corpo do texto: o catálogo não vem do Manual, e a garantia deve ser
  conferida no rótulo do produto.
- A monografia precisa declarar, na seção de limitações, que a lista de formulações não é
  do Manual e que a indicação é auxiliar à recomendação em nutriente — que continua sendo
  a saída normativa do sistema.
- `R-FOR-01` entra na trilha, com a fonte da entrada do catálogo e o aviso de que ela não
  é fonte do Manual.
- Enquanto o catálogo estiver vazio, nada disso aparece — e a suíte cobre os dois estados.

## Verificação

- `testes/unidade/test_formulacao.py` — dose, escolha, desempate, determinismo, formulação
  que não atende, dose publicada como teto, e os dois passos de trilha.
- `testes/integracao/test_laudo_formulacao.py` — motor, apresentação e tela com catálogo
  cheio e vazio; invariantes do arquivo real; recusa de garantias somando acima de 100% e
  de id repetido.
