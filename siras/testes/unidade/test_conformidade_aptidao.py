"""
Conformidade do módulo de aptidão edáfica — CCAE v1.1.

Verificação, não validação: mede se a implementação reproduz a especificação
congelada, não se a especificação está agronomicamente correta.

Arquitetura da separação:
  casos/entradas_aptidao.json  -> entradas, SEM respostas
  casos/gabarito_aptidao.csv   -> respostas, lidas SÓ por este arquivo

O módulo siras/motor/aptidao.py nunca deve importar nem abrir o gabarito.
"""
import csv
import json
import pathlib

import pytest

from siras.motor.aptidao import avaliar_aptidao_ccae

CASOS = pathlib.Path(__file__).resolve().parents[1] / "casos"


def _entradas():
    dados = json.loads((CASOS / "entradas_aptidao.json").read_text(encoding="utf-8"))
    return {c["id_caso"]: c for c in dados["casos"]}


def _gabarito():
    with open(CASOS / "gabarito_aptidao.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


ENTRADAS = _entradas()
GABARITO = _gabarito()

# Casos com status PENDENTE ainda não têm resposta; ficam fora até serem gabaritados.
# Os FORA_DAS_METRICAS são de rejeição de entrada e são exercitados em
# test_entrada_invalida, não aqui (CCAE §9.2).
CONFORMIDADE = [g for g in GABARITO
                if g["status"] in ("CONFERIDO", "CORRIGIDO_NA_CONFERENCIA")]
INVALIDOS = [g for g in GABARITO if g["status"] == "FORA_DAS_METRICAS"]
PENDENTES = [g for g in GABARITO if g["status"] == "PENDENTE"]


def _executar(gab):
    caso = ENTRADAS[gab["id_caso"]]
    return avaliar_aptidao_ccae(
        analise=caso["entrada"],
        cultura=caso["cultura"],
        cenario=gab["cenario"],
    )


@pytest.mark.parametrize("gab", CONFORMIDADE, ids=lambda g: g["id_caso"])
def test_classe_de_aptidao(gab):
    """Métrica principal de conformidade (CCAE §9.3). Meta: 100%."""
    r = _executar(gab)
    assert r.classe == gab["classe_esperada"], (
        f"{gab['id_caso']} [{gab['bloco']}/{gab['cenario']}]: "
        f"esperado {gab['classe_esperada']}, obtido {r.classe} "
        f"(determinante {r.fator_determinante})"
    )


@pytest.mark.parametrize("gab", CONFORMIDADE, ids=lambda g: g["id_caso"])
def test_fator_determinante(gab):
    """Acertar a classe pelo motivo errado é defeito que a classe esconde."""
    r = _executar(gab)
    assert r.fator_determinante == gab["fator_determinante_esperado"], (
        f"{gab['id_caso']}: determinante esperado "
        f"{gab['fator_determinante_esperado']}, obtido {r.fator_determinante}"
    )


@pytest.mark.parametrize("gab", CONFORMIDADE, ids=lambda g: g["id_caso"])
def test_graus_por_fator(gab):
    """Granularidade máxima: localiza QUAL fator divergiu, não só o resultado."""
    r = _executar(gab)
    obtidos = {f.id.split("_")[0]: f.rotulo for f in r.fatores}
    for i in range(1, 8):
        chave = f"F{i}"
        if not gab[chave]:
            continue
        assert obtidos.get(chave) == gab[chave], (
            f"{gab['id_caso']} {chave}: esperado {gab[chave]}, "
            f"obtido {obtidos.get(chave)}"
        )


@pytest.mark.parametrize("gab", [g for g in CONFORMIDADE if g["V_esperado"]],
                         ids=lambda g: g["id_caso"])
def test_derivados(gab):
    """V%, m% e classes auxiliares. Erram antes de tudo o mais errar."""
    r = _executar(gab)
    assert r.derivados["v_percent"] == pytest.approx(float(gab["V_esperado"]), abs=0.05)
    assert r.derivados["m_percent"] == pytest.approx(float(gab["m_esperado"]), abs=0.05)
    assert str(r.derivados["classe_argila"]) == gab["classe_argila"]
    assert r.derivados["classe_ctc"] == gab["classe_ctc"]


@pytest.mark.parametrize("gab", INVALIDOS, ids=lambda g: g["id_caso"])
def test_entrada_invalida(gab):
    """CCAE §5.4: falha explícita. Rejeitar, nunca imputar valor."""
    r = _executar(gab)
    assert r.classe == "INDETERMINADA"


def test_gabarito_completo():
    """O conjunto não admite casos sem resposta. Se um caso novo entrar sem
    gabarito, este teste falha antes que ele passe despercebido pela
    conformidade."""
    assert not PENDENTES, (
        "Casos sem gabarito: "
        f"{sorted(g['id_caso'] for g in PENDENTES)}. "
        "Gabarite a partir do CCAE ou remova-os do conjunto."
    )
    sem_resposta = [g["id_caso"] for g in GABARITO if not g["classe_esperada"]]
    assert not sem_resposta, f"Linhas sem classe_esperada: {sem_resposta}"


def test_cobertura_do_conjunto():
    """Guarda de integridade: todo id do gabarito existe nas entradas."""
    faltando = [g["id_caso"] for g in GABARITO if g["id_caso"] not in ENTRADAS]
    assert not faltando, f"ids no gabarito sem entrada correspondente: {faltando}"
    assert len(GABARITO) == len(ENTRADAS), (
        f"{len(GABARITO)} linhas de gabarito para {len(ENTRADAS)} entradas"
    )


def test_determinismo():
    """CCAE: função pura. Mesma entrada, mesma saída, sempre."""
    for gab in CONFORMIDADE[:20]:
        primeira, segunda = _executar(gab), _executar(gab)
        assert primeira.classe == segunda.classe
        assert primeira.fator_determinante == segunda.fator_determinante
        assert primeira.derivados == segunda.derivados


def test_versao_criterios_declarada():
    """O gabarito vale para uma versão do CCAE; se o motor implementa outra, a
    conformidade não significa nada (CCAE Apêndice C)."""
    entradas = json.loads((CASOS / "entradas_aptidao.json").read_text(encoding="utf-8"))
    r = _executar(CONFORMIDADE[0])
    assert r.versao_criterios == entradas["versao_criterios"]
