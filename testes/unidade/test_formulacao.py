"""
Indicação do adubo formulado (siras/motor/formulacao.py).

Os teores de N, P2O5 e K2O usados aqui são **fórmulas fictícias de teste**, escolhidas
para exercitar a aritmética e o desempate — não são catálogo de mercado nem transcrição
do Manual, e nenhum valor daqui pode migrar para dados/mercado/formulacoes.json, que é
preenchido pelo autor com a fonte de cada entrada.

O que se verifica é a regra, não o número: dose pela maior cobertura entre P e K, escolha
pelo menor excesso de P2O5 + K2O, desempate pela menor falta de N.
"""

import pytest

from siras.dominio.laudo import RecomendacaoAdubacao
from siras.motor.formulacao import indicar_formulacao
from siras.motor.trace import Trace


def formulacao(id_, n, p, k):
    return {"id": id_, "rotulo": id_.upper(), "n": n, "p2o5": p, "k2o": k,
            "_fonte": "fórmula fictícia de teste"}


def catalogo(*formulacoes):
    return {"descricao": "teste", "aviso": "teste", "formulacoes": list(formulacoes)}


def adubacao(n=0.0, p2o5=0.0, k2o=0.0):
    return RecomendacaoAdubacao(n=n, p2o5=p2o5, k2o=k2o)


class TestDose:
    def test_dose_e_a_maior_entre_a_que_cobre_p_e_a_que_cobre_k(self):
        # 20% de P2O5 e 20% de K2O: 90 kg de P pedem 450 kg de produto; 60 kg de K pedem
        # 300. Vence 450 — P é atendido na medida e K sobra.
        r = indicar_formulacao(adubacao(p2o5=90, k2o=60), catalogo(formulacao("a", 5, 20, 20)))

        assert r.indicada.dose_kg_ha == pytest.approx(450.0)
        assert r.indicada.excesso_p2o5 == pytest.approx(0.0)
        assert r.indicada.excesso_k2o == pytest.approx(30.0)

    def test_nenhum_nutriente_exigido_fica_devendo(self):
        r = indicar_formulacao(adubacao(p2o5=80, k2o=100), catalogo(formulacao("a", 0, 25, 25)))

        assert r.indicada.entrega_p2o5 >= 80 - 1e-9
        assert r.indicada.entrega_k2o >= 100 - 1e-9

    def test_dose_nao_vem_arredondada_do_motor(self):
        # 70 / 0,18 = 388,88... Arredondar aqui repetiria o defeito B-8 do CCAE: um valor
        # arredondado cedo passando a decidir uma comparação.
        r = indicar_formulacao(adubacao(p2o5=70), catalogo(formulacao("a", 0, 18, 0)))

        assert r.indicada.dose_kg_ha == pytest.approx(388.888, abs=1e-3)


class TestEscolha:
    def test_vence_a_de_menor_excesso_total_de_p_e_k(self):
        # 'justa' entrega P e K exatos; 'folgada' entrega K muito acima.
        r = indicar_formulacao(
            adubacao(p2o5=100, k2o=100),
            catalogo(formulacao("folgada", 0, 10, 30), formulacao("justa", 0, 20, 20)),
        )

        assert r.indicada.id == "justa"
        assert r.ranking[0].id == "justa"
        assert r.ranking[1].id == "folgada"

    def test_empate_no_excesso_desfaz_pela_menor_falta_de_n(self):
        # Mesmos teores de P e K, logo a mesma dose e o mesmo excesso; muda só o N.
        r = indicar_formulacao(
            adubacao(n=50, p2o5=100, k2o=100),
            catalogo(formulacao("sem_n", 0, 20, 20), formulacao("com_n", 10, 20, 20)),
        )

        assert r.indicada.id == "com_n"
        assert r.indicada.falta_n == pytest.approx(0.0)

    def test_ordem_e_deterministica_quando_tudo_empata(self):
        # Sem o desempate pelo rótulo a saída dependeria da ordem do arquivo, e o laudo
        # deixaria de ser reprodutível.
        direta = indicar_formulacao(
            adubacao(p2o5=100, k2o=100),
            catalogo(formulacao("bbb", 5, 20, 20), formulacao("aaa", 5, 20, 20)),
        )
        invertida = indicar_formulacao(
            adubacao(p2o5=100, k2o=100),
            catalogo(formulacao("aaa", 5, 20, 20), formulacao("bbb", 5, 20, 20)),
        )

        assert direta.indicada.id == invertida.indicada.id == "aaa"

    def test_n_nao_entra_no_criterio_de_dose(self):
        # Rica em N, pobre em P e K: a dose sai grande e o excesso de N é declarado, mas
        # quem dimensiona continuam sendo P e K.
        r = indicar_formulacao(adubacao(n=10, p2o5=50), catalogo(formulacao("a", 30, 10, 0)))

        assert r.indicada.dose_kg_ha == pytest.approx(500.0)
        assert r.indicada.falta_n == pytest.approx(0.0)
        assert r.indicada.excesso_n == pytest.approx(140.0)


class TestNaoAtende:
    def test_formulacao_sem_o_nutriente_exigido_nao_atende(self):
        r = indicar_formulacao(adubacao(p2o5=60, k2o=60), catalogo(formulacao("so_p", 0, 20, 0)))

        assert r.indicada is None
        assert "nenhuma formulação" in r.motivo_sem_indicacao

    def test_a_que_nao_atende_continua_no_ranking_com_o_motivo(self):
        r = indicar_formulacao(
            adubacao(p2o5=60, k2o=60),
            catalogo(formulacao("so_p", 0, 20, 0), formulacao("completa", 0, 20, 20)),
        )

        assert r.indicada.id == "completa"
        fora = r.ranking[-1]
        assert fora.id == "so_p" and fora.atende is False
        assert "K2O" in fora.motivo_nao_atende
        assert fora.dose_kg_ha is None

    def test_nutriente_com_dose_zero_nao_exige_nada_da_formulacao(self):
        # K2O = 0 na recomendação: uma fórmula sem potássio atende normalmente.
        r = indicar_formulacao(adubacao(p2o5=40, k2o=0), catalogo(formulacao("so_p", 0, 20, 0)))

        assert r.indicada is not None
        assert r.indicada.dose_kg_ha == pytest.approx(200.0)


class TestSemIndicacao:
    def test_catalogo_vazio_nao_e_erro(self):
        r = indicar_formulacao(adubacao(p2o5=90, k2o=60), catalogo())

        assert r.indicada is None
        assert "vazio" in r.motivo_sem_indicacao
        assert r.ranking == []

    def test_dose_publicada_como_teto_fica_fora_da_conta(self):
        # Formato do ADR 0004: o Manual publica "<= manutenção" em vez de um número.
        # Dividir isso pela garantia de um adubo inventaria precisão.
        teto = {"valor": 60, "qualificador": "ate"}
        r = indicar_formulacao(
            RecomendacaoAdubacao(n=0, p2o5=teto, k2o=teto), catalogo(formulacao("a", 0, 20, 20))
        )

        assert r.indicada is None
        assert "dose numérica" in r.motivo_sem_indicacao

    def test_falta_de_n_fica_indefinida_quando_o_manual_nao_da_numero(self):
        r = indicar_formulacao(
            RecomendacaoAdubacao(n={"pendente": True}, p2o5=100, k2o=100),
            catalogo(formulacao("a", 5, 20, 20)),
        )

        # Dizer "falta 0 de N" afirmaria que o N está coberto; o que se sabe é que não há
        # com o que comparar.
        assert r.indicada.falta_n is None
        assert r.indicada.excesso_n is None


class TestTrace:
    def test_registra_um_passo_com_a_fonte_do_catalogo(self):
        trace = Trace()
        indicar_formulacao(adubacao(p2o5=90, k2o=60), catalogo(formulacao("a", 5, 20, 20)), trace)

        passos = [p for p in trace if p.regra.startswith("R-FOR-01")]
        assert len(passos) == 1
        # A trilha precisa dizer que este número não saiu do Manual.
        assert "não é fonte do Manual" in passos[0].fonte

    def test_registra_tambem_quando_nao_ha_indicacao(self):
        trace = Trace()
        indicar_formulacao(adubacao(p2o5=90), catalogo(), trace)

        passos = [p for p in trace if p.regra.startswith("R-FOR-01")]
        assert len(passos) == 1
        assert passos[0].saida["indicada"] is None
