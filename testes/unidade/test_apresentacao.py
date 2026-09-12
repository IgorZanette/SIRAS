"""
Camada de apresentação (siras/relatorio/apresentacao.py).

As faixas usadas nos testes de posicao_na_regua são sintéticas e redondas, escolhidas
para que a conta seja conferível de cabeça. Não são as faixas do Manual e não valem como
verificação da base de conhecimento — a função é aritmética de posicionamento, e é isso
que está sendo testado.
"""

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.relatorio.apresentacao import (
    formatar_dose,
    formatar_enxuto,
    formatar_numero,
    humanizar_evidencia,
    nome_de_exibicao,
    posicao_na_regua,
    rotulo_da_classe,
    sigla_da_classe,
)

_FAIXAS_SINTETICAS = [
    {"classe": "muito_baixo", "de": None, "ate": 10.0},
    {"classe": "baixo", "de": 10.0, "ate": 20.0},
    {"classe": "medio", "de": 20.0, "ate": 30.0},
    {"classe": "alto", "de": 30.0, "ate": 40.0},
    {"classe": "muito_alto", "de": 40.0, "ate": None},
]


def test_numero_sai_com_virgula_decimal():
    assert formatar_numero(6.8, 1) == "6,8"
    assert formatar_numero(155, 0) == "155"


def test_numero_ausente_nao_vira_zero():
    """Zero é uma dose; ausência de dose não é. Confundir os dois no laudo é grave."""
    assert formatar_numero(None) == "—"


def test_dose_com_teto_preserva_o_qualificador():
    """Na classe Muito alto em 2º cultivo o Manual dá um teto, não um valor (ADR 0004)."""
    assert formatar_dose({"valor": 45.0, "qualificador": "ate"}) == "até 45"


def test_dose_em_intervalo_preserva_os_dois_extremos():
    assert formatar_dose({"min": 30.0, "max": 60.0}) == "30 a 60"


def test_dose_sem_correspondencia_no_manual_diz_isso():
    """O K da videira não tem correspondência solo-tecido declarada. Exibir um número
    ali seria inventar recomendação."""
    assert formatar_dose({"pendente": True}) == "não definido pelo Manual"


@pytest.mark.parametrize(
    "valor, classe, esperado",
    [
        (15.0, "baixo", 30.0),    # meio da 2a faixa -> 20% + metade de 20%
        (10.1, "baixo", 20.2),    # rente ao limite inferior
        (19.9, "baixo", 39.8),    # rente ao limite superior
        (25.0, "medio", 50.0),
    ],
)
def test_marcador_situa_o_valor_dentro_da_faixa(valor, classe, esperado):
    """É esta posição que responde 'quão perto da borda da classe estou' — a pergunta
    que separa a régua de um enfeite."""
    assert posicao_na_regua(valor, _FAIXAS_SINTETICAS, classe) == pytest.approx(esperado)


def test_primeira_faixa_usa_o_zero_como_piso():
    """'de' nulo não é faixa sem início: teor negativo não existe e AnaliseSolo o rejeita."""
    assert posicao_na_regua(5.0, _FAIXAS_SINTETICAS, "muito_baixo") == pytest.approx(10.0)


def test_ultima_faixa_nao_afirma_posicao():
    """Aberta para cima: não há como situar um valor dentro de uma faixa sem fim. A régua
    acende a classe e cala sobre a posição, em vez de fingir uma."""
    assert posicao_na_regua(120.0, _FAIXAS_SINTETICAS, "muito_alto") is None


def test_classe_desconhecida_nao_quebra_a_regua():
    assert posicao_na_regua(15.0, _FAIXAS_SINTETICAS, "inexistente") is None


def test_valor_inteiro_nao_ganha_casa_decimal():
    assert formatar_enxuto(100.0) == "100"
    assert formatar_enxuto(87.5) == "87,5"


def test_evidencia_sai_com_separador_decimal_unico():
    """O motor interpola floats de Python, então a mesma frase mistura o ponto do repr
    com a vírgula do limiar transcrito. Num documento isso lê como erro."""
    bruto = "pH 5.1 < 5,5; m% = 24.3 -> MODERADO"
    assert humanizar_evidencia(bruto) == "pH 5,1 < 5,5; m% = 24,3 → MODERADO"


def test_humanizar_evidencia_nao_mexe_em_identificador():
    """'grupo_2' e 'Tab. 5.3' não podem virar outra coisa: só separador decimal muda."""
    assert humanizar_evidencia("argila classe 3, grupo_2 -> baixo") == (
        "argila classe 3, grupo_2 → baixo"
    )


def test_classe_tem_sigla_e_rotulo_legivel():
    assert sigla_da_classe("muito_baixo") == "mb"
    assert rotulo_da_classe("muito_baixo") == "Muito baixo"


def test_nome_da_cultura_vem_do_anexo_2():
    assert nome_de_exibicao("soja", carregar_dados_comum()) == "Soja"


def test_cultura_fora_do_anexo_2_cai_no_identificador_legibilizado():
    """arroz_de_sequeiro está em mapa_culturas.json e não no Anexo 2. É lacuna de
    transcrição registrada, não motivo para a tela quebrar."""
    assert nome_de_exibicao("arroz_de_sequeiro", carregar_dados_comum()) == "Arroz de sequeiro"
