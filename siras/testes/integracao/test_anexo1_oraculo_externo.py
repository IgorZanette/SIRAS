"""
O Anexo 1 do Manual (p. 353-354) como oráculo externo, conferido pelo MOTOR do SIRAS.

O artigo afirma que o motor reproduz as 32 classificações de P e K que o Manual publica
para as quatro glebas (Tab. A.2 e A.3) e as três doses de calcário que o texto do anexo
calcula. Até 08/11/2026 a única conferência era `scripts/validar_anexo1.py`, que usa uma
cópia própria das tabelas, escrita no script: ela confere o critério, não a base nem o
motor. Este teste passa pelas funções que o laudo usa.

Os dados das glebas e as classes publicadas vêm do próprio script, onde o autor os
transcreveu -- uma fonte só, e nenhum número escrito aqui.
"""

import contextlib
import importlib.util
import io
from pathlib import Path

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.motor import adubacao, calagem

_SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "validar_anexo1.py"
_SIGLA = {"muito_baixo": "MB", "baixo": "B", "medio": "M", "alto": "A", "muito_alto": "MA"}


@pytest.fixture(scope="module")
def anexo1():
    especificacao = importlib.util.spec_from_file_location("validar_anexo1", _SCRIPT)
    modulo = importlib.util.module_from_spec(especificacao)
    with contextlib.redirect_stdout(io.StringIO()):  # o script imprime o relatório
        especificacao.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def dados():
    return carregar_dados_comum()


def test_o_motor_reproduz_as_32_classes_publicadas_de_p_e_k(anexo1, dados):
    divergencias = []
    total = 0
    for cultura, (grupo_p, grupo_k) in anexo1.CULTURAS.items():
        for gleba in (1, 2, 3, 4):
            g = anexo1.GLEBAS[gleba]
            p = adubacao.classificar_fosforo(f"grupo_{grupo_p}", g["argila"], g["p"], dados)
            k = adubacao.classificar_potassio(f"grupo_{grupo_k}", g["ctc"], g["k"], dados)
            for nutriente, obtida, publicada in (
                ("P", _SIGLA[p["classe"]], anexo1.A2[cultura][gleba - 1]),
                ("K", _SIGLA[k["classe"]], anexo1.A3[cultura][gleba - 1]),
            ):
                total += 1
                if obtida != publicada:
                    divergencias.append(f"{cultura}, gleba {gleba}, {nutriente}: "
                                        f"motor {obtida}, Manual {publicada}")

    assert total == 32
    assert not divergencias, divergencias


def test_a_tabela_smp_transcrita_reproduz_as_doses_do_texto_do_anexo(anexo1, dados):
    for gleba, dose_publicada in anexo1.esperado.items():
        linha, _motivo = calagem._linha_smp(
            dados["calagem_smp"]["tabela"], anexo1.GLEBAS[gleba]["smp"]
        )
        assert linha is not None, f"gleba {gleba}: SMP fora da tabela"
        assert linha["nc_ph_6_0"] == pytest.approx(dose_publicada), f"gleba {gleba}"
