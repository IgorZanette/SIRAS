# Sensibilidade da aptidão edáfica (CCAE §9.4)

Gerado por `scripts/sensibilidade_aptidao.py`. Conjunto de conformidade: **88 casos**, cada um no cenário que o gabarito declara (83 no atual, 5 no potencial).

| # | Configuração | Apta | Apta c/ restrições | Restrita | Inapta s/ correção | Mudam vs. 1 | Conformidade |
|---|---|---|---|---|---|---|---|
| 1 | Baseline: fator mínimo puro, sete fatores | 29 | 30 | 18 | 11 | — | 88/88 |
| 2 | Com rebaixamento por acúmulo (A-1) | 29 | 29 | 8 | 22 | 12 | 76/88 |
| 3 | Sem F7 (textura) | 31 | 28 | 18 | 11 | 2 | 86/88 |
| 4 | Sem F5 e F7 (fertilidade estrita) | 34 | 25 | 18 | 11 | 5 | 83/88 |

## O que muda em cada configuração

**Configuração 2** — 12 casos mudam (12 no atual, 0 no potencial): Restrita → Inapta s/ correção (11); Apta c/ restrições → Restrita (1).

Casos: `ANX-G2-MILH` (atual), `ANX-G3-EUCA` (atual), `ANX-G3-MILH` (atual), `ANX-G4-EUCA` (atual), `ANX-G4-MILH` (atual), `CAL-02` (atual), `CAL-05` (atual), `CAL-10` (atual), `CAL-13` (atual), `CONF-FR-05` (atual), `CONF-PT-05-ATU` (atual), `CONF-RB-05` (atual)

**Configuração 3** — 2 casos mudam (2 no atual, 0 no potencial): Apta c/ restrições → Apta (2).

Casos: `CONF-F7-01` (atual), `CONF-F7-04-ARGILA-20-FRONTEIRA` (atual)

**Configuração 4** — 5 casos mudam (4 no atual, 1 no potencial): Apta c/ restrições → Apta (5).

Casos: `CONF-F5-01` (atual), `CONF-F7-01` (atual), `CONF-F7-04-ARGILA-20-FRONTEIRA` (atual), `CONF-FR-14` (atual), `CONF-PT-02` (potencial)

## Como ler

A conformidade só é 100% no baseline porque o gabarito foi produzido à mão com a configuração do sistema. Nas demais, a queda **não é erro**: mede quanto a classe depende daquela decisão do autor.
