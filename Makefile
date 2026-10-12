# SIRAS — atalhos de desenvolvimento.
#
# TUDO AQUI DELEGA A `run.py`, de propósito. A lógica de criar o ambiente, instalar as
# dependências e subir o servidor mora lá, num só lugar, porque `make` NÃO vem instalado
# no Windows — e a máquina onde a defesa acontece pode não ter nenhum. Um Makefile que
# fosse a única porta de entrada transformaria a demonstração em "primeiro instale o
# make", que é exatamente o passo que não se quer descobrir na frente da banca.
#
# Então: este arquivo é o atalho de quem já tem `make`; `run.py` é a garantia.
#
#   make           sobe o servidor e abre o navegador
#   make testes    bancada rápida
#   make completa  bancada completa
#   make validar   confere a base de conhecimento contra os schemas
#   make limpar    apaga .venv, caches e saídas geradas
#
# Sem make:  python run.py [tarefa]     (ou `py run.py` no Windows)

# `py` é o lançador oficial do Windows e está no PATH mesmo quando `python` não está;
# fora do Windows, `python3`. A escolha é feita aqui para o Makefile não depender de
# qual nome o sistema usa.
ifeq ($(OS),Windows_NT)
PY := py
else
PY := python3
endif

.DEFAULT_GOAL := servir
.PHONY: servir testes completa validar limpar ajuda

servir:
	$(PY) run.py servir

testes:
	$(PY) run.py testes

completa:
	$(PY) run.py completa

validar:
	$(PY) run.py validar

limpar:
	$(PY) run.py limpar

ajuda:
	@$(PY) run.py ajuda
