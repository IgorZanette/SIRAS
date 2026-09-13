"""
A marca do SIRAS no laudo, a cena da tela de cálculo e a divisão da suíte.

Três pedidos que só se verificam olhando: um laudo que não dizia de onde vinha, uma espera
que não ensinava nada, e uma suíte que demorava tanto que ninguém a rodaria a cada ajuste.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from siras.web import criar_app

_RAIZ = Path(__file__).parent.parent.parent
_ESTATICOS = _RAIZ / "siras" / "web" / "static"
_TELAS_CSS = (_ESTATICOS / "css" / "siras-telas.css").read_text(encoding="utf-8")
_IMPRESSA_CSS = (_ESTATICOS / "css" / "siras-impressa.css").read_text(encoding="utf-8")
_GERANDO_JS = (_ESTATICOS / "js" / "gerando.js").read_text(encoding="utf-8")

_ANALISE = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}


@pytest.fixture
def cliente():
    return criar_app({"TESTING": True}).test_client()


def _documento(html: str) -> str:
    return html[html.index('<article class="doc">'):]


# --- a marca no laudo ------------------------------------------------------------

def test_o_laudo_diz_de_onde_veio(cliente):
    """Um laudo impresso, anexado a um projeto de crédito e lido por quem nunca abriu o
    sistema não dizia SIRAS em lugar nenhum."""
    documento = _documento(
        cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)
    )

    assert 'class="doc__marca"' in documento
    assert "img/marca/siras-icone-64.png" in documento
    assert 'alt="SIRAS"' in documento


def test_a_palavra_da_marca_no_papel_e_a_escura(cliente):
    """O laudo é papel branco nos dois temas: a palavra branca da barra sumiria nele."""
    documento = _documento(
        cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)
    )

    assert "img/marca/siras-texto-escuro.png" in documento
    assert "img/marca/siras-texto.png" not in documento


def test_o_rodape_repete_a_origem_com_a_data(cliente):
    """É o que se procura quando o documento já se separou da primeira folha."""
    documento = _documento(
        cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)
    )

    assert re.search(r"Laudo gerado pelo SIRAS em \d{2}/\d{2}/\d{4}", documento)


def test_a_marca_sai_no_papel(cliente):
    """Marca que só existe na tela não resolve o problema: é a cópia impressa que
    circula sem o sistema por perto."""
    documento = _documento(
        cliente.post("/analise/laudo", data=_ANALISE).get_data(as_text=True)
    )
    marca = re.search(r'<div class="doc__marca"[^>]*>', documento).group(0)

    assert "nao-imprime" not in marca


def test_a_versao_impressa_tambem_leva_a_marca(cliente):
    documento = _documento(
        cliente.post(
            "/analise/laudo", data=dict(_ANALISE, formato="impressa")
        ).get_data(as_text=True)
    )

    assert 'class="doc__marca"' in documento
    assert "Laudo gerado pelo SIRAS em" in documento


def test_no_papel_preto_e_branco_a_marca_vai_em_cinza():
    """Tirá-la da versão impressa seria tirá-la da cópia que mais circula; deixá-la
    colorida gastaria a única tinta verde da folha num logotipo."""
    assert re.search(
        r":root body\.impressa \.doc__marca img[^{]*\{[^}]*grayscale\(1\)", _IMPRESSA_CSS, re.S
    )


# --- a cena da tela de cálculo ------------------------------------------------------

def test_a_tela_de_espera_mostra_a_marca(cliente):
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert 'class="calculando__assinatura"' in html


def test_a_cena_existe_e_e_decorativa_para_o_leitor_de_tela(cliente):
    """A informação está nos cinco passos, que são texto. A cena os ilustra — anunciá-la
    a quem não a vê seria repetir a lista com ruído."""
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)
    cena = re.search(r'<svg class="cena"[^>]*>', html).group(0)

    assert 'aria-hidden="true"' in cena


@pytest.mark.parametrize("etapa", ["1", "2", "3", "4", "5", "pronto"])
def test_cada_passo_do_motor_tem_o_seu_movimento_na_cena(etapa):
    """Nada na cena se mexe por acaso: cada movimento acende junto de um módulo real do
    motor, na ordem em que gerar_laudo() os chama."""
    assert f'.calculando[data-etapa="{etapa}"]' in _TELAS_CSS, (
        f"a etapa {etapa} não desenha nada na cena"
    )


def test_o_broto_cresce_com_o_progresso_raiz_primeiro():
    """A ordem é a da planta, e não a de uma barra: raiz, caule em degraus, folhas, e a
    última folha só quando o laudo fica pronto."""
    assert re.search(r"\.calculando\.passou-1 \.cena__raizes path \{ stroke-dashoffset: 0;",
                     _TELAS_CSS)

    degraus = [
        int(re.search(rf"\.calculando\.passou-{n} \.cena__caule \{{ stroke-dashoffset: (\d+);",
                      _TELAS_CSS).group(1))
        for n in (1, 2, 3, 4)
    ]
    assert degraus == sorted(degraus, reverse=True), f"o caule não sobe em degraus: {degraus}"
    assert degraus[-1] == 0, "o caule não chega ao fim antes do pronto"

    assert re.search(r'\.calculando\[data-etapa="pronto"\] \.cena__folha--topo', _TELAS_CSS)


def test_o_script_diz_a_etapa_e_nao_desenha():
    """O que cada passo desenha mora no CSS. Assim a cena pode ser redesenhada sem tocar
    na lógica do envio."""
    assert "data-etapa" in _GERANDO_JS
    assert '"passou-"' in _GERANDO_JS
    assert "cena__" not in _GERANDO_JS, "o script está conhecendo peças da cena"


def test_a_cena_para_de_se_mexer_com_menos_movimento():
    """Os passos continuam acendendo e o broto aparece em cada degrau; só para o que se
    repete em laço, que é o que causa desconforto vestibular."""
    blocos = re.findall(r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", _TELAS_CSS, re.S)
    da_cena = [bloco for bloco in blocos if ".cena__" in bloco]

    assert da_cena, "nenhum bloco de menos movimento cobre a cena"
    assert "animation: none" in da_cena[0]
    for laco in (".cena__leitura", ".cena__calcario circle", ".cena__nutriente"):
        assert laco in da_cena[0], f"{laco} continua em laço com menos movimento"


def test_a_espera_continua_curta():
    """O pedido original era de três a cinco segundos: tempo de ler os passos, e não de
    esperar por eles."""
    espera = int(re.search(r"var ESPERA_MINIMA_MS = (\d+);", _GERANDO_JS).group(1))

    assert 3000 <= espera <= 5000


def test_a_animacao_antiga_saiu_por_inteiro():
    """Regra de CSS sem elemento que a use é resto — e resto de animação costuma voltar a
    aparecer numa refatoração."""
    for resto in (".calculando__simbolo", ".calculando__pulso", "@keyframes pulsar",
                  "@keyframes brotar"):
        assert resto not in _TELAS_CSS, f"{resto} ficou no CSS"


# --- a suíte em duas camadas -----------------------------------------------------------

def test_as_bancadas_lentas_estao_marcadas():
    for nome in ("test_bancada_cenarios.py", "test_bancada_culturas.py"):
        codigo = (_RAIZ / "testes" / "integracao" / nome).read_text(encoding="utf-8")
        assert "pytestmark = pytest.mark.lenta" in codigo, f"{nome} não está marcada"


def test_a_conformidade_do_ccae_fica_na_camada_rapida():
    """É o oráculo do trabalho e custa doze segundos. Um ajuste que a quebrasse precisa
    ser visto na hora, e não na véspera da entrega."""
    codigo = (_RAIZ / "testes" / "unidade" / "test_conformidade_aptidao.py").read_text(
        encoding="utf-8"
    )

    assert "mark.lenta" not in codigo


def _coletados(*argumentos) -> str:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "--co", "-q",
         "testes/integracao/test_bancada_culturas.py", *argumentos],
        cwd=_RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout


def test_sem_completa_a_bancada_e_retirada_da_coleta():
    """Retirada, e não pulada: dois mil e setecentos 's' na saída esconderiam o pulo que
    importa, o que alguém marcou por um motivo real."""
    saida = _coletados()

    assert "deselected" in saida
    assert "skipped" not in saida


def test_com_completa_a_bancada_volta():
    saida = _coletados("--completa")

    assert re.search(r"\d+ tests? collected", saida)
    assert "deselected" not in saida
