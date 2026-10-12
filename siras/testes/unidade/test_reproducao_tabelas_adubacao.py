"""
Reprodução exaustiva das tabelas de N/P2O5/K2O já publicadas prontas por classe (sem
correção+manutenção, ao contrário de grãos) nos grupos hortaliças, tubérculos, outras
comerciais, e nas fases pré-plantio/crescimento de frutíferas e nas fases sem fórmula de
erva-mate.

Ideia (proposta pelo autor, 2026-08-23): essas tabelas já são o valor final impresso
pela CQFS — não há cálculo do autor a conferir, só se o motor lê a célula certa. Este
arquivo cobre TODA célula de TODA cultura desses grupos (não só os casos ADU-08/09/10/
13/14 já cobertos manualmente em test_adubacao_grupos.py), como rede de segurança contra
erro de leitura de chave/índice em qualquer uma das ~40 culturas.

Estratégia: em vez de adivinhar um p_solo/k_solo "típico", cada valor de entrada é
derivado mecanicamente das PRÓPRIAS faixas de dados/comum/interpretacao_p.json,
interpretacao_k.json e classes_mo do arquivo do grupo — usando o mesmo critério de
fronteira que siras/motor/calagem.py::_classificar_faixa já usa (de < valor <= ate). Não
é suposição agronômica: é a fronteira que o próprio código (e os dados) já declaram.

Fases/formatos fora do alcance desta reprodução automática (cobertos manualmente em
test_adubacao_grupos.py, ou ainda não implementados — ver docstring de
siras/motor/adubacao.py): manutenção de frutíferas com indexação própria ou teor foliar,
e videira.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from siras.conhecimento.carregador import (
    carregar_dados_comum,
    carregar_dados_erva_mate,
    carregar_dados_frutiferas,
    carregar_dados_hortalicas,
    carregar_dados_outras,
    carregar_dados_tuberculos,
)
from siras.motor.adubacao import (
    _resolver_dose,
    calcular_adubacao_erva_mate,
    calcular_adubacao_frutiferas,
    calcular_adubacao_hortalicas,
    calcular_adubacao_outras,
    calcular_adubacao_tuberculos,
)

_DADOS_COMUNS = carregar_dados_comum()
_DADOS_HORTALICAS = carregar_dados_hortalicas()
_DADOS_TUBERCULOS = carregar_dados_tuberculos()
_DADOS_OUTRAS = carregar_dados_outras()
_DADOS_FRUTIFERAS = carregar_dados_frutiferas()
_DADOS_ERVA_MATE = carregar_dados_erva_mate()

# Classe de argila e faixa de CTC fixas para as sondas de P/K — a escolha em si é
# arbitrária (qualquer uma serve), o que importa é ficar constante entre os casos.
_CLASSE_ARGILA = "3"
_FAIXA_CTC = "b"


def _faixa_representativa(faixa: Dict[str, Any]) -> float:
    """Valor que cai dentro da faixa pelo critério de _classificar_faixa (de < valor <=
    ate; None = infinito). Não é valor agronômico — é uma sonda mecânica."""
    if faixa["ate"] is not None:
        return faixa["ate"]
    return faixa["de"] + 1


def _e_folha_de_dose(no: Any) -> bool:
    """True se `no` já é uma dose resolvível (não um dict aninhado por outro índice,
    como fase/tipo/produtividade)."""
    return isinstance(no, dict) and ("valor" in no or "min" in no)


def _mo_para_faixa(classes_mo: List[Dict[str, Any]], faixa_id: str) -> float:
    faixa = next(f for f in classes_mo if f["id"] == faixa_id)
    return _faixa_representativa(faixa)


def _classe_argila_valor() -> float:
    faixas = next(
        a["faixas"] for a in _DADOS_COMUNS["interpretacao_geral"]["atributos"] if a["atributo"] == "argila"
    )
    faixa = next(f for f in faixas if f["classe"] == _CLASSE_ARGILA)
    return _faixa_representativa(faixa)


def _faixa_ctc_valor() -> float:
    faixa = next(f for f in _DADOS_COMUNS["interpretacao_k"]["faixas_ctc"] if f["faixa"] == _FAIXA_CTC)
    return _faixa_representativa(faixa)


_ARGILA = _classe_argila_valor()
_CTC = _faixa_ctc_valor()


def _p_solo_para_classe(grupo_p: int, classe_alvo: str) -> float:
    tabela = next(t for t in _DADOS_COMUNS["interpretacao_p"]["tabelas"] if t["grupo"] == f"grupo_{grupo_p}")
    bloco = next(b for b in tabela["por_classe_argila"] if b["classe_argila"] == _CLASSE_ARGILA)
    faixa = next(f for f in bloco["faixas"] if f["classe"] == classe_alvo)
    return _faixa_representativa(faixa)


def _k_solo_para_classe(grupo_k: int, classe_alvo: str) -> float:
    tabela = next(t for t in _DADOS_COMUNS["interpretacao_k"]["tabelas"] if t["grupo"] == f"grupo_{grupo_k}")
    bloco = next(b for b in tabela["por_faixa_ctc"] if b["faixa_ctc"] == _FAIXA_CTC)
    faixa = next(f for f in bloco["faixas"] if f["classe"] == classe_alvo)
    return _faixa_representativa(faixa)


# ---------------------------------------------------------------------------------
# Hortaliças
# ---------------------------------------------------------------------------------


def _casos_n_hortalicas():
    casos = []
    for cultura_id, entrada in _DADOS_HORTALICAS["adubacao"]["culturas"].items():
        n_bloco = entrada["n"]
        if n_bloco.get("tipo") != "por_classe_mo":
            continue
        classes_mo = _DADOS_HORTALICAS["adubacao"]["classes_mo"][n_bloco["classes_mo"]]
        for faixa in classes_mo:
            esperado = _resolver_dose(n_bloco["doses"][faixa["id"]])
            casos.append(pytest.param(cultura_id, faixa["id"], esperado, id=f"{cultura_id}-{faixa['id']}"))
    return casos


@pytest.mark.parametrize("cultura_id, faixa_mo_id, esperado", _casos_n_hortalicas())
def test_hortalicas_n_reproduz_tabela(cultura_id, faixa_mo_id, esperado):
    mo = _mo_para_faixa(_DADOS_HORTALICAS["adubacao"]["classes_mo"]["padrao"], faixa_mo_id)
    resultado = calcular_adubacao_hortalicas(
        cultura_id, mo=mo, argila=_ARGILA, p_solo=10.0, k_solo=50.0, ctc_ph7=_CTC,
    )
    assert resultado["n"] == esperado


def _casos_pk_hortalicas():
    casos = []
    for cultura_id, entrada in _DADOS_HORTALICAS["adubacao"]["culturas"].items():
        pk = entrada["pk"]
        if pk.get("tipo") != "por_classe_teor":
            continue
        grupo = entrada["grupo_exigencia"]
        for classe, folha in pk["p"].items():
            if not _e_folha_de_dose(folha):
                continue
            casos.append(
                pytest.param(cultura_id, "p", grupo["p"], classe, _resolver_dose(folha), id=f"{cultura_id}-p-{classe}")
            )
        for classe, folha in pk["k"].items():
            if not _e_folha_de_dose(folha):
                continue
            casos.append(
                pytest.param(cultura_id, "k", grupo["k"], classe, _resolver_dose(folha), id=f"{cultura_id}-k-{classe}")
            )
    return casos


@pytest.mark.parametrize("cultura_id, nutriente, grupo, classe, esperado", _casos_pk_hortalicas())
def test_hortalicas_pk_reproduz_tabela(cultura_id, nutriente, grupo, classe, esperado):
    if nutriente == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo, classe), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo, classe)
    resultado = calcular_adubacao_hortalicas(
        cultura_id, mo=3.0, argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
    )
    obtido = resultado["p2o5"] if nutriente == "p" else resultado["k2o"]
    assert obtido == esperado


def _casos_aspargo():
    entrada = _DADOS_HORTALICAS["adubacao"]["culturas"]["aspargo"]
    casos = []
    n_bloco = entrada["n"]
    classes_mo = _DADOS_HORTALICAS["adubacao"]["classes_mo"][n_bloco["classes_mo"]]
    for faixa in classes_mo:
        for fase, folha in n_bloco["doses"][faixa["id"]].items():
            casos.append(pytest.param("n", faixa["id"], fase, _resolver_dose(folha), id=f"n-{faixa['id']}-{fase}"))
    pk_bloco = entrada["pk"]
    for classe, por_fase in pk_bloco["p"].items():
        for fase, folha in por_fase.items():
            if _e_folha_de_dose(folha):
                casos.append(pytest.param("p", classe, fase, _resolver_dose(folha), id=f"p-{classe}-{fase}"))
    for classe, por_fase in pk_bloco["k"].items():
        for fase, folha in por_fase.items():
            if _e_folha_de_dose(folha):
                casos.append(pytest.param("k", classe, fase, _resolver_dose(folha), id=f"k-{classe}-{fase}"))
    return casos


@pytest.mark.parametrize("eixo, chave, fase, esperado", _casos_aspargo())
def test_aspargo_reproduz_tabela(eixo, chave, fase, esperado):
    grupo_exigencia = _DADOS_HORTALICAS["adubacao"]["culturas"]["aspargo"]["grupo_exigencia"]
    # As fases de N ('instalacao'/'formacao'/'manutencao') e de P/K
    # ('pre_plantio'/'formacao'/'manutencao') do aspargo tem nomes diferentes no
    # Manual — fase_n/fase_pk isolam qual eixo a fase deste caso pertence. O motor
    # sempre calcula os dois eixos, então o eixo que não está sob teste recebe
    # 'formacao' (válido nos dois vocabulários) só para não travar por fase ausente.
    if eixo == "n":
        mo = _mo_para_faixa(_DADOS_HORTALICAS["adubacao"]["classes_mo"]["padrao"], chave)
        resultado = calcular_adubacao_hortalicas(
            "aspargo", mo=mo, argila=_ARGILA, p_solo=10.0, k_solo=50.0, ctc_ph7=_CTC,
            fase_n=fase, fase_pk="formacao",
        )
        assert resultado["n"] == esperado
        return
    if eixo == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo_exigencia["p"], chave), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo_exigencia["k"], chave)
    resultado = calcular_adubacao_hortalicas(
        "aspargo", mo=3.0, argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
        fase_n="formacao", fase_pk=fase,
    )
    obtido = resultado["p2o5"] if eixo == "p" else resultado["k2o"]
    assert obtido == esperado


# ---------------------------------------------------------------------------------
# Tubérculos (mesmo formato simples que a maioria das hortaliças)
# ---------------------------------------------------------------------------------


def _casos_n_tuberculos():
    casos = []
    for cultura_id, entrada in _DADOS_TUBERCULOS["adubacao"]["culturas"].items():
        n_bloco = entrada["n"]
        classes_mo = _DADOS_TUBERCULOS["adubacao"]["classes_mo"][n_bloco["classes_mo"]]
        for faixa in classes_mo:
            esperado = _resolver_dose(n_bloco["doses"][faixa["id"]])
            casos.append(pytest.param(cultura_id, faixa["id"], esperado, id=f"{cultura_id}-{faixa['id']}"))
    return casos


@pytest.mark.parametrize("cultura_id, faixa_mo_id, esperado", _casos_n_tuberculos())
def test_tuberculos_n_reproduz_tabela(cultura_id, faixa_mo_id, esperado):
    mo = _mo_para_faixa(_DADOS_TUBERCULOS["adubacao"]["classes_mo"]["padrao"], faixa_mo_id)
    resultado = calcular_adubacao_tuberculos(
        cultura_id, mo=mo, argila=_ARGILA, p_solo=10.0, k_solo=50.0, ctc_ph7=_CTC,
    )
    assert resultado["n"] == esperado


def _casos_pk_tuberculos():
    casos = []
    for cultura_id, entrada in _DADOS_TUBERCULOS["adubacao"]["culturas"].items():
        pk = entrada["pk"]
        grupo = entrada["grupo_exigencia"]
        for classe, folha in pk["p"].items():
            casos.append(
                pytest.param(cultura_id, "p", grupo["p"], classe, _resolver_dose(folha), id=f"{cultura_id}-p-{classe}")
            )
        for classe, folha in pk["k"].items():
            casos.append(
                pytest.param(cultura_id, "k", grupo["k"], classe, _resolver_dose(folha), id=f"{cultura_id}-k-{classe}")
            )
    return casos


@pytest.mark.parametrize("cultura_id, nutriente, grupo, classe, esperado", _casos_pk_tuberculos())
def test_tuberculos_pk_reproduz_tabela(cultura_id, nutriente, grupo, classe, esperado):
    if nutriente == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo, classe), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo, classe)
    resultado = calcular_adubacao_tuberculos(
        cultura_id, mo=3.0, argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
    )
    obtido = resultado["p2o5"] if nutriente == "p" else resultado["k2o"]
    assert obtido == esperado


# ---------------------------------------------------------------------------------
# Outras comerciais (cana-de-açúcar e tabaco)
# ---------------------------------------------------------------------------------


def _casos_cana_n():
    casos = []
    entrada = _DADOS_OUTRAS["adubacao"]["culturas"]["cana_de_acucar"]
    classes_mo = _DADOS_OUTRAS["adubacao"]["classes_mo"]["padrao"]

    n_planta = entrada["cana_planta"]["n"]
    for faixa in classes_mo:
        esperado = _resolver_dose(n_planta["doses"][faixa["id"]])
        casos.append(pytest.param("cana_planta", faixa["id"], None, esperado, id=f"planta-{faixa['id']}"))

    n_soca = entrada["cana_soca"]["n"]
    for faixa in classes_mo:
        for faixa_prod, folha in n_soca["doses"][faixa["id"]].items():
            casos.append(
                pytest.param("cana_soca", faixa["id"], faixa_prod, _resolver_dose(folha), id=f"soca-{faixa['id']}-{faixa_prod}")
            )
    return casos


@pytest.mark.parametrize("ciclo, faixa_mo_id, faixa_prod_id, esperado", _casos_cana_n())
def test_cana_n_reproduz_tabela(ciclo, faixa_mo_id, faixa_prod_id, esperado):
    mo = _mo_para_faixa(_DADOS_OUTRAS["adubacao"]["classes_mo"]["padrao"], faixa_mo_id)
    bloco = _DADOS_OUTRAS["adubacao"]["culturas"]["cana_de_acucar"][ciclo]
    produtividade = 100.0
    if faixa_prod_id is not None:
        faixa = next(f for f in bloco["pk"]["faixas_produtividade"] if f["id"] == faixa_prod_id)
        produtividade = _faixa_representativa(faixa)
    resultado = calcular_adubacao_outras(
        "cana_de_acucar", mo=mo, argila=_ARGILA, p_solo=10.0, k_solo=50.0, ctc_ph7=_CTC,
        ciclo=ciclo, produtividade_t_ha=produtividade,
    )
    assert resultado["n"] == esperado


def _casos_cana_pk():
    casos = []
    entrada = _DADOS_OUTRAS["adubacao"]["culturas"]["cana_de_acucar"]
    grupo = entrada["grupo_exigencia"]
    for ciclo in ("cana_planta", "cana_soca"):
        pk = entrada[ciclo]["pk"]
        for classe, por_prod in pk["p"].items():
            for faixa_prod, folha in por_prod.items():
                casos.append(
                    pytest.param(ciclo, "p", grupo["p"], classe, faixa_prod, _resolver_dose(folha),
                                 id=f"{ciclo}-p-{classe}-{faixa_prod}")
                )
        for classe, por_prod in pk["k"].items():
            for faixa_prod, folha in por_prod.items():
                casos.append(
                    pytest.param(ciclo, "k", grupo["k"], classe, faixa_prod, _resolver_dose(folha),
                                 id=f"{ciclo}-k-{classe}-{faixa_prod}")
                )
    return casos


@pytest.mark.parametrize("ciclo, nutriente, grupo, classe, faixa_prod_id, esperado", _casos_cana_pk())
def test_cana_pk_reproduz_tabela(ciclo, nutriente, grupo, classe, faixa_prod_id, esperado):
    bloco = _DADOS_OUTRAS["adubacao"]["culturas"]["cana_de_acucar"][ciclo]
    faixa = next(f for f in bloco["pk"]["faixas_produtividade"] if f["id"] == faixa_prod_id)
    produtividade = _faixa_representativa(faixa)
    if nutriente == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo, classe), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo, classe)
    resultado = calcular_adubacao_outras(
        "cana_de_acucar", mo=3.0, argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
        ciclo=ciclo, produtividade_t_ha=produtividade,
    )
    obtido = resultado["p2o5"] if nutriente == "p" else resultado["k2o"]
    assert obtido == esperado


def _casos_tabaco_n():
    casos = []
    entrada = _DADOS_OUTRAS["adubacao"]["culturas"]["tabaco"]
    classes_mo = _DADOS_OUTRAS["adubacao"]["classes_mo"][entrada["n"]["classes_mo"]]
    for faixa in classes_mo:
        for tipo, folha in entrada["n"]["doses"][faixa["id"]].items():
            casos.append(pytest.param(faixa["id"], tipo, _resolver_dose(folha), id=f"{faixa['id']}-{tipo}"))
    return casos


@pytest.mark.parametrize("faixa_mo_id, tipo, esperado", _casos_tabaco_n())
def test_tabaco_n_reproduz_tabela(faixa_mo_id, tipo, esperado):
    entrada = _DADOS_OUTRAS["adubacao"]["culturas"]["tabaco"]
    mo = _mo_para_faixa(_DADOS_OUTRAS["adubacao"]["classes_mo"][entrada["n"]["classes_mo"]], faixa_mo_id)
    resultado = calcular_adubacao_outras(
        "tabaco", mo=mo, argila=_ARGILA, p_solo=10.0, k_solo=50.0, ctc_ph7=_CTC, tipo=tipo,
    )
    assert resultado["n"] == esperado


def _casos_tabaco_pk():
    casos = []
    entrada = _DADOS_OUTRAS["adubacao"]["culturas"]["tabaco"]
    grupo = entrada["grupo_exigencia"]
    for classe, folha in entrada["pk"]["p"].items():
        casos.append(pytest.param("p", grupo["p"], classe, None, _resolver_dose(folha), id=f"p-{classe}"))
    for classe, por_tipo in entrada["pk"]["k"].items():
        for tipo, folha in por_tipo.items():
            casos.append(pytest.param("k", grupo["k"], classe, tipo, _resolver_dose(folha), id=f"k-{classe}-{tipo}"))
    return casos


@pytest.mark.parametrize("nutriente, grupo, classe, tipo, esperado", _casos_tabaco_pk())
def test_tabaco_pk_reproduz_tabela(nutriente, grupo, classe, tipo, esperado):
    tipo_param = tipo or "virginia"
    if nutriente == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo, classe), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo, classe)
    resultado = calcular_adubacao_outras(
        "tabaco", mo=2.5, argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC, tipo=tipo_param,
    )
    obtido = resultado["p2o5"] if nutriente == "p" else resultado["k2o"]
    assert obtido == esperado


# ---------------------------------------------------------------------------------
# Frutíferas — pré-plantio (tabela 6.5.1 comum) e crescimento
# ---------------------------------------------------------------------------------


def _culturas_pre_plantio_referencia() -> List[str]:
    return [
        cultura_id
        for cultura_id, entrada in _DADOS_FRUTIFERAS["adubacao"]["culturas"].items()
        if entrada["pre_plantio"]["pk"].get("tipo") == "referencia"
    ]


@pytest.mark.parametrize("cultura_id", _culturas_pre_plantio_referencia())
def test_frutiferas_pre_plantio_resolve_grupo_por_cultura(cultura_id):
    # Todas as frutíferas leem a MESMA tabela 6.5.1 — o que varia de cultura para
    # cultura é o grupo_exigencia usado para chegar à classe. Fixa classe "medio" dos
    # dois lados e varre as 17 culturas, para pegar erro de resolução de grupo por
    # cultura (não só na tabela em si, coberta à parte abaixo).
    entrada = _DADOS_FRUTIFERAS["adubacao"]["culturas"][cultura_id]
    grupo = entrada["grupo_exigencia"]
    tabela = _DADOS_FRUTIFERAS["adubacao"]["tabela_6_5_1"]
    p_solo = _p_solo_para_classe(grupo["p"], "medio")
    k_solo = _k_solo_para_classe(grupo["k"], "medio")
    resultado = calcular_adubacao_frutiferas(
        cultura_id, fase="pre_plantio", argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
    )
    assert resultado["p2o5"] == _resolver_dose(tabela["p"]["medio"])
    assert resultado["k2o"] == _resolver_dose(tabela["k"]["medio"])


def _casos_pre_plantio_frutiferas_exaustivo():
    casos = []
    tabela = _DADOS_FRUTIFERAS["adubacao"]["tabela_6_5_1"]
    # a tabela 6.5.1 é comum a todas as frutíferas — varrer as classes com 1 cultura
    # já basta; a resolução de grupo por cultura está no teste acima.
    cultura_id = _culturas_pre_plantio_referencia()[0]
    for classe_p, folha in tabela["p"].items():
        casos.append(pytest.param(cultura_id, "p", classe_p, _resolver_dose(folha), id=f"p-{classe_p}"))
    for classe_k, folha in tabela["k"].items():
        casos.append(pytest.param(cultura_id, "k", classe_k, _resolver_dose(folha), id=f"k-{classe_k}"))
    return casos


@pytest.mark.parametrize("cultura_id, nutriente, classe, esperado", _casos_pre_plantio_frutiferas_exaustivo())
def test_frutiferas_pre_plantio_reproduz_todas_as_classes(cultura_id, nutriente, classe, esperado):
    entrada = _DADOS_FRUTIFERAS["adubacao"]["culturas"][cultura_id]
    grupo = entrada["grupo_exigencia"]
    if nutriente == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo["p"], classe), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo["k"], classe)
    resultado = calcular_adubacao_frutiferas(
        cultura_id, fase="pre_plantio", argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
    )
    obtido = resultado["p2o5"] if nutriente == "p" else resultado["k2o"]
    assert obtido == esperado


def _casos_crescimento_frutiferas():
    casos = []
    for cultura_id, entrada in _DADOS_FRUTIFERAS["adubacao"]["culturas"].items():
        n_bloco = entrada["crescimento"]["n"]
        tipo = n_bloco.get("tipo")
        classes_mo = _DADOS_FRUTIFERAS["adubacao"]["classes_mo"][n_bloco["classes_mo"]] if tipo in (
            "por_classe_mo", "por_classe_mo_e_ano"
        ) else None
        if tipo == "por_classe_mo":
            for faixa in classes_mo:
                esperado = _resolver_dose(n_bloco["doses"][faixa["id"]])
                casos.append(pytest.param(cultura_id, faixa["id"], None, esperado, id=f"{cultura_id}-{faixa['id']}"))
        elif tipo == "por_classe_mo_e_ano":
            for faixa in classes_mo:
                for ano, folha in n_bloco["doses"][faixa["id"]].items():
                    esperado = _resolver_dose(folha)
                    casos.append(
                        pytest.param(cultura_id, faixa["id"], ano, esperado, id=f"{cultura_id}-{faixa['id']}-{ano}")
                    )
        # "nao_aplicar"/"ver_manutencao": sem tabela de crescimento por classe — fora
        # deste teste (amoreira-preta e mirtileiro/morangueiro, cobertos ou pendentes
        # conforme a fase de manutenção).
    return casos


@pytest.mark.parametrize("cultura_id, faixa_mo_id, ano, esperado", _casos_crescimento_frutiferas())
def test_frutiferas_crescimento_reproduz_tabela(cultura_id, faixa_mo_id, ano, esperado):
    entrada = _DADOS_FRUTIFERAS["adubacao"]["culturas"][cultura_id]
    classes_mo = _DADOS_FRUTIFERAS["adubacao"]["classes_mo"][entrada["crescimento"]["n"]["classes_mo"]]
    mo = _mo_para_faixa(classes_mo, faixa_mo_id)
    resultado = calcular_adubacao_frutiferas(cultura_id, fase="crescimento", mo=mo, ano=ano)
    assert resultado["n"] == esperado


def _casos_manutencao_taxa_frutiferas():
    casos = []
    for cultura_id, entrada in _DADOS_FRUTIFERAS["adubacao"]["culturas"].items():
        manutencao = entrada["manutencao"]
        if manutencao.get("tipo") != "taxa_por_tonelada_estimada":
            continue
        for nutriente in ("n", "p", "k"):
            raw = manutencao[nutriente]
            esperado = 0.0 if raw.get("tipo") == "nao_aplicar" else _resolver_dose(raw)
            casos.append(pytest.param(cultura_id, nutriente, esperado, id=f"{cultura_id}-{nutriente}"))
    return casos


@pytest.mark.parametrize("cultura_id, nutriente, esperado", _casos_manutencao_taxa_frutiferas())
def test_frutiferas_manutencao_taxa_reproduz_tabela(cultura_id, nutriente, esperado):
    # produtividade_estimada=1.0 isola a taxa em si (dose = taxa x 1).
    resultado = calcular_adubacao_frutiferas(cultura_id, fase="manutencao", produtividade_estimada=1.0)
    chave = {"n": "n", "p": "p2o5", "k": "k2o"}[nutriente]
    assert resultado[chave] == esperado


# ---------------------------------------------------------------------------------
# Erva-mate
# ---------------------------------------------------------------------------------


def _entrada_erva_mate():
    return _DADOS_ERVA_MATE["adubacao"]["culturas"]["erva_mate"]


def _casos_formacao_da_copa_n():
    entrada = _entrada_erva_mate()
    bloco = entrada["programa_desde_o_plantio"]["formacao_da_copa"]["n"]
    classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"][bloco["classes_mo"]]
    return [
        pytest.param(faixa["id"], _resolver_dose(bloco["doses"][faixa["id"]]), id=faixa["id"])
        for faixa in classes_mo
    ]


@pytest.mark.parametrize("faixa_mo_id, esperado", _casos_formacao_da_copa_n())
def test_erva_mate_formacao_da_copa_n_reproduz_tabela(faixa_mo_id, esperado):
    entrada = _entrada_erva_mate()
    classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"]["padrao"]
    mo = _mo_para_faixa(classes_mo, faixa_mo_id)
    resultado = calcular_adubacao_erva_mate(
        "desde_o_plantio", fase="formacao_da_copa", mo=mo, argila=_ARGILA, p_solo=10.0, k_solo=50.0, ctc_ph7=_CTC,
    )
    assert resultado["n"] == esperado


def _casos_formacao_da_copa_pk():
    entrada = _entrada_erva_mate()
    pk = entrada["programa_desde_o_plantio"]["formacao_da_copa"]["pk"]
    grupo = entrada["grupo_exigencia"]
    casos = []
    for classe, folha in pk["p"].items():
        casos.append(pytest.param("p", grupo["p"], classe, _resolver_dose(folha), id=f"p-{classe}"))
    for classe, folha in pk["k"].items():
        casos.append(pytest.param("k", grupo["k"], classe, _resolver_dose(folha), id=f"k-{classe}"))
    return casos


@pytest.mark.parametrize("nutriente, grupo, classe, esperado", _casos_formacao_da_copa_pk())
def test_erva_mate_formacao_da_copa_pk_reproduz_tabela(nutriente, grupo, classe, esperado):
    if nutriente == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo, classe), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo, classe)
    resultado = calcular_adubacao_erva_mate(
        "desde_o_plantio", fase="formacao_da_copa", mo=3.0, argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
    )
    obtido = resultado["p2o5"] if nutriente == "p" else resultado["k2o"]
    assert obtido == esperado


def _casos_plantio_e_crescimento():
    entrada = _entrada_erva_mate()
    bloco = entrada["programa_desde_o_plantio"]["plantio_e_crescimento"]
    classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"][bloco["n"]["classes_mo"]]
    casos = []
    for faixa in classes_mo:
        for momento, folha in bloco["n"]["doses"][faixa["id"]].items():
            casos.append(pytest.param("n", faixa["id"], momento, _resolver_dose(folha), id=f"n-{faixa['id']}-{momento}"))
    for classe, por_momento in bloco["p"]["doses"].items():
        for momento, folha in por_momento.items():
            casos.append(pytest.param("p", classe, momento, _resolver_dose(folha), id=f"p-{classe}-{momento}"))
    for classe, por_momento in bloco["k"]["doses"].items():
        for momento, folha in por_momento.items():
            casos.append(pytest.param("k", classe, momento, _resolver_dose(folha), id=f"k-{classe}-{momento}"))
    return casos


@pytest.mark.parametrize("eixo, chave, momento, esperado", _casos_plantio_e_crescimento())
def test_erva_mate_plantio_e_crescimento_reproduz_tabela(eixo, chave, momento, esperado):
    entrada = _entrada_erva_mate()
    grupo = entrada["grupo_exigencia"]
    if eixo == "n":
        classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"]["padrao"]
        mo = _mo_para_faixa(classes_mo, chave)
        resultado = calcular_adubacao_erva_mate(
            "desde_o_plantio", fase="plantio_e_crescimento", mo=mo, momento=momento,
            argila=_ARGILA, p_solo=10.0, k_solo=50.0, ctc_ph7=_CTC,
        )
        assert resultado["n"] == esperado
        return
    if eixo == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo["p"], chave), 50.0
    else:
        p_solo, k_solo = 10.0, _k_solo_para_classe(grupo["k"], chave)
    resultado = calcular_adubacao_erva_mate(
        "desde_o_plantio", fase="plantio_e_crescimento", mo=3.0, momento=momento,
        argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
    )
    obtido = resultado["p2o5"] if eixo == "p" else resultado["k2o"]
    assert obtido == esperado


def _casos_producao():
    entrada = _entrada_erva_mate()
    bloco = entrada["programa_desde_o_plantio"]["producao"]
    classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"]["padrao"]
    casos = []
    for faixa in classes_mo:
        for manejo, coef in bloco["n"]["coeficientes"][faixa["id"]].items():
            casos.append(pytest.param("n", faixa["id"], manejo, float(coef), id=f"n-{faixa['id']}-{manejo}"))
    for manejo, coefs in bloco["pk"]["coeficientes"].items():
        casos.append(pytest.param("p", None, manejo, float(coefs["p"]), id=f"p-{manejo}"))
        casos.append(pytest.param("k", None, manejo, float(coefs["k"]), id=f"k-{manejo}"))
    return casos


@pytest.mark.parametrize("eixo, faixa_mo_id, manejo, esperado", _casos_producao())
def test_erva_mate_producao_reproduz_coeficientes(eixo, faixa_mo_id, manejo, esperado):
    # massa_verde_t_ha=1.0 isola o coeficiente em si (dose = coeficiente x 1).
    classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"]["padrao"]
    mo = _mo_para_faixa(classes_mo, faixa_mo_id) if faixa_mo_id else 3.0
    resultado = calcular_adubacao_erva_mate(
        "desde_o_plantio", fase="producao", mo=mo, manejo_galho_grosso=manejo, massa_verde_t_ha=1.0,
    )
    chave = {"n": "n", "p": "p2o5", "k": "k2o"}[eixo]
    assert resultado[chave] == esperado


def _casos_recuperacao():
    entrada = _entrada_erva_mate()
    bloco = entrada["programa_recuperacao"]
    classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"]["padrao"]
    casos = []
    for faixa in classes_mo:
        for manejo, parametros in bloco["n"]["parametros"][faixa["id"]].items():
            casos.append(pytest.param("n", faixa["id"], None, manejo, float(parametros["base"]), id=f"n-{faixa['id']}-{manejo}"))
    grupo = entrada["grupo_exigencia"]
    for classe in bloco["pk"]["classes_atendidas"]:
        for manejo in bloco["pk"]["coeficientes_por_manejo"]:
            base_p = bloco["pk"]["parametros"][classe]["p"]["base"]
            base_k = bloco["pk"]["parametros"][classe]["k"]["base"]
            casos.append(pytest.param("p", None, classe, manejo, float(base_p), id=f"p-{classe}-{manejo}"))
            casos.append(pytest.param("k", None, classe, manejo, float(base_k), id=f"k-{classe}-{manejo}"))
    return casos


@pytest.mark.parametrize("eixo, faixa_mo_id, classe, manejo, esperado", _casos_recuperacao())
def test_erva_mate_recuperacao_reproduz_base(eixo, faixa_mo_id, classe, manejo, esperado):
    # massa_verde_t_ha=0.0 isola a "base" (dose = base + coeficiente x 0 = base).
    grupo = _entrada_erva_mate()["grupo_exigencia"]
    if eixo == "n":
        classes_mo = _DADOS_ERVA_MATE["adubacao"]["classes_mo"]["padrao"]
        mo = _mo_para_faixa(classes_mo, faixa_mo_id)
        resultado = calcular_adubacao_erva_mate(
            "recuperacao", mo=mo, argila=_ARGILA, p_solo=2.0, k_solo=10.0, ctc_ph7=_CTC,
            manejo_galho_grosso=manejo, massa_verde_t_ha=0.0,
        )
        assert resultado["n"] == esperado
        return
    if eixo == "p":
        p_solo, k_solo = _p_solo_para_classe(grupo["p"], classe), 10.0
    else:
        p_solo, k_solo = 2.0, _k_solo_para_classe(grupo["k"], classe)
    resultado = calcular_adubacao_erva_mate(
        "recuperacao", mo=3.0, argila=_ARGILA, p_solo=p_solo, k_solo=k_solo, ctc_ph7=_CTC,
        manejo_galho_grosso=manejo, massa_verde_t_ha=0.0,
    )
    obtido = resultado["p2o5"] if eixo == "p" else resultado["k2o"]
    assert obtido == esperado
