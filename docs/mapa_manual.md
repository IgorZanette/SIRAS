# Rastreabilidade — Manual RS/SC 2016 → base de conhecimento

Uma linha por tabela transcrita. Este documento responde à pergunta "de onde veio esse número?".
Preencher **no momento da transcrição**, nunca depois.

Fonte: Comissão de Química e Fertilidade do Solo – RS/SC. *Manual de calagem e adubação para os
estados do Rio Grande do Sul e de Santa Catarina*. 11. ed., 2016. ISBN 978-85-66301-80-9.

| Tabela | Página | Arquivo | Campo | Transcrito | Conferido |
|---|---|---|---|---|---|
| 5.1 — pH de referência por cultura | 68 | `dados/comum/ph_referencia.json` | `grupos` | 16/08/2026 | |
| 5.2 — Índice SMP × necessidade de calcário | 70 | `dados/comum/calagem_smp.json` | `tabela` | 16/08/2026 | |
| Equações de baixo poder tampão (SMP > 6,3) | 71–72 | `dados/comum/calagem_smp.json` | `ajustes.baixo_poder_tampao` | 16/08/2026 | |
| Método alternativo por saturação por bases | 71 | `dados/comum/calagem_smp.json` | `metodo_alternativo_saturacao_bases` | 16/08/2026 | |
| 5.3 — Critérios de calagem, culturas de grãos | 75 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | |
| 5.5 — Critérios, hortaliças, tubérculos e raízes | 81 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | |
| 5.6 — Critérios, frutíferas e espécies florestais | 83 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | |
| 5.7 — Critérios, outras culturas comerciais | 86 | `dados/comum/criterios_calagem.json` | `criterios` | 16/08/2026 | |
| Ajuste por faixa de plantio (DC = NC × LFA/DLP × 100/PRNT) | 83 | `dados/comum/calagem_smp.json` | `ajustes.faixa_de_plantio` | 16/08/2026 | |
| Correção pelo PRNT do corretivo | 298 | `dados/comum/calagem_smp.json` | `ajustes.prnt` | 16/08/2026 | |
| Interpretação de P por classe de argila | | `dados/comum/interpretacao_p.json` | | | |
| Interpretação de K por CTC pH 7,0 | | `dados/comum/interpretacao_k.json` | | | |

## Ponto de atenção da extração

O PDF usa fontes com codificação customizada: os símbolos **≥** e **≤** são extraídos como **=**.
Todos os operadores em `criterios_calagem.json` foram reconstruídos pelo contexto e **precisam ser
conferidos na página**. Exemplos a verificar: `Al ≥ 30%`, `V ≥ 65%`, `Ca ≥ 4,0`, `Mg ≥ 1,0`,
`Al% > 10`, `SMP ≤ 4,4`.
