from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AnaliseSolo:
    """Representa uma análise química e física de solo."""

    ph_agua: float
    indice_smp: float
    argila: float
    mo: float
    p: float
    k: float
    ctc_ph7: float
    al: float
    ca: float
    mg: float
    v_percent: float
    saturacao_al: Optional[float] = None

    def __post_init__(self) -> None:
        self._validar_campos_obrigatorios()
        self._validar_faixa_fisica_plausivel()

    def obter_saturacao_al(self) -> float:
        """Retorna a saturação por Al (m%): informada diretamente (laudo já traz o valor),
        ou calculada pela CTC efetiva quando ausente (docs/decisoes/0003, D4).

        m% = Al / (Ca + Mg + K_cmolc + Al) x 100, com K_cmolc = k (mg/dm3) / 391.
        """
        if self.saturacao_al is not None:
            return self.saturacao_al

        k_cmolc = self.k / 391
        ctc_efetiva = self.ca + self.mg + k_cmolc + self.al
        if ctc_efetiva <= 0:
            return 0.0
        return (self.al / ctc_efetiva) * 100

    def _validar_campos_obrigatorios(self) -> None:
        campos = {
            "ph_agua": self.ph_agua,
            "indice_smp": self.indice_smp,
            "argila": self.argila,
            "mo": self.mo,
            "p": self.p,
            "k": self.k,
            "ctc_ph7": self.ctc_ph7,
            "al": self.al,
            "ca": self.ca,
            "mg": self.mg,
            "v_percent": self.v_percent,
        }

        for nome, valor in campos.items():
            if valor is None:
                raise ValueError(f"Campo obrigatório '{nome}' não pode ser nulo.")

    def _validar_faixa_fisica_plausivel(self) -> None:
        # Validação estritamente física/semântica. Não adotamos limites agronômicos
        # inventados; apenas verificamos plausibilidade numérica e a ausência de valores
        # absurdos para o domínio do solo.

        if not 0.0 <= self.ph_agua <= 14.0:
            raise ValueError("'ph_agua' deve estar em faixa física plausível para pH em água (0 a 14).")

        # D2 (docs/decisoes/0002): fora de [3,0 ; 8,0] é erro de validação de entrada,
        # distinto de estar fora da faixa da Tabela 5.2 (4,4 a 7,1), que é lido pelo
        # limite inferior/superior da tabela e não é erro.
        if not 3.0 <= self.indice_smp <= 8.0:
            raise ValueError("'indice_smp' deve estar em faixa física plausível (3,0 a 8,0).")

        if self.argila < 0:
            raise ValueError("'argila' não pode ser negativo.")

        if self.mo < 0:
            raise ValueError("'mo' não pode ser negativo.")

        if self.p < 0:
            raise ValueError("'p' não pode ser negativo.")

        if self.k < 0:
            raise ValueError("'k' não pode ser negativo.")

        if self.ctc_ph7 < 0:
            raise ValueError("'ctc_ph7' não pode ser negativo.")

        if self.al < 0:
            raise ValueError("'al' não pode ser negativo.")

        if self.ca < 0:
            raise ValueError("'ca' não pode ser negativo.")

        if self.mg < 0:
            raise ValueError("'mg' não pode ser negativo.")

        if not 0.0 <= self.v_percent <= 100.0:
            raise ValueError("'v_percent' deve estar em faixa física plausível para saturação por bases (0 a 100).")

        if self.saturacao_al is not None and not 0.0 <= self.saturacao_al <= 100.0:
            raise ValueError("'saturacao_al' deve estar em faixa física plausível (0 a 100).")

        # TODO: definir limites específicos para atributos agronômicos quando a regra
        # for formalizada no Manual ou em outra fonte autoritativa do TCC.


@dataclass
class Contexto:
    """Contexto operacional do cálculo para a cultura e o manejo considerado."""

    cultura_id: str
    sistema_manejo: str
    condicao_area: str
    prnt: float
    profundidade_incorporacao_cm: float
    expectativa_rendimento: Optional[str] = None

    def __post_init__(self) -> None:
        self._validar_campos_obrigatorios()
        self._validar_faixa_fisica_plausivel()

    def _validar_campos_obrigatorios(self) -> None:
        if not self.cultura_id:
            raise ValueError("'cultura_id' é obrigatório.")
        if not self.sistema_manejo:
            raise ValueError("'sistema_manejo' é obrigatório.")
        if not self.condicao_area:
            raise ValueError("'condicao_area' é obrigatório.")
        if self.prnt is None:
            raise ValueError("'prnt' é obrigatório.")
        if self.profundidade_incorporacao_cm is None:
            raise ValueError("'profundidade_incorporacao_cm' é obrigatório.")

    def _validar_faixa_fisica_plausivel(self) -> None:
        # Validação estritamente física/operacional. Não inventamos limiares agronômicos.
        if not 0.0 <= self.prnt <= 100.0:
            raise ValueError("'prnt' deve estar em faixa física plausível para poder relativo de neutralização total (0 a 100).")

        # Decisão operacional do técnico (não é dado medido do solo), restrita às duas
        # profundidades de incorporação que o Manual discute: 0-20 cm (padrão) e 30 cm
        # (fruteiras de raiz profunda, docs/decisoes/0003). Distinta da camada AMOSTRADA,
        # que vem do critério de calagem (criterios_calagem.json, campo amostragem_cm).
        if self.profundidade_incorporacao_cm not in (20.0, 30.0):
            raise ValueError(
                "'profundidade_incorporacao_cm' deve ser 20 ou 30 (as únicas profundidades "
                "de incorporação que o Manual discute)."
            )

        # TODO: definir intervalos válidos para 'expectativa_rendimento' conforme a
        # escala agronômica adotada em cada cultura, quando esta regra for formalizada.
