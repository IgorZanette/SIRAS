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
_NARRATIVA = (_ESTATICOS / "js" / "cena-solo" / "stages.js").read_text(encoding="utf-8")

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
    cena = re.search(r'<div class="cena-solo cena-solo--palco[^>]*>', html).group(0)

    assert 'aria-hidden="true"' in cena


@pytest.mark.parametrize("etapa", [1, 2, 3, 4, 5])
def test_cada_passo_do_motor_tem_o_seu_movimento_na_cena(etapa):
    """Nada na cena se mexe por acaso: cada movimento acende junto de um módulo real do
    motor, na ordem em que gerar_laudo() os chama.

    O movimento MUDOU DE LUGAR em 11/10/2026. Era um SVG animado por CSS, e cada etapa
    tinha a sua regra `.calculando[data-etapa="N"] .cena__…`. Agora é a cena 3D, e a
    coreografia de cada etapa está declarada em `PROCESSING_STAGES` (stages.js). O que
    este teste verifica continua sendo o mesmo: a etapa N tem movimento próprio."""
    estagios = _NARRATIVA[_NARRATIVA.index("PROCESSING_STAGES"):]
    coreografias = re.findall(r"\{ id: '([a-z]+)', label:", estagios)

    assert len(coreografias) >= etapa, (
        f"a etapa {etapa} não tem coreografia: só há {len(coreografias)}"
    )
    assert coreografias[etapa - 1], f"a coreografia {etapa} não tem id"


def test_a_cena_nao_melhora_o_solo_enquanto_calcula():
    """O broto que crescia com o progresso saiu junto com o SVG, e no lugar fica a regra
    que ele quase violava.

    O solo é o mesmo do começo ao fim do cálculo. Um perfil que fosse ficando mais vivo
    a cada passo diria, sem número nenhum, que o laudo melhora a lavoura enquanto é
    calculado — e é exatamente a promessa que este sistema não pode fazer. A exceção é
    o fechamento, que alterna os dois cenários DAQUELA análise: ali a diferença é o
    resultado, e vem de dado real."""
    calculo = _NARRATIVA[_NARRATIVA.index("PROCESSING_STAGES"):_NARRATIVA.index("CENARIO_TARGETS")]

    assert "vitality" not in calculo, "algum passo do cálculo mexe na vitalidade do solo"

    fechamento = _NARRATIVA[_NARRATIVA.index("CENARIO_TARGETS"):]
    assert "vitality" in fechamento, "os dois cenários deixaram de se distinguir"


def test_o_script_diz_a_etapa_e_nao_desenha():
    """O que cada passo desenha mora no CSS. Assim a cena pode ser redesenhada sem tocar
    na lógica do envio."""
    assert "data-etapa" in _GERANDO_JS
    assert '"passou-"' in _GERANDO_JS
    assert "cena__" not in _GERANDO_JS, "o script está conhecendo peças da cena"


def test_a_cena_para_de_se_mexer_com_menos_movimento():
    """Os cinco passos continuam acendendo, a barra anda e a frase do Manual troca; só
    para o que se repete em laço, que é o que causa desconforto vestibular.

    QUEM DESLIGA MUDOU. No SVG era CSS — `animation: none` em cada peça animada. Num
    canvas não há peça a desligar, há um laço de render; então quem para é o próprio
    motor, por `reducedMotion`. O adaptador passa a preferência DA APLICAÇÃO, e não só
    a do sistema operacional, e a reaplica quando o usuário a troca, sem recarregar."""
    motor = (_ESTATICOS / "js" / "cena-solo" / "soilScene.js").read_text(encoding="utf-8")
    adaptador = (_ESTATICOS / "js" / "cena-solo.js").read_text(encoding="utf-8")

    assert "prefers-reduced-motion" in motor
    assert "setReducedMotion" in motor and "setReducedMotion" in adaptador
    assert "reducedMotion: menosMovimentoNaApp()" in adaptador
    assert "if (reducedMotion || userPaused) return;" in motor


def test_a_espera_tem_tempo_para_a_cena_acontecer():
    """A duração desta tela é decisão do autor, e mudou três vezes: 4,2 s no começo,
    6,0 s em 13/09/2026 para dar tempo de ler a regra de cada passo, e 24 s em
    11/10/2026, quando a cena 3D entrou e as cinco coreografias não cabiam — o calcário
    caía e a tela já trocava.

    O teste fixa o número para que mudá-lo seja deliberado, e fixa também o que o número
    PRECISA sustentar: cada passo com tempo de uma transição do monólito ser lida como
    movimento, e não como corte.

    É pausa deliberada, não progresso simulado: o motor responde em dezenas de
    milissegundos. Se a avaliação de usabilidade disser que 24 s é demais, este é o
    número a mudar — e nada mais."""
    espera = int(re.search(r"var ESPERA_MINIMA_MS = (\d+);", _GERANDO_JS).group(1))
    pronto = int(re.search(r"var FATIA_DO_PRONTO_MS = (\d+);", _GERANDO_JS).group(1))

    assert espera == 24000

    por_passo = (espera - pronto) / 5
    assert por_passo >= 3000, (
        f"{por_passo:.0f} ms por passo: a coreografia não tem tempo de acontecer"
    )


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


@pytest.mark.parametrize("etapa", [1, 2, 3, 4, 5])
def test_cada_passo_tem_regra_propria(cliente, etapa):
    """Cada passo cita uma regra do Manual que ele aplica — nunca curiosidade inventada.

    Havia TAMBÉM uma etiqueta desenhada no pé do monólito, dizendo o capítulo que o
    passo consulta. Ela saiu com o SVG, e o significado não se perdeu: o que o passo
    consulta está no `<small>` do próprio passo. Aliás melhorou — a etiqueta vivia
    dentro de um SVG `aria-hidden`, então quem não enxergava nunca a teve."""
    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert f"dica-passo--{etapa}" in html
    assert f'.calculando[data-etapa="{etapa}"] .dica-passo--{etapa}' in _TELAS_CSS

    passos = re.findall(r"<b>(.*?)</b>\s*<small>(.*?)</small>", html, re.S)
    assert len(passos) >= 5, f"só {len(passos)} passos com título e consulta"
    titulo, consulta = passos[etapa - 1]
    assert consulta.strip(), f"o passo {etapa} ({titulo.strip()}) não diz o que consulta"


def test_a_espera_anda_continua_e_nao_aos_saltos():
    """O script dá a duração do passo ao CSS, e a barra enche nesse tempo."""
    assert '"--passo-ms"' in _GERANDO_JS
    assert re.search(r"\.calculando__barra i \{ transition: width var\(--passo-ms", _TELAS_CSS)


def test_o_css_do_svg_antigo_saiu_por_inteiro():
    """O SVG do perfil saiu da tela de espera, e as cerca de 150 linhas que o animavam
    saíram com ele. CSS órfão de um elemento que não existe mais é a forma mais
    silenciosa de uma folha de estilo apodrecer: ninguém o vê quebrar, ele só cresce —
    e foi assim que o SVG antigo e a cena 3D chegaram a coexistir sem ninguém notar.

    Os dez tokens de cor do desenho saíram junto. Sobra `--leitura`, que não era do
    SVG: é o verde do "Você sabia?" e do traço que corre sob o passo ativo."""
    assert ".cena__" not in _TELAS_CSS, "sobrou regra do SVG antigo"
    assert ".cena {" not in _TELAS_CSS

    for token in ("--solo-a", "--solo-grao", "--calcario", "--broto", "--semente", "--vitrine"):
        assert token not in _TELAS_CSS, f"{token} ficou órfão no CSS"

    assert "--leitura: var(--v-400)" in _TELAS_CSS


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
