"""
Fluxo web ponta a ponta: formulário -> gerar_laudo() -> laudo em tela.

Critério de pronto da etapa (PLANO-FRONTEND §12): "um caso de teste de soja produz
calcário e NPK conferidos à mão". Aqui o caso ADU-01 de testes/casos/ é submetido pelo
POST real da aplicação e os números do `referencia` são procurados no HTML servido — o
caminho inteiro, incluindo leitura do formulário, montagem de AnaliseSolo e Contexto e
formatação. Nenhum valor agronômico é escrito neste arquivo.
"""

import json
import re
from pathlib import Path

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.relatorio.apresentacao import formatar_numero
from siras.web import criar_app

_CAMINHO_CASOS = Path(__file__).parent.parent / "casos" / "casos_recomendacao.json"


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


def _caso(caso_id: str) -> dict:
    dados = json.loads(_CAMINHO_CASOS.read_text(encoding="utf-8"))
    return next(c for c in dados["casos"] if c["id"] == caso_id)


def _formulario_do_caso(caso: dict) -> dict:
    """Traduz a entrada do caso para os nomes dos campos do formulário.

    Ca, Mg, Al e V% não constam dos casos de recomendação (que existem para calagem e
    adubação) e entram como zero, a mesma convenção de testes/unidade/test_casos_validados.py.
    Eles não afetam calagem nem NPK — só a aptidão, que tem conjunto de validação próprio.
    """
    entrada = caso["entrada"]
    return {
        "cultura_id": entrada["cultura"],
        "criterio_id": "graos_convencional",
        "cultivo": str(entrada.get("cultivo", 1)),
        "profundidade_incorporacao_cm": str(int(entrada["profundidade_incorporacao_cm"])),
        "antecedente": "",
        "prnt": str(entrada["prnt"]),
        "expectativa_rendimento": str(entrada.get("expectativa_rendimento", "")),
        "ph_agua": str(entrada["ph_agua"]),
        "indice_smp": str(entrada["indice_smp"]),
        "al": "0", "ca": "0", "mg": "0", "v_percent": "0", "saturacao_al": "",
        "argila": str(entrada["argila"]),
        "mo": str(entrada["mo"]),
        "p": str(entrada.get("p", 0)),
        "k": str(entrada.get("k", 0)),
        "ctc_ph7": str(entrada["ctc_ph7"]),
    }


def test_formulario_abre(cliente):
    resposta = cliente.get("/analise/dados")
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'name="indice_smp"' in html
    assert 'name="prnt"' in html


def test_formulario_oferece_as_21_culturas_de_graos(cliente):
    html = cliente.get("/analise/dados").get_data(as_text=True)
    dados = carregar_dados_comum()
    esperadas = [
        cultura_id for cultura_id, entrada in dados["mapa_culturas"]["culturas"].items()
        if entrada.get("grupo") == "graos"
    ]
    assert len(esperadas) == 21
    for cultura_id in esperadas:
        assert f'value="{cultura_id}"' in html, f"{cultura_id} não aparece no formulário"


def test_formulario_nao_oferece_criterio_fora_de_escopo(cliente):
    """Arroz irrigado está fora do escopo do SIRAS pelas próprias notas do critério:
    oferecê-lo na tela seria convidar o usuário a um erro garantido."""
    html = cliente.get("/analise/dados").get_data(as_text=True)
    assert "arroz_irrigado_solo_seco" not in html
    assert "arroz_irrigado_pregerminado" not in html


def test_adu_01_pelo_post_produz_os_numeros_da_referencia(cliente):
    caso = _caso("ADU-01")
    referencia = caso["referencia"]

    resposta = cliente.post("/analise/laudo", data=_formulario_do_caso(caso))
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)

    assert formatar_numero(referencia["nc_t_ha"], 1) in html
    for nutriente in ("n", "p2o5", "k2o"):
        assert formatar_numero(referencia[nutriente], 0) in html, (
            f"{nutriente} = {referencia[nutriente]} não aparece no laudo"
        )
    assert "Muito baixo" in html   # classe_p do caso
    assert "Médio" in html         # classe_k do caso


def test_cal_01_pelo_post_produz_a_dose_da_referencia(cliente):
    caso = _caso("CAL-01")
    resposta = cliente.post("/analise/laudo", data=_formulario_do_caso(caso))

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert formatar_numero(caso["referencia"]["nc_t_ha"], 1) in html
    # Com dose calculada, a trilha cita a tabela de onde a dose saiu.
    assert "Tab. 5.2, p. 70" in html


def test_laudo_traz_a_trilha_e_o_rodape_normativo(cliente):
    caso = _caso("ADU-01")
    html = cliente.post("/analise/laudo", data=_formulario_do_caso(caso)).get_data(as_text=True)

    assert "De onde vem cada número" in html
    # Em ADU-01 a calagem não dispara, então a fonte citada é a do critério (Tab. 5.3),
    # e não a da tabela de dose. A Tabela 5.2 é conferida no caso em que a dose existe.
    assert "Tabela 5.3, p. 75" in html
    assert "R-ADU-01" in html and "R-ADU-03" in html
    assert "Manual de Calagem e Adubação" in html
    assert "não substitui a responsabilidade técnica" in html


def test_laudo_traz_os_dois_cenarios_de_aptidao(cliente):
    caso = _caso("ADU-01")
    html = cliente.post("/analise/laudo", data=_formulario_do_caso(caso)).get_data(as_text=True)

    assert "Aptidão edáfica" in html
    assert "situação atual" in html
    assert "ganho atribuível" in html or "permanece" in html


def test_campos_em_branco_dizem_quais_faltam(cliente):
    resposta = cliente.post("/analise/laudo", data={"cultura_id": "soja"})

    assert resposta.status_code == 422
    html = resposta.get_data(as_text=True)
    assert "O laudo não foi gerado" in html
    assert "Faltam valores em:" in html
    assert "Índice SMP" in html
    assert "Argila" in html


def test_valor_fora_da_faixa_fisica_e_recusado_com_a_faixa_aceita(cliente):
    """A faixa citada é a que o domínio já valida, não uma inventada pela interface."""
    caso = _caso("ADU-01")
    formulario = _formulario_do_caso(caso)
    formulario["indice_smp"] = "12"

    resposta = cliente.post("/analise/laudo", data=formulario)

    assert resposta.status_code == 422
    html = resposta.get_data(as_text=True)
    assert "indice_smp" in html
    assert "3,0" in html and "8,0" in html


def test_formulario_volta_preenchido_apos_erro(cliente):
    """Errar um campo não pode custar a redigitação dos outros dezesseis."""
    caso = _caso("ADU-01")
    formulario = _formulario_do_caso(caso)
    formulario["argila"] = ""

    html = cliente.post("/analise/laudo", data=formulario).get_data(as_text=True)

    smp = re.escape(formulario["indice_smp"])
    assert re.search(rf'id="indice_smp"[^>]*value="{smp}"', html), "o SMP digitado se perdeu"
    assert re.search(r'class="campo campo--erro" for="argila"', html)


def test_texto_nao_numerico_e_recusado_sem_quebrar(cliente):
    caso = _caso("ADU-01")
    formulario = _formulario_do_caso(caso)
    formulario["ph_agua"] = "cinco"

    resposta = cliente.post("/analise/laudo", data=formulario)

    assert resposta.status_code == 422
    assert "não é um número" in resposta.get_data(as_text=True)


def test_virgula_decimal_e_aceita(cliente):
    """Um laudo de laboratório brasileiro imprime 5,4 — não 5.4."""
    caso = _caso("CAL-01")
    formulario = _formulario_do_caso(caso)
    formulario["indice_smp"] = "5,4"
    formulario["ph_agua"] = "5,1"

    resposta = cliente.post("/analise/laudo", data=formulario)

    assert resposta.status_code == 200
    assert formatar_numero(caso["referencia"]["nc_t_ha"], 1) in resposta.get_data(as_text=True)


def test_get_no_laudo_volta_ao_formulario(cliente):
    resposta = cliente.get("/analise/laudo")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/analise/dados")
