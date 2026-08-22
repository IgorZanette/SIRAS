"""
Testes de validação de siras/dominio/analise.py.

Testa:
- AnaliseSolo: campos obrigatórios e faixa física plausível de cada atributo
- Contexto: campos obrigatórios e faixa física plausível de prnt/profundidade_incorporacao_cm
"""

import pytest

from siras.dominio.analise import AnaliseSolo, Contexto


def _analise_valida(**sobrescreve):
    """Constrói uma AnaliseSolo válida, permitindo sobrescrever campos específicos."""
    campos = dict(
        ph_agua=5.5,
        indice_smp=5.4,
        argila=30.0,
        mo=2.5,
        p=8.0,
        k=120.0,
        ctc_ph7=12.0,
        al=0.5,
        ca=3.0,
        mg=1.5,
        v_percent=55.0,
    )
    campos.update(sobrescreve)
    return AnaliseSolo(**campos)


def _contexto_valido(**sobrescreve):
    """Constrói um Contexto válido, permitindo sobrescrever campos específicos."""
    campos = dict(
        cultura_id="soja",
        sistema_manejo="convencional",
        condicao_area="todos os casos",
        prnt=100.0,
        profundidade_incorporacao_cm=20.0,
    )
    campos.update(sobrescreve)
    return Contexto(**campos)


class TestAnaliseSoloValida:
    def test_construcao_com_valores_validos_nao_levanta(self):
        _analise_valida()


class TestAnaliseSoloCamposObrigatorios:
    @pytest.mark.parametrize(
        "campo",
        [
            "ph_agua", "indice_smp", "argila", "mo", "p", "k",
            "ctc_ph7", "al", "ca", "mg", "v_percent",
        ],
    )
    def test_campo_nulo_levanta_value_error(self, campo):
        with pytest.raises(ValueError, match=campo):
            _analise_valida(**{campo: None})


class TestAnaliseSoloFaixaFisica:
    @pytest.mark.parametrize("valor", [-0.1, 14.1])
    def test_ph_agua_fora_de_0_a_14_levanta(self, valor):
        with pytest.raises(ValueError, match="ph_agua"):
            _analise_valida(ph_agua=valor)

    def test_ph_agua_nos_limites_nao_levanta(self):
        _analise_valida(ph_agua=0.0)
        _analise_valida(ph_agua=14.0)

    @pytest.mark.parametrize("valor", [2.9, 8.1])
    def test_indice_smp_fora_de_3_a_8_levanta(self, valor):
        with pytest.raises(ValueError, match="indice_smp"):
            _analise_valida(indice_smp=valor)

    def test_indice_smp_nos_limites_nao_levanta(self):
        _analise_valida(indice_smp=3.0)
        _analise_valida(indice_smp=8.0)

    @pytest.mark.parametrize(
        "campo", ["argila", "mo", "p", "k", "ctc_ph7", "al", "ca", "mg"],
    )
    def test_campo_negativo_levanta(self, campo):
        with pytest.raises(ValueError, match=campo):
            _analise_valida(**{campo: -1.0})

    @pytest.mark.parametrize("valor", [-0.1, 100.1])
    def test_v_percent_fora_de_0_a_100_levanta(self, valor):
        with pytest.raises(ValueError, match="v_percent"):
            _analise_valida(v_percent=valor)

    def test_v_percent_nos_limites_nao_levanta(self):
        _analise_valida(v_percent=0.0)
        _analise_valida(v_percent=100.0)


class TestContextoValido:
    def test_construcao_com_valores_validos_nao_levanta(self):
        _contexto_valido()

    def test_expectativa_rendimento_e_opcional(self):
        contexto = _contexto_valido()
        assert contexto.expectativa_rendimento is None


class TestContextoCamposObrigatorios:
    @pytest.mark.parametrize(
        "campo", ["cultura_id", "sistema_manejo", "condicao_area"],
    )
    def test_string_vazia_levanta(self, campo):
        with pytest.raises(ValueError, match=campo):
            _contexto_valido(**{campo: ""})

    def test_prnt_nulo_levanta(self):
        with pytest.raises(ValueError, match="prnt"):
            _contexto_valido(prnt=None)

    def test_profundidade_incorporacao_cm_nula_levanta(self):
        with pytest.raises(ValueError, match="profundidade_incorporacao_cm"):
            _contexto_valido(profundidade_incorporacao_cm=None)


class TestContextoFaixaFisica:
    @pytest.mark.parametrize("valor", [-0.1, 100.1])
    def test_prnt_fora_de_0_a_100_levanta(self, valor):
        with pytest.raises(ValueError, match="prnt"):
            _contexto_valido(prnt=valor)

    def test_prnt_nos_limites_nao_levanta(self):
        _contexto_valido(prnt=0.0)
        _contexto_valido(prnt=100.0)

    @pytest.mark.parametrize("valor", [0.0, -10.0, 10.0, 25.0, 40.0])
    def test_profundidade_incorporacao_cm_fora_de_20_ou_30_levanta(self, valor):
        with pytest.raises(ValueError, match="profundidade_incorporacao_cm"):
            _contexto_valido(profundidade_incorporacao_cm=valor)

    def test_profundidade_incorporacao_cm_20_ou_30_nao_levanta(self):
        _contexto_valido(profundidade_incorporacao_cm=20.0)
        _contexto_valido(profundidade_incorporacao_cm=30.0)
