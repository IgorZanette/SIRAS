"""
Carregador de base de conhecimento com validação de schema e invariantes.

Responsabilidades:
- Carregar JSONs de dados/comum/ com encoding UTF-8
- Validar estrutura contra JSON Schema
- Validar invariantes agronômicas (Tabela 5.2, Tabela 5.3, Tabela 5.1)
- Cache em memória de schemas
- Erros devem apontar arquivo e campo específico, não mensagem genérica
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import Draft202012Validator, ValidationError


class ErroCarregamento(Exception):
    """Erro ao carregar ou validar base de conhecimento."""
    pass


class Carregador:
    """Carregador centralizado de base de conhecimento com validação."""

    def __init__(self):
        """Inicializa carregador com cache vazio."""
        self._cache_schemas: Dict[str, Dict] = {}
        self._cache_dados: Dict[str, Dict] = {}

    def _carregar_json(self, caminho: Path) -> Dict[str, Any]:
        """
        Carrega arquivo JSON com UTF-8.

        Args:
            caminho: Path do arquivo JSON

        Returns:
            Dict com conteúdo do JSON

        Raises:
            ErroCarregamento: se arquivo não existir ou JSON for inválido
        """
        try:
            conteudo = caminho.read_text(encoding="utf-8")
            return json.loads(conteudo)
        except FileNotFoundError:
            raise ErroCarregamento(f"Arquivo não encontrado: {caminho}")
        except json.JSONDecodeError as e:
            raise ErroCarregamento(f"JSON inválido em {caminho}: {e}")

    def _carregar_schema(self, nome_schema: str) -> Dict[str, Any]:
        """
        Carrega schema JSON com cache em memória.

        Args:
            nome_schema: Nome do schema (ex: 'calagem_smp_v1')

        Returns:
            Dict com schema JSON

        Raises:
            ErroCarregamento: se schema não existir
        """
        if nome_schema in self._cache_schemas:
            return self._cache_schemas[nome_schema]

        base_dir = Path(__file__).parent
        schema_path = base_dir / "esquemas" / f"{nome_schema}.schema.json"

        try:
            schema = self._carregar_json(schema_path)
            self._cache_schemas[nome_schema] = schema
            return schema
        except ErroCarregamento as e:
            raise ErroCarregamento(f"Erro carregando schema '{nome_schema}': {e}")

    def _validar_schema_json(self, nome_arquivo: str, nome_schema: str, dados: Dict) -> None:
        """
        Valida dados contra schema JSON.

        Args:
            nome_arquivo: Nome do arquivo sendo validado (para erro)
            nome_schema: Nome do schema
            dados: Dados a validar

        Raises:
            ErroCarregamento: se validação falhar
        """
        schema = self._carregar_schema(nome_schema)
        validator = Draft202012Validator(schema)

        try:
            validator.validate(dados)
        except ValidationError as e:
            # Montar caminho do erro
            caminho = " → ".join(str(p) for p in e.absolute_path) if e.absolute_path else "(raiz)"
            raise ErroCarregamento(
                f"{nome_arquivo}: validação de schema falhou\n"
                f"  Campo: {caminho}\n"
                f"  Erro: {e.message}"
            )

    def validar_tabela_calagem_smp(self, dados: Dict) -> None:
        """
        Valida invariantes específicas de calagem_smp.json (Tabela 5.2).

        INVARIANTES:
        - Exatamente 28 entradas
        - Índices de "<=4.4" a "7.1", passo 0.1
        - Todas as doses >= 0
        - Dose não-crescente por coluna (conforme SMP aumenta)
        - nc_ph_5_5 <= nc_ph_6_0 <= nc_ph_6_5 em cada linha
        - Na última linha (7.1), todas as doses são 0

        Args:
            dados: Dados de calagem_smp.json

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        tabela = dados.get("tabela", [])

        # Invariante 1: Exatamente 28 linhas
        if len(tabela) != 28:
            raise ErroCarregamento(
                f"calagem_smp.json: tabela deve ter 28 linhas, encontrada {len(tabela)}"
            )

        # Invariante 2: Índices de <=4.4 a 7.1 com passo 0.1
        indices_esperados = ["<=4.4"]
        smp = 4.5
        while smp <= 7.1:
            indices_esperados.append(f"{smp:.1f}")
            smp = round(smp + 0.1, 1)

        indices_obtidos = [row["indice_smp"] for row in tabela]

        if indices_obtidos != indices_esperados:
            raise ErroCarregamento(
                f"calagem_smp.json: índices SMP incorretos\n"
                f"  Esperado: {indices_esperados}\n"
                f"  Obtido: {indices_obtidos}"
            )

        # Invariante 3 e 4: Todas doses >= 0 e monotonia por coluna
        prev_row = None
        for i, row in enumerate(tabela):
            indice = row["indice_smp"]
            nc_5_5 = row["nc_ph_5_5"]
            nc_6_0 = row["nc_ph_6_0"]
            nc_6_5 = row["nc_ph_6_5"]

            # Todas doses >= 0
            if nc_5_5 < 0 or nc_6_0 < 0 or nc_6_5 < 0:
                raise ErroCarregamento(
                    f"calagem_smp.json: linha {i} ({indice}) tem dose negativa\n"
                    f"  nc_ph_5_5={nc_5_5}, nc_ph_6_0={nc_6_0}, nc_ph_6_5={nc_6_5}"
                )

            # Monotonia: dose não-crescente por coluna
            if prev_row:
                prev_nc_5_5 = prev_row["nc_ph_5_5"]
                prev_nc_6_0 = prev_row["nc_ph_6_0"]
                prev_nc_6_5 = prev_row["nc_ph_6_5"]

                if nc_5_5 > prev_nc_5_5:
                    raise ErroCarregamento(
                        f"calagem_smp.json: monotonia violada em nc_ph_5_5\n"
                        f"  Linha {i-1} ({prev_row['indice_smp']}): {prev_nc_5_5}\n"
                        f"  Linha {i} ({indice}): {nc_5_5} (MAIOR)"
                    )
                if nc_6_0 > prev_nc_6_0:
                    raise ErroCarregamento(
                        f"calagem_smp.json: monotonia violada em nc_ph_6_0\n"
                        f"  Linha {i-1} ({prev_row['indice_smp']}): {prev_nc_6_0}\n"
                        f"  Linha {i} ({indice}): {nc_6_0} (MAIOR)"
                    )
                if nc_6_5 > prev_nc_6_5:
                    raise ErroCarregamento(
                        f"calagem_smp.json: monotonia violada em nc_ph_6_5\n"
                        f"  Linha {i-1} ({prev_row['indice_smp']}): {prev_nc_6_5}\n"
                        f"  Linha {i} ({indice}): {nc_6_5} (MAIOR)"
                    )

            # Invariante 5: nc_ph_5_5 <= nc_ph_6_0 <= nc_ph_6_5
            if nc_5_5 > nc_6_0 or nc_6_0 > nc_6_5:
                raise ErroCarregamento(
                    f"calagem_smp.json: linha {i} ({indice}) viola relação nc_ph_5_5 <= nc_ph_6_0 <= nc_ph_6_5\n"
                    f"  Obtido: {nc_5_5} <= {nc_6_0} <= {nc_6_5}"
                )

            prev_row = row

        # Invariante 6: Última linha (7.1) tem todas as doses = 0
        ultima_linha = tabela[-1]
        if ultima_linha["indice_smp"] != "7.1":
            raise ErroCarregamento(
                f"calagem_smp.json: última linha esperada é '7.1', encontrada '{ultima_linha['indice_smp']}'"
            )

        if ultima_linha["nc_ph_5_5"] != 0 or ultima_linha["nc_ph_6_0"] != 0 or ultima_linha["nc_ph_6_5"] != 0:
            raise ErroCarregamento(
                f"calagem_smp.json: última linha (7.1) deve ter todas as doses = 0\n"
                f"  Obtido: nc_ph_5_5={ultima_linha['nc_ph_5_5']}, "
                f"nc_ph_6_0={ultima_linha['nc_ph_6_0']}, "
                f"nc_ph_6_5={ultima_linha['nc_ph_6_5']}"
            )

    def validar_criterios_calagem(self, dados: Dict) -> None:
        """
        Valida invariantes específicas de criterios_calagem.json.

        INVARIANTES:
        - IDs únicos
        - Todo critério com dose.tipo == 'smp' tem ph_alvo em [5.5, 6.0, 6.5] e fator em [1.0, 0.5, 0.25]
        - Todo critério com modo_aplicacao == 'superficial' declara dose.limite_t_ha
        - Todo critério com ph_referencia == null tem dose.tipo == 'saturacao_bases'
        - Todo critério tem campo fonte não-vazio

        Args:
            dados: Dados de criterios_calagem.json

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        criterios = dados.get("criterios", [])
        ids_vistos = set()

        for i, criterio in enumerate(criterios):
            id_crit = criterio.get("id")

            # Invariante 1: IDs únicos
            if id_crit in ids_vistos:
                raise ErroCarregamento(
                    f"criterios_calagem.json: critério {i} tem id duplicado '{id_crit}'"
                )
            ids_vistos.add(id_crit)

            # Invariante 5: Campo fonte não-vazio
            fonte = criterio.get("fonte", "").strip()
            if not fonte:
                raise ErroCarregamento(
                    f"criterios_calagem.json: critério {i} ('{id_crit}') tem campo 'fonte' vazio"
                )

            dose = criterio.get("dose", {})
            tipo_dose = dose.get("tipo")
            ph_referencia = criterio.get("ph_referencia")

            # Invariante 4: ph_referencia == null implica dose.tipo == 'saturacao_bases'
            if ph_referencia is None:
                if tipo_dose != "saturacao_bases":
                    raise ErroCarregamento(
                        f"criterios_calagem.json: critério {i} ('{id_crit}') tem ph_referencia=null "
                        f"mas dose.tipo='{tipo_dose}' (deve ser 'saturacao_bases')"
                    )

            # Invariante 2: dose.tipo == 'smp' deve ter ph_alvo válido e fator válido
            if tipo_dose == "smp":
                ph_alvo = dose.get("ph_alvo")
                fator = dose.get("fator")

                if ph_alvo not in [5.5, 6.0, 6.5]:
                    raise ErroCarregamento(
                        f"criterios_calagem.json: critério {i} ('{id_crit}') com dose.tipo='smp' "
                        f"tem ph_alvo={ph_alvo} (deve ser 5.5, 6.0 ou 6.5)"
                    )

                if fator not in [1.0, 0.5, 0.25]:
                    raise ErroCarregamento(
                        f"criterios_calagem.json: critério {i} ('{id_crit}') com dose.tipo='smp' "
                        f"tem fator={fator} (deve ser 1.0, 0.5 ou 0.25)"
                    )

            # Invariante 3: modo_aplicacao == 'superficial' deve ter limite_t_ha
            modo = criterio.get("modo_aplicacao")
            if modo == "superficial":
                limite = dose.get("limite_t_ha")
                if limite is None:
                    raise ErroCarregamento(
                        f"criterios_calagem.json: critério {i} ('{id_crit}') com modo_aplicacao='superficial' "
                        f"não declara dose.limite_t_ha"
                    )

    def validar_ph_referencia(self, dados: Dict) -> None:
        """
        Valida invariantes específicas de ph_referencia.json.

        INVARIANTES:
        - Nenhuma cultura repetida entre grupos, EXCETO 'camomila' que consta em dois.
          (Exceção conhecida e documentada do Manual).

        Args:
            dados: Dados de ph_referencia.json

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        grupos = dados.get("grupos", [])
        culturas_vistas: Dict[str, int] = {}  # cultura -> ph_referencia

        exceções_conhecidas = {
            "camomila": [5.5, 6.0],  # Consta em dois grupos no Manual
        }

        for grupo in grupos:
            ph_ref = grupo.get("ph_referencia")
            culturas = grupo.get("culturas", [])

            for cultura in culturas:
                if cultura in culturas_vistas:
                    # Verificar se é exceção conhecida
                    ph_anterior = culturas_vistas[cultura]
                    if cultura in exceções_conhecidas:
                        phs_esperados = sorted(exceções_conhecidas[cultura])
                        if sorted([ph_anterior, ph_ref]) == phs_esperados:
                            # Exceção conhecida, OK
                            continue

                    raise ErroCarregamento(
                        f"ph_referencia.json: cultura '{cultura}' aparece em múltiplos grupos "
                        f"com pH diferentes (pH {ph_anterior} e pH {ph_ref})"
                    )
                culturas_vistas[cultura] = ph_ref

    def carregar_dados_comum(self) -> Dict[str, Dict[str, Any]]:
        """
        Carrega e valida todos os arquivos de dados/comum/.

        Returns:
            Dict com chaves 'calagem_smp', 'criterios_calagem', 'ph_referencia'

        Raises:
            ErroCarregamento: se algum arquivo falhar na validação
        """
        base_dir = Path(__file__).parent.parent.parent  # Siras/conhecimento -> SIRAS
        dados_dir = base_dir / "dados" / "comum"

        resultado = {}

        # Carregar calagem_smp.json
        try:
            dados = self._carregar_json(dados_dir / "calagem_smp.json")
            self._validar_schema_json("calagem_smp.json", "calagem_smp_v1", dados)
            self.validar_tabela_calagem_smp(dados)
            resultado["calagem_smp"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"calagem_smp.json: {e}")

        # Carregar criterios_calagem.json
        try:
            dados = self._carregar_json(dados_dir / "criterios_calagem.json")
            self._validar_schema_json("criterios_calagem.json", "criterios_calagem_v1", dados)
            self.validar_criterios_calagem(dados)
            resultado["criterios_calagem"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"criterios_calagem.json: {e}")

        # Carregar ph_referencia.json
        try:
            dados = self._carregar_json(dados_dir / "ph_referencia.json")
            self._validar_schema_json("ph_referencia.json", "ph_referencia_v1", dados)
            self.validar_ph_referencia(dados)
            resultado["ph_referencia"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"ph_referencia.json: {e}")

        return resultado


# Função de conveniência para uso geral
_carregador_global: Optional[Carregador] = None


def carregar_dados_comum() -> Dict[str, Dict[str, Any]]:
    """
    Carrega dados comuns com cache global.

    Returns:
        Dict com 'calagem_smp', 'criterios_calagem', 'ph_referencia'

    Raises:
        ErroCarregamento: se validação falhar
    """
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_comum()
