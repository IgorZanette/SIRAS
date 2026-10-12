"""
Pontuação de CPF e CNPJ no documento do responsável.

Quem decide qual máscara vale é a contagem de dígitos: onze é CPF, quatorze é CNPJ. Não
há seletor perguntando de qual dos dois se trata, porque o próprio número já diz.

Fora dessas duas contagens o texto sai como foi digitado. Encaixar dez ou doze dígitos na
máscara do CPF à força produziria um documento que PARECE válido e não é — e num laudo
assinado isso é pior que o número cru.

Formatar não é validar: o dígito verificador não é conferido aqui, e o sistema não afirma
em lugar nenhum que o documento existe. Ele apenas escreve o que foi informado no formato
em que um conferente espera lê-lo.
"""

import re
from pathlib import Path

import pytest

from siras.web.formulario import formatar_documento

_JS = (
    Path(__file__).parent.parent.parent / "siras" / "web" / "static" / "js" / "documento.js"
).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "bruto, esperado",
    [
        ("02288399302", "022.883.993-02"),
        ("12345678000195", "12.345.678/0001-95"),
    ],
)
def test_a_contagem_de_digitos_escolhe_a_mascara(bruto, esperado):
    assert formatar_documento(bruto) == esperado


@pytest.mark.parametrize(
    "ja_pontuado",
    ["022.883.993-02", "12.345.678/0001-95"],
)
def test_pontuar_o_que_ja_esta_pontuado_nao_muda_nada(ja_pontuado):
    """É exatamente isto que volta do formulário depois do primeiro envio, e o que chega
    pelo 'Editar a análise'."""
    assert formatar_documento(ja_pontuado) == ja_pontuado


@pytest.mark.parametrize(
    "solto, esperado",
    [
        ("022 883 993 02", "022.883.993-02"),
        ("022-883-993/02", "022.883.993-02"),
        ("12.345.678.0001.95", "12.345.678/0001-95"),
    ],
)
def test_a_pontuacao_de_origem_e_refeita(solto, esperado):
    """Valor colado de planilha vem com a pontuação que a planilha usava."""
    assert formatar_documento(solto) == esperado


@pytest.mark.parametrize("fora_de_faixa", ["1234567890", "123456789012", "12345", "1"])
def test_contagem_que_nao_e_cpf_nem_cnpj_sai_como_veio(fora_de_faixa):
    """Erro visível é erro corrigível: um número encaixado à força na máscara errada
    passaria despercebido no laudo."""
    assert formatar_documento(fora_de_faixa) == fora_de_faixa


def test_campo_vazio_continua_vazio():
    assert formatar_documento("") == ""
    assert formatar_documento("   ") == ""


def test_texto_que_nao_e_documento_e_preservado():
    assert formatar_documento("a confirmar") == "a confirmar"


# --- as duas implementações precisam concordar ----------------------------------

def test_o_navegador_e_o_servidor_usam_a_mesma_tabela_de_mascaras():
    """A máscara existe em dois lugares: no servidor, que é quem pontua o que sai no
    laudo, e no navegador, que pontua enquanto se digita. Divergirem faria o campo mostrar
    um formato e o documento imprimir outro."""
    do_js = dict(
        (int(tamanho), mascara)
        for tamanho, mascara in re.findall(r'(\d+): "([#./-]+)"', _JS)
    )

    assert do_js, "não achei a tabela de máscaras no documento.js"
    assert set(do_js) == {11, 14}

    # "###.###.###-##" descreve a mesma pontuação que "{0}{1}{2}.{3}..." produz.
    for tamanho, mascara in do_js.items():
        pontuado = formatar_documento("1" * tamanho)
        assert len(pontuado) == len(mascara)
        for posicao, caractere in enumerate(mascara):
            if caractere != "#":
                assert pontuado[posicao] == caractere, (
                    f"máscara de {tamanho} dígitos diverge na posição {posicao}"
                )


def test_o_navegador_tambem_deixa_em_paz_o_que_nao_e_documento():
    assert "if (!mascara) {" in _JS
    assert "return texto;" in _JS


def test_o_cursor_e_reposicionado_por_digito_e_nao_por_caractere():
    """Ao inserir um ponto antes do cursor, a posição em caracteres muda e a posição em
    dígitos não. Sem isso, corrigir um número no meio do campo jogava o cursor para o fim
    a cada tecla."""
    assert "digitosAteOCursor" in _JS
    assert "posicaoDoDigito" in _JS
    assert "setSelectionRange" in _JS
