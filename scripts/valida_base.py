from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from SIRAS.conhecimento.carregador import carregar_base_comum


def main() -> int:
    try:
        dados = carregar_base_comum()
        print("Validação de schema concluída com sucesso.")
        for nome in ("calagem_smp.json", "criterios_calagem.json", "ph_referencia.json"):
            print(f"- {nome}: OK")
        print("Verificação de consistência da Tabela 5.2: OK")
        return 0
    except Exception as exc:  # pragma: no cover - CLI de diagnóstico
        print(f"ERRO DE VALIDAÇÃO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
