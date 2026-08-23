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

        # Invariante 2: Índices de 4.4 a 7.1 com passo 0.1
        indices_esperados = [4.4]
        smp = 4.5
        while smp <= 7.1:
            indices_esperados.append(round(smp, 1))
            smp = round(smp + 0.1, 1)

        indices_obtidos = [row["indice_smp"] for row in tabela]

        indices_divergem = len(indices_obtidos) != len(indices_esperados) or any(
            abs(obtido - esperado) >= 1e-9
            for obtido, esperado in zip(indices_obtidos, indices_esperados)
        )
        if indices_divergem:
            raise ErroCarregamento(
                f"calagem_smp.json: índices SMP incorretos\n"
                f"  Esperado: {indices_esperados}\n"
                f"  Obtido: {indices_obtidos}"
            )

        # Invariante 2b: primeira linha (4.4) deve ser marcada como limite_inferior
        if not tabela[0].get("limite_inferior"):
            raise ErroCarregamento(
                f"calagem_smp.json: primeira linha (indice_smp=4.4) deve ter limite_inferior=true"
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
        if abs(ultima_linha["indice_smp"] - 7.1) >= 1e-9:
            raise ErroCarregamento(
                f"calagem_smp.json: última linha esperada é 7.1, encontrada {ultima_linha['indice_smp']}"
            )

        if ultima_linha["nc_ph_5_5"] != 0 or ultima_linha["nc_ph_6_0"] != 0 or ultima_linha["nc_ph_6_5"] != 0:
            raise ErroCarregamento(
                f"calagem_smp.json: última linha (7.1) deve ter todas as doses = 0\n"
                f"  Obtido: nc_ph_5_5={ultima_linha['nc_ph_5_5']}, "
                f"nc_ph_6_0={ultima_linha['nc_ph_6_0']}, "
                f"nc_ph_6_5={ultima_linha['nc_ph_6_5']}"
            )

        # Invariante 7: soma das colunas bate com o checksum transcrito em dados/comum/
        checksum = dados.get("checksum_colunas", {})
        esperado_5_5 = checksum.get("nc_ph_5_5")
        esperado_6_0 = checksum.get("nc_ph_6_0")
        esperado_6_5 = checksum.get("nc_ph_6_5")

        soma_5_5 = round(sum(row["nc_ph_5_5"] for row in tabela), 1)
        soma_6_0 = round(sum(row["nc_ph_6_0"] for row in tabela), 1)
        soma_6_5 = round(sum(row["nc_ph_6_5"] for row in tabela), 1)

        if (soma_5_5, soma_6_0, soma_6_5) != (esperado_5_5, esperado_6_0, esperado_6_5):
            raise ErroCarregamento(
                f"calagem_smp.json: soma das colunas não bate com checksum_colunas\n"
                f"  Esperado (checksum_colunas): nc_ph_5_5={esperado_5_5}, "
                f"nc_ph_6_0={esperado_6_0}, nc_ph_6_5={esperado_6_5}\n"
                f"  Obtido (soma da tabela): nc_ph_5_5={soma_5_5}, nc_ph_6_0={soma_6_0}, "
                f"nc_ph_6_5={soma_6_5}"
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

    def validar_mapa_culturas(self, dados: Dict, criterios_calagem: Dict) -> None:
        """
        Valida invariantes específicas de mapa_culturas.json.

        INVARIANTES:
        - Todo "grupo" declarado existe em algum critério de criterios_calagem.json
        - Todo "criterio_calagem" declarado existe em criterios_calagem.json

        Args:
            dados: Dados de mapa_culturas.json
            criterios_calagem: Dados já carregados de criterios_calagem.json

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        grupos_conhecidos = {c["grupo"] for c in criterios_calagem["criterios"]}
        ids_conhecidos = {c["id"] for c in criterios_calagem["criterios"]}

        for cultura, entrada in dados.get("culturas", {}).items():
            grupo = entrada.get("grupo")
            if grupo not in grupos_conhecidos:
                raise ErroCarregamento(
                    f"mapa_culturas.json: cultura '{cultura}' aponta para grupo '{grupo}', "
                    f"que não existe em nenhum critério de criterios_calagem.json"
                )

            criterio_calagem = entrada.get("criterio_calagem")
            if criterio_calagem is not None and criterio_calagem not in ids_conhecidos:
                raise ErroCarregamento(
                    f"mapa_culturas.json: cultura '{cultura}' aponta para criterio_calagem "
                    f"'{criterio_calagem}', que não existe em criterios_calagem.json"
                )

    def _validar_faixas_contiguas(self, faixas: list, contexto: str, chave_rotulo: str = "classe") -> None:
        """
        Valida que uma lista de faixas (rótulo/de/ate) é contígua e sem lacunas:
        - primeira faixa com "de" == null (aberta à esquerda)
        - última faixa com "ate" == null (aberta à direita)
        - faixas[i]["ate"] == faixas[i+1]["de"] para todo par consecutivo

        Args:
            faixas: lista de dicts com "de", "ate" e um rótulo (chave_rotulo)
            contexto: prefixo descritivo para a mensagem de erro
            chave_rotulo: nome do campo usado como rótulo da faixa nas mensagens de erro
                ("classe" nas tabelas de interpretação, "id" nas classes de MO)

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        if not faixas:
            raise ErroCarregamento(f"{contexto}: lista de faixas vazia")

        if faixas[0].get("de") is not None:
            raise ErroCarregamento(
                f"{contexto}: primeira faixa ('{faixas[0].get(chave_rotulo)}') deveria ter "
                f"'de'=null (aberta à esquerda), encontrado {faixas[0].get('de')}"
            )
        if faixas[-1].get("ate") is not None:
            raise ErroCarregamento(
                f"{contexto}: última faixa ('{faixas[-1].get(chave_rotulo)}') deveria ter "
                f"'ate'=null (aberta à direita), encontrado {faixas[-1].get('ate')}"
            )

        for i in range(len(faixas) - 1):
            atual_ate = faixas[i].get("ate")
            proxima_de = faixas[i + 1].get("de")
            if atual_ate != proxima_de:
                raise ErroCarregamento(
                    f"{contexto}: faixas descontínuas entre '{faixas[i].get(chave_rotulo)}' "
                    f"(ate={atual_ate}) e '{faixas[i + 1].get(chave_rotulo)}' (de={proxima_de})"
                )

    def validar_interpretacao_geral(self, dados: Dict) -> None:
        """
        Valida invariantes de interpretacao_geral.json: faixas de cada atributo contíguas.

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        for atributo in dados.get("atributos", []):
            nome = atributo.get("atributo")
            self._validar_faixas_contiguas(
                atributo.get("faixas", []), f"interpretacao_geral.json: atributo '{nome}'"
            )

    def validar_interpretacao_k(self, dados: Dict) -> None:
        """
        Valida invariantes de interpretacao_k.json: faixas_ctc contíguas, toda faixa_ctc
        referenciada nas tabelas existe em faixas_ctc, e faixas de dose contíguas.

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        faixas_ctc = dados.get("faixas_ctc", [])
        self._validar_faixas_contiguas(faixas_ctc, "interpretacao_k.json: faixas_ctc")
        faixas_ctc_conhecidas = {f["faixa"] for f in faixas_ctc}

        for tabela in dados.get("tabelas", []):
            grupo = tabela.get("grupo")
            for bloco in tabela.get("por_faixa_ctc", []):
                faixa_ctc = bloco.get("faixa_ctc")
                if faixa_ctc not in faixas_ctc_conhecidas:
                    raise ErroCarregamento(
                        f"interpretacao_k.json: tabela '{grupo}' referencia faixa_ctc "
                        f"'{faixa_ctc}', que não existe em faixas_ctc"
                    )
                self._validar_faixas_contiguas(
                    bloco.get("faixas", []),
                    f"interpretacao_k.json: tabela '{grupo}', faixa_ctc '{faixa_ctc}'"
                )

    def validar_interpretacao_p(self, dados: Dict) -> None:
        """
        Valida invariantes de interpretacao_p.json: faixas de dose contíguas, por classe
        de argila (ou sem classe de argila, caso do arroz irrigado).

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        for tabela in dados.get("tabelas", []):
            grupo = tabela.get("grupo")
            if "por_classe_argila" in tabela:
                for bloco in tabela["por_classe_argila"]:
                    classe_argila = bloco.get("classe_argila")
                    self._validar_faixas_contiguas(
                        bloco.get("faixas", []),
                        f"interpretacao_p.json: tabela '{grupo}', classe_argila '{classe_argila}'"
                    )
            elif "sem_classe_argila" in tabela:
                self._validar_faixas_contiguas(
                    tabela["sem_classe_argila"], f"interpretacao_p.json: tabela '{grupo}'"
                )
            else:
                raise ErroCarregamento(
                    f"interpretacao_p.json: tabela '{grupo}' não declara "
                    f"'por_classe_argila' nem 'sem_classe_argila'"
                )

    def validar_graos_adubacao_n(self, dados: Dict) -> None:
        """
        Valida invariantes de graos_adubacao_n.json contra o checksum já transcrito:
        número de culturas e contagem por modelo.

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        culturas = dados.get("culturas", {})
        checksum = dados.get("checksum", {})

        if len(culturas) != checksum.get("culturas"):
            raise ErroCarregamento(
                f"graos_adubacao_n.json: checksum.culturas={checksum.get('culturas')}, "
                f"mas há {len(culturas)} entradas em 'culturas'"
            )

        contagem_por_modelo: Dict[str, int] = {}
        for entrada in culturas.values():
            modelo = entrada.get("modelo")
            contagem_por_modelo[modelo] = contagem_por_modelo.get(modelo, 0) + 1

        esperado = checksum.get("por_modelo", {})
        if contagem_por_modelo != esperado:
            raise ErroCarregamento(
                f"graos_adubacao_n.json: contagem por modelo não bate com checksum.por_modelo\n"
                f"  Esperado: {esperado}\n"
                f"  Obtido: {contagem_por_modelo}"
            )

    def validar_graos_adubacao_pk(self, dados: Dict) -> None:
        """
        Valida invariantes de graos_adubacao_pk.json contra o checksum já transcrito:
        número de culturas e soma de manutenção de P2O5/K2O.

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        culturas = dados.get("manutencao_por_cultura", {}).get("culturas", {})
        checksum = dados.get("checksum", {})

        if len(culturas) != checksum.get("culturas"):
            raise ErroCarregamento(
                f"graos_adubacao_pk.json: checksum.culturas={checksum.get('culturas')}, "
                f"mas há {len(culturas)} entradas em manutencao_por_cultura.culturas"
            )

        soma_p2o5 = sum(c["p2o5_manutencao"] for c in culturas.values())
        soma_k2o = sum(c["k2o_manutencao"] for c in culturas.values())

        if soma_p2o5 != checksum.get("soma_p2o5_manutencao"):
            raise ErroCarregamento(
                f"graos_adubacao_pk.json: soma de p2o5_manutencao={soma_p2o5}, "
                f"checksum.soma_p2o5_manutencao={checksum.get('soma_p2o5_manutencao')}"
            )
        if soma_k2o != checksum.get("soma_k2o_manutencao"):
            raise ErroCarregamento(
                f"graos_adubacao_pk.json: soma de k2o_manutencao={soma_k2o}, "
                f"checksum.soma_k2o_manutencao={checksum.get('soma_k2o_manutencao')}"
            )

    # Ordem oficial das classes de teor (Cap. 6), do menor ao maior — usada para checar
    # monotonicidade das doses de P/K nos arquivos de adubação por grupo de cultura.
    _ORDEM_CLASSES_TEOR = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]

    def _e_serie_por_teor(self, no: Any) -> bool:
        """True se `no` é um dict indexado diretamente pelas 5 classes de teor."""
        return isinstance(no, dict) and self._ORDEM_CLASSES_TEOR[0] in no

    def _valor_comparavel_dose(self, dose: Any) -> Optional[float]:
        """Valor comparável de uma dose para checar monotonicidade: usa o limite
        superior quando há faixa; None quando a dose é 'nao_aplicar' (não comparável)."""
        if not isinstance(dose, dict):
            return None
        if "valor" in dose:
            return dose["valor"]
        if "max" in dose:
            return dose["max"]
        return None

    def _validar_formato_dose(self, dose: Any, contexto: str) -> None:
        """
        I4 (docs/decisoes/0004, D4.1): toda dose é um objeto válido —
        {"valor"}, {"valor","qualificador":"ate"}, {"min","max"} ou {"tipo":"nao_aplicar"}.
        """
        if not isinstance(dose, dict):
            raise ErroCarregamento(f"{contexto}: dose não é objeto ({dose!r})")

        chaves = set(dose)
        valido = (
            (chaves <= {"valor", "qualificador"} and "valor" in dose)
            or chaves == {"min", "max"}
            or chaves == {"tipo"}
        )
        if not valido:
            raise ErroCarregamento(f"{contexto}: formato de dose inválido ({sorted(chaves)})")

        if "qualificador" in dose and dose["qualificador"] != "ate":
            raise ErroCarregamento(
                f"{contexto}: qualificador desconhecido '{dose['qualificador']}' (só 'ate' é aceito)"
            )
        if chaves == {"min", "max"} and dose["min"] > dose["max"]:
            raise ErroCarregamento(f"{contexto}: faixa invertida {dose}")

    def _validar_monotonicidade(self, valores: list, rotulos: list, contexto: str) -> None:
        """I3: a dose não pode aumentar conforme a classe de teor sobe."""
        for anterior, atual, rotulo_a, rotulo_b in zip(valores, valores[1:], rotulos, rotulos[1:]):
            if anterior is not None and atual is not None and atual > anterior:
                raise ErroCarregamento(
                    f"{contexto}: dose sobe de {rotulo_a}={anterior} para {rotulo_b}={atual} "
                    f"(deveria ser não-crescente conforme o teor melhora)"
                )

    def _validar_serie_teor(self, serie: Dict[str, Any], contexto: str) -> None:
        """
        I2/I3/I4: toda série de dose por classe de teor tem as 5 classes, cada dose tem
        formato válido, e a dose não aumenta conforme a classe de teor sobe. Cobre séries
        simples (uma dose por classe) e séries com subcolunas (ex.: por fase, por
        produtividade) — um nível de aninhamento.
        """
        faltando = [c for c in self._ORDEM_CLASSES_TEOR if c not in serie]
        if faltando:
            raise ErroCarregamento(f"{contexto}: classes de teor ausentes {faltando}")

        primeiro = serie[self._ORDEM_CLASSES_TEOR[0]]
        if not isinstance(primeiro, dict):
            raise ErroCarregamento(f"{contexto}.{self._ORDEM_CLASSES_TEOR[0]}: não é objeto")

        if {"valor", "min", "tipo"} & set(primeiro):
            # Série simples: uma dose por classe de teor.
            valores = []
            for classe in self._ORDEM_CLASSES_TEOR:
                self._validar_formato_dose(serie[classe], f"{contexto}.{classe}")
                valores.append(self._valor_comparavel_dose(serie[classe]))
            self._validar_monotonicidade(valores, self._ORDEM_CLASSES_TEOR, contexto)
        else:
            # Série com subcolunas (fase, produtividade etc.): checa a monotonicidade
            # dentro de cada coluna.
            for coluna in primeiro:
                valores = []
                for classe in self._ORDEM_CLASSES_TEOR:
                    sub = serie[classe].get(coluna) if isinstance(serie[classe], dict) else None
                    if sub is None:
                        raise ErroCarregamento(f"{contexto}.{classe}: falta a coluna '{coluna}'")
                    self._validar_formato_dose(sub, f"{contexto}.{classe}.{coluna}")
                    valores.append(self._valor_comparavel_dose(sub))
                self._validar_monotonicidade(
                    valores, self._ORDEM_CLASSES_TEOR, f"{contexto}[{coluna}]"
                )

    def _percorrer_series_p_k(self, no: Any, contexto: str) -> None:
        """
        Percorre recursivamente um documento de adubação procurando blocos 'p'/'k'
        indexados por classe de teor — diretamente ou sob uma chave 'doses' — e valida
        cada um (I2/I3/I4). Blocos cujas chaves não são as classes de teor (ex.: videira,
        indexada por classe de tecido foliar) são ignorados propositalmente: a
        correspondência solo→tecido é regra agronômica registrada em ADR, não invariante
        estrutural.

        Args:
            no: nó atual da árvore (dict, list ou valor escalar)
            contexto: caminho descritivo até este nó, para mensagens de erro

        Raises:
            ErroCarregamento: se alguma série de teor encontrada violar I2/I3/I4
        """
        if not isinstance(no, dict):
            return

        for chave in ("p", "k"):
            bloco = no.get(chave)
            if self._e_serie_por_teor(bloco):
                self._validar_serie_teor(bloco, f"{contexto}.{chave}")
            elif isinstance(bloco, dict) and self._e_serie_por_teor(bloco.get("doses")):
                self._validar_serie_teor(bloco["doses"], f"{contexto}.{chave}.doses")

        for chave, sub in no.items():
            if chave not in ("p", "k"):
                self._percorrer_series_p_k(sub, f"{contexto}.{chave}")

    def _soma_numerica(self, no: Any) -> float:
        """Soma recursiva de todos os valores numéricos de um nó (dict/list/escalar).

        bool é excluído propositalmente: em Python, bool é subclasse de int, e
        True/False somariam 1/0 ao total sem serem doses de verdade.
        """
        if isinstance(no, dict):
            return sum(self._soma_numerica(v) for v in no.values())
        if isinstance(no, list):
            return sum(self._soma_numerica(v) for v in no)
        if isinstance(no, bool):
            return 0.0
        if isinstance(no, (int, float)):
            return no
        return 0.0

    def validar_adubacao_por_grupo(self, dados: Dict, nome_arquivo: str) -> None:
        """
        Valida invariantes comuns aos arquivos de adubação por grupo de cultura
        (hortaliças, tubérculos, outras comerciais, frutíferas, erva-mate):
        - I1: cada lista em 'classes_mo' é contígua e sem lacunas
        - I2/I3/I4: toda série 'p'/'k' por classe de teor tem as 5 classes, doses em
          formato válido, e não aumenta conforme o teor sobe (docs/decisoes/0004, D4.1)
        - I5: checksum — número de culturas e soma de todos os valores numéricos em
          'culturas' batem com o que o autor conferiu contra o Manual

        Args:
            dados: dados já carregados do arquivo
            nome_arquivo: nome do arquivo, para as mensagens de erro

        Raises:
            ErroCarregamento: se alguma invariante falhar
        """
        for nome_classes, faixas in dados.get("classes_mo", {}).items():
            self._validar_faixas_contiguas(
                faixas, f"{nome_arquivo}: classes_mo.{nome_classes}", chave_rotulo="id"
            )

        for id_cultura, cultura in dados.get("culturas", {}).items():
            self._percorrer_series_p_k(cultura, f"{nome_arquivo}:{id_cultura}")

        culturas = dados.get("culturas", {})
        checksum = dados.get("checksum", {})

        if len(culturas) != checksum.get("culturas"):
            raise ErroCarregamento(
                f"{nome_arquivo}: checksum.culturas={checksum.get('culturas')}, "
                f"mas há {len(culturas)} entradas em 'culturas'"
            )

        soma_obtida = round(self._soma_numerica(culturas), 2)
        soma_esperada = checksum.get("soma_total")
        if soma_esperada is not None:
            soma_esperada = round(soma_esperada, 2)
        if soma_obtida != soma_esperada:
            raise ErroCarregamento(
                f"{nome_arquivo}: soma_total esperada {soma_esperada}, obtida {soma_obtida} "
                f"— algum valor em 'culturas' foi alterado sem atualizar o checksum"
            )

    def carregar_dados_comum(self) -> Dict[str, Dict[str, Any]]:
        """
        Carrega e valida todos os arquivos de dados/comum/.

        Returns:
            Dict com chaves 'calagem_smp', 'criterios_calagem', 'ph_referencia', 'mapa_culturas'

        Raises:
            ErroCarregamento: se algum arquivo falhar na validação
        """
        base_dir = Path(__file__).parent.parent.parent  # siras/conhecimento -> raiz do repo
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

        # Carregar mapa_culturas.json
        try:
            dados = self._carregar_json(dados_dir / "mapa_culturas.json")
            self._validar_schema_json("mapa_culturas.json", "mapa_culturas_v1", dados)
            self.validar_mapa_culturas(dados, resultado["criterios_calagem"])
            resultado["mapa_culturas"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"mapa_culturas.json: {e}")

        # Carregar interpretacao_geral.json
        try:
            dados = self._carregar_json(dados_dir / "interpretacao_geral.json")
            self._validar_schema_json("interpretacao_geral.json", "interpretacao_geral_v1", dados)
            self.validar_interpretacao_geral(dados)
            resultado["interpretacao_geral"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"interpretacao_geral.json: {e}")

        # Carregar interpretacao_k.json
        try:
            dados = self._carregar_json(dados_dir / "interpretacao_k.json")
            self._validar_schema_json("interpretacao_k.json", "interpretacao_k_v1", dados)
            self.validar_interpretacao_k(dados)
            resultado["interpretacao_k"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"interpretacao_k.json: {e}")

        # Carregar interpretacao_p.json
        try:
            dados = self._carregar_json(dados_dir / "interpretacao_p.json")
            self._validar_schema_json("interpretacao_p.json", "interpretacao_p_v1", dados)
            self.validar_interpretacao_p(dados)
            resultado["interpretacao_p"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"interpretacao_p.json: {e}")

        return resultado

    def carregar_dados_graos(self) -> Dict[str, Dict[str, Any]]:
        """
        Carrega e valida os arquivos de dados/culturas/graos/.

        Returns:
            Dict com chaves 'adubacao_n', 'adubacao_pk'

        Raises:
            ErroCarregamento: se algum arquivo falhar na validação
        """
        base_dir = Path(__file__).parent.parent.parent  # siras/conhecimento -> raiz do repo
        dados_dir = base_dir / "dados" / "culturas" / "graos"

        resultado = {}

        # Carregar graos_adubacao_n.json
        try:
            dados = self._carregar_json(dados_dir / "graos_adubacao_n.json")
            self._validar_schema_json("graos_adubacao_n.json", "graos_adubacao_n_v1", dados)
            self.validar_graos_adubacao_n(dados)
            resultado["adubacao_n"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"graos_adubacao_n.json: {e}")

        # Carregar graos_adubacao_pk.json
        try:
            dados = self._carregar_json(dados_dir / "graos_adubacao_pk.json")
            self._validar_schema_json("graos_adubacao_pk.json", "graos_adubacao_pk_v1", dados)
            self.validar_graos_adubacao_pk(dados)
            resultado["adubacao_pk"] = dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"graos_adubacao_pk.json: {e}")

        return resultado

    def _carregar_adubacao_por_grupo(
        self, grupo: str, nome_arquivo: str, nome_schema: str
    ) -> Dict[str, Any]:
        """
        Carrega e valida um arquivo de adubação de dados/culturas/<grupo>/.

        Args:
            grupo: nome da pasta em dados/culturas/ (ex.: "hortalicas")
            nome_arquivo: nome do arquivo JSON (ex.: "hortalicas_adubacao.json")
            nome_schema: nome do schema (ex.: "hortalicas_adubacao_v1")

        Raises:
            ErroCarregamento: se o arquivo falhar na validação
        """
        base_dir = Path(__file__).parent.parent.parent  # siras/conhecimento -> raiz do repo
        caminho = base_dir / "dados" / "culturas" / grupo / nome_arquivo

        try:
            dados = self._carregar_json(caminho)
            self._validar_schema_json(nome_arquivo, nome_schema, dados)
            self.validar_adubacao_por_grupo(dados, nome_arquivo)
            return dados
        except ErroCarregamento as e:
            raise ErroCarregamento(f"{nome_arquivo}: {e}")

    def carregar_dados_hortalicas(self) -> Dict[str, Dict[str, Any]]:
        """Carrega e valida dados/culturas/hortalicas/hortalicas_adubacao.json."""
        return {
            "adubacao": self._carregar_adubacao_por_grupo(
                "hortalicas", "hortalicas_adubacao.json", "hortalicas_adubacao_v1"
            )
        }

    def carregar_dados_tuberculos(self) -> Dict[str, Dict[str, Any]]:
        """Carrega e valida dados/culturas/tuberculos/tuberculos_adubacao.json."""
        return {
            "adubacao": self._carregar_adubacao_por_grupo(
                "tuberculos", "tuberculos_adubacao.json", "tuberculos_adubacao_v1"
            )
        }

    def carregar_dados_outras(self) -> Dict[str, Dict[str, Any]]:
        """Carrega e valida dados/culturas/outras/outras_comerciais_adubacao.json."""
        return {
            "adubacao": self._carregar_adubacao_por_grupo(
                "outras", "outras_comerciais_adubacao.json", "outras_comerciais_adubacao_v1"
            )
        }

    def carregar_dados_frutiferas(self) -> Dict[str, Dict[str, Any]]:
        """Carrega e valida dados/culturas/frutiferas/frutiferas_adubacao.json."""
        return {
            "adubacao": self._carregar_adubacao_por_grupo(
                "frutiferas", "frutiferas_adubacao.json", "frutiferas_adubacao_v1"
            )
        }

    def carregar_dados_erva_mate(self) -> Dict[str, Dict[str, Any]]:
        """Carrega e valida dados/culturas/erva_mate/erva_mate_adubacao.json."""
        return {
            "adubacao": self._carregar_adubacao_por_grupo(
                "erva_mate", "erva_mate_adubacao.json", "erva_mate_adubacao_v1"
            )
        }


# Função de conveniência para uso geral
_carregador_global: Optional[Carregador] = None


def carregar_dados_comum() -> Dict[str, Dict[str, Any]]:
    """
    Carrega dados comuns com cache global.

    Returns:
        Dict com 'calagem_smp', 'criterios_calagem', 'ph_referencia', 'mapa_culturas',
        'interpretacao_geral', 'interpretacao_k', 'interpretacao_p'

    Raises:
        ErroCarregamento: se validação falhar
    """
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_comum()


def carregar_dados_graos() -> Dict[str, Dict[str, Any]]:
    """
    Carrega dados de adubação de grãos com cache global.

    Returns:
        Dict com 'adubacao_n', 'adubacao_pk'

    Raises:
        ErroCarregamento: se validação falhar
    """
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_graos()


def carregar_dados_hortalicas() -> Dict[str, Dict[str, Any]]:
    """Carrega dados de adubação de hortaliças com cache global."""
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_hortalicas()


def carregar_dados_tuberculos() -> Dict[str, Dict[str, Any]]:
    """Carrega dados de adubação de tubérculos com cache global."""
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_tuberculos()


def carregar_dados_outras() -> Dict[str, Dict[str, Any]]:
    """Carrega dados de adubação de cana e tabaco com cache global."""
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_outras()


def carregar_dados_frutiferas() -> Dict[str, Dict[str, Any]]:
    """Carrega dados de adubação de frutíferas com cache global."""
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_frutiferas()


def carregar_dados_erva_mate() -> Dict[str, Dict[str, Any]]:
    """Carrega dados de adubação de erva-mate com cache global."""
    global _carregador_global
    if _carregador_global is None:
        _carregador_global = Carregador()
    return _carregador_global.carregar_dados_erva_mate()
