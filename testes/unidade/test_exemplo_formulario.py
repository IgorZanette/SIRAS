"""
Os dez exemplos de preenchimento do formulário (siras/web/exemplo.py).

Dois tipos de guarda aqui, e os dois existem por motivos diferentes.

O primeiro é COERÊNCIA INTERNA dos perfis de solo. Eles são valores de entrada
inventados para a demonstração, mas inventados não quer dizer arbitrários: a saturação
por bases e a saturação por alumínio são deriváveis dos cátions do mesmo perfil, e um
laudo de demonstração que se contradiz é pior que nenhum — quem for conferir à mão na
banca acha a contradição antes de achar o recurso.

O segundo é COBERTURA. Sete perfis só se justificam se percorrerem caminhos diferentes
do motor; se dois caírem na mesma classe de tudo, um deles é redundante e o conjunto
promete mais do que entrega.

Estes testes NÃO verificam dose: isso é papel de `testes/casos/`, com oráculo. Aqui se
verifica que o exemplo é consistente e variado.
"""

import pytest

from siras.conhecimento.carregador import carregar_dados_comum
from siras.motor.adubacao import classificar_fosforo, classificar_potassio
from siras.web.exemplo import EXEMPLOS, PADRAO, PERFIS, TIPOS, escolher, montar

#: Massa molar do K para converter mg/dm3 em cmolc/dm3 na conferência da saturação.
_MASSA_K = 391.0


def _n(texto: str) -> float:
    return float(texto.replace(",", "."))


def _cations(perfil):
    ca, mg = _n(perfil["ca"]), _n(perfil["mg"])
    k_cmolc = _n(perfil["k"]) / _MASSA_K
    return ca + mg + k_cmolc, _n(perfil["al"])


class TestCoerenciaDosPerfis:
    @pytest.mark.parametrize("perfil_id", sorted(PERFIS))
    def test_saturacao_por_bases_bate_com_os_cations(self, perfil_id):
        """V% = (Ca + Mg + K) / CTC a pH 7,0. Tolerância de 0,2 ponto: os valores são
        guardados com uma casa decimal."""
        perfil = PERFIS[perfil_id]
        soma, _ = _cations(perfil)
        esperado = soma / _n(perfil["ctc_ph7"]) * 100
        assert abs(esperado - _n(perfil["v_percent"])) < 0.2, (
            f"{perfil_id}: V% declarada {perfil['v_percent']}, cátions dão {esperado:.1f}"
        )

    @pytest.mark.parametrize("perfil_id", sorted(PERFIS))
    def test_saturacao_por_aluminio_bate_com_a_ctc_efetiva(self, perfil_id):
        """m% = Al / (Al + Ca + Mg + K), a CTC efetiva."""
        perfil = PERFIS[perfil_id]
        soma, al = _cations(perfil)
        esperado = al / (soma + al) * 100
        assert abs(esperado - _n(perfil["saturacao_al"])) < 0.2, (
            f"{perfil_id}: m% declarada {perfil['saturacao_al']}, cátions dão {esperado:.1f}"
        )

    @pytest.mark.parametrize("perfil_id", sorted(PERFIS))
    def test_a_soma_de_bases_nao_passa_da_ctc(self, perfil_id):
        soma, _ = _cations(PERFIS[perfil_id])
        assert soma <= _n(PERFIS[perfil_id]["ctc_ph7"])

    @pytest.mark.parametrize("perfil_id", sorted(PERFIS))
    def test_o_indice_smp_cabe_na_tabela(self, perfil_id):
        """Fora de 4,4 a 7,1 o motor recusa, e com razão (CLAUDE.md). Um exemplo que não
        gera laudo não é exemplo."""
        assert 4.4 <= _n(PERFIS[perfil_id]["indice_smp"]) <= 7.1

    @pytest.mark.parametrize("perfil_id", sorted(PERFIS))
    def test_a_subsuperficie_e_mais_acida_que_a_superficie(self, perfil_id):
        """Não é lei da natureza, mas é o padrão do solo sob plantio direto, e o exemplo
        que invertesse isso sem dizer por quê confundiria quem está aprendendo."""
        perfil = PERFIS[perfil_id]
        assert _n(perfil["sub_ph_agua"]) <= _n(perfil["ph_agua"])
        assert _n(perfil["sub_v_percent"]) <= _n(perfil["v_percent"])
        assert _n(perfil["sub_al"]) >= _n(perfil["al"])


class TestCoberturaDosPerfis:
    def _classes(self):
        dados = carregar_dados_comum()
        vistas = {}
        for perfil_id, perfil in PERFIS.items():
            p = classificar_fosforo("grupo_2", _n(perfil["argila"]), _n(perfil["p"]), dados)
            k = classificar_potassio("grupo_2", _n(perfil["ctc_ph7"]), _n(perfil["k"]), dados)
            vistas[perfil_id] = (p["classe_argila"], p["classe"], k["faixa_ctc"], k["classe"])
        return vistas

    def test_nenhum_perfil_repete_outro(self):
        """Sete perfis idênticos em classe seriam um perfil só, sete vezes."""
        vistas = self._classes()
        assert len(set(vistas.values())) == len(vistas), vistas

    def test_as_cinco_classes_de_fosforo_aparecem(self):
        classes = {v[1] for v in self._classes().values()}
        assert classes == {"muito_baixo", "baixo", "medio", "alto", "muito_alto"}

    def test_as_quatro_classes_de_argila_aparecem(self):
        assert {v[0] for v in self._classes().values()} == {"1", "2", "3", "4"}

    def test_mais_de_uma_faixa_de_ctc_aparece(self):
        # A faixa "d" (CTC acima de 30) não entra: é de solo orgânico, e um perfil assim
        # entre sete de lavoura seria exceção apresentada como se fosse comum.
        assert {v[2] for v in self._classes().values()} >= {"a", "b", "c"}


class TestConjuntoDeExemplos:
    def test_sao_dez_com_ids_unicos(self):
        ids = [e["id"] for e in EXEMPLOS]
        assert len(ids) == 10
        assert len(set(ids)) == 10

    def test_sete_de_uma_area_e_tres_de_varias(self):
        assert sum(1 for e in EXEMPLOS if e["tipo"] == "unico") == 7
        assert sum(1 for e in EXEMPLOS if e["tipo"] == "multiplo") == 3

    def test_os_exemplos_de_varias_areas_tem_2_4_e_6_talhoes(self):
        quantidades = sorted(len(e["talhoes"]) for e in EXEMPLOS if e["tipo"] == "multiplo")
        assert quantidades == [2, 4, 6]

    def test_todo_exemplo_de_uma_area_tem_exatamente_um_talhao(self):
        for exemplo in EXEMPLOS:
            if exemplo["tipo"] == "unico":
                assert len(exemplo["talhoes"]) == 1, exemplo["id"]

    def test_todo_talhao_aponta_para_um_perfil_existente(self):
        for exemplo in EXEMPLOS:
            for _nome, _area, perfil_id in exemplo["talhoes"]:
                assert perfil_id in PERFIS, f"{exemplo['id']} usa perfil '{perfil_id}'"

    def test_todo_talhao_tem_nome_e_area(self):
        """A área de TODOS os talhões é o que destrava o total a comprar: com uma
        faltando, o laudo soma sobre um conjunto incompleto e não consolida."""
        for exemplo in EXEMPLOS:
            for nome, area, _perfil in exemplo["talhoes"]:
                assert nome.strip(), exemplo["id"]
                assert _n(area) > 0, exemplo["id"]

    def test_os_nomes_de_talhao_nao_se_repetem_dentro_do_exemplo(self):
        for exemplo in EXEMPLOS:
            nomes = [nome for nome, _a, _p in exemplo["talhoes"]]
            assert len(set(nomes)) == len(nomes), exemplo["id"]

    def test_as_formulas_saem_do_catalogo_e_nao_de_invencao(self):
        from siras.conhecimento.carregador import carregar_formulas_npk

        catalogo = {item["id"] for item in carregar_formulas_npk()["formulas"]["itens"]}
        for exemplo in EXEMPLOS:
            assert len(exemplo["formulas"]) == 3, exemplo["id"]
            for formula in exemplo["formulas"]:
                assert formula in catalogo, f"{exemplo['id']}: '{formula}' fora do catálogo"

    def test_todo_cpf_de_exemplo_e_invalido_por_construcao(self):
        """Sequência de dígito repetido: a regra de verificação brasileira rejeita todas,
        então nenhum CPF do exemplo pode pertencer a alguém."""
        for exemplo in EXEMPLOS:
            _nome, _registro, documento = exemplo["responsavel"]
            digitos = "".join(c for c in documento if c.isdigit())
            assert len(digitos) == 11, exemplo["id"]
            assert len(set(digitos)) == 1, f"{exemplo['id']}: CPF {documento} não é repetido"

    def test_todo_exemplo_declara_a_propria_cultura(self):
        """É o que permite garantir que não sobra campo em branco: campo condicional que
        só uma cultura exige não tem valor único que sirva para as 61."""
        from siras.dominio.escopo import no_escopo_de_recomendacao

        for exemplo in EXEMPLOS:
            cultura = exemplo.get("cultura")
            assert cultura, exemplo["id"]
            assert no_escopo_de_recomendacao(cultura), f"{exemplo['id']}: {cultura}"

    def test_os_dez_cobrem_os_seis_grupos_de_cultura(self):
        """Um conjunto que só demonstrasse grãos esconderia cinco sextos do sistema."""
        mapa = carregar_dados_comum()["mapa_culturas"]["culturas"]
        grupos = {mapa[e["cultura"]]["grupo"] for e in EXEMPLOS}
        assert grupos == {"graos", "hortalicas", "tuberculos", "frutiferas",
                          "outras", "erva_mate"}

    def test_cada_exemplo_tem_responsavel_e_propriedade_proprios(self):
        propriedades = [e["propriedade"] for e in EXEMPLOS]
        nomes = [e["responsavel"][0] for e in EXEMPLOS]
        assert len(set(propriedades)) == len(propriedades)
        assert len(set(nomes)) == len(nomes)


class TestEscolha:
    def test_o_id_de_um_exemplo_fixa_aquele(self):
        for exemplo in EXEMPLOS:
            assert escolher(exemplo["id"])["id"] == exemplo["id"]

    @pytest.mark.parametrize("tipo", [t["id"] for t in TIPOS])
    def test_o_tipo_sorteia_dentro_do_tipo(self, tipo):
        for _ in range(50):
            assert escolher(tipo)["tipo"] == tipo

    def test_o_sorteio_alcanca_todos_os_exemplos_do_tipo(self):
        import random

        sorteio = random.Random(20261011)
        caidos = {escolher("unico", sorteio)["id"] for _ in range(300)}
        assert len(caidos) == 7

    @pytest.mark.parametrize("pedido", ["", "1", "argiloso", "nao-existe"])
    def test_pedido_desconhecido_cai_no_padrao(self, pedido):
        """As bancadas de testes/integracao/ chamam com `exemplo=1` para as 61 culturas,
        e a tela não pode devolver erro por causa de um id que não existe mais."""
        assert escolher(pedido)["id"] == PADRAO["id"]


class TestMontagem:
    def _montar(self, exemplo_id):
        dados = carregar_dados_comum()
        from siras.web import formulario

        return montar(
            "soja", "graos", dados,
            formulario.opcoes_de_manejo(dados, "graos"),
            [],
            None,
            exemplo=escolher(exemplo_id),
        )

    def test_o_primeiro_talhao_ocupa_os_campos_sem_sufixo(self):
        valores = self._montar("multi-2-talhoes")
        assert valores["talhao"] == "Volta do Arroio"
        assert valores["talhao__2"] == "Topo da Coxilha"
        assert "talhao__1" not in valores

    @pytest.mark.parametrize("exemplo_id,esperado", [
        ("unico-argiloso-acido", []),
        ("multi-2-talhoes", [2]),
        ("multi-4-talhoes", [2, 3, 4]),
        ("multi-6-talhoes", [2, 3, 4, 5, 6]),
    ])
    def test_os_sufixos_dos_talhoes_adicionais(self, exemplo_id, esperado):
        from siras.web.formulario import indices_de_talhoes

        assert indices_de_talhoes(self._montar(exemplo_id)) == esperado

    def test_o_criterio_preferido_vale_quando_a_cultura_o_oferece(self):
        assert self._montar("multi-6-talhoes")["criterio_id"] == "graos_pd_com_restricoes"

    def test_o_criterio_preferido_cede_quando_a_cultura_nao_o_oferece(self):
        """A rota aceita emprestar a análise de um exemplo a outra cultura, e a lista de
        manejos depende do grupo: frutífera nenhuma oferece o plantio direto de grãos."""
        dados = carregar_dados_comum()
        from siras.web import formulario

        manejos = formulario.opcoes_de_manejo(dados, "frutiferas")
        valores = montar("macieira", "frutiferas", dados, manejos, [], None,
                         exemplo=escolher("multi-6-talhoes"))

        assert valores["criterio_id"] == manejos[0][0]
        assert valores["criterio_id"] != "graos_pd_com_restricoes"
