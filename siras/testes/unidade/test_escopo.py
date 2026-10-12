"""
Escopo de recomendação (siras/dominio/escopo.py, docs/decisoes/0006).

Guarda a distinção entre estar mapeada em mapa_culturas.json e estar no escopo das 61
culturas da Proposta §4.2.1. Confundir as duas coisas já produziu uma contagem errada do
escopo, e é o tipo de erro que só reaparece meses depois, numa tabela da monografia.
"""

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.escopo import ESPECIES_FLORESTAIS, no_escopo_de_recomendacao
from siras.web.formulario import culturas_disponiveis

_DADOS = carregar_dados_comum()


@pytest.mark.parametrize(
    "cultura",
    ["eucalipto", "pinus", "bracatinga", "acácia-negra", "araucária", "cedro-australiano"],
)
def test_especie_florestal_esta_fora_do_escopo_de_recomendacao(cultura):
    assert not no_escopo_de_recomendacao(cultura)


@pytest.mark.parametrize("grafia", ["acacia_negra", "Acácia-Negra", "ACACIA NEGRA"])
def test_exclusao_independe_da_grafia(grafia):
    """Os conjuntos de teste escrevem 'acacia_negra' e a base escreve 'acácia-negra'."""
    assert not no_escopo_de_recomendacao(grafia)


def test_erva_mate_continua_no_escopo():
    """Compartilha o critério de calagem com as florestais e é a exceção declarada da
    Proposta §4.2.1 — por isso a lista de exclusão é explícita e não derivada do critério."""
    assert no_escopo_de_recomendacao("erva-mate")


@pytest.mark.parametrize("cultura", ["soja", "milho", "macieira", "tomate"])
def test_cultura_de_escopo_permanece_no_escopo(cultura):
    assert no_escopo_de_recomendacao(cultura)


def test_florestais_estao_mapeadas_apesar_de_fora_do_escopo():
    """O módulo de aptidão precisa do mapeamento para calcular F1 no cenário POTENCIAL:
    sem ele o CONF-PT-05 falha (medido). Estar mapeada é invariante de carregamento, não
    afirmação de escopo — CCAE v1.1, Apêndice B, B-4."""
    mapeadas = _DADOS["mapa_culturas"]["culturas"]
    for cultura in ("eucalipto", "pinus", "bracatinga"):
        assert cultura in mapeadas


def test_interface_nao_oferece_especie_florestal():
    oferecidas = {identificador for identificador, _ in culturas_disponiveis(_DADOS, "erva_mate")}
    assert oferecidas == {"erva-mate"}, (
        f"o grupo erva_mate deveria oferecer só a erva-mate, ofereceu {oferecidas}"
    )


def test_catalogo_de_graos_nao_e_afetado():
    oferecidas = culturas_disponiveis(_DADOS, "graos")
    assert len(oferecidas) == 21


def test_exclusao_cobre_exatamente_seis_especies():
    """A Proposta §4.2.1 nomeia seis. Se a lista crescer ou encolher, é decisão de escopo
    e precisa passar pelo ADR, não por um commit de conveniência."""
    assert len(ESPECIES_FLORESTAIS) == 6
