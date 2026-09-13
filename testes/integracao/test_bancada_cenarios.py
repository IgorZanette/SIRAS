"""
Bancada ampla: as 61 culturas do escopo, dez cenários cada, pelo caminho real da aplicação.

O QUE ESTA BANCADA VERIFICA — e o que ela deliberadamente NÃO verifica.

Ela verifica que toda cultura, sob dez condições de solo diferentes e percorrendo os
estados que ela própria declara, produz um laudo COMPLETO e bem formado: as quatro doses,
as duas aptidões, a trilha de rastreabilidade, e nenhum vocabulário de máquina vazando
para o documento.

Ela NÃO verifica se as doses estão certas. O valor de referência de cada recomendação é
calculado à mão pelo autor a partir do Manual e vive em `testes/casos/` — é lá que a
correção agronômica é validada, e nenhum número esperado é escrito aqui. Afirmar aqui qual
dose é a certa seria fabricar o gabarito.

A distinção importa na defesa: esta bancada responde "o sistema atende toda cultura do
escopo sem quebrar?"; os casos de referência respondem "ele acerta?".

OS VALORES DE ENTRADA são perfis de solo, e não dados do Manual: cumprem o papel do laudo
de laboratório, e por isso podem ser escritos aqui. Cobrem faixas deliberadamente
distintas — ácido e corrigido, argiloso e arenoso, pobre e fértil, CTC baixa e alta, poder
tampão normal e baixo — para que nenhuma cultura passe por acaso, por todos os cenários
caírem na mesma classe de interpretação.

OS ESTADOS DA CULTURA vêm da própria tela, e giram com o cenário: fase do pomar, momento
da aplicação, sistema de manejo, cultivo, antecedente. É o que exercita a erva-mate em
todas as fases e programas que ela declara.

O QUE A BANCADA ENCONTROU, e que está corrigido:

- o laudo imprimia "Dose definida pela faixa de matéria orgânica da amostra (None)" para
  toda cultura que não dosa N por faixa de MO — afirmando um critério que não foi usado, e
  com um None dentro de um documento assinado;
- escolher "Manutenção" numa macieira derrubava a aplicação com HTTP 500 e rastro de
  pilha: o motor levanta NotImplementedError nas fases que o Manual indexa por análise
  foliar, e a rota não tratava isso;
- a tela oferecia a fase "Crescimento" ao mirtileiro e ao morangueiro, que declaram na
  base crescimento e manutenção unificados — uma opção que o motor recusava sempre.
"""

import re

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.escopo import TOTAL_DE_CULTURAS_NO_ESCOPO, no_escopo_de_recomendacao
from siras.web import criar_app

#: Bancada ampla: roda antes de entregar, e não a cada alteração. Concentra a maior
#: parte do tempo da suíte e repete em volume o que os testes por grupo cobrem por
#: amostra — ver conftest.py na raiz. Para rodá-la: python -m pytest --completa
pytestmark = pytest.mark.lenta

_DADOS = carregar_dados_comum()
_CULTURAS = sorted(
    cultura for cultura in _DADOS["mapa_culturas"]["culturas"]
    if no_escopo_de_recomendacao(cultura)
)

#: Dez perfis de solo. São ENTRADAS de teste — o que viria de um laudo de laboratório — e
#: não valores transcritos do Manual.
#:
#: O índice SMP fica dentro da faixa da Tabela 5.2 (4,4 a 7,1) em todos: fora dela o
#: sistema recusa por validação, e recusar não é o que esta bancada mede. O perfil
#: 'tampao_baixo' passa de 6,3 de propósito, que é onde a calagem troca a tabela pelas
#: equações polinomiais.
_PERFIS = (
    ("acido_argiloso_pobre", {
        "ph_agua": "4.6", "indice_smp": "4.8", "argila": "62", "mo": "2.1",
        "p": "2.4", "k": "38", "ctc_ph7": "11.8",
        "al": "3.4", "ca": "1.2", "mg": "0.6", "v_percent": "21",
    }),
    ("acido_medio", {
        "ph_agua": "5.0", "indice_smp": "5.3", "argila": "38", "mo": "2.8",
        "p": "6.5", "k": "62", "ctc_ph7": "9.4",
        "al": "1.6", "ca": "2.2", "mg": "0.9", "v_percent": "38",
    }),
    ("corrigido_fertil", {
        "ph_agua": "6.3", "indice_smp": "6.2", "argila": "44", "mo": "3.6",
        "p": "28.0", "k": "210", "ctc_ph7": "14.2",
        "al": "0.0", "ca": "7.4", "mg": "2.8", "v_percent": "78",
    }),
    ("arenoso_pobre", {
        "ph_agua": "4.9", "indice_smp": "5.6", "argila": "12", "mo": "1.1",
        "p": "4.0", "k": "28", "ctc_ph7": "4.2",
        "al": "1.1", "ca": "0.9", "mg": "0.4", "v_percent": "29",
    }),
    ("arenoso_corrigido", {
        "ph_agua": "6.0", "indice_smp": "6.1", "argila": "16", "mo": "1.6",
        "p": "22.0", "k": "120", "ctc_ph7": "5.1",
        "al": "0.0", "ca": "3.1", "mg": "1.2", "v_percent": "68",
    }),
    ("argila_alta_rico", {
        "ph_agua": "5.8", "indice_smp": "5.9", "argila": "72", "mo": "4.2",
        "p": "42.0", "k": "260", "ctc_ph7": "16.5",
        "al": "0.2", "ca": "6.8", "mg": "2.4", "v_percent": "62",
    }),
    ("ctc_baixa", {
        "ph_agua": "5.2", "indice_smp": "5.8", "argila": "22", "mo": "1.4",
        "p": "9.0", "k": "45", "ctc_ph7": "3.8",
        "al": "0.7", "ca": "1.4", "mg": "0.5", "v_percent": "44",
    }),
    ("mo_alta", {
        "ph_agua": "5.4", "indice_smp": "5.5", "argila": "48", "mo": "5.8",
        "p": "14.0", "k": "95", "ctc_ph7": "12.6",
        "al": "0.9", "ca": "3.6", "mg": "1.5", "v_percent": "48",
    }),
    ("tampao_baixo", {
        "ph_agua": "5.6", "indice_smp": "6.5", "argila": "18", "mo": "1.9",
        "p": "11.0", "k": "70", "ctc_ph7": "4.6",
        "al": "0.4", "ca": "2.0", "mg": "0.8", "v_percent": "55",
    }),
    ("limiar_de_calagem", {
        "ph_agua": "5.5", "indice_smp": "5.7", "argila": "34", "mo": "3.0",
        "p": "12.0", "k": "80", "ctc_ph7": "8.8",
        "al": "0.5", "ca": "3.0", "mg": "1.1", "v_percent": "52",
    }),
)

#: A camada de 10-20 cm acompanha cada perfil, um degrau mais pobre e mais ácida. Vai
#: preenchida em todos porque um dos sistemas de manejo decide por ela (Tab. 5.3, notas
#: 6-7): sem esses valores, esse critério não poderia ser exercitado.
_SUBSUPERFICIE = {
    "sub_ph_agua": "4.8", "sub_indice_smp": "5.1", "sub_v_percent": "34",
    "sub_al": "1.8", "sub_ca": "1.6", "sub_mg": "0.7", "sub_k": "48",
}

#: LIMITES DECLARADOS: estados que a tela oferece e que o SIRAS não recomenda, por decisão
#: registrada — o Manual indexa essas fases pela análise foliar, sem publicar a
#: correspondência com a análise de solo, e o motor se recusa a converter.
#:
#: A lista é explícita de propósito. Aceitar "qualquer recusa que se diga declarada"
#: deixaria uma regressão nova passar disfarçada de limite conhecido; assim, um estado que
#: PARE de funcionar aparece como falha.
_LIMITES_DECLARADOS = {
    ("ameixeira", "fase", "manutencao"),
    ("macieira", "fase", "manutencao"),
    ("maracujazeiro", "fase", "manutencao"),
    ("pessegueiro_nectarineira", "fase", "manutencao"),
    ("videira", "fase", "crescimento"),
}

#: RECUSAS POR CAMPO DEPENDENTE: a fase escolhida exige um dado que só ela exige — o ano
#: após o plantio, a produtividade estimada, o manejo do galho grosso. São recusas
#: CORRETAS, com mensagem que nomeia o campo que falta; entram aqui para que a bancada
#: exija justamente isso: recusa explicada, e nunca queda nem silêncio.
_EXIGEM_CAMPO_DEPENDENTE = {
    ("abacateiro", "fase", "crescimento"), ("abacateiro", "fase", "manutencao"),
    ("ameixeira", "fase", "crescimento"),
    ("bananeira", "fase", "manutencao"),
    ("caquizeiro", "fase", "crescimento"), ("caquizeiro", "fase", "manutencao"),
    ("citros", "fase", "crescimento"), ("citros", "fase", "manutencao"),
    ("erva-mate", "programa", "recuperacao"), ("erva-mate", "fase", "producao"),
    ("figueira", "fase", "crescimento"), ("figueira", "fase", "manutencao"),
    ("macieira", "fase", "crescimento"),
    ("oliveira", "fase", "crescimento"), ("oliveira", "fase", "manutencao"),
    ("pereira", "fase", "crescimento"), ("pereira", "fase", "manutencao"),
    ("pessegueiro_nectarineira", "fase", "crescimento"),
    ("quivizeiro", "fase", "crescimento"), ("quivizeiro", "fase", "manutencao"),
}

_RECUSAS_CONHECIDAS = _LIMITES_DECLARADOS | _EXIGEM_CAMPO_DEPENDENTE

_CASOS = [(cultura, nome) for cultura in _CULTURAS for nome, _ in _PERFIS]
_NOMES_DOS_PERFIS = [nome for nome, _ in _PERFIS]


@pytest.fixture(scope="module")
def cliente():
    return criar_app({"TESTING": True}).test_client()


@pytest.fixture(scope="module")
def telas():
    """A tela de cada cultura, lida uma vez só: são 61 renderizações, e refazê-las a cada
    um dos 610 casos dominaria o tempo da bancada sem acrescentar cobertura."""
    return {}


def _tela(cliente, telas, cultura):
    if cultura not in telas:
        resposta = cliente.get(f"/analise/dados?cultura_id={cultura}&exemplo=1")
        assert resposta.status_code == 200, f"{cultura}: a tela não abriu"
        telas[cultura] = resposta.get_data(as_text=True)
    return telas[cultura]


def _campos_da_tela(html: str) -> dict:
    """O que o navegador enviaria: valor de cada input e opção marcada de cada select."""
    campos = dict(re.findall(r'<input[^>]*id="(\w+)"[^>]*value="([^"]*)"', html))
    for nome, corpo in re.findall(r'<select[^>]*id="(\w+)"[^>]*>(.*?)</select>', html, re.S):
        escolhida = (
            re.search(r'<option value="([^"]*)" selected', corpo)
            or re.search(r'<option value="([^"]*)"', corpo)
        )
        if escolhida:
            campos[nome] = escolhida.group(1)
    return campos


def _opcoes_da_tela(html: str) -> dict:
    """Todas as opções que cada seletor oferece — é daqui que saem os estados da cultura.

    A opção vazia fica de fora: ela significa "não se aplica", e percorrê-la junto das
    demais produziria combinação que a própria tela não propõe — escolher a fase de
    plantio e deixar o momento em branco, por exemplo. O erro seria do teste."""
    opcoes = {}
    for nome, corpo in re.findall(r'<select[^>]*id="(\w+)"[^>]*>(.*?)</select>', html, re.S):
        valores = [v for v in re.findall(r'<option value="([^"]*)"', corpo) if v != ""]
        if valores:
            opcoes[nome] = valores
    return opcoes


def _montar(html: str, cultura: str, indice: int) -> dict:
    """Um cenário: o perfil de solo de índice `indice` mais um estado da cultura.

    Os estados giram com o índice, então dez cenários percorrem as fases, os momentos e os
    sistemas de manejo que aquela cultura declara. Os estados de recusa conhecida ficam de
    fora daqui — eles têm teste próprio, que cobra a recusa explicada."""
    campos = _campos_da_tela(html)
    campos["cultura_id"] = cultura

    for seletor, valores in _opcoes_da_tela(html).items():
        disponiveis = [
            valor for valor in valores
            if (cultura, seletor, valor) not in _RECUSAS_CONHECIDAS
        ]
        if disponiveis:
            campos[seletor] = disponiveis[indice % len(disponiveis)]

    campos.update(_PERFIS[indice][1])
    campos.update(_SUBSUPERFICIE)
    # A saturação por alumínio fica em branco de propósito: assim o cenário também
    # exercita a derivação a partir de Al, Ca, Mg e K (docs/decisoes/0002, D4).
    campos["saturacao_al"] = ""
    return campos


def _motivo(resposta) -> str:
    texto = re.sub(r"<[^>]+>", " ", resposta.get_data(as_text=True))
    achado = re.search(r"O laudo não foi gerado\s*(.{0,240})", texto)
    if not achado:
        return f"HTTP {resposta.status_code}"
    return re.sub(r"  +", " ", achado.group(1)).strip()


# --- o alcance da bancada -------------------------------------------------------

def test_a_bancada_cobre_o_escopo_inteiro():
    assert len(_CULTURAS) == TOTAL_DE_CULTURAS_NO_ESCOPO
    assert len(_PERFIS) == 10, "dez cenários por cultura"
    assert len(_CASOS) == TOTAL_DE_CULTURAS_NO_ESCOPO * 10


def test_os_perfis_sao_mesmo_diferentes_entre_si():
    """Dez cenários que caíssem todos na mesma classe de interpretação seriam um cenário
    repetido dez vezes — e uma cultura poderia passar por acaso."""
    for atributo in ("p", "k", "argila", "ctc_ph7", "ph_agua", "mo"):
        valores = {perfil[atributo] for _, perfil in _PERFIS}
        assert len(valores) >= 8, f"{atributo} quase não varia entre os perfis"


# --- o laudo de cada cultura em cada cenário ------------------------------------

@pytest.mark.parametrize("cultura, cenario", _CASOS)
def test_toda_cultura_gera_laudo_em_todo_cenario(cliente, telas, cultura, cenario):
    """O caminho inteiro, da tela ao documento, sob dez condições diferentes."""
    html = _tela(cliente, telas, cultura)
    indice = _NOMES_DOS_PERFIS.index(cenario)

    resposta = cliente.post("/analise/laudo", data=_montar(html, cultura, indice))

    assert resposta.status_code == 200, f"{cultura} / {cenario}: {_motivo(resposta)}"


@pytest.mark.parametrize("cultura, cenario", _CASOS)
def test_todo_laudo_sai_completo(cliente, telas, cultura, cenario):
    """Um laudo sem dose, sem aptidão ou sem trilha passaria no teste acima e mesmo assim
    estaria quebrado."""
    html = _tela(cliente, telas, cultura)
    indice = _NOMES_DOS_PERFIS.index(cenario)

    laudo = cliente.post(
        "/analise/laudo", data=_montar(html, cultura, indice)
    ).get_data(as_text=True)

    assert len(re.findall(r'class="dose[ "]', laudo)) == 4, (
        f"{cultura} / {cenario}: o veredito não tem as quatro saídas"
    )
    # O delimitador depois de "selo" é necessário: o selo ganha o modificador
    # --atencao quando a classe é "Apta com restrições", e a classe exata deixaria de
    # casar justamente nesses laudos.
    assert len(re.findall(r'class="aptidao__selo[ "]', laudo)) == 2, (
        f"{cultura} / {cenario}: falta um dos dois cenários de aptidão"
    )
    assert 'class="trilha__passo"' in laudo, f"{cultura} / {cenario}: laudo sem trilha"


@pytest.mark.parametrize("cultura, cenario", _CASOS)
def test_nenhum_vocabulario_de_maquina_chega_ao_documento(cliente, telas, cultura, cenario):
    """O laudo é assinado por um profissional e anexado a projeto de crédito rural. Um
    'None' ou um nome de exceção no meio de uma frase denunciam o programa vazando para o
    documento — e foi exatamente isso que esta bancada encontrou na observação da dose de
    nitrogênio das culturas que não dosam N por faixa de matéria orgânica."""
    html = _tela(cliente, telas, cultura)
    indice = _NOMES_DOS_PERFIS.index(cenario)

    laudo = cliente.post(
        "/analise/laudo", data=_montar(html, cultura, indice)
    ).get_data(as_text=True)
    corpo = laudo[laudo.index('<article class="doc">'):]
    # A trilha cita identificadores de propósito: é ela que permite conferir a regra
    # aplicada contra a base. O que não pode é vocabulário cru fora dela.
    fora_da_trilha = corpo[:corpo.index("De onde vem cada número")]
    texto = re.sub(r"<[^>]+>", " ", fora_da_trilha)

    for cru in ("(None)", "None.", "NotImplementedError", "ErroAdubacao", "Traceback"):
        assert cru not in texto, f"{cultura} / {cenario}: '{cru}' vazou para o documento"


@pytest.mark.parametrize("cultura, cenario", _CASOS)
def test_a_leitura_ao_vivo_responde_em_todo_cenario(cliente, telas, cultura, cenario):
    html = _tela(cliente, telas, cultura)
    indice = _NOMES_DOS_PERFIS.index(cenario)

    corpo = cliente.post("/api/interpretar", json=_montar(html, cultura, indice)).get_json()

    assert corpo["classes"]["p"], f"{cultura} / {cenario}: sem classe de fósforo"
    assert corpo["classes"]["k"], f"{cultura} / {cenario}: sem classe de potássio"


# --- todo estado que a tela oferece ---------------------------------------------

@pytest.mark.parametrize("cultura", _CULTURAS)
def test_todo_estado_oferecido_e_atendido_ou_recusado_com_explicacao(
    cliente, telas, cultura
):
    """Uma opção que a tela oferece e o programa não sabe tratar é o pior defeito possível
    de formulário. Aqui cada estado precisa cair num de dois destinos: laudo pronto, ou
    recusa que EXPLICA — nunca uma queda, nunca um erro de programa na tela.

    É o teste que exercita a erva-mate em todas as fases e programas que ela declara, e as
    frutíferas em todas as fases do pomar. Foi ele que achou o HTTP 500 da macieira."""
    html = _tela(cliente, telas, cultura)
    base = _montar(html, cultura, 1)

    for seletor, valores in _opcoes_da_tela(html).items():
        for valor in valores:
            campos = dict(base)
            campos[seletor] = valor
            resposta = cliente.post("/analise/laudo", data=campos)

            assert resposta.status_code in (200, 422), (
                f"{cultura}: {seletor}={valor} derrubou a aplicação "
                f"(HTTP {resposta.status_code})"
            )
            if resposta.status_code == 200:
                continue

            chave = (cultura, seletor, valor)
            assert chave in _RECUSAS_CONHECIDAS, (
                f"{cultura}: a tela oferece {seletor}={valor} e o motor recusou sem que "
                f"isso esteja no inventário de recusas — {_motivo(resposta)}"
            )
            assert _motivo(resposta), f"{cultura}: {seletor}={valor} recusado sem explicação"


@pytest.mark.parametrize("cultura, seletor, valor", sorted(_LIMITES_DECLARADOS))
def test_o_limite_declarado_e_apresentado_como_limite_e_nao_como_falha(
    cliente, telas, cultura, seletor, valor
):
    """'O sistema falhou' e 'o Manual não publica a correspondência que essa recomendação
    exigiria' são coisas diferentes, e a segunda é resposta legítima de um sistema
    especialista honesto. Antes desta bancada, era um HTTP 500 com rastro de pilha."""
    html = _tela(cliente, telas, cultura)
    campos = _montar(html, cultura, 1)
    campos[seletor] = valor

    resposta = cliente.post("/analise/laudo", data=campos)

    assert resposta.status_code == 422
    assert "fora do que o SIRAS recomenda" in _motivo(resposta)


@pytest.mark.parametrize("cultura, seletor, valor", sorted(_EXIGEM_CAMPO_DEPENDENTE))
def test_a_recusa_por_campo_dependente_nomeia_o_campo(
    cliente, telas, cultura, seletor, valor
):
    """A fase escolhida exige um dado que só ela exige. Recusar está certo; recusar sem
    dizer qual campo falta deixaria o usuário adivinhando entre vinte."""
    html = _tela(cliente, telas, cultura)
    campos = _montar(html, cultura, 1)
    campos[seletor] = valor

    motivo = _motivo(cliente.post("/analise/laudo", data=campos))

    assert any(
        campo in motivo
        for campo in ("ano", "produtividade_estimada", "manejo_galho_grosso",
                      "massa_verde_t_ha", "momento")
    ), f"{cultura}: recusa não nomeia o campo que falta — {motivo}"


def test_a_tela_nao_oferece_fase_que_a_base_declara_unificada(cliente, telas):
    """O mirtileiro e o morangueiro declaram na base crescimento e manutenção unificados.
    Oferecer 'Crescimento' era propor uma opção que o motor recusava sempre."""
    for cultura in ("mirtileiro", "morangueiro"):
        opcoes = _opcoes_da_tela(_tela(cliente, telas, cultura))
        assert "crescimento" not in opcoes.get("fase", []), (
            f"{cultura}: a tela ainda oferece uma fase que nunca produz laudo"
        )
