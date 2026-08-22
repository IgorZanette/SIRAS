"""
Testes das invariantes da base de conhecimento.

Testa:
- Tabela 5.2 (calagem_smp.json): 28 linhas, índices, monotonia, relações
- Tabela 5.3 (criterios_calagem.json): IDs únicos, fator/ph_alvo, superficial/limite
- Tabela 5.1 (ph_referencia.json): culturas únicas, exceção camomila
- mapa_culturas.json: grupo e criterio_calagem consistentes com criterios_calagem.json
- interpretacao_geral.json, interpretacao_k.json, interpretacao_p.json: faixas contíguas
"""

import pytest
from siras.conhecimento.carregador import Carregador


@pytest.fixture
def carregador():
    """Fixture que fornece um carregador."""
    return Carregador()


@pytest.fixture
def dados_comum(carregador):
    """Fixture que carrega todos os dados comuns."""
    return carregador.carregar_dados_comum()


class TestCalageSMP:
    """Testes de invariantes de calagem_smp.json (Tabela 5.2)."""

    def test_tabela_tem_28_linhas(self, dados_comum):
        """Invariante: tabela deve ter exatamente 28 linhas."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        assert len(tabela) == 28, f"Esperado 28 linhas, encontrado {len(tabela)}"

    def test_indices_de_4_4_a_7_1_passo_0_1(self, dados_comum):
        """Invariante: índices de <=4.4 a 7.1 com passo 0.1."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        indices_obtidos = [row["indice_smp"] for row in tabela]

        indices_esperados = [4.4]
        smp = 4.5
        while smp <= 7.1:
            indices_esperados.append(round(smp, 1))
            smp = round(smp + 0.1, 1)

        assert len(indices_obtidos) == len(indices_esperados) and all(
            abs(obtido - esperado) < 1e-9
            for obtido, esperado in zip(indices_obtidos, indices_esperados)
        ), f"Índices esperados: {indices_esperados}\nÍndices obtidos: {indices_obtidos}"

        assert tabela[0].get("limite_inferior") is True, \
            "Primeira linha (indice_smp=4.4) deve ter limite_inferior=true"

    def test_todas_doses_nao_negativas(self, dados_comum):
        """Invariante: todas as doses >= 0."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        for i, row in enumerate(tabela):
            assert row["nc_ph_5_5"] >= 0, f"Linha {i}: nc_ph_5_5 negativa"
            assert row["nc_ph_6_0"] >= 0, f"Linha {i}: nc_ph_6_0 negativa"
            assert row["nc_ph_6_5"] >= 0, f"Linha {i}: nc_ph_6_5 negativa"

    def test_monotonia_ph_5_5(self, dados_comum):
        """Invariante: nc_ph_5_5 não-crescente conforme SMP aumenta."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        for i in range(len(tabela) - 1):
            atual = tabela[i]["nc_ph_5_5"]
            proximo = tabela[i + 1]["nc_ph_5_5"]
            assert proximo <= atual, \
                f"Linha {i} -> {i+1}: nc_ph_5_5 cresce ({atual} -> {proximo})"

    def test_monotonia_ph_6_0(self, dados_comum):
        """Invariante: nc_ph_6_0 não-crescente conforme SMP aumenta."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        for i in range(len(tabela) - 1):
            atual = tabela[i]["nc_ph_6_0"]
            proximo = tabela[i + 1]["nc_ph_6_0"]
            assert proximo <= atual, \
                f"Linha {i} -> {i+1}: nc_ph_6_0 cresce ({atual} -> {proximo})"

    def test_monotonia_ph_6_5(self, dados_comum):
        """Invariante: nc_ph_6_5 não-crescente conforme SMP aumenta."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        for i in range(len(tabela) - 1):
            atual = tabela[i]["nc_ph_6_5"]
            proximo = tabela[i + 1]["nc_ph_6_5"]
            assert proximo <= atual, \
                f"Linha {i} -> {i+1}: nc_ph_6_5 cresce ({atual} -> {proximo})"

    def test_relacao_ph_5_5_menor_igual_6_0(self, dados_comum):
        """Invariante: nc_ph_5_5 <= nc_ph_6_0 em cada linha."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        for i, row in enumerate(tabela):
            assert row["nc_ph_5_5"] <= row["nc_ph_6_0"], \
                f"Linha {i}: nc_ph_5_5 ({row['nc_ph_5_5']}) > nc_ph_6_0 ({row['nc_ph_6_0']})"

    def test_relacao_ph_6_0_menor_igual_6_5(self, dados_comum):
        """Invariante: nc_ph_6_0 <= nc_ph_6_5 em cada linha."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        for i, row in enumerate(tabela):
            assert row["nc_ph_6_0"] <= row["nc_ph_6_5"], \
                f"Linha {i}: nc_ph_6_0 ({row['nc_ph_6_0']}) > nc_ph_6_5 ({row['nc_ph_6_5']})"

    def test_ultima_linha_todas_doses_zero(self, dados_comum):
        """Invariante: última linha (7.1) tem todas as doses = 0."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        ultima = tabela[-1]
        assert abs(ultima["indice_smp"] - 7.1) < 1e-9, \
            f"Última linha esperada é 7.1, encontrada {ultima['indice_smp']}"
        assert ultima["nc_ph_5_5"] == 0, f"nc_ph_5_5 na linha 7.1 deve ser 0"
        assert ultima["nc_ph_6_0"] == 0, f"nc_ph_6_0 na linha 7.1 deve ser 0"
        assert ultima["nc_ph_6_5"] == 0, f"nc_ph_6_5 na linha 7.1 deve ser 0"

    def test_soma_colunas_bate_com_checksum(self, dados_comum):
        """Invariante: soma das colunas da Tabela 5.2 bate com checksum_colunas (28 linhas)."""
        tabela = dados_comum["calagem_smp"]["tabela"]
        assert len(tabela) == 28, f"Esperado 28 linhas, encontrado {len(tabela)}"

        checksum = dados_comum["calagem_smp"]["checksum_colunas"]

        soma_5_5 = round(sum(row["nc_ph_5_5"] for row in tabela), 1)
        soma_6_0 = round(sum(row["nc_ph_6_0"] for row in tabela), 1)
        soma_6_5 = round(sum(row["nc_ph_6_5"] for row in tabela), 1)

        assert soma_5_5 == checksum["nc_ph_5_5"], \
            f"Soma de nc_ph_5_5 esperada {checksum['nc_ph_5_5']}, obtida {soma_5_5}"
        assert soma_6_0 == checksum["nc_ph_6_0"], \
            f"Soma de nc_ph_6_0 esperada {checksum['nc_ph_6_0']}, obtida {soma_6_0}"
        assert soma_6_5 == checksum["nc_ph_6_5"], \
            f"Soma de nc_ph_6_5 esperada {checksum['nc_ph_6_5']}, obtida {soma_6_5}"


class TestCriteriosCalagem:
    """Testes de invariantes de criterios_calagem.json."""

    def test_ids_unicos(self, dados_comum):
        """Invariante: todos os critérios têm IDs únicos."""
        criterios = dados_comum["criterios_calagem"]["criterios"]
        ids = [c["id"] for c in criterios]
        assert len(ids) == len(set(ids)), \
            f"IDs duplicados: {[x for x in ids if ids.count(x) > 1]}"

    def test_criterio_smp_com_ph_alvo_valido(self, dados_comum):
        """Invariante: dose.tipo='smp' deve ter ph_alvo em [5.5, 6.0, 6.5]."""
        criterios = dados_comum["criterios_calagem"]["criterios"]
        for criterio in criterios:
            if criterio["dose"]["tipo"] == "smp":
                ph_alvo = criterio["dose"]["ph_alvo"]
                assert ph_alvo in [5.5, 6.0, 6.5], \
                    f"Critério {criterio['id']}: ph_alvo={ph_alvo} inválido"

    def test_criterio_smp_com_fator_valido(self, dados_comum):
        """Invariante: dose.tipo='smp' deve ter fator em [1.0, 0.5, 0.25]."""
        criterios = dados_comum["criterios_calagem"]["criterios"]
        for criterio in criterios:
            if criterio["dose"]["tipo"] == "smp":
                fator = criterio["dose"]["fator"]
                assert fator in [1.0, 0.5, 0.25], \
                    f"Critério {criterio['id']}: fator={fator} inválido"

    def test_modo_superficial_tem_limite_t_ha(self, dados_comum):
        """Invariante: modo_aplicacao='superficial' deve ter dose.limite_t_ha."""
        criterios = dados_comum["criterios_calagem"]["criterios"]
        for criterio in criterios:
            if criterio["modo_aplicacao"] == "superficial":
                limite = criterio["dose"].get("limite_t_ha")
                assert limite is not None, \
                    f"Critério {criterio['id']} (superficial) não tem dose.limite_t_ha"

    def test_todos_criterios_com_fonte_nao_vazia(self, dados_comum):
        """Invariante: todo critério tem campo fonte não-vazio."""
        criterios = dados_comum["criterios_calagem"]["criterios"]
        for criterio in criterios:
            fonte = criterio.get("fonte", "").strip()
            assert fonte, \
                f"Critério {criterio['id']} tem campo 'fonte' vazio"

    def test_ph_referencia_null_implica_dose_saturacao_bases(self, dados_comum):
        """Invariante: se ph_referencia=null, dose.tipo deve ser 'saturacao_bases'."""
        criterios = dados_comum["criterios_calagem"]["criterios"]
        for criterio in criterios:
            ph_ref = criterio.get("ph_referencia")
            if ph_ref is None:
                dose_tipo = criterio["dose"].get("tipo")
                assert dose_tipo == "saturacao_bases", \
                    f"Critério {criterio['id']}: ph_referencia=null mas dose.tipo='{dose_tipo}' " \
                    f"(deve ser 'saturacao_bases')"


class TestPHReferencia:
    """Testes de invariantes de ph_referencia.json."""

    def test_culturas_unicas_exceto_camomila(self, dados_comum):
        """Invariante: culturas únicas entre grupos, exceto camomila."""
        grupos = dados_comum["ph_referencia"]["grupos"]
        culturas_vistas = {}

        exceções_conhecidas = {
            "camomila": [5.5, 6.0],
        }

        for grupo in grupos:
            ph_ref = grupo["ph_referencia"]
            for cultura in grupo["culturas"]:
                if cultura in culturas_vistas:
                    ph_anterior = culturas_vistas[cultura]
                    if cultura in exceções_conhecidas:
                        phs_esperados = sorted(exceções_conhecidas[cultura])
                        if sorted([ph_anterior, ph_ref]) == phs_esperados:
                            continue

                    pytest.fail(
                        f"Cultura '{cultura}' aparece em múltiplos grupos "
                        f"com pH diferentes (pH {ph_anterior} e pH {ph_ref})"
                    )
                culturas_vistas[cultura] = ph_ref

    def test_camomila_em_dois_grupos(self, dados_comum):
        """Verificação: camomila deve estar em exatamente 2 grupos (pH 5.5 e 6.0)."""
        grupos = dados_comum["ph_referencia"]["grupos"]
        phs_camomila = []

        for grupo in grupos:
            if "camomila" in grupo["culturas"]:
                phs_camomila.append(grupo["ph_referencia"])

        assert phs_camomila == [5.5, 6.0] or phs_camomila == [6.0, 5.5], \
            f"Camomila encontrada em pH {phs_camomila}, esperado [5.5, 6.0]"


class TestMapaCulturas:
    """Testes de invariantes de mapa_culturas.json."""

    def test_todo_grupo_existe_em_criterios_calagem(self, dados_comum):
        grupos_conhecidos = {c["grupo"] for c in dados_comum["criterios_calagem"]["criterios"]}
        for cultura, entrada in dados_comum["mapa_culturas"]["culturas"].items():
            assert entrada["grupo"] in grupos_conhecidos, \
                f"cultura '{cultura}': grupo '{entrada['grupo']}' não existe em criterios_calagem.json"

    def test_todo_criterio_calagem_existe_em_criterios_calagem(self, dados_comum):
        ids_conhecidos = {c["id"] for c in dados_comum["criterios_calagem"]["criterios"]}
        for cultura, entrada in dados_comum["mapa_culturas"]["culturas"].items():
            criterio_calagem = entrada.get("criterio_calagem")
            if criterio_calagem is not None:
                assert criterio_calagem in ids_conhecidos, \
                    f"cultura '{cultura}': criterio_calagem '{criterio_calagem}' não existe em criterios_calagem.json"


def _assert_faixas_contiguas(faixas, contexto):
    """Helper: primeira faixa aberta à esquerda, última aberta à direita, sem lacunas."""
    assert faixas, f"{contexto}: lista de faixas vazia"
    assert faixas[0]["de"] is None, \
        f"{contexto}: primeira faixa ('{faixas[0]['classe']}') deveria ter de=None"
    assert faixas[-1]["ate"] is None, \
        f"{contexto}: última faixa ('{faixas[-1]['classe']}') deveria ter ate=None"
    for i in range(len(faixas) - 1):
        assert faixas[i]["ate"] == faixas[i + 1]["de"], \
            f"{contexto}: lacuna entre '{faixas[i]['classe']}' (ate={faixas[i]['ate']}) " \
            f"e '{faixas[i + 1]['classe']}' (de={faixas[i + 1]['de']})"


class TestInterpretacaoGeral:
    """Testes de invariantes de interpretacao_geral.json."""

    def test_faixas_de_cada_atributo_sao_contiguas(self, dados_comum):
        for atributo in dados_comum["interpretacao_geral"]["atributos"]:
            _assert_faixas_contiguas(
                atributo["faixas"], f"atributo '{atributo['atributo']}'"
            )


class TestInterpretacaoK:
    """Testes de invariantes de interpretacao_k.json."""

    def test_faixas_ctc_sao_contiguas(self, dados_comum):
        _assert_faixas_contiguas(dados_comum["interpretacao_k"]["faixas_ctc"], "faixas_ctc")

    def test_toda_faixa_ctc_referenciada_existe(self, dados_comum):
        faixas_conhecidas = {f["faixa"] for f in dados_comum["interpretacao_k"]["faixas_ctc"]}
        for tabela in dados_comum["interpretacao_k"]["tabelas"]:
            for bloco in tabela["por_faixa_ctc"]:
                assert bloco["faixa_ctc"] in faixas_conhecidas, \
                    f"tabela '{tabela['grupo']}': faixa_ctc '{bloco['faixa_ctc']}' desconhecida"

    def test_faixas_de_dose_sao_contiguas(self, dados_comum):
        for tabela in dados_comum["interpretacao_k"]["tabelas"]:
            for bloco in tabela["por_faixa_ctc"]:
                _assert_faixas_contiguas(
                    bloco["faixas"],
                    f"tabela '{tabela['grupo']}', faixa_ctc '{bloco['faixa_ctc']}'"
                )


class TestInterpretacaoP:
    """Testes de invariantes de interpretacao_p.json."""

    def test_faixas_de_dose_sao_contiguas(self, dados_comum):
        for tabela in dados_comum["interpretacao_p"]["tabelas"]:
            grupo = tabela["grupo"]
            if "por_classe_argila" in tabela:
                for bloco in tabela["por_classe_argila"]:
                    _assert_faixas_contiguas(
                        bloco["faixas"],
                        f"tabela '{grupo}', classe_argila '{bloco['classe_argila']}'"
                    )
            elif "sem_classe_argila" in tabela:
                _assert_faixas_contiguas(tabela["sem_classe_argila"], f"tabela '{grupo}'")
            else:
                pytest.fail(f"tabela '{grupo}' não declara por_classe_argila nem sem_classe_argila")
