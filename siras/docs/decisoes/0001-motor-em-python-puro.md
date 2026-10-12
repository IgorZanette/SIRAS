# ADR 0001 — Motor de inferência em Python puro

**Status:** aceito · **Data:** 2026-08-16

## Contexto

O SIRAS é um sistema especialista baseado em regras. Existem bibliotecas de inferência para Python
(Experta, PyKE) que implementam encadeamento de regras e resolução de conflitos.

## Decisão

Implementar o motor diretamente em Python, sem biblioteca externa de inferência.

## Justificativa

- **Auditabilidade:** cada regra é código legível e rastreável, requisito declarado na proposta.
- As regras do Manual são consultas a tabelas e condicionais encadeadas, sem necessidade de
  encadeamento complexo nem de resolução de conflitos entre regras.
- Menos dependências e menor risco de incompatibilidade com versões recentes do Python.

## Consequências

- Mais código próprio a escrever e testar.
- Exige disciplina no registro dos passos de inferência — atendida pelo `Trace`.
