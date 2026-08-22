# Base de conhecimento — formato dos arquivos

Todo arquivo em `dados/` é **dado**, nunca código. A regra é que atualizar o Manual não deve exigir
tocar em nenhum arquivo `.py`.

## Regras gerais

- Codificação UTF-8, indentação de 2 espaços, chaves em `snake_case` sem acento.
- Todo arquivo tem um bloco `fonte` com manual, tabela, página e datas de transcrição e conferência.
- Valor ainda não transcrito: `null` ou `"PREENCHER"`. **Nunca** um valor aproximado.
- Todo arquivo transcrito ganha uma linha em `docs/mapa_manual.md` **no momento da transcrição**.

## Arquivos comuns (`dados/comum/`)

| Arquivo | Origem | Estado |
|---|---|---|
| `calagem_smp.json` | Tabela 5.2, p. 70 + ajustes das p. 71–72, 83 e 298 | transcrito e conferido |
| `ph_referencia.json` | Tabela 5.1, p. 68 | transcrito e conferido |
| `criterios_calagem.json` | Tabelas 5.3 (p. 75), 5.5 (p. 81), 5.6 (p. 83), 5.7 (p. 86) | transcrito e conferido |
| `mapa_culturas.json` | Resolução cultura → critério de calagem (não é tabela do Manual) | parcial — só soja/macieira/erva-mate |
| `interpretacao_p.json` | Tabelas 6.2–6.6, p. 93–94 — classes de P por classe de argila | transcrito e conferido |
| `interpretacao_k.json` | Tabelas 6.7–6.10, p. 95–96 — classes de K por CTC pH 7,0 | transcrito e conferido |
| `interpretacao_geral.json` | Tabelas 6.1, 6.11, 6.12, p. 91/97/98 — MO, CTC, argila, Ca, Mg, S, micronutrientes | transcrito e conferido |
| `corretivos.json` | Cap. 8 — PRNT, tipos de calcário | pendente |

### Arquivos por grupo de cultura (`dados/culturas/<grupo>/`)

Tabelas compartilhadas por todas as culturas de um grupo (não uma por cultura individual):

| Arquivo | Origem | Estado |
|---|---|---|
| `dados/culturas/graos/graos_adubacao_n.json` | Tabelas 6.1.2–6.1.22, p. 116–133 — N por cultura e faixa de MO | transcrito e conferido |
| `dados/culturas/graos/graos_adubacao_pk.json` | Tabelas 6.1.1–6.1.4, p. 105–108 — correção, manutenção e exportação de P/K | transcrito e conferido |

## Arquivos de cultura (`dados/culturas/<grupo>/<cultura>.json`)

Não force um schema único para os 61 itens. Cada arquivo declara qual schema segue, no campo
`schema`, e é validado contra o JSON Schema correspondente em `siras/conhecimento/esquemas/`:

| Schema | Grupos | Particularidade |
|---|---|---|
| `graos_v1` | grãos (21) | dose por classe de disponibilidade × expectativa de rendimento |
| `hortalicas_v1` | hortaliças (18), tubérculos (2) | lógica próxima à de grãos |
| `frutifera_v1` | frutíferas (17) | três fases; P e K de pré-plantio em tabela compartilhada |
| `erva_mate_v1` | erva-mate (1) | dois programas; produção calculada por massa verde e manejo |
| `outras_v1` | cana, tabaco (2) | variantes (planta/soca; Virgínia/Burley) |

### Esqueleto de uma cultura de grãos

```jsonc
{
  "schema": "graos_v1",
  "id": "soja",
  "nome": "Soja",
  "grupo": "graos",
  "fonte": { "manual": "CQFS-RS/SC, 11. ed., 2016", "capitulo": "6.x",
             "tabelas": [], "paginas": [],
             "transcrito_em": null, "conferido_em": null },

  "criterio_calagem": "graos_convencional",   // id em criterios_calagem.json

  "nitrogenio": { "aplica": false, "motivo": "fixacao_biologica_de_nitrogenio" },
  "fosforo":  { "unidade": "kg/ha de P2O5", "modelo": "classe_x_expectativa_rendimento",
                "expectativas_rendimento": [], "doses": {} },
  "potassio": { "unidade": "kg/ha de K2O",  "modelo": "classe_x_expectativa_rendimento",
                "expectativas_rendimento": [], "doses": {} },

  "aptidao_edafica": {
    "fonte": "PREENCHER - fonte INDEPENDENTE do Manual (ver docs/VALIDACAO.md)",
    "criterios": []
  }
}
```

As chaves de classe de disponibilidade são sempre: `muito_baixo`, `baixo`, `medio`, `alto`,
`muito_alto`.

## Validação

`scripts/valida_base.py` percorre `dados/` e valida cada arquivo contra o schema declarado. Deve
falhar apontando arquivo e campo. Rode antes de cada commit que toque em `dados/`.
