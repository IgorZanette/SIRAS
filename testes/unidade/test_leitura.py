"""
Leitura ao vivo (siras/motor/leitura.py).

O teste que importa neste arquivo é o de concordância: para uma análise completa, o que
o painel mostra enquanto o usuário digita tem de ser o que o laudo emite no fim. Se os
dois puderem divergir, a leitura ao vivo deixa de ser uma prévia e passa a ser uma
segunda opinião — que é exatamente o risco que a §9.4 do plano manda evitar.
"""

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.laudo import gerar_laudo
from siras.motor.leitura import interpretar_parcial

_DADOS = carregar_dados_comum()

_ANALISE_COMPLETA = dict(
    ph_agua=5.1, indice_smp=5.4, argila=38, mo=2.8, p=11, k=96,
    ctc_ph7=9.4, al=1.2, ca=2.4, mg=1.1, v_percent=42,
)


def _ler(campos, **kwargs):
    padrao = dict(cultura_id="soja", grupo="graos", dados=_DADOS)
    padrao.update(kwargs)
    return interpretar_parcial(campos, **padrao)


def test_formulario_vazio_nao_afirma_nada():
    """Nenhuma leitura é melhor que uma leitura calculada sobre zeros."""
    leitura = _ler({})

    assert leitura["fosforo"] is None
    assert leitura["potassio"] is None
    assert leitura["calagem"] is None
    assert leitura["saturacao_al"] is None


def test_fosforo_aparece_com_argila_e_teor():
    """Dois campos bastam para a classe de P: é o que faz o erro de transcrição ser
    percebido no campo em que ocorreu."""
    leitura = _ler({"argila": 38, "p": 11})

    assert leitura["fosforo"]["classe"]
    assert leitura["fosforo"]["faixas"]
    assert leitura["potassio"] is None


def test_potassio_depende_da_ctc_e_nao_da_argila():
    leitura = _ler({"ctc_ph7": 9.4, "k": 96})

    assert leitura["potassio"]["classe"]
    assert leitura["fosforo"] is None


def test_saturacao_por_aluminio_e_derivada_quando_nao_informada():
    leitura = _ler({"al": 1.2, "ca": 2.4, "mg": 1.1, "k": 96})

    assert leitura["saturacao_al"] == pytest.approx(
        AnaliseSolo(**_ANALISE_COMPLETA).obter_saturacao_al()
    )


def test_saturacao_informada_no_laudo_prevalece_sobre_a_derivada():
    leitura = _ler({"al": 1.2, "ca": 2.4, "mg": 1.1, "k": 96, "saturacao_al": 31.0})

    assert leitura["saturacao_al"] == 31.0


def test_calagem_so_aparece_com_a_analise_inteira():
    """Completar com zero o que falta mudaria a dose dos critérios que leem V% ou
    saturação por Al — a estimativa calaria melhor do que mentiria."""
    quase = dict(_ANALISE_COMPLETA)
    del quase["v_percent"]

    assert _ler(quase, criterio_id="graos_convencional", prnt=100)["calagem"] is None
    assert _ler(_ANALISE_COMPLETA, criterio_id="graos_convencional", prnt=100)["calagem"]


def test_leitura_ao_vivo_concorda_com_o_laudo():
    """O ponto inteiro da opção B da §9.4: uma implementação só da interpretação."""
    leitura = _ler(_ANALISE_COMPLETA, criterio_id="graos_convencional", prnt=100)

    laudo = gerar_laudo(
        AnaliseSolo(**_ANALISE_COMPLETA),
        "soja",
        Contexto(
            cultura_id="soja", sistema_manejo="convencional", condicao_area="todos os casos",
            prnt=100, profundidade_incorporacao_cm=20,
        ),
    )

    assert leitura["fosforo"]["classe"] == laudo.adubacao.classe_p
    assert leitura["potassio"]["classe"] == laudo.adubacao.classe_k
    assert leitura["calagem"]["nc_t_ha"] == laudo.calagem.nc_t_ha
    assert leitura["fosforo"]["faixas"] == laudo.adubacao.faixas_p


def test_valor_fora_de_faixa_fisica_nao_quebra_o_painel():
    """Quem explica o erro é a validação do formulário, na hora de gerar o laudo. O
    painel não é lugar de mensagem de erro sobre algo que ainda está sendo digitado."""
    impossivel = dict(_ANALISE_COMPLETA, indice_smp=99)

    leitura = _ler(impossivel, criterio_id="graos_convencional", prnt=100)

    assert leitura["calagem"] is None
    assert leitura["fosforo"]["classe"]  # o que era interpretável continua interpretado


def test_cultura_nao_escolhida_ainda_deriva_a_saturacao():
    """Saturação por Al não depende de cultura: é aritmética da própria análise."""
    leitura = _ler({"al": 1.2, "ca": 2.4, "mg": 1.1, "k": 96}, cultura_id="", grupo="")

    assert leitura["saturacao_al"] is not None
    assert leitura["fosforo"] is None
