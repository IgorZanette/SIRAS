# 0006 — Espécies florestais: mapeadas para a aptidão, fora do escopo de recomendação

- **Status:** aceito
- **Data:** 2026-09-12
- **Contexto:** conflito apontado pelo autor entre a Proposta_TCC_v9 §4.2.1 e
  `dados/comum/mapa_culturas.json`, ao revisar a contagem do escopo durante a etapa 2 do
  plano de front-end
- **Complementa:** 0002 (calagem dirigida por critério de grupo), 0005 (motor de aptidão);
  nenhuma revogada

## Contexto

A Proposta §4.2.1 exclui do escopo, em texto explícito, o arroz irrigado por alagamento,
a mandioca e **as espécies florestais tolerantes à acidez** — estas últimas porque não têm
pH de referência na Tabela 5.1 e a lógica de calagem delas não cabe no modelo padronizado
das demais culturas. A erva-mate, que compartilha o mesmo critério, é a exceção declarada
e permanece no escopo.

Mesmo assim, `dados/comum/mapa_culturas.json` mapeia as seis florestais (acácia-negra,
araucária, bracatinga, cedro-australiano, eucalipto e pinus) para o critério
`erva_mate_e_florestais`. O mapeamento não foi acidente: entrou em 2026-09-10 como a
resolução da divergência **B-4** do `docs/CCAE-v1.1.md`, Apêndice B, onde o caso
`CONF-PT-05` (eucalipto, cenário POTENCIAL) falhava porque, sem a cultura mapeada, a dose
de calcário não era calculável e o motor não conseguia verificar a exequibilidade da
correção (CCAE §7.2).

A revisão do autor expôs a consequência de contagem: lida como catálogo de escopo, a
presença das seis faz `mapa_culturas.json` parecer cobrir 29 das 61 culturas, quando o que
ele cobre do escopo aprovado são 23 — os 21 grãos, a macieira e a erva-mate.

## Problema

Os dois usos do arquivo são incompatíveis se tratados como um só:

- **remover as seis** honra a Proposta e conserta a contagem, mas quebra o `CONF-PT-05` —
  medido: o conjunto de conformidade cai de 80/80 para 79/80 — e reabre o B-4, que o CCAE
  v1.1 registra como resolvido. Onze dos 84 casos de aptidão usam espécie florestal;
- **mantê-las sem qualificar** preserva a conformidade e deixa o repositório afirmando, na
  prática, um escopo que a Proposta nega.

## Decisão

**D6.1 — Estar mapeada e estar no escopo de recomendação são eixos distintos, e o segundo
é declarado em código, não em `dados/`.**

`mapa_culturas.json` responde "qual critério de calagem se aplica a esta cultura". É
invariante de carregamento, e o próprio B-4 já o dizia:

> Todas declaram `grupo: "erva_mate"` porque essa é a chave do grupo desse critério em
> `criterios_calagem.json` — invariante do carregador, não afirmação agronômica sobre a
> espécie.

O escopo de recomendação passa a ser declarado em `siras/dominio/escopo.py`, com as seis
florestais nomeadas explicitamente e o total de 61 registrado. Fica em código, e não na
base, porque escopo do trabalho é decisão de projeto — não transcrição do Manual, que é o
que `dados/` guarda.

**D6.2 — As seis continuam mapeadas e continuam sendo avaliadas pelo módulo de aptidão.**

Nada muda para `motor/aptidao.py`: eucalipto e acácia-negra seguem produzindo classe de
aptidão, e os onze casos de conformidade seguem valendo. A aptidão edáfica de uma área
sob eucalipto é uma pergunta legítima e respondível; o que o SIRAS não faz é **recomendar**
calagem e adubação para ela.

**D6.3 — As seis não são oferecidas na interface.**

`culturas_disponiveis()` filtra por `no_escopo_de_recomendacao()`. A tela nunca oferece uma
cultura para a qual o sistema não se propõe a emitir recomendação.

**D6.4 — Distinto de `criterios_aptidao.json → fora_de_escopo`.**

Aquele bloco (mandioca, arroz irrigado) faz a cultura ser recusada com `ErroAptidao`,
porque está fora do escopo do módulo de aptidão inteiro. Aqui a cultura é avaliada
normalmente e apenas não entra no catálogo de recomendação. São duas exclusões diferentes
e continuam em lugares diferentes de propósito.

## Consequências

- a contagem do escopo volta a ser a da Proposta: 61 culturas, sem as florestais;
- `CONF-PT-05` e os outros dez casos com espécie florestal continuam passando —
  conformidade em 80/80, gabarito intocado;
- o B-4 do CCAE v1.1 permanece resolvido, e esta decisão explicita o porquê;
- a pergunta "quantas das 61 culturas já estão mapeadas?" passa a ter resposta
  verificável por teste, em vez de sair da contagem de linhas do JSON;
- quem ler `mapa_culturas.json` isolado ainda verá as seis. O comentário do campo
  `descricao` do arquivo é o lugar de apontar para este ADR, e essa edição é do autor.

## Pendência que este ADR não resolve

A revisão que originou esta decisão também apontou divergência de identificador entre
`mapa_culturas.json` e `dados/culturas/hortalicas/hortalicas_adubacao.json` em oito
hortaliças — inclusive duas de mérito, não de grafia: se alface e almeirão/chicória/
rúcula/salsa são uma cultura ou duas, e se repolho e tomate são uma ou duas. Está com o
autor, para conferência no Manual, e não foi tocada aqui.
