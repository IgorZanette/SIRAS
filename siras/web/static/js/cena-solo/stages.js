/**
 * stages.js — Configuração declarativa da cena 3D do SIRAS.
 *
 * A cena não sabe agronomia: ela interpola parâmetros VISUAIS (0..1) entre
 * estágios e mostra pontos de leitura cujo estado vem de fora (do DOM, que
 * por sua vez vem do servidor). Nenhum número agronômico passa por aqui.
 *
 * NARRATIVA (por que não "solo degradado → solo rico"):
 *   Uma hero que mostra o solo "melhorando" diz, visualmente, que usar o
 *   SIRAS melhora o solo — promessa que o projeto não faz. A narrativa
 *   abaixo conta o que o sistema realmente faz:
 *     1. O solo como está           — perfil neutro, atributos lidos
 *     2. O que a análise revela     — leitura percorre o perfil; limitações aparecem
 *     3. Aptidão potencial          — o MESMO solo após as correções recomendadas:
 *                                     limitações corrigíveis tratadas, permanentes
 *                                     (ex.: CTC, textura) continuam visíveis
 *   Por isso a "vitalidade" muda pouco entre os estágios: o perfil é o mesmo.
 *
 * Parâmetros visuais (todos 0..1):
 *  vitality, plantGrowth, rootGrowth, rootGlow, grassDensity, layerSeparation,
 *  scan (linha de leitura), leitura (visibilidade dos pontos de leitura),
 *  particles, glow, sprouts (brotos extras; mantidos em 0 de propósito),
 *  calagem / adubacao (efeitos de etapa: grânulos que caem e assentam na
 *  superfície; representam a PRÁTICA recomendada e não mudam a cor do solo),
 *  moleculas (CaCO₃ e MgCO₃ em "bola e vareta" sobre o calcário),
 *  npk (selos N, P, K sobre o adubo; a cor identifica o nutriente, nunca a
 *  quantidade), agrupar (na formulação, os grânulos se juntam em três montes
 *  N, P, K: iguais por padrão = proporção ilustrativa; com setNPK() seguem a
 *  formulação REAL calculada pelo servidor).
 *
 * ESCOPO: a cena existe só na interface ATÉ a geração do laudo (página
 * inicial, formulário da análise, tela de espera). O laudo — em tela e
 * impresso — não recebe nada de 3D.
 *
 * `marcadores` diz como os pontos de leitura se apresentam no estágio:
 *   'leitura'      todos como "lido" (sem juízo de valor)
 *   'diagnostico'  atributos com limitação => "limitante"
 *   'potencial'    corrigível => "corrigido"; permanente => "permanente"
 *   'dois-cenarios' alterna diagnóstico ⇄ potencial (fechamento da tela de espera)
 */

const BASE = { vitality: 0.5, plantGrowth: 0.45, rootGrowth: 0.5, rootGlow: 0, grassDensity: 0.45,
  layerSeparation: 0, scan: 0, leitura: 1, particles: 0.24, glow: 0.46, sprouts: 0, calagem: 0, adubacao: 0,
  moleculas: 0, npk: 0, agrupar: 0 };

export const HERO_STAGES = [
  {
    id: 'como-esta',
    label: 'O solo como está',
    durationMs: 6500,
    marcadores: 'leitura',
    targets: { ...BASE },
  },
  {
    id: 'analise-revela',
    label: 'O que a análise revela',
    durationMs: 7500,
    marcadores: 'diagnostico',
    targets: { ...BASE, rootGlow: 0.6, layerSeparation: 1, scan: 1, particles: 0.48, glow: 0.56 },
  },
  {
    id: 'aptidao-potencial',
    label: 'Aptidão potencial',
    durationMs: 8500,
    marcadores: 'potencial',
    // O mesmo solo APÓS as correções recomendadas: o calcário e o adubo ficam
    // visíveis na superfície como a CAUSA da melhora (sem rótulos, para não
    // poluir a hero). Limitações permanentes continuam marcadas.
    targets: { ...BASE, vitality: 0.72, plantGrowth: 0.7, rootGrowth: 0.7, rootGlow: 0.1, grassDensity: 0.7, particles: 0.34, glow: 0.64, calagem: 1, adubacao: 1 },
  },
];

/**
 * Tela de geração do laudo. UM estágio por passo de gerar_laudo(), na ordem
 * em que os módulos são chamados. O avanço vem do atributo data-etapa="N"
 * (1..N) que gerando.js já mantém — a cena só observa esse contrato.
 *
 * AJUSTAR: a sequência abaixo segue a proposta (diagnóstico, calagem,
 * adubação, formulação, aptidão). CONFIRA contra os módulos REAIS de
 * gerar_laudo() e o número de passos de _parciais/gerando.html; remova,
 * reordene ou renomeie. "Laudo pronto" NÃO é um passo: é o fim do último.
 *
 * Regra: a vitalidade do solo NÃO muda entre passos (há teste para isso).
 * Efeitos mostram a prática recomendada; o solo é o mesmo do começo ao fim,
 * exceto no fechamento 'dois-cenarios', que alterna atual ⇄ potencial.
 */
export const PROCESSING_STAGES = [
  { id: 'diagnostico', label: 'Diagnóstico inicial', marcadores: 'leitura',
    targets: { ...BASE, scan: 1, rootGlow: 0.3 } },
  { id: 'calagem', label: 'Calagem', marcadores: 'leitura',
    targets: { ...BASE, calagem: 1, moleculas: 1, scan: 0.3 } },
  // o calcário continua na superfície: as etapas se somam
  { id: 'adubacao', label: 'Adubação', marcadores: 'leitura',
    targets: { ...BASE, calagem: 1, adubacao: 1, npk: 1, rootGlow: 0.5 } },
  { id: 'formulacao', label: 'Formulação', marcadores: 'diagnostico',
    targets: { ...BASE, calagem: 1, adubacao: 1, npk: 1, agrupar: 1 } },
  // Fechamento: os DOIS cenários daquela análise (dados reais vindos do DOM).
  { id: 'aptidao', label: 'Aptidão edáfica', marcadores: 'dois-cenarios',
    targets: { ...BASE, glow: 0.7 } },
];

/** Alvos visuais extras de cada cenário no fechamento 'dois-cenarios'. */
export const CENARIO_TARGETS = {
  // atual: o solo como chegou, sem as correções
  diagnostico: { vitality: 0.5, plantGrowth: 0.45, grassDensity: 0.45, calagem: 0, adubacao: 0, npk: 0, agrupar: 0 },
  // potencial: após calagem e adubação recomendadas (grânulos visíveis = a causa)
  potencial:   { vitality: 0.72, plantGrowth: 0.7, grassDensity: 0.7, calagem: 1, adubacao: 1, npk: 0, agrupar: 0 },
};

/**
 * Converte a classificação de um atributo no estado do ponto de leitura.
 * @param {''|'corrigivel'|'permanente'|'ausente'} limitacao  vem do DOM (data-limitacao)
 * @param {'leitura'|'diagnostico'|'potencial'} modo
 * 'ausente' = não informado na análise: continua assim em qualquer modo
 * (a cena nunca "preenche" um dado que não existe).
 */
export function estadoDoAtributo(limitacao, modo) {
  if (limitacao === 'ausente') return 'ausente';
  if (modo === 'leitura' || !limitacao) return 'lido';
  if (modo === 'diagnostico') return 'limitante';
  return limitacao === 'permanente' ? 'permanente' : 'corrigido';
}

/**
 * Camadas do bloco (de baixo para cima). ILUSTRATIVAS: não são horizontes
 * pedológicos nem profundidades de amostragem, e nunca recebem rótulo.
 */
export const SOIL_LAYERS = [
  { id: 'base',     thickness: 0.34, rich: '#9a8064', dull: '#8d8478', grain: '#5e4c3a', pebbles: 14, pebbleSize: 0.075 },
  { id: 'arenosa',  thickness: 0.30, rich: '#d4b48a', dull: '#bdb1a0', grain: '#9c7f5c', pebbles: 8,  pebbleSize: 0.05  },
  { id: 'argilosa', thickness: 0.26, rich: '#b8763f', dull: '#9e8a76', grain: '#7a4a24', pebbles: 4,  pebbleSize: 0.04  },
  { id: 'vermelha', thickness: 0.22, rich: '#b4532a', dull: '#957d6c', grain: '#6e2f14', pebbles: 2,  pebbleSize: 0.035 },
  { id: 'organica', thickness: 0.44, rich: '#4a3020', dull: '#7a6a58', grain: '#24160c', pebbles: 6,  pebbleSize: 0.04  },
];

/** Paleta. AJUSTAR para os tokens reais de siras-telas.css. */
export const PALETTE = {
  accent: '#8CE23F',
  accentDeep: '#3f8f1f',
  leaf: '#6fd13c',
  leafDry: '#a89a5a',
  moss: '#5fae2e',
  mossDry: '#8a7a4c',
  root: '#c9a06e',
};
