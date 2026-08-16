# ADR 0002 — Calagem dirigida por critério de grupo, não pelo pH de referência

**Status:** aceito · **Data:** 2026-08-16

## Contexto

A leitura inicial da proposta assumia que a calagem seria calculada a partir do pH de referência da
cultura (Tabela 5.1) aplicado à tabela do índice SMP (Tabela 5.2).

A extração do Capítulo 5 do Manual mostrou que isso está incorreto. O pH de referência identifica a
exigência da espécie, mas a **condição de disparo** e o **pH alvo da dose** vêm das Tabelas 5.3 a
5.7, organizadas por grupo de cultura e sistema de manejo, e frequentemente divergem do pH de
referência:

- grãos: pH de referência 6,0, disparo em pH < 5,5, dose para pH 6,0;
- aspargo: pH de referência 6,5, disparo em pH < 6,0, dose para pH 6,5;
- plantio direto consolidado: fator de 1/4 sobre a dose, aplicação superficial limitada a 5 t/ha;
- erva-mate e florestais: sem pH de referência, critério por saturação por bases (V = 40%).

## Decisão

`dados/comum/criterios_calagem.json` é a tabela que dirige o módulo de calagem. A cadeia é
`cultura + sistema + condição da área -> critério -> (disparo, pH alvo, fator) -> Tabela 5.2`.

`ph_referencia.json` permanece na base para exibição no laudo e para a regra de rotação de culturas
(usar o pH de referência da cultura mais sensível), mas **não** dispara a calagem.

## Consequências

- O sistema de manejo (convencional / plantio direto e sua condição) passa a ser entrada obrigatória
  do formulário, não opcional.
- A Seção 3.1.2 da proposta precisa ser corrigida: hoje descreve o método da saturação por bases,
  que o Manual traz apenas como alternativa, e não menciona o índice SMP.
