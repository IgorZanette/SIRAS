"""
A formulação do adubo, do motor até a tela (ADR 0009).

Quatro garantias que a banca vai cobrar, e que são o motivo deste arquivo existir:

1. o **método** é do Manual (§8.3, p. 311) e o **catálogo** não é — e o laudo diz as duas
   coisas onde a pessoa lê, não em nota de rodapé;
2. catálogo vazio não quebra nada: a fórmula ideal e a mistura de simples seguem, porque
   nenhuma das duas depende de lista de mercado;
3. o que o usuário informa — N de semeadura e fórmula disponível — atravessa o formulário
   inteiro até o laudo;
4. os arquivos reais carregam, e as invariantes pegam erro de transcrição.

As fórmulas dos testes de comportamento são fictícias, injetadas pelo teste. O arquivo
real é dado do autor, e amarrar o teste ao conteúdo dele faria a suíte quebrar no dia em
que ele acrescentasse uma fórmula.
"""

from types import SimpleNamespace

import pytest

from siras.conhecimento.carregador import Carregador, ErroCarregamento, carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.laudo import gerar_laudo
from siras.relatorio.apresentacao import apresentar_laudo, insumos_para_custo
from siras.web import criar_app

_DADOS_DO_TALHAO = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100", "expectativa_rendimento": "3",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}

_SIMPLES = [
    {"id": "ureia", "n": 45, "p2o5": 0, "k2o": 0, "uso": ["cobertura_n"]},
    {"id": "superfosfato_triplo", "n": 0, "p2o5": 41, "k2o": 0, "uso": ["complemento_p"]},
    {"id": "cloreto_de_potassio", "n": 0, "p2o5": 0, "k2o": 58, "uso": ["complemento_k"]},
]


def _f(id_, n, p, k, evidencia="nenhuma"):
    return {"id": id_, "n": n, "p2o5": p, "k2o": k, "uso": ["plantio"],
            "fontes": ["teste"], "evidencia_comercial": evidencia}


_EVIDENCIA = {
    "forte": "fabricante identificado ou compra pública",
    "media": "citada por fonte técnica",
    "fraca": "só anúncio de revenda",
    "nenhuma": "exemplo de cálculo, sem prova de venda",
    "regra": "o nível é o mais alto entre as fontes da fórmula",
}


def _catalogo(*formulas):
    return {
        "schema": "formulas_npk_v1",
        "fontes": {"teste": "fórmula fictícia de teste"},
        "fertilizantes_simples": {"_fonte": "teste", "itens": _SIMPLES},
        "formulas": {"_evidencia": _EVIDENCIA, "itens": list(formulas)},
    }


@pytest.fixture
def com_catalogo(monkeypatch):
    def instalar(*formulas):
        catalogo = _catalogo(*formulas)
        monkeypatch.setattr("siras.motor.laudo.carregar_formulas_npk", lambda: catalogo)
        return catalogo
    return instalar


def _laudo(n_plantio=None, formulas_usuario=()):
    analise = AnaliseSolo(
        ph_agua=5.1, indice_smp=5.4, argila=38.0, mo=2.8,
        p=11.0, k=96.0, ctc_ph7=9.4, al=1.2, ca=2.4, mg=1.1, v_percent=42.0,
    )
    contexto = Contexto(
        cultura_id="soja", sistema_manejo="convencional", condicao_area="todos os casos",
        prnt=100.0, profundidade_incorporacao_cm=20.0, cultivo=1,
        expectativa_rendimento=3.0, n_plantio=n_plantio,
        formulas_usuario=tuple(formulas_usuario),
    )
    return gerar_laudo(analise, "soja", contexto, carregar_dados_comum())


# --- o motor -----------------------------------------------------------------------

def test_o_laudo_traz_os_tres_caminhos(com_catalogo):
    com_catalogo(_f("00-20-20", 0, 20, 20), _f("00-20-05", 0, 20, 5))

    f = _laudo().formulacao

    assert len(f.ideais) == 3, "fórmula ideal em três concentrações"
    assert f.catalogo, "as melhores do catálogo"
    assert f.mistura is not None, "mistura de simples"
    assert f.catalogo[0].formula_id == "00-20-20"


def test_catalogo_vazio_deixa_os_outros_dois_caminhos(com_catalogo):
    com_catalogo()

    f = _laudo().formulacao

    assert f.catalogo == []
    # A razão de existirem três caminhos: sem lista de mercado, dois ainda respondem.
    assert len(f.ideais) == 3
    assert f.mistura is not None


def test_a_soja_penaliza_a_formula_rica_em_n(com_catalogo):
    # Leguminosa: n = 0 por fixação biológica, e todo N da fórmula é adubo sem função.
    com_catalogo(_f("20-20-20", 20, 20, 20), _f("00-20-20", 0, 20, 20))

    f = _laudo().formulacao

    assert f.catalogo[0].formula_id == "00-20-20"
    assert f.catalogo[-1].excesso["n"] > 0


def test_o_n_de_semeadura_do_usuario_chega_a_formula_ideal(com_catalogo):
    com_catalogo()

    sem = _laudo().formulacao
    com = _laudo(n_plantio=12).formulacao

    assert sem.sem_n_de_plantio is True
    assert all(o.teores["n"] == 0 for o in sem.ideais)
    assert com.sem_n_de_plantio is False
    # Soja não recebe N, então mesmo informado o plantio a ideal fica sem nitrogênio:
    # o que muda é a declaração, não o número. Este caso guarda isso.
    assert com.ideais


def test_a_formula_do_usuario_entra_no_ranking(com_catalogo):
    com_catalogo(_f("05-20-05", 5, 20, 5))

    f = _laudo(formulas_usuario=("00-20-20",)).formulacao

    assert any(o.tipo == "usuario" for o in f.catalogo)


def test_a_trilha_registra_a_escolha_e_os_pontos_de_quebra(com_catalogo):
    com_catalogo(_f("00-20-20", 0, 20, 20))

    laudo = _laudo()

    escolha = next(p for p in laudo.trace if p.regra.startswith("R-FOR-01"))
    assert "p. 311" in escolha.fonte
    assert any(p.regra.startswith("R-FOR-02") for p in laudo.trace)


def test_o_laudo_real_usa_o_catalogo_de_verdade():
    f = _laudo().formulacao

    assert f.catalogo and f.ideais and f.mistura is not None


# --- a apresentação ----------------------------------------------------------------

def test_o_cartao_traz_os_tres_caminhos_e_os_avisos(com_catalogo):
    com_catalogo(_f("00-20-05", 0, 20, 5))

    cartao = apresentar_laudo(_laudo(), carregar_dados_comum())["formulacao"]

    assert cartao["tem"] is True
    assert cartao["ideais"] and cartao["catalogo"] and cartao["mistura"]
    assert len(cartao["avisos"]) >= 3
    # Fórmula pobre em K: precisa sair complemento de cloreto de potássio.
    produtos = [c["produto"] for c in cartao["catalogo"][0]["complementos"]]
    assert "cloreto de potássio" in produtos


def test_sem_catalogo_o_cartao_continua_aparecendo(com_catalogo):
    com_catalogo()

    cartao = apresentar_laudo(_laudo(), carregar_dados_comum())["formulacao"]

    assert cartao["tem"] is True
    assert cartao["catalogo"] == []
    assert cartao["mistura"] is not None


def test_a_calculadora_abre_com_as_do_catalogo(com_catalogo):
    com_catalogo(_f("00-20-20", 0, 20, 20), _f("00-20-05", 0, 20, 5))

    custo = insumos_para_custo([
        SimpleNamespace(rotulo="A1", area_ha=10.0, laudo=_laudo())
    ])

    assert custo["sugeridas"][0]["formula"] == "0-20-20"


def test_sem_catalogo_a_calculadora_abre_em_branco(com_catalogo):
    com_catalogo()

    custo = insumos_para_custo([
        SimpleNamespace(rotulo="", area_ha=None, laudo=_laudo())
    ])

    # A fórmula ideal NÃO entra na calculadora de preço: ela é referência para encomenda,
    # e cotar um produto que não está na prateleira seria convite a erro.
    assert custo["sugeridas"] == []


# --- a tela ------------------------------------------------------------------------

def test_a_tela_mostra_os_tres_caminhos_e_separa_metodo_de_catalogo(com_catalogo):
    com_catalogo(_f("00-20-20", 0, 20, 20))
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.post("/analise/laudo", data=_DADOS_DO_TALHAO).get_data(as_text=True)

    assert "Qual adubo comprar" in html
    assert "Fórmula ideal para esta recomendação" in html
    assert "Melhores opções prontas" in html
    assert "Mistura de adubos simples" in html
    # As duas procedências, cada uma dita por inteiro.
    assert "§8.3, p. 311" in html
    assert "não publica lista de adubos comerciais" in html
    # E a limitação que o Manual impõe e o SIRAS não cumpre.
    assert "não tem preços" in html


def test_sem_catalogo_a_tela_ainda_traz_a_secao(com_catalogo):
    com_catalogo()
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.post("/analise/laudo", data=_DADOS_DO_TALHAO).get_data(as_text=True)

    assert "Qual adubo comprar" in html
    assert "Mistura de adubos simples" in html
    assert "Melhores opções prontas" not in html


def test_o_formulario_oferece_os_campos_do_adubo():
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.get("/analise/dados?cultura_id=milho").get_data(as_text=True)

    assert 'name="n_plantio"' in html
    assert html.count('name="formula_usuario"') == 3


def test_leguminosa_nao_pergunta_quanto_de_n_vai_na_semeadura():
    """Soja não recebe adubação nitrogenada — fixação biológica. Perguntar quanto do N
    vai no plantio a quem não aplica N nenhum é pergunta sem resposta possível."""
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.get("/analise/dados?cultura_id=soja").get_data(as_text=True)

    assert 'name="n_plantio"' not in html
    # As fórmulas continuam: a soja compra adubo formulado como qualquer outra.
    assert html.count('name="formula_usuario"') == 3


def test_formula_do_usuario_invalida_e_recusada_com_explicacao():
    cliente = criar_app({"TESTING": True}).test_client()
    dados = dict(_DADOS_DO_TALHAO, formula_usuario="abacaxi")

    html = cliente.post("/analise/laudo", data=dados).get_data(as_text=True)

    assert "Fórmula disponível" in html
    assert "05-20-20" in html, "a mensagem precisa mostrar o formato esperado"


def test_n_de_semeadura_do_formulario_chega_ao_laudo():
    cliente = criar_app({"TESTING": True}).test_client()
    dados = dict(_DADOS_DO_TALHAO, n_plantio="15")

    html = cliente.post("/analise/laudo", data=dados).get_data(as_text=True)

    # Informado, o laudo deixa de exibir a ressalva de que a ideal saiu sem nitrogênio.
    assert "Saíram sem nitrogênio" not in html


# --- os arquivos reais -------------------------------------------------------------

def test_o_catalogo_de_formulas_carrega_e_tem_as_tres_fontes_de_complemento():
    catalogo = Carregador().carregar_formulas_npk()
    ids = {s["id"] for s in catalogo["fertilizantes_simples"]["itens"]}

    assert {"superfosfato_triplo", "cloreto_de_potassio", "ureia"} <= ids
    assert catalogo["formulas"]["itens"], "catálogo semente não pode estar vazio"


def test_toda_formula_diz_quao_forte_e_a_prova_de_que_e_vendida():
    """O campo que responde "de onde saiu este catálogo?" com critério, não com lista.

    Os quatro níveis estão descritos no próprio arquivo, no bloco `_evidencia`, e o
    carregador recusa nível que não esteja lá.
    """
    catalogo = Carregador().carregar_formulas_npk()
    descritos = set(catalogo["formulas"]["_evidencia"]) - {"regra"}

    assert descritos == {"forte", "media", "fraca", "nenhuma"}
    for f in catalogo["formulas"]["itens"]:
        assert f["evidencia_comercial"] in descritos, f["id"]


def test_o_catalogo_mantem_cobertura_de_mercado():
    """O piso existe para que uma edição futura não derrube a cobertura sem perceber.

    Fórmulas de nível `nenhuma` — exemplos de cálculo do Manual e composições
    ilustrativas do IAC — ficam no arquivo porque o método precisa delas, mas NÃO
    contam: o que sustenta o argumento é a prova de que o produto é vendido.
    """
    itens = Carregador().carregar_formulas_npk()["formulas"]["itens"]
    com_prova = [f for f in itens if f["evidencia_comercial"] != "nenhuma"]

    assert len(com_prova) >= Carregador.MINIMO_COM_EVIDENCIA_COMERCIAL
    # E o argumento mais forte não depende dos anúncios de revenda: mesmo descartando
    # os de evidência fraca, resta a maior parte do catálogo.
    robustas = [f for f in com_prova if f["evidencia_comercial"] in ("forte", "media")]
    assert len(robustas) >= 35


def test_nivel_de_evidencia_fora_do_bloco_descrito_e_recusado():
    orfa = _f("05-20-20", 5, 20, 20)
    orfa["evidencia_comercial"] = "altissima"
    with pytest.raises(ErroCarregamento, match="não está descrita"):
        Carregador().validar_formulas_npk(_catalogo(orfa))


def test_o_catalogo_tem_formula_com_evidencia_no_rio_grande_do_sul():
    """O trabalho é para o RS, e a pergunta "isso se compra aqui?" é legítima.

    Não se exige um número: exige-se que exista evidência regional, para que a seção de
    limitações possa dizer quanta, em vez de silenciar sobre o assunto.
    """
    catalogo = Carregador().carregar_formulas_npk()
    do_rs = [
        f for f in catalogo["formulas"]["itens"]
        if "RS" in (f.get("regiao") or "") and f["evidencia_comercial"] != "nenhuma"
    ]

    assert do_rs, "nenhuma fórmula com evidência de ser comercializada no RS"


def test_id_da_formula_tem_de_bater_com_as_garantias():
    with pytest.raises(ErroCarregamento, match="as garantias dizem"):
        Carregador().validar_formulas_npk(_catalogo(_f("05-20-20", 5, 20, 25)))


def test_formula_que_cita_fonte_inexistente_e_recusada():
    orfa = _f("05-20-20", 5, 20, 20)
    orfa["fontes"] = ["fonte_que_nao_existe"]
    with pytest.raises(ErroCarregamento, match="sem procedência rastreável"):
        Carregador().validar_formulas_npk(_catalogo(orfa))


def test_catalogo_sem_fonte_de_complemento_e_recusado():
    catalogo = _catalogo(_f("05-20-20", 5, 20, 20))
    catalogo["fertilizantes_simples"]["itens"] = [_SIMPLES[0]]  # só ureia
    with pytest.raises(ErroCarregamento, match="superfosfato_triplo"):
        Carregador().validar_formulas_npk(catalogo)


def test_corretivos_carrega_e_declara_o_status_de_cada_bloco():
    corretivos = Carregador().carregar_corretivos()

    # O que torna este arquivo defensável é não misturar origens. As faixas comerciais
    # NÃO são lei vigente, e o arquivo precisa continuar dizendo isso.
    assert corretivos["legislacao_vigente"]["_status"].startswith("lei_vigente")
    assert corretivos["faixas_prnt_comerciais"]["_status"] == "convencao_comercial_historica"
    assert corretivos["classificacao_mgo"]["_status"] == (
        "convencao_tecnica_sem_base_legal_vigente"
    )
    assert corretivos["orientacoes_manual_rs_sc"]["_status"] == "manual_rs_sc"


def test_prnt_acima_do_pn_e_recusado_quando_nao_declarado():
    corretivos = Carregador().carregar_corretivos()
    produto = dict(corretivos["produtos_referencia_mercado"]["produtos"][0])
    produto["pn"], produto["prnt"] = 80.0, 90.0
    produto.pop("inconsistencias", None)
    corretivos["produtos_referencia_mercado"]["produtos"] = [produto]

    with pytest.raises(ErroCarregamento, match="impossível"):
        Carregador().validar_corretivos(corretivos)


def test_pn_acima_de_cem_nao_e_erro():
    # 1% de MgO neutraliza como 2,481% de CaCO3, contra 1,783% do CaO: o Mg é mais leve.
    # Um dolomito puro passa de 100% de PN por estequiometria, não por erro.
    corretivos = Carregador().carregar_corretivos()
    itapeva = next(
        p for p in corretivos["produtos_referencia_mercado"]["produtos"]
        if p["id"] == "itau_itapeva"
    )

    assert itapeva["pn"] > 100
    assert itapeva["cao"] * 1.783 + itapeva["mgo"] * 2.481 == pytest.approx(itapeva["pn"], abs=5)


def test_faixas_de_prnt_sao_contiguas():
    corretivos = Carregador().carregar_corretivos()
    faixas = corretivos["faixas_prnt_comerciais"]["faixas"]

    for anterior, seguinte in zip(faixas, faixas[1:]):
        inicio = seguinte.get("prnt_min_inclusivo", seguinte.get("prnt_min_exclusivo"))
        assert inicio == anterior["prnt_max_inclusivo"]
