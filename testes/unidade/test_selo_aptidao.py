"""
Cor do selo de aptidão.

"Apta com restrições" era âmbar, e âmbar ali dizia que a área não está apta. Ela está: a
restrição qualifica a aptidão, não a retira. Um selo amarelo logo abaixo da recomendação
fazia o leitor entender que a recomendação emitida não seria suficiente — conclusão oposta
à do CCAE, e a mais cara que este documento pode induzir.

As duas classes aptas são verdes, separadas por vivacidade. A ressalva ganha uma marca de
atenção pequena, em âmbar, no canto do selo: presente o bastante para ser notada, discreta
o bastante para não disputar com o veredito.

As cores foram MEDIDAS, e não escolhidas no olho: o selo é componente, e o piso é 3:1
(WCAG 1.4.11).
"""

import sys
from pathlib import Path

import pytest

from siras.relatorio.apresentacao import (
    _AMBAR_DE_ATENCAO,
    _SELO_POR_CLASSE_APTIDAO,
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from conferir_contraste import contraste  # noqa: E402

_PAPEL = "#FFFFFF"
#: Piso de componente da WCAG 2.2 (1.4.11). O selo é gráfico, e não texto.
_PISO = 3.0


@pytest.mark.parametrize("classe", ["APTA", "APTA_COM_RESTRICOES"])
def test_as_duas_classes_aptas_sao_verdes(classe):
    """A ressalva não tira a aptidão — e a cor não pode dizer que tira."""
    cor = _SELO_POR_CLASSE_APTIDAO[classe][0]

    vermelho, verde, azul = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    assert verde > vermelho and verde > azul, f"{classe} não é verde: {cor}"


def test_a_apta_e_mais_viva_que_a_apta_com_restricoes():
    """A distinção entre as duas está na vivacidade, e não na família de cor."""
    import colorsys

    def saturacao(cor):
        canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        return colorsys.rgb_to_hls(*canais)[2]

    def luminosidade(cor):
        canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        return colorsys.rgb_to_hls(*canais)[1]

    apta = _SELO_POR_CLASSE_APTIDAO["APTA"][0]
    ressalva = _SELO_POR_CLASSE_APTIDAO["APTA_COM_RESTRICOES"][0]

    assert saturacao(apta) > saturacao(ressalva), "a apta deveria ser a mais viva"
    assert luminosidade(ressalva) > luminosidade(apta), "a com restrições deveria ser mais clara"


@pytest.mark.parametrize("classe", ["APTA", "APTA_COM_RESTRICOES"])
def test_o_selo_passa_no_piso_de_componente_sobre_o_papel(classe):
    """É este piso que limita quanto o verde da ressalva pode clarear: um contorno que
    ninguém enxerga não informa nada."""
    cor = _SELO_POR_CLASSE_APTIDAO[classe][0]

    razao = contraste(cor, _PAPEL)
    assert razao >= _PISO, f"{classe} em {razao:.2f}:1 sobre o papel, abaixo de {_PISO}:1"


def test_o_ambar_de_atencao_tambem_passa():
    """É um sinal pequeno, e pequeno demais para valer menos que o piso."""
    assert contraste(_AMBAR_DE_ATENCAO, _PAPEL) >= _PISO


def test_so_a_ressalva_recebe_a_marca_de_atencao():
    for classe, (_cor, _icone, atencao) in _SELO_POR_CLASSE_APTIDAO.items():
        assert atencao == (classe == "APTA_COM_RESTRICOES"), (
            f"{classe} não deveria decidir assim a marca de atenção"
        )


@pytest.mark.parametrize("classe", ["APTA", "APTA_COM_RESTRICOES"])
def test_a_cor_do_selo_nao_muda_com_o_tema(classe):
    """O selo vive dentro do laudo, que é papel branco nos dois temas. Com um token de
    tema, ele saía em #FFC93D sobre branco no modo escuro — 1,54:1, invisível."""
    cor = _SELO_POR_CLASSE_APTIDAO[classe][0]

    assert cor.startswith("#"), f"{classe} usa token de tema: {cor}"
    assert "var(" not in cor
