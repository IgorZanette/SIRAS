"""
A fórmula de NC do ramo (b) existe em dois lugares, de propósito — débito 4 do roadmap.

A mesma expressão `NC = (40 - V%)/100 x CTC_pH7` vive em `motor/aptidao.py`, onde decide o
F1, e em `motor/calagem.py`, onde recomenda a dose. O CCAE v1.2 §7.1(b) registra a
duplicação como deliberada — o F1 não chama a calagem porque a pastagem natural não tem
critério de calagem mapeado — e põe uma condição para ela ser aceitável: "um teste deve
comparar as duas implementações nas culturas em que ambas existem, e falhar se
divergirem. Sem esse teste, a duplicação deixa de ser deliberada e vira o próximo defeito
invisível."

Este é esse teste. Ele não reimplementa a fórmula: chama os dois módulos e compara.

A comparação é feita no arredondamento da calagem (uma casa, ADR 0002), porque é a dose
arredondada o que a calagem devolve. O F1 lê a NC ANTES do arredondamento; a parte do
contrato que depende disso — a fronteira exata em V% = 40 — é medida em
test_equivalencia_ccae_v11_v12.py.
"""

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.dominio.analise import AnaliseSolo, Contexto
from siras.motor.aptidao import (
    _MANEJO_PARA_CONTEXTO,
    _nomes_candidatos,
    _resolver_ph_referencia,
    necessidade_de_calcario_ramo_b,
)
from siras.motor.calagem import _arredondar, calcular_calagem, resolver_criterio_id
from siras.motor.trace import Trace

_DADOS = carregar_dados_comum()
_SEM = _DADOS["criterios_aptidao"]["F1_acidez"]["sem_ph_referencia"]


def _contexto(cultura: str) -> Contexto:
    sistema_manejo, condicao_area = _MANEJO_PARA_CONTEXTO["convencional"]
    return Contexto(
        cultura_id=cultura, sistema_manejo=sistema_manejo, condicao_area=condicao_area,
        prnt=100.0, profundidade_incorporacao_cm=20.0,
    )


def _criterio(cultura: str):
    criterio_id = resolver_criterio_id(cultura, _contexto(cultura), _DADOS)
    return next(c for c in _DADOS["criterios_calagem"]["criterios"] if c["id"] == criterio_id)


def _culturas_em_que_as_duas_existem():
    """Culturas do ramo (b) — sem pH de referência — que também têm critério de calagem
    por saturação de bases. É o conjunto que o CCAE manda comparar."""
    culturas = []
    for cultura in sorted(_DADOS["mapa_culturas"]["culturas"]):
        try:
            referencia = _resolver_ph_referencia(
                cultura, _DADOS["ph_referencia"], _nomes_candidatos(cultura, _DADOS)
            )
        except Exception:
            continue
        if referencia is not None:
            continue
        try:
            criterio = _criterio(cultura)
        except Exception:
            continue
        notas = " ".join(criterio.get("notas", [])).lower()
        if criterio["dose"]["tipo"] == "saturacao_bases" and "fora do escopo" not in notas:
            culturas.append(cultura)
    return culturas


_RAMO_B = _culturas_em_que_as_duas_existem()

_V = (0.0, 12.5, 30.0, 39.0, 39.5, 39.9, 39.99, 40.0, 40.01, 55.0, 90.0)
_CTC = (0.5, 4.0, 10.3, 30.0, 55.0)


def test_o_conjunto_comparado_nao_esta_vazio():
    """Um filtro que esvaziasse a lista faria todos os testes abaixo passarem sem comparar
    nada."""
    assert "erva-mate" in _RAMO_B
    assert len(_RAMO_B) >= 2


@pytest.mark.parametrize("cultura", _RAMO_B)
def test_os_dois_modulos_leem_os_mesmos_parametros(cultura):
    """Mesma fórmula com parâmetros diferentes seria a divergência mais silenciosa de todas."""
    criterio = _criterio(cultura)

    assert criterio["dose"]["v_alvo"] == _SEM["v_minimo"]
    assert criterio["decisao"]["v"] == _SEM["v_minimo"]
    condicoes = {c["campo"]: c["valor"] for c in criterio["decisao"]["nao_aplicar_se"]["condicoes"]}
    assert condicoes == {"ca": _SEM["excecao_ca_minimo"], "mg": _SEM["excecao_mg_minimo"]}


@pytest.mark.parametrize("cultura", _RAMO_B)
@pytest.mark.parametrize("v_percent", _V)
@pytest.mark.parametrize("ctc", _CTC)
def test_a_dose_da_calagem_e_a_nc_do_f1_coincidem(cultura, v_percent, ctc):
    analise = AnaliseSolo(
        ph_agua=5.0, indice_smp=5.5, argila=30, mo=3.0, p=12.0, k=80,
        ctc_ph7=ctc, al=0.2, ca=3.0, mg=0.8, v_percent=v_percent,
    )

    dose_calagem = calcular_calagem(analise, _criterio(cultura)["id"], _contexto(cultura), Trace())["nc_t_ha"]
    nc_f1 = necessidade_de_calcario_ramo_b(v_percent, ctc, _SEM["v_minimo"])

    esperado = _arredondar(nc_f1, 1) if nc_f1 > 0 else 0.0
    assert dose_calagem == esperado, (
        f"{cultura}: V% {v_percent}, CTC {ctc} -> calagem {dose_calagem}, NC do F1 {nc_f1}"
    )
