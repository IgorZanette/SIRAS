"""
Escopo de recomendação do SIRAS: quais culturas o sistema se propõe a recomendar.

Existe para separar dois eixos que `dados/comum/mapa_culturas.json` não separa, e cuja
confusão já produziu uma contagem errada do escopo:

1. **estar mapeada** — a cultura tem uma entrada em `mapa_culturas.json` porque algum
   módulo precisa resolver o critério de calagem dela. É invariante de carregamento;
2. **estar no escopo de recomendação** — a cultura é uma das 61 que a Proposta (§4.2.1)
   declara que o SIRAS cobre, e que a interface oferece.

As seis espécies florestais tolerantes à acidez estão no primeiro conjunto e fora do
segundo: o módulo de aptidão precisa delas mapeadas para calcular F1 no cenário POTENCIAL
(onze dos casos de conformidade as usam, e desmapeá-las derruba o CONF-PT-05), mas a
Proposta as exclui explicitamente do escopo de recomendação, porque não têm pH de
referência e a lógica de calagem delas não cabe no modelo padronizado.

Ver docs/decisoes/0006. O CCAE v1.1, Apêndice B, B-4 já havia registrado que o
mapeamento é "invariante do carregador, não afirmação agronômica sobre a espécie".

Distinto de `criterios_aptidao.json → fora_de_escopo` (mandioca e arroz irrigado): lá a
cultura é recusada com ErroAptidao, porque está fora do escopo do módulo de aptidão
inteiro. Aqui a cultura é avaliada normalmente e apenas não é oferecida para recomendação.
"""

from __future__ import annotations

from typing import FrozenSet

from siras.dominio.nomes import normalizar_nome_cultura

#: As seis espécies florestais tolerantes à acidez, na forma canônica de comparação.
#: Compartilham o critério de calagem `erva_mate_e_florestais` com a erva-mate, que
#: **está** no escopo — por isso a lista é explícita, e não derivada do critério.
ESPECIES_FLORESTAIS: FrozenSet[str] = frozenset(
    normalizar_nome_cultura(nome)
    for nome in (
        "acácia-negra",
        "araucária",
        "bracatinga",
        "cedro-australiano",
        "eucalipto",
        "pinus",
    )
)

#: Total de culturas e grupos de culturas do escopo aprovado (Proposta §4.2.1):
#: 21 grãos + 18 hortaliças + 2 tubérculos + 17 frutíferas + 1 erva-mate + 2 outras.
TOTAL_DE_CULTURAS_NO_ESCOPO = 61


def no_escopo_de_recomendacao(cultura_id: str) -> bool:
    """A cultura é uma das 61 que o SIRAS se propõe a recomendar?

    Falso não significa "não avaliável": significa "não oferecida para recomendação".
    A aptidão edáfica das espécies florestais continua sendo calculada normalmente.
    """
    return normalizar_nome_cultura(cultura_id) not in ESPECIES_FLORESTAIS


__all__ = [
    "ESPECIES_FLORESTAIS",
    "TOTAL_DE_CULTURAS_NO_ESCOPO",
    "no_escopo_de_recomendacao",
]
