"""
A indicação do adubo formulado, do motor até a tela.

Duas garantias que a banca vai cobrar, e que são o motivo deste arquivo existir:

1. o catálogo de formulações **não é do Manual**, e o laudo diz isso onde a pessoa lê;
2. catálogo vazio não quebra nada — o cartão some e o laudo segue completo, porque o
   catálogo depende do autor e o sistema não pode ficar refém dele.

As formulações usadas aqui são fictícias, injetadas pelo teste. O arquivo real
(dados/mercado/formulacoes.json) é preenchido pelo autor, com a fonte de cada entrada.
"""

import pytest

from siras.conhecimento.carregador import Carregador, ErroCarregamento
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.laudo import gerar_laudo
from siras.relatorio.apresentacao import apresentar_laudo, insumos_para_custo
from siras.conhecimento.carregador import carregar_dados_comum
from siras.web import criar_app

_DADOS_DO_TALHAO = {
    "cultura_id": "soja", "criterio_id": "graos_convencional", "cultivo": "1",
    "profundidade_incorporacao_cm": "20", "prnt": "100", "expectativa_rendimento": "3",
    "ph_agua": "5.1", "indice_smp": "5.4", "argila": "38", "mo": "2.8",
    "p": "11", "k": "96", "ctc_ph7": "9.4",
    "al": "1.2", "ca": "2.4", "mg": "1.1", "v_percent": "42",
}


def _catalogo(*formulacoes):
    return {
        "descricao": "catálogo fictício de teste",
        "aviso": "não é transcrição do Manual",
        "formulacoes": list(formulacoes),
    }


def _f(id_, rotulo, n, p, k):
    return {"id": id_, "rotulo": rotulo, "n": n, "p2o5": p, "k2o": k,
            "_fonte": "fórmula fictícia de teste"}


@pytest.fixture
def com_catalogo(monkeypatch):
    """Injeta um catálogo fictício no lugar do arquivo real.

    O arquivo real nasce vazio e é do autor; amarrar o teste ao conteúdo dele faria a
    suíte quebrar no dia em que ele preenchesse o catálogo.
    """
    def instalar(*formulacoes):
        catalogo = _catalogo(*formulacoes)
        monkeypatch.setattr("siras.motor.laudo.carregar_formulacoes", lambda: catalogo)
        return catalogo
    return instalar


def _laudo(dados=None):
    analise = AnaliseSolo(
        ph_agua=5.1, indice_smp=5.4, argila=38.0, mo=2.8,
        p=11.0, k=96.0, ctc_ph7=9.4, al=1.2, ca=2.4, mg=1.1, v_percent=42.0,
    )
    contexto = Contexto(
        cultura_id="soja", sistema_manejo="convencional", condicao_area="todos os casos",
        prnt=100.0, profundidade_incorporacao_cm=20.0, cultivo=1,
        expectativa_rendimento=3.0,
    )
    return gerar_laudo(analise, "soja", contexto, dados or carregar_dados_comum())


# --- o motor -----------------------------------------------------------------------

def test_o_laudo_indica_a_formulacao_de_menor_sobra(com_catalogo):
    com_catalogo(_f("justa", "10-20-20", 10, 20, 20), _f("folgada", "05-10-30", 5, 10, 30))

    laudo = _laudo()

    assert laudo.formulacao.indicada.rotulo == "10-20-20"
    assert laudo.formulacao.indicada.dose_kg_ha > 0


def test_catalogo_vazio_deixa_o_laudo_completo(com_catalogo):
    com_catalogo()

    laudo = _laudo()

    assert laudo.formulacao.indicada is None
    assert "vazio" in laudo.formulacao.motivo_sem_indicacao
    # O que importa: o resto do laudo não foi afetado.
    assert laudo.calagem is not None
    assert laudo.aptidao_atual is not None and laudo.aptidao_potencial is not None


def test_a_trilha_registra_a_indicacao(com_catalogo):
    com_catalogo(_f("justa", "10-20-20", 10, 20, 20))

    laudo = _laudo()

    assert any(p.regra.startswith("R-FOR-01") for p in laudo.trace)


# --- a apresentação ----------------------------------------------------------------

def test_o_cartao_traz_a_fonte_da_formulacao(com_catalogo):
    com_catalogo(_f("justa", "10-20-20", 10, 20, 20))

    modelo = apresentar_laudo(_laudo(), carregar_dados_comum())

    assert modelo["formulacao"]["tem"] is True
    assert modelo["formulacao"]["indicada"]["fonte"] == "fórmula fictícia de teste"


def test_sem_catalogo_o_cartao_nao_aparece(com_catalogo):
    com_catalogo()

    modelo = apresentar_laudo(_laudo(), carregar_dados_comum())

    assert modelo["formulacao"]["tem"] is False
    assert modelo["formulacao"]["indicada"] is None


def test_a_calculadora_abre_com_as_indicadas(com_catalogo):
    com_catalogo(_f("justa", "10-20-20", 10, 20, 20), _f("folgada", "05-10-30", 5, 10, 30))

    from types import SimpleNamespace
    bloco = SimpleNamespace(rotulo="A1", area_ha=10.0, laudo=_laudo())
    custo = insumos_para_custo([bloco])

    assert [s["formula"] for s in custo["sugeridas"]] == ["10-20-20", "5-10-30"]


def test_sem_catalogo_a_calculadora_abre_em_branco(com_catalogo):
    com_catalogo()

    from types import SimpleNamespace
    custo = insumos_para_custo([SimpleNamespace(rotulo="", area_ha=None, laudo=_laudo())])

    assert custo["sugeridas"] == []


# --- a tela ------------------------------------------------------------------------

def test_a_tela_do_laudo_mostra_a_indicacao_e_de_onde_ela_vem(com_catalogo):
    com_catalogo(_f("justa", "10-20-20", 10, 20, 20))
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.post("/analise/laudo", data=_DADOS_DO_TALHAO).get_data(as_text=True)

    assert "Qual adubo comprar" in html
    assert "10-20-20" in html
    # A ressalva de procedência é obrigatória: é o que separa dado de mercado de norma.
    assert "não publica lista de adubos comerciais" in html


def test_sem_catalogo_a_tela_do_laudo_nao_traz_a_secao(com_catalogo):
    com_catalogo()
    cliente = criar_app({"TESTING": True}).test_client()

    html = cliente.post("/analise/laudo", data=_DADOS_DO_TALHAO).get_data(as_text=True)

    assert "Qual adubo comprar" not in html
    assert html.count("Interpretação dos atributos") >= 1  # o resto do laudo continua lá


# --- o arquivo real ----------------------------------------------------------------

def test_o_catalogo_real_carrega_e_declara_que_nao_e_do_manual():
    catalogo = Carregador().carregar_formulacoes()

    assert "NAO E TRANSCRICAO DO MANUAL" in catalogo["aviso"].upper()
    # Cada entrada precisa de fonte própria — é o que separa dado conferido de número
    # digitado de memória. Vale para o arquivo vazio de hoje e para o preenchido de amanhã.
    for entrada in catalogo["formulacoes"]:
        assert entrada["_fonte"].strip()


def test_garantias_acima_de_cem_por_cento_sao_recusadas():
    with pytest.raises(ErroCarregamento, match="não podem passar de 100"):
        Carregador().validar_formulacoes(_catalogo(_f("impossivel", "50-50-50", 50, 50, 50)))


def test_id_repetido_e_recusado():
    with pytest.raises(ErroCarregamento, match="id repetido"):
        Carregador().validar_formulacoes(
            _catalogo(_f("a", "10-10-10", 10, 10, 10), _f("a", "20-20-20", 20, 20, 20))
        )
