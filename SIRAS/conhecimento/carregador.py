from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable

from jsonschema import Draft202012Validator

ROOT_DIR = Path(__file__).resolve().parents[2]
DADOS_COMUM_DIR = ROOT_DIR / "dados" / "comum"
SCHEMAS_DIR = Path(__file__).resolve().parent / "esquemas"


@lru_cache(maxsize=None)
def _carregar_json(path: str) -> Any:
    caminho = Path(path)
    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


@lru_cache(maxsize=None)
def _carregar_schema(nome_schema: str) -> Dict[str, Any]:
    caminho = SCHEMAS_DIR / f"{nome_schema}.schema.json"
    return _carregar_json(str(caminho))


def _formatar_caminho_do_campo(caminho: Iterable[Any]) -> str:
    partes = [str(p) for p in caminho]
    return ".".join(partes) if partes else "$"


def _mensagem_erro_validacao(caminho_arquivo: Path, erro: Any) -> str:
    campo = _formatar_caminho_do_campo(erro.absolute_path)
    return f"Arquivo '{caminho_arquivo.name}' campo '{campo}': {erro.message}"


def _validar_schema_json(caminho_arquivo: Path, dados: Any, nome_schema: str) -> None:
    schema = _carregar_schema(nome_schema)
    validador = Draft202012Validator(schema)
    erros = sorted(validador.iter_errors(dados), key=lambda item: list(item.path))

    if erros:
        detalhes = "; ".join(_mensagem_erro_validacao(caminho_arquivo, erro) for erro in erros)
        raise ValueError(detalhes)


def _parse_smp(valor: str) -> float:
    texto = valor.strip()
    if texto.startswith("<="):
        texto = texto[2:]
    return float(texto)


def validar_tabela_calagem_smp(dados: Dict[str, Any]) -> None:
    tabela = dados.get("tabela")
    if not isinstance(tabela, list):
        raise ValueError("Arquivo 'calagem_smp.json' campo 'tabela': tabela de calagem deve ser uma lista.")

    for indice, linha in enumerate(tabela):
        for campo in ("nc_ph_5_5", "nc_ph_6_0", "nc_ph_6_5"):
            if campo not in linha:
                raise ValueError(f"Arquivo 'calagem_smp.json' campo 'tabela[{indice}].{campo}': campo ausente.")
            valor = linha[campo]
            if not isinstance(valor, (int, float)):
                raise ValueError(f"Arquivo 'calagem_smp.json' campo 'tabela[{indice}].{campo}': valor deve ser numérico.")

        valores_mesmo_smp = [
            float(linha["nc_ph_5_5"]),
            float(linha["nc_ph_6_0"]),
            float(linha["nc_ph_6_5"]),
        ]
        if max(valores_mesmo_smp) > 0 and (valores_mesmo_smp[0] > valores_mesmo_smp[1] or valores_mesmo_smp[1] > valores_mesmo_smp[2]):
            raise ValueError(
                "Arquivo 'calagem_smp.json' campo 'tabela[{indice}].nc_ph_*': "
                "as doses para o mesmo SMP devem crescer de pH 5,5 para 6,0 para 6,5."
            )

    for campo in ("nc_ph_5_5", "nc_ph_6_0", "nc_ph_6_5"):
        anterior: float | None = None
        for indice, linha in enumerate(tabela):
            valor = float(linha[campo])
            if anterior is not None and valor > anterior + 1e-9:
                raise ValueError(
                    f"Arquivo 'calagem_smp.json' campo 'tabela[{indice}].{campo}': "
                    "a dose deve decrescer monotonicamente conforme o índice SMP aumenta."
                )
            anterior = valor


def carregar_dados_comum(nome_arquivo: str) -> Dict[str, Any]:
    caminho = DADOS_COMUM_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: '{caminho}'")

    dados = _carregar_json(str(caminho))

    if nome_arquivo == "calagem_smp.json":
        _validar_schema_json(caminho, dados, "calagem_smp")
        validar_tabela_calagem_smp(dados)
    elif nome_arquivo == "criterios_calagem.json":
        _validar_schema_json(caminho, dados, "criterios_calagem")
    elif nome_arquivo == "ph_referencia.json":
        _validar_schema_json(caminho, dados, "ph_referencia")
    else:
        raise ValueError(f"Arquivo de dados não suportado: '{nome_arquivo}'")

    return dados


def carregar_base_comum() -> Dict[str, Dict[str, Any]]:
    retorno = {}
    for nome_arquivo in ("calagem_smp.json", "criterios_calagem.json", "ph_referencia.json"):
        retorno[nome_arquivo] = carregar_dados_comum(nome_arquivo)
    return retorno
