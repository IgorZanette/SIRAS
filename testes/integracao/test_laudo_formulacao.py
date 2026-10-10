"""
A indicação do adubo formulado, do motor até a tela.

Três garantias que a banca vai cobrar, e que são o motivo deste arquivo existir:

1. o **método** é do Manual (§8.3, p. 311) e o **catálogo** não é — e o laudo diz as duas
   coisas onde a pessoa lê, não em nota de rodapé;
2. catálogo vazio não quebra nada: o cartão some e o laudo segue completo;
3. o arquivo real carrega, e as invariantes de física pegam erro de transcrição.

As fórmulas dos testes de comportamento são fictícias, injetadas pelo teste. O arquivo
real (dados/mercado/formulas_npk.json) é dado do autor, e amarrar o teste ao conteúdo
dele faria a suíte quebrar no dia em que ele acrescentasse uma fórmula.
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


def _f(id_, n, p, k):
    return {"id": id_, "n": n, "p2o5": p, "k2o": k, "uso": ["plantio"],
            "fontes": ["teste"], "origem": "composicao_ilustrativa"}


def _catalogo(*formulas):
    return {
        "schema": "formulas_npk_v1",
        "fontes": {"teste": "fórmula fictícia de teste"},
        "fertilizantes_simples": {"_fonte": "teste", "itens": _SIMPLES},
        "formulas": {"itens": list(formulas)},
    }


@pytest.fixture
def com_catalogo(monkeypatch):
    """Injeta um catálogo fictício no lugar do arquivo real."""
    def instalar(*formulas):
        catalogo = _catalogo(*formulas)
        monkeypatch.setattr("siras.motor.laudo.carregar_formulas_npk", lambda: catalogo)
        return catalogo
    return instalar


def _laudo():
    analise = AnaliseSolo(
        ph_agua=5.1, indice_smp=5.4, argila=38.0, mo=2.8,
        p=11.0, k=96.0, ctc_ph7=9.4, al=1.2, ca=2.4, mg=1.1, v_percent=42.0,
    )
    contexto = Contexto(
        cultura_id="soja", sistema_manejo="convencional", condicao_area="todos os casos",
        prnt=100.0, profundidade_incorporacao_cm=20.0, cultivo=1,
        expectativa_rendimento=3.0,
    )
    return gerar_laudo(analise, "soja", contexto, carregar_dados_comum())


# --- o motor -----------------------------------------------------------------------

def test_o_laudo_indica_a_formula_de_menor_desvio(com_catalogo):
    com_catalogo(_f("00-20-20", 0, 20, 20), _f("00-20-05", 0, 20, 5))

    laudo = _laudo()

    assert laudo.formulacao.indicada.id == "00-20-20"
    assert laudo.formulacao.indicada.dose_kg_ha > 0
    # A âncora precisa ser um dos dois, e precisa ter saído da classe de teor.
    assert laudo.formulacao.indicada.ancora in ("p2o5", "k2o")
    assert laudo.formulacao.indicada.ancora_por_fallback is False


def test_a_soja_penaliza_a_formula_rica_em_n(com_catalogo):
    # Leguminosa: n = 0 por fixação biológica, e todo N da fórmula é adubo sem função.
    com_catalogo(_f("20-20-20", 20, 20, 20), _f("02-20-20", 2, 20, 20))

    laudo = _laudo()

    assert laudo.formulacao.indicada.id == "02-20-20"
    assert laudo.formulacao.ranking[-1].excesso_n > 0


def test_catalogo_vazio_deixa_o_laudo_completo(com_catalogo):
    com_catalogo()

    laudo = _laudo()

    assert laudo.formulacao.indicada is None
    assert "vazio" in laudo.formulacao.motivo_sem_indicacao
    assert laudo.calagem is not None
    assert laudo.aptidao_atual is not None and laudo.aptidao_potencial is not None


def test_a_trilha_registra_a_escolha(com_catalogo):
    com_catalogo(_f("00-20-20", 0, 20, 20))

    laudo = _laudo()

    passo = next(p for p in laudo.trace if p.regra.startswith("R-FOR-01"))
    assert passo.entradas["ancora"] in ("p2o5", "k2o")
    assert "p. 311" in passo.fonte


def test_o_laudo_real_usa_o_catalogo_de_verdade():
    # Sem monkeypatch: o arquivo do autor precisa produzir indicação num caso comum.
    laudo = _laudo()

    assert laudo.formulacao.indicada is not None
    assert laudo.formulacao.indicada.dose_kg_ha > 0


# --- a apresentação ----------------------------------------------------------------

def test_o_cartao_traz_dose_entrega_e_complementos(com_catalogo):
    com_catalogo(_f("00-20-05", 0, 20, 5))

    modelo = apresentar_laudo(_laudo(), carregar_dados_comum())
    cartao = modelo["formulacao"]

    assert cartao["tem"] is True
    assert cartao["indicada"]["dose"] != "—"
    # Fórmula pobre em K: precisa sair complemento de cloreto de potássio.
    produtos = [c["produto"] for c in cartao["indicada"]["complementos"]]
    assert "cloreto de potássio" in produtos


def test_sem_catalogo_o_cartao_nao_aparece(com_catalogo):
    com_catalogo()

    modelo = apresentar_laudo(_laudo(), carregar_dados_comum())

    assert modelo["formulacao"]["tem"] is False
    assert modelo["formulacao"]["indicada"] is None


def test_a_calculadora_abre_com_as_indicadas(com_catalogo):
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

    assert custo["sugeridas"] == []


# --- a tela ------------------------------------------------------------------------

def test_a_tela_mostra_a_indicacao_e_separa_metodo_de_catalogo(com_catalogo):
    com_catalogo(_f("00-20-20", 0, 20, 20))
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.post("/analise/laudo", data=_DADOS_DO_TALHAO).get_data(as_text=True)

    assert "Qual adubo comprar" in html
    assert "00-20-20" in html
    # As duas procedências, cada uma dita por inteiro: é o que separa norma de mercado.
    assert "§8.3, p. 311" in html
    assert "não publica lista de adubos comerciais" in html
    # E a limitação que o Manual impõe e o SIRAS não cumpre.
    assert "não tem preços" in html


def test_sem_catalogo_a_tela_nao_traz_a_secao(com_catalogo):
    com_catalogo()
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.post("/analise/laudo", data=_DADOS_DO_TALHAO).get_data(as_text=True)

    assert "Qual adubo comprar" not in html
    assert "Interpretação dos atributos" in html


# --- os arquivos reais -------------------------------------------------------------

def test_o_catalogo_de_formulas_carrega_e_tem_as_tres_fontes_de_complemento():
    catalogo = Carregador().carregar_formulas_npk()
    ids = {s["id"] for s in catalogo["fertilizantes_simples"]["itens"]}

    assert {"superfosfato_triplo", "cloreto_de_potassio", "ureia"} <= ids
    assert catalogo["formulas"]["itens"], "catálogo semente não pode estar vazio"


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
