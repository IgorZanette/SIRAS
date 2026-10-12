"""
POST /api/interpretar — a leitura ao vivo pelo caminho real.

O critério de pronto da etapa (PLANO-FRONTEND §12) é "digitar 110 em fósforo muda a
classe em menos de 500 ms". A latência em localhost não é o que arrisca falhar; o que
arrisca é a regra migrar para o JavaScript com o tempo. Por isso há aqui também uma
guarda sobre o conteúdo de leitura-ao-vivo.js.
"""

import json
import re
from pathlib import Path

import pytest

from siras.web import criar_app

_JS = Path(__file__).parent.parent.parent / "siras" / "web" / "static" / "js" / "leitura-ao-vivo.js"

_ANALISE = {
    "cultura_id": "soja",
    "criterio_id": "graos_convencional",
    "prnt": "100",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


def test_erro_de_transcricao_em_fosforo_muda_a_classe(cliente):
    """Digitar 110 em vez de 11,0 salta a classe. É a justificativa nº 2 da §9.3: o erro
    é percebido no campo em que ocorreu, e não três telas adiante."""
    certo = cliente.post("/api/interpretar", json=_ANALISE).get_json()
    errado = cliente.post("/api/interpretar", json=dict(_ANALISE, p="110")).get_json()

    assert certo["classes"]["p"] != errado["classes"]["p"]
    assert errado["classes"]["p"] == "muito_alto"


def test_resposta_traz_a_marcacao_pronta(cliente):
    corpo = cliente.post("/api/interpretar", json=_ANALISE).get_json()

    assert "regua" in corpo["html"]
    assert "ficha" in corpo["html"]
    assert "Calcário estimado" in corpo["html"]


def test_formulario_vazio_responde_com_o_convite(cliente):
    corpo = cliente.post("/api/interpretar", json={}).get_json()

    assert corpo["classes"] == {"p": None, "k": None}
    assert "assim que você digitar o primeiro valor" in corpo["html"]


def test_virgula_decimal_e_aceita_pela_api(cliente):
    com_ponto = cliente.post("/api/interpretar", json=_ANALISE).get_json()
    com_virgula = cliente.post("/api/interpretar", json=dict(_ANALISE, p="11,0")).get_json()

    assert com_ponto["classes"] == com_virgula["classes"]


def test_corpo_invalido_nao_derruba_a_rota(cliente):
    """O painel não pode ser um caminho para 500 na tela do usuário."""
    resposta = cliente.post("/api/interpretar", data="nada disso",
                            content_type="application/json")

    assert resposta.status_code == 200
    assert resposta.get_json()["classes"] == {"p": None, "k": None}


def test_a_api_responde_rapido_o_bastante_para_o_painel(cliente):
    """O limite de 500 ms da §12 vale para a percepção; aqui se mede o servidor, sem o
    debounce de 300 ms do cliente."""
    import time

    inicio = time.perf_counter()
    for _ in range(5):
        cliente.post("/api/interpretar", json=_ANALISE)
    media_ms = (time.perf_counter() - inicio) / 5 * 1000

    assert media_ms < 200, f"média de {media_ms:.0f} ms por interpretação"


def test_o_javascript_nao_carrega_regra_agronomica():
    """A opção A da §9.4 é a que mais frequentemente derruba a validação de um sistema
    especialista: a regra existe em Python e em JavaScript, e as duas divergem. Esta
    guarda falha se alguém começar a classificar no cliente."""
    codigo = _JS.read_text(encoding="utf-8")

    for termo in ("muito_baixo", "muito_alto", "Tabela", "PRNT", "SMP", "p2o5", "k2o"):
        assert termo not in codigo, f"'{termo}' apareceu no JavaScript da leitura ao vivo"

    # Nenhum vetor de limiares: uma tabela de classificação sempre vira um array.
    assert not re.search(r"\[\s*\d+(\.\d+)?\s*,\s*\d+", codigo), "vetor de limiares no JS"


def test_o_debounce_declarado_e_o_do_plano():
    codigo = _JS.read_text(encoding="utf-8")
    assert re.search(r"ESPERA_MS\s*=\s*300", codigo)
