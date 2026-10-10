"""
Escolha do adubo formulado (siras/motor/formulacao.py), método do Manual §8.3, p. 311.

O teste mais importante deste arquivo é `TestExemploDoManual`: o Manual publica uma
recomendação e as doses das três fórmulas que a atendem, e essas doses são oráculo
externo — não foram calculadas por nós. Se o motor as reproduz, o método está portado
certo.

Os teores usados nos demais testes são de fórmulas fictícias, montadas para exercitar
âncora, falta, sobra e desempate. Não são catálogo de mercado nem transcrição do Manual,
e nenhum valor daqui pode migrar para dados/mercado/formulas_npk.json.
"""

import pytest

from siras.conhecimento.carregador import carregar_formulas_npk
from siras.dominio.laudo import RecomendacaoAdubacao
from siras.motor.formulacao import escolher_ancora, indicar_formulacao
from siras.motor.trace import Trace

_SIMPLES = [
    {"id": "ureia", "n": 45, "p2o5": 0, "k2o": 0, "uso": ["cobertura_n"]},
    {"id": "superfosfato_triplo", "n": 0, "p2o5": 41, "k2o": 0, "uso": ["complemento_p"]},
    {"id": "cloreto_de_potassio", "n": 0, "p2o5": 0, "k2o": 58, "uso": ["complemento_k"]},
]


def formula(id_, n, p, k, uso=("plantio",)):
    return {"id": id_, "n": n, "p2o5": p, "k2o": k, "uso": list(uso),
            "fontes": ["teste"], "origem": "composicao_ilustrativa"}


def catalogo(*formulas):
    return {
        "fontes": {"teste": "fórmula fictícia de teste"},
        "fertilizantes_simples": {"_fonte": "teste", "itens": _SIMPLES},
        "formulas": {"itens": list(formulas)},
    }


def adubacao(n=0.0, p2o5=0.0, k2o=0.0, classe_p="muito_baixo", classe_k="alto"):
    return RecomendacaoAdubacao(
        n=n, p2o5=p2o5, k2o=k2o, classe_p=classe_p, classe_k=classe_k
    )


class TestExemploDoManual:
    """Oráculo externo: Manual §8.3, p. 311.

    Para a recomendação de plantio 10-120-80, o Manual publica três fórmulas adequadas e
    a dose de cada uma: 02-18-12 a 667 kg/ha, 02-24-16 a 500 e 03-30-20 a 400. São as
    três um múltiplo da proporção 1:12:8, e o Manual as apresenta já calculadas.
    """

    RECOMENDACAO = dict(n=10, p2o5=120, k2o=80, classe_p="muito_baixo", classe_k="medio")

    @pytest.mark.parametrize(
        "formula_id, teores, dose_do_manual",
        [("02-18-12", (2, 18, 12), 667), ("02-24-16", (2, 24, 16), 500),
         ("03-30-20", (3, 30, 20), 400)],
    )
    def test_reproduz_a_dose_que_o_manual_publica(self, formula_id, teores, dose_do_manual):
        r = indicar_formulacao(
            adubacao(**self.RECOMENDACAO), catalogo(formula(formula_id, *teores))
        )

        assert round(r.indicada.dose_kg_ha) == dose_do_manual

    def test_as_tres_do_manual_atendem_p_e_k_exatamente(self):
        # São múltiplos da proporção da recomendação: nenhuma deixa falta nem sobra.
        r = indicar_formulacao(
            adubacao(**self.RECOMENDACAO),
            catalogo(formula("02-18-12", 2, 18, 12), formula("02-24-16", 2, 24, 16),
                     formula("03-30-20", 3, 30, 20)),
        )

        for opcao in r.ranking:
            assert opcao.falta_p2o5 == pytest.approx(0.0, abs=1e-9)
            assert opcao.falta_k2o == pytest.approx(0.0, abs=1e-9)
            assert opcao.excesso_p2o5 == pytest.approx(0.0, abs=1e-9)
            assert opcao.excesso_k2o == pytest.approx(0.0, abs=1e-9)

    def test_vence_a_que_tambem_acerta_o_n(self):
        # Entre as três, só a 02-24-16 entrega exatamente os 10 kg/ha de N recomendados:
        # 500 x 2% = 10. As outras duas sobram N, e é isso que o desvio captura.
        r = indicar_formulacao(
            adubacao(**self.RECOMENDACAO),
            catalogo(formula("02-18-12", 2, 18, 12), formula("02-24-16", 2, 24, 16),
                     formula("03-30-20", 3, 30, 20)),
        )

        assert r.indicada.id == "02-24-16"
        assert r.indicada.desvio_relativo == pytest.approx(0.0, abs=1e-9)
        assert r.indicada.n_cobertura == pytest.approx(0.0, abs=1e-9)


class TestAncora:
    def test_ancora_no_nutriente_de_classe_mais_baixa(self):
        # P muito baixo e K alto: a dose se ancora no P, que é atendido exatamente.
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=40, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("10-20-20", 10, 20, 20)),
        )

        assert r.indicada.ancora == "p2o5"
        assert r.indicada.entrega_p2o5 == pytest.approx(100.0)
        assert r.indicada.dose_kg_ha == pytest.approx(500.0)

    def test_ancora_no_k_quando_e_o_mais_deficiente(self):
        r = indicar_formulacao(
            adubacao(p2o5=40, k2o=100, classe_p="alto", classe_k="muito_baixo"),
            catalogo(formula("10-20-20", 10, 20, 20)),
        )

        assert r.indicada.ancora == "k2o"
        assert r.indicada.entrega_k2o == pytest.approx(100.0)

    def test_empate_de_classe_ancora_na_maior_dose(self):
        # Decisão do autor (ADR 0008): o Manual não trata o empate.
        ancora, fallback = escolher_ancora(60, 90, "medio", "medio")

        assert ancora == "k2o" and fallback is False

    def test_classe_ausente_cai_no_fallback_e_declara(self):
        # Fases de frutífera que não dosam por classe. Ancora pela maior dose, e diz que
        # ancorou assim — a alternativa seria afirmar uma deficiência que não se sabe.
        ancora, fallback = escolher_ancora(60, 90, None, None)

        assert ancora == "k2o" and fallback is True

    def test_nutriente_com_dose_zero_nao_disputa_a_ancora(self):
        ancora, _ = escolher_ancora(80, 0, "alto", "muito_baixo")

        assert ancora == "p2o5"


class TestFaltaSobraEComplemento:
    def test_o_outro_nutriente_falta_e_vira_complemento(self):
        # Fórmula pobre em K frente à recomendação: o K fica devendo e sai como KCl.
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=100, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("00-20-10", 0, 20, 10)),
        )

        assert r.indicada.dose_kg_ha == pytest.approx(500.0)
        assert r.indicada.falta_k2o == pytest.approx(50.0)
        kcl = next(c for c in r.indicada.complementos if c.nutriente == "k2o")
        assert kcl.produto == "cloreto_de_potassio"
        assert kcl.dose_kg_ha == pytest.approx(50.0 * 100 / 58)

    def test_o_outro_nutriente_sobra_e_fica_declarado(self):
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=50, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("00-20-20", 0, 20, 20)),
        )

        assert r.indicada.excesso_k2o == pytest.approx(50.0)
        assert r.indicada.falta_k2o == pytest.approx(0.0)

    def test_o_n_que_falta_vai_para_cobertura_com_ureia(self):
        r = indicar_formulacao(
            adubacao(n=90, p2o5=100, k2o=100, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("02-20-20", 2, 20, 20)),
        )

        # 500 kg/ha x 2% = 10 kg de N; faltam 80 para os 90 recomendados.
        assert r.indicada.n_cobertura == pytest.approx(80.0)
        ureia = next(c for c in r.indicada.complementos if c.momento == "cobertura")
        assert ureia.dose_kg_ha == pytest.approx(80.0 * 100 / 45)

    def test_falta_irrisoria_nao_vira_operacao_de_campo(self):
        # Abaixo de 0,5 kg/ha não compensa uma passada de máquina (ADR 0008).
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=100.4, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("00-20-20", 0, 20, 20)),
        )

        assert r.indicada.complementos == []


class TestLeguminosa:
    def test_n_da_formula_conta_como_excesso_quando_a_cultura_nao_recebe_n(self):
        # Soja: n = 0 por fixação biológica. Todo N da fórmula é adubo pago sem função.
        r = indicar_formulacao(
            adubacao(n=0, p2o5=100, k2o=100, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("10-20-20", 10, 20, 20)),
        )

        assert r.indicada.excesso_n == pytest.approx(50.0)
        assert r.indicada.n_cobertura == pytest.approx(0.0)

    def test_entre_duas_iguais_em_p_e_k_vence_a_de_menos_n(self):
        r = indicar_formulacao(
            adubacao(n=0, p2o5=100, k2o=100, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("10-20-20", 10, 20, 20), formula("02-20-20", 2, 20, 20)),
        )

        assert r.indicada.id == "02-20-20"


class TestOrdenacao:
    def test_vence_a_de_menor_desvio(self):
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=100, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("00-20-20", 0, 20, 20), formula("00-20-05", 0, 20, 5)),
        )

        assert r.indicada.id == "00-20-20"
        assert [o.id for o in r.ranking] == ["00-20-20", "00-20-05"]

    def test_empate_de_desvio_desfaz_pela_formula_mais_concentrada(self):
        # Mesma proporção, concentrações diferentes: as duas acertam P e K, e vence a que
        # exige menos massa — menos frete e menos embalagem (Manual, p. 310).
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=100, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("00-10-10", 0, 10, 10), formula("00-25-25", 0, 25, 25)),
        )

        assert r.indicada.id == "00-25-25"
        assert r.indicada.dose_kg_ha < 500

    def test_ordem_e_deterministica_quando_tudo_empata(self):
        direta = indicar_formulacao(
            adubacao(p2o5=100, k2o=100),
            catalogo(formula("00-20-20", 0, 20, 20), formula("00-20-20", 0, 20, 20)),
        )
        assert direta.indicada.id == "00-20-20"

    def test_dose_nao_vem_arredondada_do_motor(self):
        # 70 / 0,18 = 388,88... Arredondar aqui repetiria o defeito B-8 do CCAE: um valor
        # arredondado cedo passando a decidir uma comparação.
        r = indicar_formulacao(
            adubacao(p2o5=70, k2o=0, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("00-18-00", 0, 18, 0)),
        )

        assert r.indicada.dose_kg_ha == pytest.approx(388.888, abs=1e-3)


class TestSemIndicacao:
    def test_catalogo_vazio_nao_e_erro(self):
        r = indicar_formulacao(adubacao(p2o5=90, k2o=60), catalogo())

        assert r.indicada is None
        assert "vazio" in r.motivo_sem_indicacao
        assert r.ranking == []

    def test_sem_dose_de_p_nem_de_k_nao_ha_o_que_ancorar(self):
        r = indicar_formulacao(
            adubacao(n=40, p2o5=0, k2o=0), catalogo(formula("10-20-20", 10, 20, 20))
        )

        assert r.indicada is None
        assert "ancora" in r.motivo_sem_indicacao

    def test_dose_publicada_como_teto_fica_fora_da_conta(self):
        # Formato do ADR 0004: o Manual publica "<= manutenção" em vez de um número.
        teto = {"valor": 60, "qualificador": "ate"}
        r = indicar_formulacao(
            RecomendacaoAdubacao(n=0, p2o5=teto, k2o=teto),
            catalogo(formula("10-20-20", 10, 20, 20)),
        )

        assert r.indicada is None

    def test_formula_sem_o_nutriente_ancora_fica_fora_do_ranking(self):
        # Ancorar no outro nutriente mudaria o método no meio da comparação.
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=40, classe_p="muito_baixo", classe_k="alto"),
            catalogo(formula("20-00-20", 20, 0, 20), formula("00-20-20", 0, 20, 20)),
        )

        assert [o.id for o in r.ranking] == ["00-20-20"]

    def test_nenhuma_formula_do_uso_pedido(self):
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=100),
            catalogo(formula("00-20-20", 0, 20, 20, uso=("cobertura",))),
        )

        assert r.indicada is None
        assert "plantio" in r.motivo_sem_indicacao


class TestTrace:
    def test_registra_um_passo_dizendo_metodo_e_catalogo(self):
        trace = Trace()
        indicar_formulacao(
            adubacao(p2o5=100, k2o=100), catalogo(formula("00-20-20", 0, 20, 20)), trace
        )

        passos = [p for p in trace if p.regra.startswith("R-FOR-01")]
        assert len(passos) == 1
        # A trilha precisa separar as duas procedências numa frase só.
        assert "p. 311" in passos[0].fonte
        assert "não é fonte do Manual" in passos[0].fonte

    def test_registra_tambem_quando_nao_ha_indicacao(self):
        trace = Trace()
        indicar_formulacao(adubacao(p2o5=90), catalogo(), trace)

        passos = [p for p in trace if p.regra.startswith("R-FOR-01")]
        assert len(passos) == 1
        assert passos[0].saida["indicada"] is None


class TestCatalogoReal:
    def test_o_catalogo_real_atende_o_exemplo_do_manual(self):
        # Integração com o arquivo de verdade: as três fórmulas do Manual estão nele, e a
        # 08-30-20, citada por produtores do RS/PR/MS, tem a mesma proporção 3:2 e por
        # isso também atende P e K exatamente. Achar a fórmula real de mercado que o
        # Manual não cita é o que o catálogo acrescenta ao método.
        r = indicar_formulacao(
            adubacao(n=10, p2o5=120, k2o=80, classe_p="muito_baixo", classe_k="medio"),
            carregar_formulas_npk(),
        )

        exatas = {
            o.id for o in r.ranking
            if o.falta_p2o5 < 0.01 and o.falta_k2o < 0.01
            and o.excesso_p2o5 < 0.01 and o.excesso_k2o < 0.01
        }
        assert {"02-18-12", "02-24-16", "03-30-20", "08-30-20"} <= exatas

    def test_toda_formula_do_catalogo_real_cita_fonte_existente(self):
        catalogo_real = carregar_formulas_npk()
        chaves = set(catalogo_real["fontes"])

        for f in catalogo_real["formulas"]["itens"]:
            assert f["fontes"], f"{f['id']} sem fonte"
            assert set(f["fontes"]) <= chaves, f"{f['id']} cita fonte inexistente"
