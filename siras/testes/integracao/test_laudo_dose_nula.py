"""
O laudo no ponto em que a calagem dispara e a dose é zero — débito 2 do roadmap.

No ramo (b), o gatilho das Tabelas 5.4 e 5.6 inclui o próprio 40 (`V% <= 40`), e ali a
fórmula dá `NC = (40 - 40)/100 x CTC = 0`. Logo abaixo de 40, a dose é positiva mas tão
pequena que arredonda a 0,0 t/ha. Nesses pontos o laudo imprimia, no cartão do calcário,
"Calagem não indicada — None.": o motivo vem vazio quando o critério dispara, e a frase
o interpolava assim mesmo.

O defeito não era só no ponto 40: cobria toda a faixa em que a dose arredonda a zero.
"""

import re
import sys
from pathlib import Path

import pytest

from siras.web import criar_app

sys.path.insert(0, str(Path(__file__).parent))
from test_bancada_cenarios import _campos_da_tela  # noqa: E402


@pytest.fixture(scope="module")
def cliente():
    return criar_app({"TESTING": True}).test_client()


@pytest.fixture(scope="module")
def campos_da_erva_mate(cliente):
    """A erva-mate exige fase, programa e momento; o exemplo da tela os preenche."""
    tela = cliente.get("/analise/dados?cultura_id=erva-mate&exemplo=1").get_data(as_text=True)
    campos = _campos_da_tela(tela)
    campos["cultura_id"] = "erva-mate"
    campos.update(
        ph_agua="5.0", indice_smp="5.5", argila="30", mo="3.0", p="12", k="78.2",
        ctc_ph7="10", al="0.2", ca="3.0", mg="0.8", saturacao_al="", prnt="100",
    )
    return campos


def _observacao_do_calcario(cliente, campos, v_percent):
    resposta = cliente.post("/analise/laudo", data=dict(campos, v_percent=v_percent))
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    documento = html[html.index('<article class="doc">'):]
    return re.search(
        r'dose__nome">Calcário</div>.*?dose__obs">([^<]*)<', documento, re.S
    ).group(1)


@pytest.mark.parametrize("v_percent", ["40.0", "39.99", "39.9"])
def test_dose_nula_com_criterio_atingido_nao_imprime_none(cliente, campos_da_erva_mate, v_percent):
    observacao = _observacao_do_calcario(cliente, campos_da_erva_mate, v_percent)

    assert "None" not in observacao
    assert "o critério da cultura é atingido, mas a dose calculada é de 0,0 t/ha" in observacao


def test_com_dose_positiva_a_observacao_continua_a_de_sempre(cliente, campos_da_erva_mate):
    observacao = _observacao_do_calcario(cliente, campos_da_erva_mate, "38")

    assert observacao.startswith("Dose do corretivo")


def test_sem_disparo_a_observacao_continua_dizendo_o_motivo(cliente, campos_da_erva_mate):
    """Acima de 40 o critério nem dispara, e o motivo existe: essa frase não mudou."""
    observacao = _observacao_do_calcario(cliente, campos_da_erva_mate, "55")

    assert observacao.startswith("Calagem não indicada —")
    assert "None" not in observacao
