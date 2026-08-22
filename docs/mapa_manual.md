# Rastreabilidade — Manual RS/SC 2016 → base de conhecimento

Uma linha por tabela transcrita. Este documento responde à pergunta "de onde veio esse número?".
Preencher **no momento da transcrição**, nunca depois.

Fonte: Comissão de Química e Fertilidade do Solo – RS/SC. *Manual de calagem e adubação para os
estados do Rio Grande do Sul e de Santa Catarina*. 11. ed., 2016. ISBN 978-85-66301-80-9.

| Tabela | Página | Arquivo | Campo | Transcrito | Conferido |
|---|---|---|---|---|---|
| 5.1 — pH de referência por cultura | 68 | `dados/comum/ph_referencia.json` | `grupos` | 16/08/2026 | 16/08/2026 |
| 5.2 — Índice SMP × necessidade de calcário | 70 | `dados/comum/calagem_smp.json` | `tabela` | 16/08/2026 | 16/08/2026 |
| Equações de baixo poder tampão (SMP > 6,3) | 71–72 | `dados/comum/calagem_smp.json` | `ajustes.baixo_poder_tampao` | 16/08/2026 | 16/08/2026 |
| Método alternativo por saturação por bases | 71 | `dados/comum/calagem_smp.json` | `metodo_alternativo_saturacao_bases` | 16/08/2026 | 16/08/2026 |
| 5.3 — Critérios de calagem, culturas de grãos | 75 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | 16/08/2026 |
| 5.5 — Critérios, hortaliças, tubérculos e raízes | 81 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | 16/08/2026 |
| 5.6 — Critérios, frutíferas e espécies florestais | 83 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | 16/08/2026 |
| 5.7 — Critérios, outras culturas comerciais | 86 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | 16/08/2026 |
| Ajuste por faixa de plantio (DC = NC × LFA/DLP × 100/PRNT) | 83 | `dados/comum/calagem_smp.json` | `ajustes.faixa_de_plantio` | 16/08/2026 | 16/08/2026 |
| Correção pelo PRNT do corretivo | 298 | `dados/comum/calagem_smp.json` | `ajustes.prnt` | 16/08/2026 | 16/08/2026 |
| 6.2–6.6 — Interpretação de P por classe de argila | 93–94 | `dados/comum/interpretacao_p.json` | `tabelas` | 17/08/2026 | 22/08/2026 |
| 6.7–6.10 — Interpretação de K por CTC pH 7,0 | 95–96 | `dados/comum/interpretacao_k.json` | `tabelas` | 17/08/2026 | 22/08/2026 |
| 6.1, 6.11, 6.12 — Argila, MO, CTC, Ca, Mg, S, micronutrientes | 91, 97, 98 | `dados/comum/interpretacao_geral.json` | `atributos` | 17/08/2026 | 22/08/2026 |
| 6.1.2–6.1.22 — Adubação nitrogenada de grãos por MO | 116–133 | `dados/culturas/graos/graos_adubacao_n.json` | `culturas` | 17/08/2026 | 22/08/2026 |
| 6.1.1–6.1.4 — Correção, manutenção e exportação de P/K, grãos | 105–108 | `dados/culturas/graos/graos_adubacao_pk.json` | `manutencao_por_cultura`, `exportacao_nos_graos` | 17/08/2026 | 22/08/2026 |

## Ponto de atenção da extração

O PDF usa fontes com codificação customizada: os símbolos **≥** e **≤** são extraídos como **=**.
Todos os operadores em `criterios_calagem.json` foram reconstruídos pelo contexto — `Al ≥ 30%`,
`V ≥ 65%`, `Ca ≥ 4,0`, `Mg ≥ 1,0`, `Al% > 10`, `SMP ≤ 4,4` — e **conferidos na página** pelo autor em
16/08/2026 (ver `fonte.conferido_operadores_em` em `criterios_calagem.json`).
