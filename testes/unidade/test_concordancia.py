"""
Apuração da concordância (siras/validacao/concordancia.py).

Este arquivo guarda o número que vai à monografia. A tabela de Resultados é gerada por
`scripts/gera_tabela_concordancia.py`, que usa este mesmo módulo — então o que a suíte
verifica aqui é literalmente o que o artigo publica.

Dois tipos de teste: a aritmética do intervalo de Wilson, contra valores conhecidos; e a
apuração sobre o conjunto real, incluindo a detecção de discordância, que é o que de
fato importa — um apurador que nunca reprova não mede nada.
"""

import pytest

from siras.validacao.concordancia import (
    _grupo_da_cultura,
    apurar_aptidao,
    apurar_caso,
    apurar_recomendacao,
    campos_nao_lidos,
    carregar_casos,
    wilson,
)
from siras.conhecimento.carregador import carregar_dados_comum


class TestWilson:
    def test_sem_casos_nao_ha_intervalo(self):
        assert wilson(0, 0) is None

    def test_nunca_sai_do_intervalo_unitario(self):
        # É por isto que o protocolo manda usar Wilson e não o intervalo normal: com
        # proporção 1, o normal devolveria limite superior acima de 1.
        for n in range(1, 60):
            inferior, superior = wilson(n, n)
            assert 0.0 <= inferior <= superior <= 1.0

    def test_cresce_com_o_tamanho_da_amostra(self):
        # Mais casos com o mesmo acerto = mais confiança, logo limite inferior maior.
        assert wilson(10, 10)[0] < wilson(20, 20)[0] < wilson(40, 40)[0]

    def test_quinze_acertos_nao_alcancam_o_limiar_de_oitenta(self):
        """O achado que decide o tamanho mínimo do conjunto.

        A H1.1 declara concordância >= 80%. Com 15 casos e 100% de acerto, o limite
        inferior do IC 95% fica em 79,6% — abaixo do limiar. Com 16 casos passa a 80,6%.
        Este teste existe para que ninguém escreva no texto que 15 casos sustentam a
        hipótese sem antes tropeçar aqui.
        """
        assert wilson(15, 15)[0] < 0.80
        assert wilson(16, 16)[0] >= 0.80

    def test_metade_dos_casos_da_intervalo_centrado_perto_de_meio(self):
        inferior, superior = wilson(50, 100)
        assert inferior < 0.5 < superior


class TestApuracaoDaRecomendacao:
    def test_o_conjunto_atual_esta_integralmente_concordante(self):
        apuracao = apurar_recomendacao()

        assert apuracao.total > 0
        assert apuracao.discordantes == [], [
            (r.id, r.erro, [(d.campo, d.esperado, d.obtido) for d in r.divergencias])
            for r in apuracao.discordantes
        ]
        assert apuracao.taxa() == 1.0

    def test_todo_caso_cai_num_grupo_conhecido(self):
        # Grupo "?" significa cultura fora de mapa_culturas.json: o caso entraria na
        # taxa global sem entrar em grupo nenhum, e a soma por grupo não fecharia.
        apuracao = apurar_recomendacao()

        assert all(r.grupo != "?" for r in apuracao.resultados)
        soma = sum(p.total for p in apuracao.por_grupo().values())
        assert soma == apuracao.total

    def test_o_conjunto_atual_sustenta_a_H1_1(self):
        """Fecha a pendência P9: o conjunto tinha 15 casos e o limite inferior do IC 95%
        caía em 79,6%, abaixo dos 80% que a H1.1 declara. Os casos ADU-20 a ADU-28 e
        CAL-12 (2026-10-10) levaram o conjunto a 25, e o limite inferior a 86,7%.

        O teste é sobre o TAMANHO, não sobre a taxa: se alguém remover casos e voltar
        abaixo do limiar, o artigo não pode continuar afirmando a hipótese.
        """
        apuracao = apurar_recomendacao()
        inferior, _ = apuracao.intervalo()
        assert inferior >= 0.80, (
            f"{apuracao.concordantes}/{apuracao.total} dá limite inferior {inferior:.3f}: "
            f"abaixo de 0,80, a H1.1 não se sustenta com este conjunto"
        )

    def test_nenhum_caso_carrega_campo_que_o_motor_ignora(self):
        """Regressão do ADU-23 (ver campos_nao_lidos() em concordancia.py).

        Um caso que declara exercitar a expectativa de rendimento, mas escreve o campo
        com o nome de outro grupo, passa sem exercitar nada — e o 100% de concordância
        passa a incluir um caso vazio.
        """
        dados = carregar_dados_comum()
        sobras = {}
        for caso in carregar_casos():
            grupo = _grupo_da_cultura(caso["entrada"]["cultura"], dados)
            ignorados = campos_nao_lidos(caso["entrada"], grupo)
            if ignorados:
                sobras[caso["id"]] = (grupo, ignorados)
        assert sobras == {}, sobras

    def test_detecta_divergencia(self):
        """Um apurador que nunca reprova não mede nada."""
        dados = carregar_dados_comum()
        caso = {
            "id": "FALSO-01",
            "descricao": "caso adulterado para verificar que o apurador reprova",
            "entrada": {
                "cultura": "soja", "sistema_manejo": "convencional",
                "ph_agua": 5.1, "indice_smp": 5.4, "argila": 45, "mo": 3.2,
                "ctc_ph7": 9.5, "v_percent": 50, "saturacao_al": 15,
                "prnt": 75, "profundidade_incorporacao_cm": 20,
            },
            # O CAL-02 tem referência 2,3 t/ha; aqui se pede 9,9 de propósito.
            "referencia": {"nc_t_ha": 9.9},
        }
        # O id precisa estar no mapa de critérios para o caso ser executável.
        from siras.validacao import concordancia
        concordancia.CRITERIO_POR_CASO["FALSO-01"] = "graos_pd_consolidado"
        try:
            resultado = apurar_caso(caso, dados)
        finally:
            del concordancia.CRITERIO_POR_CASO["FALSO-01"]

        assert resultado.concordante is False
        assert [d.campo for d in resultado.divergencias] == ["nc_t_ha"]
        # O protocolo exige analisar o discordante com o Trace; sem ele, a análise seria
        # "deu diferente" e nada mais.
        assert resultado.trace

    def test_tolerancia_de_arredondamento_nao_inventa_discordancia(self):
        dados = carregar_dados_comum()
        caso = {
            "id": "CAL-02", "descricao": "mesma entrada do CAL-02",
            "entrada": {
                "cultura": "soja", "sistema_manejo": "plantio_direto_consolidado",
                "condicao_area": "sem_restricoes",
                "ph_agua": 5.1, "indice_smp": 5.4, "argila": 45, "mo": 3.2,
                "ctc_ph7": 9.5, "v_percent": 50, "saturacao_al": 15,
                "prnt": 75, "profundidade_incorporacao_cm": 20,
            },
            "referencia": {"nc_t_ha": 2.3},
        }

        assert apurar_caso(caso, dados).concordante is True


class TestApuracaoDaAptidao:
    def test_conformidade_integral_em_classe_e_em_fator(self):
        apuracao = apurar_aptidao()

        assert apuracao.total > 0
        assert apuracao.divergentes == [], apuracao.divergentes
        assert apuracao.taxa_classe() == 1.0
        assert apuracao.taxa_fator() == 1.0

    def test_o_conjunto_da_aptidao_e_maior_que_o_da_recomendacao(self):
        # Registro de uma assimetria real do trabalho, e não um capricho: a evidência da
        # aptidão é muito mais robusta que a da recomendação, e o artigo precisa dizer
        # isso em vez de apresentar os dois "100%" como se pesassem igual.
        assert apurar_aptidao().total > apurar_recomendacao().total
