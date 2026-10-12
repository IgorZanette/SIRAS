"""
Coerência entre dados/comum/mapa_culturas.json e as culturas transcritas na adubação.

Existe porque essa divergência é silenciosa: um identificador escrito
`beterraba_e_cenoura` de um lado e `beterraba_cenoura` do outro passa em schema, passa
no carregador e só aparece quando alguém gera um laudo para beterraba e recebe
ErroAdubacao. Uma revisão de 2026-09-12 encontrou nove ids nessa situação de uma vez.

Também trava a contagem do escopo em 61. A contagem errada anterior (29 de 61) nasceu de
somar linhas do JSON sem separar "mapeada" de "no escopo de recomendação" — ver
docs/decisoes/0006.
"""

import json
from pathlib import Path

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.escopo import (
    ESPECIES_FLORESTAIS,
    TOTAL_DE_CULTURAS_NO_ESCOPO,
    no_escopo_de_recomendacao,
)

_CULTURAS_DIR = Path(__file__).parent.parent.parent / "dados" / "culturas"
_DADOS = carregar_dados_comum()
_MAPA = _DADOS["mapa_culturas"]["culturas"]

#: Arquivo de adubação de cada grupo, pela chave de grupo de mapa_culturas.json.
#: 'erva_mate' fica de fora: o arquivo dela é indexado por programa e fase, não por
#: cultura, e o grupo inteiro tem uma cultura só no escopo.
_ADUBACAO_POR_GRUPO = {
    "graos": "graos/graos_adubacao_n.json",
    "hortalicas": "hortalicas/hortalicas_adubacao.json",
    "tuberculos": "tuberculos/tuberculos_adubacao.json",
    "outras": "outras/outras_comerciais_adubacao.json",
    "frutiferas": "frutiferas/frutiferas_adubacao.json",
}


def _transcritas(grupo: str) -> set:
    caminho = _CULTURAS_DIR / _ADUBACAO_POR_GRUPO[grupo]
    return set(json.loads(caminho.read_text(encoding="utf-8"))["culturas"])


def _mapeadas(grupo: str) -> set:
    return {
        cultura for cultura, entrada in _MAPA.items() if entrada.get("grupo") == grupo
    }


@pytest.mark.parametrize("grupo", sorted(_ADUBACAO_POR_GRUPO))
def test_toda_cultura_mapeada_no_escopo_tem_dado_de_adubacao(grupo):
    """Sem isso, a cultura aparece na tela e falha na hora de gerar o laudo."""
    sem_dado = sorted(
        cultura
        for cultura in _mapeadas(grupo)
        if no_escopo_de_recomendacao(cultura) and cultura not in _transcritas(grupo)
    )
    assert not sem_dado, (
        f"{grupo}: mapeadas no escopo e sem entrada na adubação: {sem_dado}"
    )


@pytest.mark.parametrize("grupo", sorted(_ADUBACAO_POR_GRUPO))
def test_toda_cultura_com_dado_de_adubacao_esta_mapeada(grupo):
    """A direção contrária: dado transcrito que nenhuma tela alcança é trabalho perdido,
    e normalmente significa que o identificador foi escrito diferente nos dois lados."""
    sem_mapa = sorted(_transcritas(grupo) - _mapeadas(grupo))
    assert not sem_mapa, f"{grupo}: transcritas na adubação e fora do mapa: {sem_mapa}"


def test_erva_mate_esta_mapeada():
    assert "erva-mate" in _MAPA


def test_o_escopo_de_recomendacao_fecha_em_61():
    """21 grãos + 18 hortaliças + 2 tubérculos + 17 frutíferas + 1 erva-mate + 2 outras,
    descontando as seis florestais (Proposta §4.2.1, docs/decisoes/0006)."""
    no_escopo = [c for c in _MAPA if no_escopo_de_recomendacao(c)]
    assert len(no_escopo) == TOTAL_DE_CULTURAS_NO_ESCOPO


def test_as_seis_florestais_continuam_mapeadas():
    """Fora do escopo de recomendação e dentro do mapa: o módulo de aptidão precisa
    delas para calcular F1 no cenário POTENCIAL (CONF-PT-05)."""
    mapeadas_sem_escopo = {c for c in _MAPA if not no_escopo_de_recomendacao(c)}
    assert len(mapeadas_sem_escopo) == len(ESPECIES_FLORESTAIS) == 6


def test_nenhuma_chave_chegou_com_acentuacao_corrompida():
    """UTF-8 lido como cp1252 produz 'acÃ¡cia-negra'. Não é defeito cosmético: a chave
    corrompida não normaliza para 'acacia-negra', escapa do filtro de escopo e a espécie
    florestal volta a ser oferecida na tela."""
    corrompidas = sorted(c for c in _MAPA if "Ã" in c or "Â" in c)
    assert not corrompidas, f"chaves com acentuação corrompida: {corrompidas}"
