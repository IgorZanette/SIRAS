# Concordância da validação

Gerado por `scripts/gera_tabela_concordancia.py`. Protocolo em `docs/validacao/protocolo.md`.

## Dimensão 1 — recomendação de calagem e adubação (H1.1)

Um caso é concordante quando **todas** as saídas que a referência declara coincidem com a saída do motor, admitida apenas tolerância de arredondamento (calcário com uma casa em t/ha, nutrientes inteiros em kg/ha). Acertar três de quatro é discordância.

| Grupo | Casos | Concordantes | Taxa | IC 95% (Wilson) |
|---|---|---|---|---|
| Erva-mate | 2 | 2 | 100,0% | [34,2%; 100,0%] |
| Frutíferas | 4 | 4 | 100,0% | [51,0%; 100,0%] |
| Grãos | 12 | 12 | 100,0% | [75,8%; 100,0%] |
| Hortaliças | 3 | 3 | 100,0% | [43,9%; 100,0%] |
| Cana e tabaco | 3 | 3 | 100,0% | [43,9%; 100,0%] |
| Tubérculos | 1 | 1 | 100,0% | [20,7%; 100,0%] |
| **Global** | **25** | **25** | **100,0%** | **[86,7%; 100,0%]** |

Casos com oráculo: **25**. O protocolo declara alvo de 40 a 80 — a diferença precisa ser declarada na monografia, junto do motivo, e não compensada no texto.

Nenhum caso discordante.

## Dimensão 2 — conformidade da aptidão edáfica (CCAE)

**Conformidade, não concordância.** Mede se a implementação reproduz o Caderno de Critérios congelado, não se os critérios estão agronomicamente corretos — a distinção é do próprio CCAE, §9, e precisa aparecer no texto.

| Métrica | Casos | Acertos | Taxa | IC 95% (Wilson) |
|---|---|---|---|---|
| Classe de aptidão | 88 | 88 | 100,0% | [95,8%; 100,0%] |
| Fator determinante | 88 | 88 | 100,0% | — |

Nenhuma divergência.

