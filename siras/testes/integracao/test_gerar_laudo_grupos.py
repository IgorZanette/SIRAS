"""
gerar_laudo() nos seis grupos de cultura.

Grãos já são cobertos por test_gerar_laudo.py. Aqui entram os cinco grupos que o Manual
publica com a dose pronta por classe de teor, e que passaram a ser despachados pelo
orquestrador — hortaliças, tubérculos, outras comerciais, frutíferas e erva-mate.

Os casos ADU-15 (amoreira-preta em manutenção), ADU-16 (maracujazeiro em manutenção) e
ADU-17 (videira em crescimento) são os dos demais grupos com `referencia` no arquivo de
casos, e por isso os únicos com valores conferidos aqui. Para os outros a
verificação é de contrato: o laudo sai, sai completo e sai com trilha — os valores de cada
grupo já são conferidos célula a célula em testes/unidade/test_adubacao_grupos.py.
"""

import json
from pathlib import Path

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.laudo import ErroLaudo, gerar_laudo

_CAMINHO_CASOS = Path(__file__).parent.parent / "casos" / "casos_recomendacao.json"

#: Análise única para os testes de contrato: o que se verifica aqui é o despacho, não a
#: dose. Valores plausíveis de um laudo de laboratório, sem papel de oráculo.
_ANALISE = AnaliseSolo(
    ph_agua=5.1, indice_smp=5.4, argila=38, mo=2.8, p=11, k=96,
    ctc_ph7=9.4, al=1.2, ca=2.4, mg=1.1, v_percent=42,
)

#: (cultura, variáveis condicionais que o grupo exige). O par sistema_manejo/condição da
#: área NÃO é escrito aqui: sai da base, pelo mesmo caminho que o formulário usa. Escrevê-lo
#: à mão faria o teste falhar por divergência de string, não por defeito do motor.
_CULTURAS_POR_GRUPO = [
    ("tomate", {}),
    ("alho", {}),
    ("batata", {}),
    ("batata_doce", {}),
    ("tabaco", {"tipo": "virginia"}),
    ("cana_de_acucar", {"ciclo": "cana_planta", "produtividade_t_ha": 90}),
    ("citros", {"fase": "pre_plantio"}),
    ("macieira", {"fase": "crescimento", "ano": 2}),
    ("erva-mate",
     {"programa": "desde_o_plantio", "fase": "producao",
      "manejo_galho_grosso": "manejo_1_retido", "massa_verde_t_ha": 6}),
]

_DADOS = carregar_dados_comum()


def _criterio_aplicavel(cultura: str) -> tuple:
    """(sistema_manejo, condicao_area) do critério transcrito para a cultura — a mesma
    resolução que siras/web/formulario.py oferece na tela."""
    entrada = _DADOS["mapa_culturas"]["culturas"][cultura]
    criterios = _DADOS["criterios_calagem"]["criterios"]
    if "criterio_calagem" in entrada:
        criterio = next(c for c in criterios if c["id"] == entrada["criterio_calagem"])
    else:
        criterio = next(
            c for c in criterios
            if c["grupo"] == entrada["grupo"]
            and not any("fora do escopo" in nota.lower() for nota in c.get("notas", []))
        )
    return criterio["sistema_manejo"], criterio["condicao_area"]


def _contexto(cultura, variaveis):
    sistema_manejo, condicao_area = _criterio_aplicavel(cultura)
    return Contexto(
        cultura_id=cultura,
        sistema_manejo=sistema_manejo,
        condicao_area=condicao_area,
        prnt=100,
        profundidade_incorporacao_cm=20,
        variaveis=variaveis,
    )


@pytest.mark.parametrize(
    "cultura, variaveis", _CULTURAS_POR_GRUPO,
    ids=[c[0] for c in _CULTURAS_POR_GRUPO],
)
def test_laudo_sai_completo_em_todos_os_grupos(cultura, variaveis):
    laudo = gerar_laudo(_ANALISE, cultura, _contexto(cultura, variaveis))

    assert laudo.calagem.criterio_id
    assert laudo.adubacao.n is not None
    assert laudo.adubacao.p2o5 is not None
    assert laudo.adubacao.k2o is not None
    assert laudo.aptidao_atual.classe
    assert laudo.aptidao_potencial.classe
    assert len(laudo.trace) > 0
    assert all(passo.fonte for passo in laudo.trace)


def test_adu_15_amoreira_preta_bate_com_a_referencia():
    """Único caso dos demais grupos com valores conferidos à mão no arquivo de casos."""
    casos = json.loads(_CAMINHO_CASOS.read_text(encoding="utf-8"))["casos"]
    caso = next(c for c in casos if c["id"] == "ADU-15")
    entrada, referencia = caso["entrada"], caso["referencia"]

    analise = AnaliseSolo(
        ph_agua=6.0, indice_smp=6.2,
        argila=entrada["argila"], mo=entrada["mo"], p=entrada["p"], k=entrada["k"],
        ctc_ph7=entrada["ctc_ph7"], al=0.0, ca=0.0, mg=0.0, v_percent=0.0,
    )
    contexto = _contexto(
        entrada["cultura"],
        {"fase": entrada["fase"], "ano": entrada["ano"],
         "produtividade_estimada": entrada["produtividade_estimada"]},
    )

    laudo = gerar_laudo(analise, entrada["cultura"], contexto)

    assert laudo.adubacao.n == referencia["n"]
    assert laudo.adubacao.p2o5 == referencia["p2o5"]
    assert laudo.adubacao.k2o == referencia["k2o"]


@pytest.mark.parametrize("id_caso", ["ADU-16", "ADU-17"])
def test_frutiferas_conferidas_em_2026_09_13_batem_no_laudo(id_caso):
    casos = json.loads(_CAMINHO_CASOS.read_text(encoding="utf-8"))["casos"]
    caso = next(c for c in casos if c["id"] == id_caso)
    entrada, referencia = caso["entrada"], caso["referencia"]

    analise = AnaliseSolo(
        ph_agua=6.0, indice_smp=6.2,
        argila=entrada["argila"], mo=entrada["mo"], p=entrada["p"], k=entrada["k"],
        ctc_ph7=entrada["ctc_ph7"], al=0.0, ca=0.0, mg=0.0, v_percent=0.0,
    )
    variaveis = {
        chave: entrada[chave]
        for chave in ("fase", "ano", "produtividade_estimada", "tipo_uva")
        if chave in entrada
    }

    laudo = gerar_laudo(analise, entrada["cultura"], _contexto(entrada["cultura"], variaveis))

    assert laudo.adubacao.n == referencia["n"]
    assert laudo.adubacao.p2o5 == referencia["p2o5"]
    assert laudo.adubacao.k2o == referencia["k2o"]


def test_classe_de_teor_e_faixa_da_regua_vem_da_mesma_leitura():
    """Guarda contra a régua apontar uma faixa e a ficha dizer outra classe: o
    orquestrador confere as duas leituras e estoura se divergirem."""
    laudo = gerar_laudo(_ANALISE, "tomate", _contexto("tomate", {}))

    assert laudo.adubacao.classe_p
    assert any(faixa["classe"] == laudo.adubacao.classe_p for faixa in laudo.adubacao.faixas_p)
    assert any(faixa["classe"] == laudo.adubacao.classe_k for faixa in laudo.adubacao.faixas_k)


def test_fase_do_pomar_ausente_falha_com_mensagem_de_dominio():
    with pytest.raises(ErroLaudo, match="informe 'fase'"):
        gerar_laudo(_ANALISE, "citros", _contexto("citros", {}))


def test_programa_da_erva_mate_ausente_falha_com_mensagem_de_dominio():
    with pytest.raises(ErroLaudo, match="programa"):
        gerar_laudo(_ANALISE, "erva-mate", _contexto("erva-mate", {}))


# --- CCAE v1.4, §7.2: o teto segue o modo que o laudo manda (05/11/2026) -------------

#: Erval com dose de calcário entre os dois tetos (5 t/ha em superfície, 20 incorporado):
#: V baixo e CTC alta. Entradas de teste, como um laudo de laboratório; a dose sai da
#: fórmula da Tab. 5.6 e não é conferida aqui -- só o lado do teto em que ela cai.
_ERVAL_ACIDO = AnaliseSolo(
    ph_agua=4.5, indice_smp=4.8, argila=55, mo=3.0, p=6, k=20,
    ctc_ph7=20.0, al=3.0, ca=0.6, mg=0.2, v_percent=4.3,
)


def _f1_potencial(variaveis):
    laudo = gerar_laudo(_ERVAL_ACIDO, "erva-mate", _contexto("erva-mate", variaveis))
    nc_bruta = (40 - _ERVAL_ACIDO.v_percent) / 100 * _ERVAL_ACIDO.ctc_ph7
    config = _DADOS["config_aptidao"]
    assert config["NC_MAX_SUPERFICIAL_T_HA"] < nc_bruta <= config["NC_MAX_INCORPORADO_T_HA"], (
        "a análise de teste deixou de cair entre os dois tetos"
    )
    f1 = next(f for f in laudo.aptidao_potencial.fatores if f.id == "F1_acidez")
    return laudo, f1


def test_erval_estabelecido_projeta_correcao_plurianual_pelo_teto_superficial():
    laudo, f1 = _f1_potencial({
        "programa": "recuperacao",
        "manejo_galho_grosso": "manejo_1_retido", "massa_verde_t_ha": 6,
    })

    assert laudo.calagem.criterio["modo_aplicacao"] == "superficial"
    assert f1.rotulo == "LIGEIRO"
    assert "superficial" in f1.evidencia


def test_implantacao_do_erval_segue_o_teto_da_incorporacao():
    laudo, f1 = _f1_potencial({
        "programa": "desde_o_plantio", "fase": "plantio_e_crescimento", "momento": "plantio",
    })

    assert laudo.calagem.criterio["modo_aplicacao"] == "incorporado"
    assert f1.rotulo == "NULO"
