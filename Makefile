# SIRAS — atalhos. Tudo delega a run.py, que funciona sem make.
#
#   make           sobe o servidor e abre o navegador
#   make testes    bancada rápida
#   make completa  bancada completa
#   make validar   confere a base de conhecimento contra os schemas
#   make limpar    apaga .venv, caches e saídas geradas
#
# Sem make:  py run.py [tarefa]   (Windows)   ·   python3 run.py [tarefa]

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
