"""
Formulação do adubo (siras/motor/formulacao.py) — casos T1 a T17 da ADR 0009.

O caso mais importante é o T11: o Manual publica, na p. 311, uma recomendação e as doses
das três fórmulas que a atendem. Esses números são **oráculo externo** — não foram
calculados por nós. Se o motor os reproduz, o método está portado certo.

Os T8, T9 e T15 são testes de PROPRIEDADE sobre uma grade de recomendações, e não casos
pontuais. São eles que sustentam a afirmação central da ADR 0009: avaliar os dois pontos
de quebra nunca é pior do que escolher um deles de antemão. Usam
`pytest.mark.parametrize` e não `hypothesis`, porque o CLAUDE.md restringe dependências.

O T3 vive em arquivo separado (`test_selecao_formula_t3.py`), por ter sido escrito antes
do código.

Os teores usados aqui são de fórmulas fictícias, montadas para exercitar a regra. Não são
catálogo de mercado nem transcrição do Manual, e nenhum valor daqui pode migrar para
dados/mercado/formulas_npk.json.
"""

import pytest

from siras.conhecimento.carregador import carregar_formulas_npk
from siras.dominio.laudo import RecomendacaoAdubacao
from siras.motor.formulacao import (
    ErroFormulacao,
    W_EXC,
    W_FALTA,
    W_OP,
    formula_ideal,
    interpretar_formula_do_usuario,
    mistura_simples,
    recomendar_formulacao,
)

_SIMPLES = [
    {"id": "ureia", "n": 45, "p2o5": 0, "k2o": 0, "uso": ["cobertura_n"]},
    {"id": "superfosfato_triplo", "n": 0, "p2o5": 41, "k2o": 0, "uso": ["complemento_p"]},
    {"id": "cloreto_de_potassio", "n": 0, "p2o5": 0, "k2o": 58, "uso": ["complemento_k"]},
]
_MAPA_SIMPLES = {s["id"]: s for s in _SIMPLES}


def formula(id_, n, p, k, uso=("plantio",), evidencia="nenhuma"):
    return {"id": id_, "n": n, "p2o5": p, "k2o": k, "uso": list(uso),
            "fontes": ["teste"], "evidencia_comercial": evidencia}


#: Os quatro níveis, como o catálogo real os descreve. O carregador exige que todo
#: nível usado esteja descrito aqui.
_EVIDENCIA = {
    "forte": "fabricante identificado ou compra pública",
    "media": "citada por fonte técnica",
    "fraca": "só anúncio de revenda",
    "nenhuma": "exemplo de cálculo, sem prova de venda",
    "regra": "o nível é o mais alto entre as fontes da fórmula",
}


def catalogo(*formulas):
    return {
        "fontes": {"teste": "fórmula fictícia de teste"},
        "fertilizantes_simples": {"_fonte": "teste", "itens": _SIMPLES},
        "formulas": {"_evidencia": _EVIDENCIA, "itens": list(formulas)},
    }


def rec(n=0.0, p2o5=0.0, k2o=0.0):
    return RecomendacaoAdubacao(
        n=n, p2o5=p2o5, k2o=k2o, classe_p="muito_baixo", classe_k="muito_baixo"
    )


def por_id(resultado, formula_id):
    return next(o for o in resultado.catalogo if o.formula_id == formula_id)


def dose_de(opcao, produto):
    return next(c.dose_kg_ha for c in opcao.complementos if c.produto == produto)


# --- T1, T2: o exemplo do Manual, pelo catálogo --------------------------------------

_MANUAL = dict(n=60, p2o5=120, k2o=80)
_N_PLANTIO_DO_MANUAL = 10


class TestExemploDoManualPeloCatalogo:
    """Oráculo externo: Manual, §8.3, p. 311 — recomendação de plantio 10-120-80.

    As três fórmulas que o Manual lista são múltiplas da proporção 1:12:8 e, por isso,
    atendem P e K exatamente. A 08-30-20, do levantamento de fórmulas usadas por
    produtores do Sul, tem a mesma proporção 3:2 e também zera o custo — é a fórmula real
    de mercado que o Manual não cita.
    """

    CATALOGO = catalogo(
        formula("02-18-12", 2, 18, 12), formula("02-24-16", 2, 24, 16),
        formula("03-30-20", 3, 30, 20), formula("08-30-20", 8, 30, 20),
    )

    @pytest.mark.parametrize(
        "formula_id, dose_do_manual",
        [("02-18-12", 667), ("02-24-16", 500), ("03-30-20", 400), ("08-30-20", 400)],
    )
    def test_t1_custo_zero_e_a_dose_que_o_manual_publica(self, formula_id, dose_do_manual):
        r = recomendar_formulacao(rec(**_MANUAL), self.CATALOGO,
                                  n_plantio=_N_PLANTIO_DO_MANUAL)
        # Todas as quatro entram no catálogo (top 3 cortaria uma), então avalio direto.
        opcao = next(
            o for o in recomendar_formulacao(
                rec(**_MANUAL), catalogo(next(
                    f for f in self.CATALOGO["formulas"]["itens"] if f["id"] == formula_id
                )), n_plantio=_N_PLANTIO_DO_MANUAL
            ).catalogo
        )

        assert opcao.custo == pytest.approx(0.0)
        assert round(opcao.dose_kg_ha) == dose_do_manual
        assert r.catalogo, "o catálogo completo também precisa devolver opções"

    def test_t2_o_n_restante_vira_ureia_em_cobertura(self):
        r = recomendar_formulacao(
            rec(**_MANUAL), catalogo(formula("03-30-20", 3, 30, 20)),
            n_plantio=_N_PLANTIO_DO_MANUAL,
        )
        opcao = por_id(r, "03-30-20")

        # 400 kg/ha x 3% = 12 kg de N; faltam 48 dos 60 totais; 48 / 0,45 = 107.
        assert opcao.fornecido["n"] == pytest.approx(12.0)
        assert round(dose_de(opcao, "ureia")) == 107


# --- T4, T6: mistura de simples --------------------------------------------------------

class TestMisturaDeSimples:
    def test_t4_doses_exatas_de_tsp_e_kcl(self):
        r = recomendar_formulacao(rec(n=0, p2o5=60, k2o=60), catalogo())

        assert round(dose_de(r.mistura, "superfosfato_triplo")) == 146
        assert round(dose_de(r.mistura, "cloreto_de_potassio")) == 103
        assert all(c.produto != "ureia" for c in r.mistura.complementos)

    def test_t6_so_n_resolve_com_ureia_e_nao_ha_formula_a_indicar(self):
        r = recomendar_formulacao(rec(n=60, p2o5=0, k2o=0),
                                  catalogo(formula("10-20-20", 10, 20, 20)))

        assert r.catalogo == []
        assert r.ideais == []
        assert round(dose_de(r.mistura, "ureia")) == 133
        assert "dose numérica" in r.motivo_sem_indicacao

    def test_a_mistura_atende_exatamente_e_por_isso_custa_zero(self):
        r = recomendar_formulacao(rec(n=40, p2o5=60, k2o=60), catalogo())

        assert r.mistura.custo == 0.0
        assert all(v == 0.0 for v in r.mistura.excesso.values())
        assert all(v == 0.0 for v in r.mistura.falta.values())


# --- T5, T7: casos de borda da recomendação -------------------------------------------

def test_t5_leguminosa_penaliza_toda_formula_com_nitrogenio():
    # Soja: n_total = 0 por fixação biológica, e todo N da fórmula é adubo sem função.
    r = recomendar_formulacao(
        rec(n=0, p2o5=60, k2o=60),
        catalogo(formula("10-20-20", 10, 20, 20), formula("02-20-20", 2, 20, 20),
                 formula("00-20-20", 0, 20, 20)),
    )

    for opcao in r.catalogo:
        tem_n = opcao.teores["n"] > 0
        assert (opcao.excesso["n"] > 0) is tem_n
    # E a sem nitrogênio vence, porque é a única que não desperdiça nada.
    assert r.catalogo[0].formula_id == "00-20-20"


def test_t7_sem_fosforo_recomendado_a_ancora_e_sempre_o_potassio():
    r = recomendar_formulacao(
        rec(n=60, p2o5=0, k2o=80),
        catalogo(formula("10-20-20", 10, 20, 20), formula("00-00-60", 0, 0, 60)),
    )

    for opcao in r.catalogo:
        assert opcao.ancora == "k2o"
        assert (opcao.excesso["p2o5"] > 0) is (opcao.teores["p2o5"] > 0)


# --- T8, T9: propriedades sobre grade --------------------------------------------------

_GRADE = [
    (n, p, k)
    for n in (0, 60)
    for p in (0, 30, 60, 90, 120, 150, 180)
    for k in (0, 30, 60, 90, 120, 150, 180)
    if p > 0 or k > 0
]

_FORMULAS_DA_GRADE = (
    formula("05-20-20", 5, 20, 20), formula("10-15-15", 10, 15, 15),
    formula("02-24-16", 2, 24, 16), formula("08-30-20", 8, 30, 20),
    formula("00-20-05", 0, 20, 5), formula("20-05-20", 20, 5, 20),
)


def _custo_manual(teores, recomendacao, nutriente):
    """Custo da dose que atende exatamente um nutriente — a regra literal do Manual."""
    if recomendacao[nutriente] <= 0 or teores[nutriente] <= 0:
        return None
    dose = recomendacao[nutriente] * 100.0 / teores[nutriente]
    fornecido = {i: dose * teores[i] / 100.0 for i in ("n", "p2o5", "k2o")}
    excesso = sum(max(0.0, fornecido[i] - recomendacao[i]) for i in ("n", "p2o5", "k2o"))
    faltas = {i: max(0.0, recomendacao[i] - fornecido[i]) for i in ("p2o5", "k2o")}
    operacoes = sum(1 for v in faltas.values() if v > 0.5)
    return W_EXC * excesso + W_FALTA * sum(faltas.values()) + W_OP * operacoes


@pytest.mark.parametrize("n, p, k", _GRADE, ids=lambda v: str(v))
def test_t8_o_otimo_nunca_e_pior_que_qualquer_ponto_de_quebra(n, p, k):
    """A afirmação central da ADR 0009, verificada em vez de argumentada.

    A regra do Manual — ancorar num nutriente escolhido de antemão — produz um dos dois
    pontos de quebra. Avaliar os dois e ficar com o melhor, portanto, nunca é pior.
    """
    recomendacao = {"n": float(n), "p2o5": float(p), "k2o": float(k)}
    r = recomendar_formulacao(rec(n=n, p2o5=p, k2o=k), catalogo(*_FORMULAS_DA_GRADE))

    for opcao in r.catalogo:
        for nutriente in ("p2o5", "k2o"):
            referencia = _custo_manual(opcao.teores, recomendacao, nutriente)
            if referencia is not None:
                assert opcao.custo <= referencia + 1e-9, (
                    f"{opcao.formula_id}: ótimo {opcao.custo:.3f} pior que a âncora "
                    f"em {nutriente} ({referencia:.3f})"
                )


@pytest.mark.parametrize("n, p, k", _GRADE, ids=lambda v: str(v))
def test_t9_formula_mais_complementos_nunca_deixam_faltar_p_nem_k(n, p, k):
    r = recomendar_formulacao(rec(n=n, p2o5=p, k2o=k), catalogo(*_FORMULAS_DA_GRADE))

    for opcao in r.catalogo:
        for nutriente, produto, teor in (
            ("p2o5", "superfosfato_triplo", 41), ("k2o", "cloreto_de_potassio", 58)
        ):
            entregue = opcao.fornecido[nutriente] + sum(
                c.dose_kg_ha * teor / 100.0
                for c in opcao.complementos if c.produto == produto
            )
            # A tolerância é a do próprio corte: falta abaixo de 0,5 kg/ha não vira
            # operação de campo, por decisão declarada.
            assert entregue >= float({"p2o5": p, "k2o": k}[nutriente]) - 0.5


@pytest.mark.parametrize("n, p, k", _GRADE[::7], ids=lambda v: str(v))
def test_t15_toda_formula_ideal_atende_o_minimo_legal(n, p, k):
    """A soma das garantias é >= T por construção, e o menor T é 18 (IN 39/2018)."""
    recomendacao = {"n": float(n), "p2o5": float(p), "k2o": float(k)}
    for opcao in formula_ideal(recomendacao, float(n) / 2, _MAPA_SIMPLES):
        soma = sum(opcao.teores.values())
        ternaria = all(v > 0 for v in opcao.teores.values())
        assert soma >= (18 if ternaria else 15), f"{opcao.formula_id} soma {soma}"


# --- T10: determinismo ------------------------------------------------------------------

def test_t10_mesma_entrada_produz_mesma_saida_e_mesma_ordem():
    entrada = rec(n=90, p2o5=100, k2o=70)
    uma = recomendar_formulacao(entrada, catalogo(*_FORMULAS_DA_GRADE), n_plantio=20)
    outra = recomendar_formulacao(entrada, catalogo(*_FORMULAS_DA_GRADE), n_plantio=20)

    assert [o.formula_id for o in uma.catalogo] == [o.formula_id for o in outra.catalogo]
    assert [o.formula_id for o in uma.ideais] == [o.formula_id for o in outra.ideais]
    assert [o.custo for o in uma.catalogo] == [o.custo for o in outra.catalogo]


# --- T11, T12, T13: a fórmula ideal ------------------------------------------------------

class TestFormulaIdeal:
    def test_t11_reproduz_as_tres_formulas_e_doses_do_manual(self):
        """Oráculo externo. Só passa com o N de plantio informado — ver a ADR 0009."""
        r = recomendar_formulacao(rec(**_MANUAL), catalogo(),
                                  n_plantio=_N_PLANTIO_DO_MANUAL)

        assert [o.formula_id for o in r.ideais] == ["02-18-12", "02-24-16", "03-30-20"]
        assert [round(o.dose_kg_ha) for o in r.ideais] == [667, 500, 400]
        assert r.sem_n_de_plantio is False

    def test_sem_n_de_plantio_a_ideal_sai_binaria_e_declara(self):
        r = recomendar_formulacao(rec(**_MANUAL), catalogo())

        assert [o.formula_id for o in r.ideais] == ["00-18-12", "00-24-16", "00-30-20"]
        assert r.sem_n_de_plantio is True

    def test_t12_soja_sem_nitrogenio(self):
        r = recomendar_formulacao(rec(n=0, p2o5=90, k2o=60), catalogo(), n_plantio=0)

        assert [o.formula_id for o in r.ideais] == ["00-18-12", "00-24-16", "00-30-20"]
        assert [round(o.dose_kg_ha) for o in r.ideais] == [500, 375, 300]

    def test_t13_quando_o_potassio_e_maior_a_ancora_passa_a_ser_ele(self):
        r = recomendar_formulacao(rec(n=120, p2o5=60, k2o=120), catalogo(), n_plantio=20)

        assert [o.formula_id for o in r.ideais] == ["03-09-18", "04-12-24", "05-15-30"]
        assert [round(o.dose_kg_ha) for o in r.ideais] == [667, 500, 400]
        assert all(o.ancora == "k2o" for o in r.ideais)

    def test_a_ideal_atende_p_e_k_praticamente_na_medida(self):
        # O arredondamento das garantias ao inteiro desvia o nutriente secundário em
        # poucos kg/ha. O laudo mostra esse desvio; aqui se guarda a ordem de grandeza.
        r = recomendar_formulacao(rec(n=60, p2o5=120, k2o=80), catalogo(),
                                  n_plantio=_N_PLANTIO_DO_MANUAL)

        for opcao in r.ideais:
            assert opcao.excesso["p2o5"] + opcao.falta["p2o5"] < 1.0
            assert opcao.excesso["k2o"] + opcao.falta["k2o"] < 5.0


# --- T14: desempate por massa total -------------------------------------------------------

def test_t14_entre_custos_iguais_vence_a_de_menor_massa_total():
    """D9. As três atendem P na medida e deixam o mesmo K faltando, logo custam igual.

    O que as separa é quanto produto desce do caminhão: fórmula mais complemento mais
    ureia. 10-25-25 traz mais N, precisa de menos ureia, e por isso ganha.
    """
    r = recomendar_formulacao(
        rec(n=120, p2o5=60, k2o=120),
        catalogo(formula("04-20-20", 4, 20, 20), formula("05-25-25", 5, 25, 25),
                 formula("10-25-25", 10, 25, 25)),
    )

    assert [o.formula_id for o in r.catalogo] == ["10-25-25", "05-25-25", "04-20-20"]
    assert len({round(o.custo, 6) for o in r.catalogo}) == 1, "os três custam igual"
    assert [round(o.massa_total_kg_ha) for o in r.catalogo] == [557, 583, 643]


# --- T16, T17: fórmula informada pelo usuário ---------------------------------------------

class TestFormulaDoUsuario:
    def test_t16_a_formula_do_usuario_entra_no_ranking_e_pode_vencer(self):
        r = recomendar_formulacao(
            rec(n=0, p2o5=60, k2o=90),
            catalogo(formula("05-20-20", 5, 20, 20)),
            formulas_usuario=("00-20-30",),
        )

        primeira = r.catalogo[0]
        assert primeira.formula_id == "00-20-30"
        assert primeira.tipo == "usuario"
        assert round(primeira.dose_kg_ha) == 300
        assert primeira.custo == pytest.approx(0.0)

    def test_t17_formato_invalido_e_erro(self):
        with pytest.raises(ErroFormulacao, match="formato"):
            interpretar_formula_do_usuario("abc")

    def test_t17_soma_abaixo_do_minimo_legal_e_aviso_e_nao_erro(self):
        # Pode ser organomineral, cujo mínimo é menor — recusar seria exagero.
        entrada = interpretar_formula_do_usuario("04-05-04")

        assert entrada["id"] == "04-05-04"
        assert any("IN 39/2018" in a for a in entrada["_avisos"])

    def test_soma_acima_do_minimo_nao_gera_aviso(self):
        # "5-10-5" soma 20, acima dos 18 exigidos de uma ternária. O plano v2 listava
        # esta fórmula como exemplo de aviso; pela aritmética da IN 39/2018 ela passa.
        assert interpretar_formula_do_usuario("5-10-5")["_avisos"] == []

    def test_garantias_somando_acima_de_cem_sao_recusadas(self):
        with pytest.raises(ErroFormulacao, match="100"):
            interpretar_formula_do_usuario("50-40-30")

    def test_o_aviso_do_usuario_chega_ao_resultado(self):
        r = recomendar_formulacao(
            rec(n=0, p2o5=60, k2o=60), catalogo(), formulas_usuario=("04-05-04",)
        )

        assert any("IN 39/2018" in a for a in r.avisos)


# --- avisos fixos e trilha ------------------------------------------------------------------

def test_os_avisos_do_laudo_estao_sempre_presentes():
    r = recomendar_formulacao(rec(n=60, p2o5=60, k2o=60), catalogo())

    texto = " ".join(r.avisos)
    assert "não tem preços" in texto           # D12, critério nutricional
    assert "enxofre" in texto                  # D12, S em fórmulas concentradas
    assert "compatibilidade" in texto          # D12, mistura de simples


def test_a_trilha_registra_os_pontos_de_quebra_e_a_escolha():
    from siras.motor.trace import Trace

    trace = Trace()
    recomendar_formulacao(
        rec(n=120, p2o5=60, k2o=120), catalogo(formula("05-25-25", 5, 25, 25)), trace
    )

    quebras = [p for p in trace if p.regra.startswith("R-FOR-02")]
    assert len(quebras) == 1
    assert "05-25-25" in quebras[0].regra
    assert set(quebras[0].entradas["doses_candidatas"]) == {"p2o5", "k2o"}
    assert set(quebras[0].saida["custos"]) == {"p2o5", "k2o"}

    escolha = [p for p in trace if p.regra.startswith("R-FOR-01")]
    assert len(escolha) == 1
    assert "p. 311" in escolha[0].fonte
    assert "não é fonte do Manual" in escolha[0].fonte


# --- o catálogo real --------------------------------------------------------------------------

class TestCatalogoReal:
    def test_o_catalogo_real_resolve_o_exemplo_do_manual(self):
        r = recomendar_formulacao(
            rec(**_MANUAL), carregar_formulas_npk(), n_plantio=_N_PLANTIO_DO_MANUAL
        )

        # Cinco fórmulas do catálogo têm a proporção 3:2 e zeram o custo; o top 3
        # mostra três delas. Três são do exemplo do Manual; as outras duas são de
        # mercado — a 08-30-20, citada por produtores do Sul, e a 10-30-20, de um
        # pregão do IF Farroupilha com entregas no RS. Que o método encontre produto
        # real com a proporção exata do exemplo publicado é o argumento do catálogo.
        assert all(o.custo == pytest.approx(0.0) for o in r.catalogo)
        assert {o.formula_id for o in r.catalogo} <= {
            "02-18-12", "02-24-16", "03-30-20", "08-30-20", "10-30-20"
        }

    def test_entre_as_exatas_vence_a_que_exige_menos_massa_total(self):
        # Todas custam zero, e o desempate de D9 decide: a 10-30-20 traz mais N, precisa
        # de menos ureia em cobertura, e por isso desce menos produto do caminhão.
        r = recomendar_formulacao(
            rec(**_MANUAL), carregar_formulas_npk(), n_plantio=_N_PLANTIO_DO_MANUAL
        )

        assert r.catalogo[0].formula_id == "10-30-20"
        massas = [o.massa_total_kg_ha for o in r.catalogo]
        assert massas == sorted(massas)

    def test_a_ideal_e_a_mistura_funcionam_com_o_catalogo_real(self):
        r = recomendar_formulacao(rec(n=40, p2o5=80, k2o=50), carregar_formulas_npk())

        assert len(r.ideais) == 3
        assert r.mistura is not None
        assert len(r.catalogo) == 3
