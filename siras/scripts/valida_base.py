#!/usr/bin/env python3
"""
Script para validar a base de conhecimento.

Execução:
    python scripts/valida_base.py

Sai com código 0 se OK, 1 se houver erro.
"""

import sys
from pathlib import Path

# Adicionar siras ao path
projeto_root = Path(__file__).parent.parent
sys.path.insert(0, str(projeto_root))

# Força UTF-8 no stdout
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from siras.conhecimento.carregador import Carregador, ErroCarregamento


def main():
    """Valida base de conhecimento e sai com código apropriado."""
    carregador = Carregador()

    print("=" * 70)
    print("VALIDAÇÃO DA BASE DE CONHECIMENTO")
    print("=" * 70)

    try:
        dados = carregador.carregar_dados_comum()

        print("\n[OK] calagem_smp.json")
        print("[OK] criterios_calagem.json")
        print("[OK] ph_referencia.json")
        print("[OK] mapa_culturas.json")

        print("\n" + "=" * 70)
        print("Validação de schema concluída com sucesso.")
        print("=" * 70)
        return 0

    except ErroCarregamento as e:
        print(f"\n[ERRO] VALIDAÇÃO FALHOU:\n{e}", file=sys.stderr)
        print("\n" + "=" * 70)
        print("Validação falhou.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
