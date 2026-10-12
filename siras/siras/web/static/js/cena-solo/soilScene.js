/**
 * soilScene.js — Motor da cena 3D "transformação do solo" do SIRAS (choreography v7).
 *
 * Framework-agnóstico: usa apenas Three.js. O wrapper React
 * (SoilTransformationScene.jsx) só cria/destroi esta cena; você também
 * pode usá-la em Vue, Svelte ou HTML puro.
 *
 * Toda a geometria é PROCEDURAL (gerada por código), não há modelos GLB.
 * Vantagens: zero assets para baixar, tudo parametrizável e animável.
 * Se no futuro houver um GLB feito no Blender, troque apenas a função
 * correspondente (ex.: buildPlant) — o resto da cena continua igual.
 *
 * No SIRAS, quem cria a cena é o adaptador static/js/cena-solo.js (IIFE).
 * Extensões feitas para o SIRAS: setMarkers() (pontos de leitura por
 * atributo, com estado vindo do DOM) e setReducedMotion() (controle
 * "menos movimento" da aplicação em tempo de execução).
 *
 * Uso mínimo:
 *   import { createSoilScene } from './soilScene.js';
 *   const scene = createSoilScene(containerEl, { onStageChange: (i) => ... });
 *   scene.setStage(2);   // vai para o estágio "potencial produtivo"
 *   scene.dispose();     // SEMPRE ao desmontar (libera GPU e listeners)
 */
import * as THREE from 'three';
import { HERO_STAGES, SOIL_LAYERS, PALETTE } from './stages.js';

/* ------------------------------------------------------------------ */
/* Utilitários                                                          */
/* ------------------------------------------------------------------ */

/** PRNG determinístico (mulberry32): a cena fica igual a cada carga. */
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Value noise 3D simples (hash + interpolação suave), saída em [-1, 1]. */
function hash3(x, y, z) {
  const s = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
  return s - Math.floor(s);
}
function noise3(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const xf = x - xi, yf = y - yi, zf = z - zi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), w = zf * zf * (3 - 2 * zf);
  const lerp = THREE.MathUtils.lerp;
  const c = (dx, dy, dz) => hash3(xi + dx, yi + dy, zi + dz);
  const x00 = lerp(c(0, 0, 0), c(1, 0, 0), u), x10 = lerp(c(0, 1, 0), c(1, 1, 0), u);
  const x01 = lerp(c(0, 0, 1), c(1, 0, 1), u), x11 = lerp(c(0, 1, 1), c(1, 1, 1), u);
  return lerp(lerp(x00, x10, v), lerp(x01, x11, v), w) * 2 - 1;
}

const smoothstep = (a, b, x) => {
  const t = THREE.MathUtils.clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
};

/** Aproximação exponencial independente de FPS (amortecimento). */
const damp = (current, target, speed, dt) => current + (target - current) * (1 - Math.exp(-speed * dt));

/** Cria uma CanvasTexture a partir de uma função de desenho. */
function canvasTexture(size, draw, { srgb = true, repeat = false } = {}) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const tex = new THREE.CanvasTexture(c);
  if (srgb) tex.colorSpace = THREE.SRGBColorSpace;
  if (repeat) tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = 4;
  return tex;
}

/** Gradiente radial (para halo, partículas e sombra de contato). */
function radialTexture(stops) {
  return canvasTexture(128, (ctx, s) => {
    const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
    stops.forEach(([o, c]) => g.addColorStop(o, c));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, s, s);
  });
}

/**
 * Textura de "grãos" do solo em tons de cinza. A cor final vem de
 * material.color (multiplicação), o que permite animar a paleta entre
 * "apagada" e "rica" sem gerar duas texturas.
 */
function soilGrainTexture(rand, density, coarse) {
  return canvasTexture(256, (ctx, s) => {
    ctx.fillStyle = '#e6e6e6';
    ctx.fillRect(0, 0, s, s);
    const dot = (x, y, r, col) => {
      ctx.fillStyle = col;
      // desenha cópias nas bordas para a textura repetir sem emenda
      for (const ox of [-s, 0, s]) for (const oy of [-s, 0, s]) {
        if (x + ox < -r || x + ox > s + r || y + oy < -r || y + oy > s + r) continue;
        ctx.beginPath(); ctx.arc(x + ox, y + oy, r, 0, Math.PI * 2); ctx.fill();
      }
    };
    for (let i = 0; i < 5200 * density; i++) {     // grãos finos, contraste baixo
      const l = Math.floor(165 + rand() * 90);
      dot(rand() * s, rand() * s, 0.4 + rand() * 0.9, `rgb(${l},${l},${l})`);
    }
    for (let i = 0; i < 26 * coarse; i++) {        // agregados com luz em cima
      const x = rand() * s, y = rand() * s, r = 1.2 + rand() * 2.2;
      dot(x, y + r * 0.35, r, 'rgb(150,150,150)');
      dot(x, y, r * 0.8, 'rgb(238,238,238)');
    }
    for (let i = 0; i < 34 * density; i++) {       // poros: pontos escuros pequenos
      dot(rand() * s, rand() * s, 0.7 + rand() * 1.1, 'rgb(72,72,72)');
    }
  }, { repeat: true });
}

/**
 * Textura da superfície em tons de cinza (húmus granulado). A cor vem de
 * material.color: seca/clara no estágio 1, húmus escuro no estágio 3.
 * O verde da superfície vem dos tufos de vegetação, não da textura.
 */
function topSurfaceTexture(rand) {
  return canvasTexture(256, (ctx, s) => {
    ctx.fillStyle = '#c8c8c8';
    ctx.fillRect(0, 0, s, s);
    for (let i = 0; i < 6000; i++) {
      const l = Math.floor(110 + rand() * 145);
      ctx.fillStyle = `rgb(${l},${l},${l})`;
      ctx.beginPath(); ctx.arc(rand() * s, rand() * s, 0.5 + rand() * 1.3, 0, Math.PI * 2); ctx.fill();
    }
  }, { repeat: true });
}

/** Junta várias BufferGeometries indexadas em uma (1 draw call). */
function mergeIndexed(geometries, attrNames) {
  let vCount = 0, iCount = 0;
  geometries.forEach((g) => { vCount += g.attributes.position.count; iCount += g.index.count; });
  const out = new THREE.BufferGeometry();
  const index = new Uint32Array(iCount);
  const arrays = {};
  attrNames.forEach((n) => {
    const size = geometries[0].attributes[n].itemSize;
    arrays[n] = { size, data: new Float32Array(vCount * size) };
  });
  let vOff = 0, iOff = 0;
  geometries.forEach((g) => {
    attrNames.forEach((n) => arrays[n].data.set(g.attributes[n].array, vOff * arrays[n].size));
    for (let i = 0; i < g.index.count; i++) index[iOff + i] = g.index.array[i] + vOff;
    vOff += g.attributes.position.count; iOff += g.index.count;
    g.dispose();
  });
  attrNames.forEach((n) => out.setAttribute(n, new THREE.BufferAttribute(arrays[n].data, arrays[n].size)));
  out.setIndex(new THREE.BufferAttribute(index, 1));
  return out;
}

/** Detecta suporte a WebGL sem criar o renderer completo. */
export function isWebGLAvailable() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch {
    return false;
  }
}

/**
 * true quando o navegador desenha WebGL só com o processador (SwiftShader,
 * llvmpipe, "Microsoft Basic Render"...). Nesses casos a cena pesa demais em
 * máquinas antigas: o adaptador prefere a imagem estática.
 */
export function isSoftwareRenderer() {
  try {
    const c = document.createElement('canvas');
    const gl = c.getContext('webgl2') || c.getContext('webgl');
    if (!gl) return false;
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    const r = String(gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER) || '');
    gl.getExtension('WEBGL_lose_context')?.loseContext();
    return /swiftshader|llvmpipe|softpipe|software|basic render/i.test(r);
  } catch {
    return false;
  }
}

/** Escolhe um perfil de qualidade conforme o dispositivo. */
function resolveQuality(q) {
  if (q !== 'auto') return q;
  const coarse = window.matchMedia?.('(pointer: coarse)').matches;
  const small = Math.min(window.innerWidth, window.innerHeight) < 700;
  const weakCpu = (navigator.hardwareConcurrency || 8) <= 4;
  if ((coarse && small) || weakCpu) return 'low';
  if (coarse || small) return 'medium';
  return 'high';
}

const QUALITY = {
  high:   { dpr: 2,    seg: 44, particles: 260, grassClusters: 170, rootDetail: 1,   crumbs: 22, straw: 260, granules: 170 },
  medium: { dpr: 1.5,  seg: 32, particles: 150, grassClusters: 120, rootDetail: 0.8, crumbs: 14, straw: 170, granules: 110 },
  low:    { dpr: 1.25, seg: 22, particles: 70,  grassClusters: 80,  rootDetail: 0.6, crumbs: 7,  straw: 90,  granules: 60 },
};

/**
 * Linguagem de movimento v6: a cena continua viva, mas sem o aspecto de
 * "objeto flutuando". A prioridade é comunicar mudança de estado com
 * movimentos curtos, amortecidos e intencionais.
 */
const MOTION = {
  idleYaw: 0.026,
  idleBob: 0.007,
  parallaxYaw: 0.09,
  parallaxPitch: 0.026,
  stageDamp: 4.4,
  settleDamp: 4.0,
  markerPulse: 0.045,
  particleDrift: 0.34,
};

const PROCESSING_IDS = new Set(['diagnostico', 'calagem', 'adubacao', 'formulacao', 'aptidao']);

function stageMotion(stage) {
  const id = stage?.id || '';
  // Cada passo tem um enquadramento próprio, mas a diferença é deliberadamente
  // pequena: a coreografia vem da ação, não de movimentos de câmera chamativos.
  if (id === 'analise-revela') return { yaw: -0.045, pitch: 0.012, scale: 1.015 };
  if (id === 'diagnostico') return { yaw: -0.055, pitch: 0.014, scale: 1.022 };
  if (id === 'calagem') return { yaw: -0.028, pitch: -0.012, scale: 1.025 };
  if (id === 'adubacao') return { yaw: 0.032, pitch: 0.002, scale: 1.024 };
  if (id === 'formulacao') return { yaw: 0.012, pitch: 0.012, scale: 1.03 };
  if (id === 'aptidao') return { yaw: 0.036, pitch: -0.008, scale: 0.998 };
  if (id === 'aptidao-potencial') return { yaw: 0.042, pitch: -0.008, scale: 1.02 };
  return { yaw: 0, pitch: 0, scale: 1 };
}

/**
 * Coreografia v7 da tela de geração do laudo.
 * Não cria lógica agronômica: apenas organiza no tempo os elementos visuais
 * existentes. Servidor/DOM continuam sendo a fonte da verdade.
 */
function stageChoreography(stage, t, animate = true) {
  const id = stage?.id || '';
  const reveal = (a, b) => animate ? smoothstep(a, b, t) : 1;
  const pulse = (a, b) => {
    if (!animate) return 0;
    const x = smoothstep(a, b, t);
    return Math.sin(Math.PI * x);
  };
  const base = {
    limeGate: 1,
    moleculeWaves: [1, 1, 1],
    fertGate: 1,
    npkWaves: [1, 1, 1],
    npkLabelWaves: [1, 1, 1],
    groupGate: 1,
    outline: 0,
    outlineScale: 1,
    rootFocus: 0,
    lightLift: 0,
    particleFactor: 1,
    scanGain: 1,
    cameraYaw: 0,
    cameraPitch: 0,
    cameraScale: 0,
  };
  if (!PROCESSING_IDS.has(id)) return base;

  if (id === 'diagnostico') {
    const p = pulse(0.12, 1.18);
    return { ...base,
      outline: 0.055 + 0.17 * p, outlineScale: 1 + 0.014 * p,
      rootFocus: 0.10 * reveal(0.78, 1.45), lightLift: 0.035 * p,
      particleFactor: 0.72, scanGain: 1.08, cameraScale: 0.004 * p };
  }
  if (id === 'calagem') {
    const p = pulse(0.10, 1.35);
    return { ...base,
      limeGate: reveal(0.15, 0.92),
      moleculeWaves: [reveal(0.95, 1.48), reveal(1.20, 1.73), reveal(1.45, 1.98)],
      outline: 0.065 + 0.20 * p, outlineScale: 1 + 0.018 * p,
      lightLift: 0.05 * p, particleFactor: 0.62, scanGain: 0.82,
      cameraPitch: -0.005 * p };
  }
  if (id === 'adubacao') {
    const p = pulse(0.10, 1.55);
    return { ...base,
      fertGate: reveal(0.12, 0.72),
      npkWaves: [reveal(0.16, 0.78), reveal(0.46, 1.08), reveal(0.76, 1.38)],
      npkLabelWaves: [reveal(0.58, 1.08), reveal(0.83, 1.33), reveal(1.08, 1.58)],
      outline: 0.055 + 0.18 * p, outlineScale: 1 + 0.015 * p,
      rootFocus: 0.12 * reveal(1.0, 1.75), lightLift: 0.045 * p,
      particleFactor: 0.68, cameraYaw: 0.010 * p };
  }
  if (id === 'formulacao') {
    const p = pulse(0.18, 1.55);
    const group = reveal(0.24, 1.42);
    return { ...base,
      groupGate: group, outline: 0.07 + 0.19 * p,
      outlineScale: 1 + 0.017 * p, lightLift: 0.04 * p,
      particleFactor: 0.50, cameraScale: 0.010 * group };
  }
  const p = pulse(0.12, 1.42);
  const settle = reveal(0.38, 1.28);
  return { ...base,
    outline: 0.10 + 0.18 * p, outlineScale: 1 + 0.026 * p,
    lightLift: 0.12 * settle, particleFactor: 0.52,
    cameraScale: -0.012 * settle };
}

/* ------------------------------------------------------------------ */
/* Cena                                                                 */
/* ------------------------------------------------------------------ */

/**
 * @param {HTMLElement} container  Elemento que recebe o <canvas> (posicione-o
 *                                 atrás do conteúdo via CSS).
 * @param {object} [opts]
 * @param {Array}   [opts.stages=HERO_STAGES]
 * @param {number}  [opts.initialStage=0]
 * @param {object}  [opts.enterFrom]            Estado de onde a cena ENTRA no primeiro
 *   estágio. Sem ele a cena abre já no estado final do estágio inicial, e a primeira
 *   transição não acontece.
 * @param {boolean} [opts.autoplay=true]       Avança os estágios sozinho.
 * @param {'dark'|'light'} [opts.theme='dark']
 * @param {'auto'|'high'|'medium'|'low'} [opts.quality='auto']
 * @param {boolean} [opts.reducedMotion]       Padrão: prefers-reduced-motion.
 * @param {boolean} [opts.interactive=true]    Paralaxe, hover e clique.
 * @param {boolean} [opts.clickToAdvance=true] Clique no bloco avança o estágio.
 * @param {(w:number,h:number)=>{offsetX:number,offsetY:number,zoom:number}} [opts.layout]
 * @param {boolean} [opts.preserveDrawingBuffer=false] Só para capturas.
 * @param {boolean} [opts.effects=true]  Halo e partículas (blending aditivo).
 * @param {(i:number, stage:object, info:{source:string})=>void} [opts.onStageChange]
 * @param {(layer:object|null)=>void} [opts.onLayerHover]
 * @param {(err:Error)=>void} [opts.onError]
 */
export function createSoilScene(container, opts = {}) {
  const {
    stages = HERO_STAGES,
    initialStage = 0,
    theme: initialTheme = 'dark',
    quality: qualityOpt = 'auto',
    interactive = true,
    clickToAdvance = true,
    preserveDrawingBuffer = false,
    effects = true,           // false: sem halo/partículas (útil para gerar PNG de fallback)
    layout = defaultLayout,
    onStageChange = () => {},
    onLayerHover = () => {},
    onError = (e) => console.error('[SoilScene]', e),
  } = opts;

  if (!isWebGLAvailable()) {
    const err = new Error('WebGL indisponível');
    onError(err);
    throw err;
  }

  const motionQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)');
  let forcedReduced = !!opts.reducedMotion;   // controle "menos movimento" da aplicação
  let reducedMotion = forcedReduced || !!motionQuery?.matches;
  const baseAutoplay = opts.autoplay ?? true;
  let autoplay = baseAutoplay && !reducedMotion;

  const Q = QUALITY[resolveQuality(qualityOpt)];
  const rand = mulberry32(20261010);

  /* ---------- Renderer (fundo transparente real) ---------- */
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,                 // canvas transparente: a página aparece por trás
      powerPreference: 'low-power',// é um fundo decorativo: poupe bateria
      preserveDrawingBuffer,
    });
  } catch (e) {
    onError(e);
    throw e;
  }
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  const canvas = renderer.domElement;
  canvas.setAttribute('aria-hidden', 'true'); // decorativo: leitores de tela ignoram
  canvas.style.cssText = 'display:block;width:100%;height:100%;';
  container.appendChild(canvas);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 50);
  // Câmera em ~30° de azimute: face frontal (+z) dominante, lateral (+x) visível
  const camAzimuth = THREE.MathUtils.degToRad(32);
  camera.position.set(Math.sin(camAzimuth) * 8.4, 2.9, Math.cos(camAzimuth) * 8.4);
  const lookTarget = new THREE.Vector3(0, 0.35, 0);
  camera.lookAt(lookTarget);

  /* ---------- Luzes ---------- */
  const hemi = new THREE.HemisphereLight(0xeaf7e0, 0x20150c, 1.1);
  const key = new THREE.DirectionalLight(0xfff1dc, 2.2);
  key.position.set(3, 6, 5);
  const rim = new THREE.DirectionalLight(new THREE.Color(PALETTE.accent), 1.6); // contraluz verde
  rim.position.set(-5, 2.5, -4);
  const fill = new THREE.DirectionalLight(0xbfd8ff, 0.35);
  fill.position.set(-4, 1, 4);
  scene.add(hemi, key, rim, fill);

  /* ---------- Raiz da composição (recebe paralaxe/flutuação) ---------- */
  const root = new THREE.Group();
  scene.add(root);

  /* ---------- Parâmetros animados ---------- */
  // "params" = valores atuais; "targets" = para onde estão indo.
  /* `enterFrom` existe por causa da tela de espera.
     Sem ele, `params` e `targets` nascem IGUAIS, e o primeiro estágio não tem o que
     animar: a cena abre já no estado final dele. Nos outros usos isso é o certo — a
     hero deve abrir mostrando o solo, e não montando-o. Mas numa sequência de cinco
     etapas, a primeira ficava parada enquanto as outras quatro se moviam, e parecia
     travada, que é como o autor a descreveu em 11/10/2026.
     Com `enterFrom`, `params` começa no repouso e o primeiro estágio é uma transição
     como qualquer outra. */
  const params = { ...stages[initialStage].targets, ...(opts.enterFrom || {}), hover: 0 };
  const targets = { ...stages[initialStage].targets };
  const disposables = [];   // tudo que precisa de .dispose()
  const track = (o) => (disposables.push(o), o);
  const timeUniform = { value: 0 };

  /* ================================================================ */
  /* 1. Bloco de solo em camadas                                      */
  /* ================================================================ */
  const W = 2.0, D = 2.0, R = 0.2;       // largura, profundidade, raio dos cantos
  const N = SOIL_LAYERS.length;
  const totalH = SOIL_LAYERS.reduce((s, l) => s + l.thickness, 0);
  const bases = [-totalH / 2];
  SOIL_LAYERS.forEach((l, i) => bases.push(bases[i] + l.thickness));

  /** Altura da fronteira k (0 = fundo, N = superfície) em (x, z): ondulada. */
  function boundaryY(k, x, z) {
    if (k === 0) return bases[0] + 0.02 * noise3(x * 2, 0, z * 2);
    const amp = k === N ? 0.025 : 0.065;
    const wave = 0.6 * Math.sin(x * 2.1 + k * 1.3) + 0.4 * Math.sin(z * 1.7 + k * 2.1)
      + 0.45 * noise3(x * 1.4 + k * 7, k, z * 1.4);
    return bases[k] + amp * wave;
  }

  /** Mapeia um ponto do quadrado para o "quadrado de cantos arredondados". */
  function roundCorner(x, z) {
    const cx = Math.sign(x) * (W / 2 - R), cz = Math.sign(z) * (D / 2 - R);
    if (Math.abs(x) > W / 2 - R && Math.abs(z) > D / 2 - R) {
      const dx = x - cx, dz = z - cz;
      const len = Math.hypot(dx, dz) || 1;
      const k = Math.max(Math.abs(dx), Math.abs(dz)) / len;
      return [cx + dx * k, cz + dz * k, dx / len, dz / len, true];
    }
    return [x, z, 0, 0, false];
  }

  /**
   * Constrói uma camada: BoxGeometry subdividida cujos vértices são
   * deformados (cantos arredondados, topo/fundo ondulados, laterais
   * irregulares). UVs são recalculados por projeção planar para que os
   * grãos da textura não fiquem esticados.
   */
  function buildSlabGeometry(k) {
    const seg = Q.seg;
    const g = new THREE.BoxGeometry(1, 1, 1, seg, 5, seg);
    const pos = g.attributes.position, nor = g.attributes.normal, uv = g.attributes.uv;
    const sideNormals = [];
    for (let i = 0; i < pos.count; i++) {
      const ux = pos.getX(i), uy = pos.getY(i), uz = pos.getZ(i);
      const nx = nor.getX(i), ny = nor.getY(i), nz = nor.getZ(i);
      let [x, z, cnx, cnz, corner] = roundCorner(ux * W, uz * D);
      const t = uy + 0.5;
      let y = THREE.MathUtils.lerp(boundaryY(k, x, z), boundaryY(k + 1, x, z), t);
      const isSide = Math.abs(ny) < 0.5;
      if (isSide) {
        // normal horizontal "para fora" (arco no canto, face reta no resto)
        const ox = corner ? cnx : nx, oz = corner ? cnz : nz;
        const bump = 0.012 * noise3(x * 6, y * 6, z * 6);
        x += ox * bump; z += oz * bump;
        sideNormals.push([i, ox, oz]);
      }
      pos.setXYZ(i, x, y, z);
      // projeção planar pelo eixo dominante da normal original
      const sc = 1.5; // repetições da textura por unidade (grão mais fino)
      if (Math.abs(ny) > 0.5) uv.setXY(i, x * sc, z * sc);
      else if (Math.abs(nx) > Math.abs(nz)) uv.setXY(i, z * sc + k * 0.37, y * sc);
      else uv.setXY(i, x * sc + k * 0.37, y * sc);
    }
    g.computeVertexNormals();
    // laterais: normal analítica (evita costuras de sombreamento no arco)
    sideNormals.forEach(([i, ox, oz]) => nor.setXYZ(i, ox, 0, oz));
    nor.needsUpdate = true;
    return g;
  }

  const pebbleGeo = track(new THREE.IcosahedronGeometry(1, 2));
  {
    // deforma a esfera para parecer pedra
    const p = pebbleGeo.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const v = new THREE.Vector3().fromBufferAttribute(p, i);
      v.multiplyScalar(1 + 0.18 * noise3(v.x * 2.3, v.y * 2.3, v.z * 2.3));
      p.setXYZ(i, v.x, v.y * 0.8, v.z);
    }
    pebbleGeo.computeVertexNormals();
  }
  const pebbleMat = track(new THREE.MeshStandardMaterial({ color: 0x6f655a, roughness: 0.7 }));

  const layers = SOIL_LAYERS.map((cfg, k) => {
    const group = new THREE.Group();
    const tex = track(soilGrainTexture(rand, k === N - 1 ? 1.3 : 1, cfg.pebbles / 6));
    const sideMat = track(new THREE.MeshStandardMaterial({
      map: tex, bumpMap: tex, bumpScale: 2.5, roughness: 0.95, metalness: 0,
      emissive: new THREE.Color(PALETTE.accent), emissiveIntensity: 0,
    }));
    let material = sideMat;
    let topMat = null;
    if (k === N - 1) {
      const ttex = track(topSurfaceTexture(rand));
      topMat = track(new THREE.MeshStandardMaterial({ map: ttex, bumpMap: ttex, bumpScale: 3, roughness: 1 }));
      // ordem dos grupos da BoxGeometry: +x, -x, +y(topo), -y, +z, -z
      material = [sideMat, sideMat, topMat, sideMat, sideMat, sideMat];
    }
    const mesh = new THREE.Mesh(track(buildSlabGeometry(k)), material);
    mesh.userData.layerIndex = k;
    group.add(mesh);

    // Pedras incrustadas nas faces laterais
    const count = cfg.pebbles;
    const pebbles = new THREE.InstancedMesh(pebbleGeo, pebbleMat, Math.max(count, 1));
    pebbles.count = count;
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
    for (let i = 0; i < count; i++) {
      const size = cfg.pebbleSize * (0.6 + rand() * 0.8);
      const face = rand();
      const s = (rand() * 2 - 1) * (W / 2 - R - 0.05);
      let x, z;
      if (face < 0.42) { x = s; z = D / 2 - size * 0.35; }
      else if (face < 0.84) { x = W / 2 - size * 0.35; z = s; }
      else if (face < 0.92) { x = s; z = -D / 2 + size * 0.35; }
      else { x = -W / 2 + size * 0.35; z = s; }
      const y0 = boundaryY(k, x, z) + size, y1 = boundaryY(k + 1, x, z) - size;
      if (y1 <= y0) { m.makeScale(0, 0, 0); pebbles.setMatrixAt(i, m); continue; }
      const y = THREE.MathUtils.lerp(y0, y1, rand());
      e.set(rand() * 3, rand() * 3, rand() * 3);
      m.compose(new THREE.Vector3(x, y, z), q.setFromEuler(e),
        new THREE.Vector3(size * (1 + rand() * 0.4), size, size * (1 + rand() * 0.3)));
      pebbles.setMatrixAt(i, m);
    }
    group.add(pebbles);
    root.add(group);
    return { cfg, group, mesh, sideMat, topMat, pebbles, hover: 0,
      rich: new THREE.Color(cfg.rich), dull: new THREE.Color(cfg.dull) };
  });
  const topLayer = layers[N - 1];
  const surfaceY = (x, z) => boundaryY(N, x, z);

  /* ---------- Torrões sobre a superfície ---------- */
  {
    const clods = new THREE.InstancedMesh(pebbleGeo, track(new THREE.MeshStandardMaterial({ color: 0x3f2b1c, roughness: 1 })), 10);
    const m = new THREE.Matrix4(), q = new THREE.Quaternion();
    for (let i = 0; i < 10; i++) {
      const x = (rand() * 2 - 1) * 0.8, z = (rand() * 2 - 1) * 0.8;
      const s = 0.03 + rand() * 0.04;
      m.compose(new THREE.Vector3(x, surfaceY(x, z) + s * 0.3, z),
        q.setFromEuler(new THREE.Euler(rand() * 3, rand() * 3, 0)), new THREE.Vector3(s * 1.3, s, s));
      clods.setMatrixAt(i, m);
    }
    topLayer.group.add(clods);
  }

  const PLANT_Z_CONST = 0.45; // posição z da muda (usada antes de PLANT_Z)
  // Montes N, P, K da formulação: na frente do topo, onde a câmera vê melhor.
  const HEAPS = [[-0.52, 0.6], [0.04, 0.78], [0.56, 0.5]];
  // Manchas de palhada: a grama desvia delas para a cobertura aparecer.
  const STRAW_PATCHES = Array.from({ length: 9 }, () => [(rand() * 2 - 1) * 0.75, (rand() * 2 - 1) * 0.75]);
  const livre = (x, z, raioPalha, raioMonte) =>
    STRAW_PATCHES.every(([px, pz]) => Math.hypot(x - px, z - pz) > raioPalha) &&
    HEAPS.every(([hx, hz]) => Math.hypot(x - hx, z - hz) > raioMonte);

  /* ---------- Agregados nas faces de corte (por camada) ---------- */
  // Pequenos grumos em relevo, na cor da própria camada: dão volume ao corte
  // sem nenhum arquivo de modelo.
  const crumbGeo = track(new THREE.IcosahedronGeometry(1, 0));
  layers.forEach((L, k) => {
    const mat = track(new THREE.MeshStandardMaterial({ color: L.cfg.rich, roughness: 1, flatShading: true }));
    const n = Q.crumbs;
    const inst = new THREE.InstancedMesh(crumbGeo, mat, n);
    const m = new THREE.Matrix4(), q = new THREE.Quaternion();
    for (let i = 0; i < n; i++) {
      const size = 0.012 + rand() * 0.02;
      const s = (rand() * 2 - 1) * (W / 2 - R - 0.04);
      const front = rand() < 0.55;
      const x = front ? s : W / 2 - size * 0.3, z = front ? D / 2 - size * 0.3 : s;
      const y0 = boundaryY(k, x, z) + size, y1 = boundaryY(k + 1, x, z) - size;
      const y = y1 > y0 ? THREE.MathUtils.lerp(y0, y1, rand()) : -99;
      m.compose(new THREE.Vector3(x, y, z), q.setFromEuler(new THREE.Euler(rand() * 3, rand() * 3, rand() * 3)),
        new THREE.Vector3(size * 1.3, size, size * 1.1).multiplyScalar(y > -90 ? 1 : 0));
      inst.setMatrixAt(i, m);
    }
    L.group.add(inst);
    L.crumbMat = mat;
    L.crumbs = inst;
  });

  /* ---------- Palhada (cobertura morta) ---------- */
  // Fragmentos achatados e levemente curvos de colmo/folha seca, deitados e
  // sobrepostos em manchas: a cobertura típica do plantio direto. Cada
  // fragmento tem tom próprio (palha nova, palha velha, em decomposição).
  const strawMat = track(new THREE.MeshStandardMaterial({ roughness: 0.85, side: THREE.DoubleSide }));
  {
    const g = new THREE.PlaneGeometry(1, 1, 8, 1);
    const pp = g.attributes.position;
    for (let i = 0; i < pp.count; i++) {
      const x = pp.getX(i);
      pp.setZ(i, Math.sin((x + 0.5) * Math.PI) * 0.012);  // arqueado ao longo do comprimento
    }
    g.rotateX(-Math.PI / 2);
    g.computeVertexNormals();
    track(g);
    const n = Q.straw;
    const straw = new THREE.InstancedMesh(g, strawMat, n);
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
    const tons = ['#dcc791', '#cdb67b', '#c0a667', '#e5d6a6', '#a98f58', '#8c7549', '#d3bf8a'];
    // 70% nas manchas (cobertura densa), 30% espalhados
    for (let i = 0; i < n; i++) {
      const [cx, cz] = i % 10 < 7 ? STRAW_PATCHES[i % STRAW_PATCHES.length] : [(rand() * 2 - 1) * 0.8, (rand() * 2 - 1) * 0.8];
      const espalhar = i % 10 < 7 ? 0.36 : 0.2;
      let x = cx + (rand() - 0.5) * espalhar, z = cz + (rand() - 0.5) * espalhar;
      [x, z] = roundCorner(THREE.MathUtils.clamp(x, -W / 2 + 0.06, W / 2 - 0.06), THREE.MathUtils.clamp(z, -D / 2 + 0.06, D / 2 - 0.06));
      if (Math.hypot(x, z - PLANT_Z_CONST) < 0.09) z -= 0.12;  // não cobre a base da muda
      const comp = 0.08 + rand() * 0.18, larg = 0.01 + rand() * 0.016;
      m.compose(new THREE.Vector3(x, surfaceY(x, z) + 0.003 + (i % 4) * 0.0015, z),
        q.setFromEuler(new THREE.Euler((rand() - 0.5) * 0.12, rand() * Math.PI, (rand() - 0.5) * 0.12)),
        new THREE.Vector3(comp, 1, larg));
      straw.setMatrixAt(i, m);
      straw.setColorAt(i, c.set(tons[Math.floor(rand() * tons.length)]));
    }
    topLayer.group.add(straw);
    layers[N - 1].straw = straw;
  }

  /* ---------- Efeitos de etapa: calcário e adubo ---------- */
  // Representam a PRÁTICA que o laudo recomenda (calagem e adubação), não um
  // resultado medido. A cor do solo não muda durante a espera.
  //  - Calcário: pó/grânulos finos, brancos e foscos.
  //  - Adubo: grânulos maiores e brilhantes, em TRÊS cores de IDENTIDADE
  //    (N azul, P laranja, K rosa). A cor diz QUAL nutriente, nunca QUANTO.
  //  - Na formulação, os grânulos se agrupam em três montes N, P e K. Sem
  //    dado real os montes têm o MESMO tamanho (proporção ilustrativa); com
  //    setNPK([n,p,k]) vindo do servidor, seguem a formulação calculada.
  const NPK_COR = { N: '#4f9fe0', P: '#f0972e', K: '#e0517c' };
  const NPK = ['N', 'P', 'K'];
  const granuleGeo = track(new THREE.IcosahedronGeometry(1, 1));
  function buildGranules(count, opts) {
    const mat = track(new THREE.MeshStandardMaterial({ roughness: opts.rough, metalness: 0 }));
    const mesh = new THREE.InstancedMesh(granuleGeo, mat, count);
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    const items = [];
    const c = new THREE.Color();
    const porTipo = [0, 0, 0];
    for (let i = 0; i < count; i++) {
      const [x, z] = roundCorner((rand() * 2 - 1) * (W / 2 - 0.08), (rand() * 2 - 1) * (D / 2 - 0.08));
      const tipo = opts.npk ? i % 3 : -1;
      const it = { x, z, y0: surfaceY(x, z) + 0.9 + rand() * 0.9, y1: surfaceY(x, z) + opts.size * 0.6,
        delay: rand() * 0.6, speed: 0.55 + rand() * 0.5, s: opts.size * (0.75 + rand() * 0.5), g: 0, tipo, ativo: true };
      if (opts.npk) {
        // posição no monte: espiral (ângulo áureo) a partir do centro
        const j = porTipo[tipo]++;
        const r = 0.03 * Math.sqrt(j), a = j * 2.39996;
        const [hx, hz] = HEAPS[tipo];
        it.j = j;
        it.hx = hx + Math.cos(a) * r; it.hz = hz + Math.sin(a) * r;
        it.hy = surfaceY(it.hx, it.hz) + opts.size * 0.6 + Math.max(0, 0.14 - r) * 0.9; // monte
        mesh.setColorAt(i, c.set(NPK_COR[NPK[tipo]]).offsetHSL(0, 0, (rand() - 0.5) * 0.08));
      } else {
        mesh.setColorAt(i, c.set(opts.colors[Math.floor(rand() * opts.colors.length)]));
      }
      items.push(it);
    }
    topLayer.group.add(mesh);
    return { mesh, items, vis: 0, agrupado: 0, porTipo };
  }
  const nG = Q.granules;
  const lime = buildGranules(Math.round(nG * 1.3), { colors: ['#f5f2eb', '#ebe7de', '#fbfaf6', '#e2ddd2'], size: 0.012, rough: 0.95 });
  const fert = buildGranules(Math.round(nG * 0.75), { npk: true, size: 0.026, rough: 0.3 });

  /** Proporção dos montes: null = ilustrativa (iguais); [n,p,k] = dado real. */
  function setNPK(ratio) {
    const max = ratio ? Math.max(...ratio, 1e-6) : 1;
    fert.items.forEach((it) => {
      const total = fert.porTipo[it.tipo];
      const mostrar = ratio ? Math.round(total * ratio[it.tipo] / max) : total;
      it.ativo = it.j < mostrar; // espiral: os de dentro ficam, o monte encolhe por fora
    });
    requestRender();
  }

  const _gm = new THREE.Matrix4(), _gq = new THREE.Quaternion(), _gs = new THREE.Vector3(), _gp = new THREE.Vector3();
  function updateGranules(sys, target, dt, animate, agrupar = 0, typeReveal = null) {
    sys.vis = animate ? damp(sys.vis, target, 3.4, dt) : target;
    sys.agrupado = animate ? damp(sys.agrupado, agrupar, 1.9, dt) : agrupar;
    const active = target > 0.5;
    const a = smoothstep(0, 1, sys.agrupado);
    sys.items.forEach((it, i) => {
      const reveal = it.tipo >= 0 && typeReveal ? (typeReveal[it.tipo] ?? 1) : 1;
      const canFall = active && reveal > 0.03;
      if (!animate) it.g = canFall ? 1 : 0;
      else if (canFall) it.g = Math.min(1, it.g + dt * it.speed * (it.g > 0 || sys.vis > it.delay ? 1 : 0));
      else if (sys.vis < 0.02) it.g = 0;
      const e = it.g * it.g;
      _gp.set(it.x, THREE.MathUtils.lerp(it.y0, it.y1, e), it.z);
      if (it.hx !== undefined && a > 0) {
        // Formulação: convergência curta e legível, sem explosão de partículas.
        _gp.x = THREE.MathUtils.lerp(_gp.x, it.hx, a);
        _gp.z = THREE.MathUtils.lerp(_gp.z, it.hz, a);
        _gp.y = THREE.MathUtils.lerp(_gp.y, it.hy, a) + Math.sin(a * Math.PI) * 0.10;
      }
      const sumir = it.ativo || a < 0.5 ? 1 : 1 - smoothstep(0.5, 0.9, a);
      const wave = it.tipo >= 0 ? reveal : 1;
      _gs.setScalar(it.s * sys.vis * wave * (it.g > 0 ? 1 : 0) * sumir);
      _gm.compose(_gp, _gq, _gs);
      sys.mesh.setMatrixAt(i, _gm);
    });
    sys.mesh.instanceMatrix.needsUpdate = true;
    sys.mesh.visible = sys.vis > 0.01;
  }

  /* ---------- Rótulos químicos: moléculas do calcário e N, P, K ---------- */
  /** Texto com dígitos em subscrito (CaCO3 -> CaCO₃) numa "pílula". */
  function labelTexture(texto, cor) {
    return canvasTexture(256, (ctx, S) => {
      const h = S / 2;
      ctx.clearRect(0, 0, S, S);
      ctx.fillStyle = 'rgba(10,15,12,0.78)';
      const rr = 30, x0 = 8, y0 = h / 2 + 8, w = S - 16, hh = h - 16;
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x0, y0, w, hh, rr) : ctx.rect(x0, y0, w, hh); ctx.fill();
      ctx.strokeStyle = cor; ctx.lineWidth = 4; ctx.stroke();
      // mede e desenha caractere a caractere (dígito = subscrito)
      const big = '600 64px system-ui, "Segoe UI", sans-serif', small = '600 40px system-ui, "Segoe UI", sans-serif';
      let total = 0;
      for (const ch of texto) { ctx.font = /\d/.test(ch) ? small : big; total += ctx.measureText(ch).width; }
      let x = S / 2 - total / 2;
      const base = y0 + hh / 2 + 22;
      ctx.fillStyle = '#f4f7f1';
      for (const ch of texto) {
        const sub = /\d/.test(ch);
        ctx.font = sub ? small : big;
        ctx.fillText(ch, x, base + (sub ? 12 : 0));
        x += ctx.measureText(ch).width;
      }
    });
  }
  function badgeTexture(letra, cor) {
    return canvasTexture(128, (ctx, S) => {
      ctx.fillStyle = cor; ctx.beginPath(); ctx.arc(S / 2, S / 2, S / 2 - 6, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 5; ctx.stroke();
      ctx.fillStyle = '#ffffff'; ctx.font = '700 66px system-ui, "Segoe UI", sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(letra, S / 2, S / 2 + 4);
    });
  }

  // Moléculas "bola e vareta": carbonato (C no centro, 3 O em triângulo) +
  // o cátion (Ca ou Mg). CaCO₃ e MgCO₃ = carbonatos que compõem o calcário
  // (calcítico ou dolomítico). Qual corretivo usar fica no TEXTO do laudo.
  const atomGeo = track(new THREE.IcosahedronGeometry(1, 2));
  const bondGeo = track(new THREE.CylinderGeometry(1, 1, 1, 8));
  const ATOM_COR = { C: '#3d4248', O: '#e2534b', Ca: '#7fcf62', Mg: '#cfd96a' };
  const atomMats = Object.fromEntries(Object.entries(ATOM_COR).map(([k, v]) =>
    [k, track(new THREE.MeshStandardMaterial({ color: v, roughness: 0.35, transparent: true }))]));
  const bondMat = track(new THREE.MeshStandardMaterial({ color: '#d9d9d9', roughness: 0.5, transparent: true }));
  function bond(a, b, r) {
    const m = new THREE.Mesh(bondGeo, bondMat);
    const d = b.clone().sub(a);
    m.position.copy(a).addScaledVector(d, 0.5);
    m.scale.set(r, d.length(), r);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
    return m;
  }
  function molecule(cation, x, z, fase) {
    const g = new THREE.Group();
    const C = new THREE.Vector3(0, 0, 0);
    const Os = [0, 1, 2].map((k) => new THREE.Vector3(Math.cos(k * 2.094) * 0.06, 0, Math.sin(k * 2.094) * 0.06));
    const M = Os[0].clone().multiplyScalar(2.1);
    const add = (el, v, r) => { const a = new THREE.Mesh(atomGeo, atomMats[el]); a.position.copy(v); a.scale.setScalar(r); g.add(a); };
    add('C', C, 0.022); Os.forEach((o) => { add('O', o, 0.02); g.add(bond(C, o, 0.006)); });
    add(cation, M, 0.03); g.add(bond(Os[0], M, 0.004));
    const spr = new THREE.Sprite(track(new THREE.SpriteMaterial({ map: track(labelTexture(cation + 'CO3', ATOM_COR[cation])), transparent: true, depthWrite: false, depthTest: false })));
    spr.scale.set(0.3, 0.3, 1);
    const wrap = new THREE.Group();
    wrap.add(g, spr);
    spr.position.set(0, 0.13, 0);
    wrap.position.set(x, surfaceY(x, z) + 0.36, z);
    topLayer.group.add(wrap);
    return { wrap, g, spr, fase };
  }
  const moleculas = [molecule('Ca', -0.55, 0.35, 0), molecule('Ca', 0.6, -0.1, 2.1), molecule('Mg', -0.15, -0.55, 4.2)];

  // Selos N, P e K: flutuam sobre a área adubada e, na formulação, descem
  // para cima de cada monte.
  const selos = NPK.map((el, k) => {
    const spr = new THREE.Sprite(track(new THREE.SpriteMaterial({ map: track(badgeTexture(el, NPK_COR[el])), transparent: true, depthWrite: false, depthTest: false })));
    spr.scale.setScalar(0.13);
    topLayer.group.add(spr);
    const [hx, hz] = HEAPS[k];
    return { spr, solto: new THREE.Vector3(hx * 1.1, surfaceY(hx, hz) + 0.42, hz - 0.35), monte: new THREE.Vector3(hx, surfaceY(hx, hz) + 0.27, hz), fase: k * 2 };
  });
  const rot = { mol: 0, npk: 0 };
  function updateRotulos(t, dt, animate, cue) {
    rot.mol = animate ? damp(rot.mol, params.moleculas ?? 0, 3.2, dt) : (params.moleculas ?? 0);
    rot.npk = animate ? damp(rot.npk, params.npk ?? 0, 3.2, dt) : (params.npk ?? 0);
    moleculas.forEach((m, i) => {
      const local = rot.mol * (cue?.moleculeWaves?.[i] ?? 1);
      m.wrap.visible = local > 0.01;
      m.wrap.scale.setScalar(0.62 + 0.38 * local);
      m.g.rotation.y = animate ? t * 0.34 + m.fase : m.fase;
      m.g.rotation.x = animate ? 0.22 + Math.sin(t * 0.55 + m.fase) * 0.12 : 0.22;
      m.wrap.position.y = surfaceY(m.wrap.position.x, m.wrap.position.z) + 0.36
        + (animate ? Math.sin(t * 0.75 + m.fase) * 0.012 : 0);
      m.g.children.forEach((c) => { c.material.opacity = local; });
      m.spr.material.opacity = local;
    });
    const a = smoothstep(0, 1, fert.agrupado);
    selos.forEach((s, i) => {
      const local = rot.npk * (cue?.npkLabelWaves?.[i] ?? 1);
      s.spr.visible = local > 0.01;
      s.spr.material.opacity = local;
      s.spr.position.lerpVectors(s.solto, s.monte, a);
      if (animate) s.spr.position.y += Math.sin(t * 0.9 + s.fase) * 0.008 * (1 - a);
    });
  }

  /* ================================================================ */
  /* 2. Vegetação rasteira (tufos + trevos, vento no shader)          */
  /* ================================================================ */
  // Folha de grama: mais segmentos, base mais escura (cor por vértice) e
  // largura/altura/tom variando por instância.
  const blade = new THREE.PlaneGeometry(1, 1, 1, 6);
  blade.translate(0, 0.5, 0);
  {
    const p = blade.attributes.position;
    const cols = [];
    for (let i = 0; i < p.count; i++) {
      const y = p.getY(i);
      p.setX(i, p.getX(i) * 0.034 * Math.pow(1 - y, 0.7)); // afina até a ponta
      p.setZ(i, y * y * 0.16);                               // curva natural
      const sh = 0.5 + 0.55 * y;
      cols.push(sh * 0.95, sh, sh * 0.9);
    }
    blade.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
    blade.computeVertexNormals();
  }
  track(blade);
  const grassMat = track(new THREE.MeshStandardMaterial({ color: PALETTE.moss, roughness: 0.55, side: THREE.DoubleSide, vertexColors: true }));
  const windShader = (shader) => {
    // Vento barato: desloca só a ponta da folha (position.y ~ altura 0..1)
    shader.uniforms.uTime = timeUniform;
    shader.vertexShader = 'uniform float uTime;\n' + shader.vertexShader.replace(
      '#include <begin_vertex>',
      `#include <begin_vertex>
       vec4 ip = instanceMatrix[3];
       float h = position.y * position.y;
       transformed.x += sin(uTime * 1.45 + ip.x * 5.0 + ip.z * 3.0) * 0.035 * h;
       transformed.z += cos(uTime * 1.1 + ip.z * 4.0) * 0.024 * h;`);
  };
  grassMat.onBeforeCompile = windShader;
  const grassItems = [];
  for (let c = 0, tentativas = 0; c < Q.grassClusters && tentativas < Q.grassClusters * 6; tentativas++) {
    const cx = (rand() * 2 - 1) * (W / 2 - 0.08), cz = (rand() * 2 - 1) * (D / 2 - 0.08);
    const [rx, rz] = roundCorner(cx, cz);
    if (!livre(rx, rz, 0.16, 0.2)) continue;
    c++;
    const threshold = rand() * 0.92;            // densidade em que o tufo aparece
    const blades = 6 + Math.floor(rand() * 7);
    const alto = 0.05 + rand() * 0.09;          // tufos baixos e altos
    for (let b = 0; b < blades; b++) {
      const ang = rand() * Math.PI * 2, rad = rand() * 0.05;
      const x = rx + Math.cos(ang) * rad, z = rz + Math.sin(ang) * rad;
      grassItems.push({
        pos: new THREE.Vector3(x, surfaceY(x, z) - 0.004, z),
        // inclinação "para fora" do centro do tufo, como numa touceira
        rot: new THREE.Euler(Math.sin(ang) * 0.45 * (rad / 0.05), ang + Math.PI / 2, -Math.cos(ang) * 0.45 * (rad / 0.05)),
        height: alto * (0.6 + rand() * 0.7),
        width: 0.7 + rand() * 0.8,
        threshold,
      });
    }
  }
  const grass = new THREE.InstancedMesh(blade, grassMat, grassItems.length);
  grass.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  {
    const c = new THREE.Color();
    const tons = [[1, 1, 1], [0.86, 0.96, 0.78], [1.08, 1.02, 0.82], [0.78, 0.9, 0.74], [1.12, 1.06, 0.9]];
    grassItems.forEach((_, i) => { const t = tons[Math.floor(rand() * tons.length)]; grass.setColorAt(i, c.setRGB(t[0], t[1], t[2])); });
  }
  topLayer.group.add(grass);

  // Trevos (folhas largas rasteiras): 3 folíolos em coração, instanciados.
  const cloverGeo = (() => {
    const parts = [0, 1, 2].map((k) => {
      const shp = new THREE.Shape();
      shp.moveTo(0, 0);
      shp.bezierCurveTo(0.012, 0.004, 0.026, 0.02, 0.016, 0.03);
      shp.bezierCurveTo(0.01, 0.036, 0.002, 0.03, 0, 0.026);
      shp.bezierCurveTo(-0.002, 0.03, -0.01, 0.036, -0.016, 0.03);
      shp.bezierCurveTo(-0.026, 0.02, -0.012, 0.004, 0, 0);
      const g = new THREE.ShapeGeometry(shp, 6);
      g.rotateX(-Math.PI / 2 + 0.25);           // quase deitado, levemente em taça
      g.rotateY(k * 2.094);
      g.translate(0, 0.012, 0);
      return g;
    });
    return track(mergeIndexed(parts, ['position', 'normal']));
  })();
  const cloverMat = track(new THREE.MeshStandardMaterial({ color: '#5aa83a', roughness: 0.5, side: THREE.DoubleSide }));
  const cloverItems = Array.from({ length: Math.round(Q.grassClusters * 0.35) }, () => {
    let x, z, n = 0;
    do { [x, z] = roundCorner((rand() * 2 - 1) * (W / 2 - 0.1), (rand() * 2 - 1) * (D / 2 - 0.1)); } while (!livre(x, z, 0.12, 0.2) && ++n < 20);
    return { pos: new THREE.Vector3(x, surfaceY(x, z) + 0.002, z), rot: new THREE.Euler(0, rand() * 6.28, 0), s: 0.8 + rand() * 0.7, threshold: 0.15 + rand() * 0.8 };
  });
  const clover = new THREE.InstancedMesh(cloverGeo, cloverMat, cloverItems.length);
  clover.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  topLayer.group.add(clover);

  let lastGrassDensity = -1;
  const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _s = new THREE.Vector3();
  function updateGrass(density) {
    if (Math.abs(density - lastGrassDensity) < 0.002) return;
    lastGrassDensity = density;
    grassItems.forEach((it, i) => {
      const k = smoothstep(it.threshold, it.threshold + 0.12, density);
      _s.set(k * it.width, it.height * k, k);
      _m.compose(it.pos, _q.setFromEuler(it.rot), _s);
      grass.setMatrixAt(i, _m);
    });
    grass.instanceMatrix.needsUpdate = true;
    cloverItems.forEach((it, i) => {
      const k = smoothstep(it.threshold, it.threshold + 0.15, density);
      _m.compose(it.pos, _q.setFromEuler(it.rot), _s.setScalar(it.s * k));
      clover.setMatrixAt(i, _m);
    });
    clover.instanceMatrix.needsUpdate = true;
  }

  /* ================================================================ */
  /* 3. Muda genérica (a MESMA para todas as culturas)                */
  /* ================================================================ */
  /**
   * Folha em grade fina: margem levemente serrilhada, dobra na nervura,
   * nervuras laterais clareadas por cor de vértice, ponta curvada e leve
   * torção. `forma` < 1 deixa a folha mais arredondada (cotilédone).
   */
  function leafGeometry(L, w, { forma = 0.8, serra = 1 } = {}) {
    const nL = 24, nW = 10;
    const pos = [], col = [], idx = [];
    for (let i = 0; i <= nL; i++) {
      const u = i / nL;
      let half = w * Math.pow(Math.sin(Math.PI * Math.pow(u, forma)), 0.85);
      if (u > 0.12 && u < 0.97) half *= 1 - 0.05 * serra * Math.abs(Math.sin(u * 46)); // serrilhado
      const twist = (u - 0.3) * 0.35;
      for (let j = 0; j <= nW; j++) {
        const v = (j / nW) * 2 - 1;
        const x = u * L;
        let z = v * half;
        let y = Math.abs(z) * 0.5 + 0.22 * x - 0.65 * (x * x) / L; // dobra + arqueamento
        // torção suave ao longo do comprimento
        const zy = z * Math.cos(twist) - y * Math.sin(twist), yy = z * Math.sin(twist) + y * Math.cos(twist);
        z = zy; y = yy;
        pos.push(x, y, z);
        // sombreamento: base mais escura, nervura central e laterais mais claras,
        // margem levemente amarelada
        const lateral = Math.abs(((u - Math.abs(v) * 0.38) * 7) % 1 - 0.5) < 0.07 && u > 0.08 && Math.abs(v) < 0.85;
        let r = 0.68 + 0.32 * u, g = 0.72 + 0.3 * u, b = 0.66 + 0.28 * u;
        if (Math.abs(v) < 0.09) { r += 0.2; g += 0.18; b += 0.1; }
        else if (lateral) { r += 0.08; g += 0.09; b += 0.04; }
        if (Math.abs(v) > 0.85) { r += 0.06; g += 0.02; b -= 0.06; }
        col.push(r, g, b);
      }
    }
    for (let i = 0; i < nL; i++) for (let j = 0; j < nW; j++) {
      const a = i * (nW + 1) + j, b2 = a + nW + 1;
      idx.push(a, b2, a + 1, b2, b2 + 1, a + 1);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    return track(g);
  }

  const leafMat = track(new THREE.MeshStandardMaterial({
    color: PALETTE.leaf, vertexColors: true, roughness: 0.38, side: THREE.DoubleSide,
    emissive: new THREE.Color(PALETTE.accentDeep), emissiveIntensity: 0.12,
  }));
  const stemMat = track(new THREE.MeshStandardMaterial({ color: 0x8fd35a, roughness: 0.5, vertexColors: true }));
  const petioleGeo = track(new THREE.CylinderGeometry(0.006, 0.009, 1, 6).translate(0, 0.5, 0).rotateZ(-Math.PI / 2));

  /** Cria uma planta; scale define o porte máximo. Retorna o objeto e um updater. */
  function buildPlant(scale, seedOffset) {
    const plant = new THREE.Group();
    const r2 = mulberry32(99 + seedOffset);
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, -0.02, 0), new THREE.Vector3(0.025, 0.25, 0.01),
      new THREE.Vector3(-0.02, 0.5, 0), new THREE.Vector3(0.015, 0.76, -0.01),
      new THREE.Vector3(0, 1.0, 0),
    ]);
    const stemGeo = new THREE.TubeGeometry(curve, 48, 0.03, 8);
    { // afina o caule, engrossa nos nós e escurece a base
      const p = stemGeo.attributes.position, cols = [];
      const nos = [0.16, 0.38, 0.6, 0.8, 0.95];
      for (let i = 0; i < p.count; i++) {
        const ring = Math.floor(i / 9) / 48;
        const c = curve.getPointAt(Math.min(ring, 1));
        const no = nos.some((n) => Math.abs(ring - n) < 0.015) ? 1.25 : 1;
        const k = (1 - 0.55 * ring) * no;
        p.setXYZ(i, c.x + (p.getX(i) - c.x) * k, p.getY(i), c.z + (p.getZ(i) - c.z) * k);
        const sh = 0.72 + 0.35 * ring;
        cols.push(sh, sh, sh * 0.95);
      }
      stemGeo.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
      stemGeo.computeVertexNormals();
    }
    plant.add(new THREE.Mesh(track(stemGeo), stemMat));

    // nós: [posição no caule, limiar de surgimento, comprimento, largura, opções]
    const nodes = [
      [0.16, 0.0, 0.2, 0.1, { forma: 0.55, serra: 0 }],  // cotilédones arredondados
      [0.38, 0.18, 0.44, 0.18, {}],
      [0.6, 0.38, 0.52, 0.21, {}],
      [0.8, 0.58, 0.44, 0.18, {}],
      [0.95, 0.76, 0.28, 0.11, {}],
    ];
    const leaves = [];
    nodes.forEach(([t, thr, L, w, op], n) => {
      const p = curve.getPointAt(t);
      for (const side of [0, 1]) {
        const pivot = new THREE.Group();
        pivot.position.copy(p);
        pivot.rotation.y = n * 1.57 + side * Math.PI + (r2() - 0.5) * 0.35; // filotaxia cruzada
        const petLen = n === 0 ? 0.02 : 0.05 + L * 0.08;
        const pet = new THREE.Mesh(petioleGeo, stemMat);
        pet.scale.set(petLen, 1, 1);
        const leaf = new THREE.Mesh(leafGeometry(L, w, op), leafMat);
        leaf.position.x = petLen;
        const hinge = new THREE.Group();            // pecíolo + folha giram juntos
        hinge.add(pet, leaf);
        hinge.rotation.z = 0.6 - n * 0.06;          // ângulo de inserção
        pivot.add(hinge);
        plant.add(pivot);
        leaves.push({ pivot, leaf: hinge, thr, phase: r2() * 6.28, baseZ: hinge.rotation.z });
      }
    });
    // gema apical: duas folhinhas fechadas no topo
    const bud = new THREE.Group();
    bud.position.copy(curve.getPointAt(1));
    [0, Math.PI].forEach((ry) => {
      const f = new THREE.Mesh(leafGeometry(0.1, 0.035, { serra: 0 }), leafMat);
      f.rotation.set(0, ry, 1.25);
      bud.add(f);
    });
    plant.add(bud);

    function update(growth, t, animate) {
      const s = scale * (0.28 + 0.72 * growth);
      plant.scale.setScalar(s);
      leaves.forEach((lf) => {
        const k = smoothstep(lf.thr, lf.thr + 0.2, growth);
        lf.pivot.scale.setScalar(Math.max(k, 0.0001));
        // folhas "abrem" ao crescer e balançam levemente
        const sway = animate ? Math.sin(t * 0.9 + lf.phase) * 0.035 : 0;
        lf.leaf.rotation.z = lf.baseZ + (1 - k) * 0.9 + sway;
      });
      bud.scale.setScalar(Math.max(0.0001, smoothstep(0.2, 0.5, growth)));
      plant.rotation.z = animate ? Math.sin(t * 0.55 + seedOffset) * 0.016 : 0;
    }
    return { plant, update };
  }

  const PLANT_Z = PLANT_Z_CONST;
  const mainPlant = buildPlant(0.9, 0);
  mainPlant.plant.position.set(0, surfaceY(0, PLANT_Z), PLANT_Z);
  topLayer.group.add(mainPlant.plant);

  // brotos extras (estágio 3)
  const sprouts = [[-0.55, -0.35, 0.35], [0.6, -0.5, 0.3], [-0.45, 0.6, 0.28], [0.55, 0.45, 0.25]].map(([x, z, sc], i) => {
    const p = buildPlant(sc, i + 1);
    p.plant.position.set(x, surfaceY(x, z), z);
    p.thr = i * 0.18;
    topLayer.group.add(p.plant);
    return p;
  });

  /* ================================================================ */
  /* 4. Raízes — uma única malha, revelada por shader                 */
  /* ================================================================ */
  // Cada vértice guarda aBirth (0..1): "quando" ele nasce. O fragment
  // shader descarta o que ainda não nasceu => crescimento contínuo com
  // 1 draw call. aLayer é a posição FRACIONÁRIA do vértice no empilhamento
  // (ex.: 2.5 = meio da camada 2), para que as raízes se "estiquem" de forma
  // contínua quando as camadas se separam (sem rasgos entre camadas).
  const layerOffsets = { value: new Array(N).fill(0) };
  const sepU = { value: 0 };
  const rootGrowthU = { value: 0 };
  const rootTipU = { value: 0 };
  const FRONT_Z = D / 2 + 0.014;

  function layerAt(x, y) {
    for (let k = N - 1; k >= 0; k--) {
      const b0 = boundaryY(k, x, D / 2), b1 = boundaryY(k + 1, x, D / 2);
      if (y >= b0) return k + THREE.MathUtils.clamp((y - b0) / (b1 - b0), 0, 1);
    }
    return 0;
  }

  const rootPieces = [];
  let maxBirth = 0;
  function growRoot(start, angle, length, radius, depth, t0, span, rr) {
    const steps = Math.max(6, Math.round(14 * length * Q.rootDetail));
    const seg = length / steps;
    const pts = [start.clone()];
    let a = angle, p = start.clone();
    for (let i = 0; i < steps; i++) {
      a += (rr() - 0.5) * 0.5;
      a = THREE.MathUtils.clamp(a, -1.25, 1.25);   // sempre "para baixo"
      p = p.clone().add(new THREE.Vector3(Math.sin(a) * seg, -Math.cos(a) * seg, 0));
      p.x = THREE.MathUtils.clamp(p.x, -W / 2 + R + 0.02, W / 2 - R - 0.02);
      if (p.y < bases[0] + 0.1) break;
      p.z = FRONT_Z + rr() * 0.004;
      pts.push(p);
    }
    if (pts.length < 3) return;
    const curve = new THREE.CatmullRomCurve3(pts);
    const tub = pts.length * 3, rad = 5;
    const g = new THREE.TubeGeometry(curve, tub, radius, rad);
    const pos = g.attributes.position;
    const birth = new Float32Array(pos.count), lay = new Float32Array(pos.count);
    for (let i = 0; i < pos.count; i++) {
      const ring = Math.floor(i / (rad + 1)) / tub;
      const c = curve.getPointAt(Math.min(ring, 1));
      const k = 1 - 0.75 * ring;                        // afina até a ponta
      pos.setXYZ(i, c.x + (pos.getX(i) - c.x) * k, c.y + (pos.getY(i) - c.y) * k, c.z + (pos.getZ(i) - c.z) * k);
      birth[i] = t0 + ring * span;
      lay[i] = layerAt(c.x, c.y);
    }
    maxBirth = Math.max(maxBirth, t0 + span);
    g.computeVertexNormals();
    g.setAttribute('aBirth', new THREE.BufferAttribute(birth, 1));
    g.setAttribute('aLayer', new THREE.BufferAttribute(lay, 1));
    rootPieces.push(g);
    if (depth >= 3 || (depth === 2 && Q.rootDetail < 0.8)) return;
    // raízes finas: mais ramificação no último nível em qualidade alta
    const children = depth === 0 ? 6 : depth === 1 ? 3 + Math.floor(rr() * 2) : (Q.rootDetail >= 1 ? 2 : 1) + Math.floor(rr() * 2);
    for (let c = 0; c < children; c++) {
      const f = 0.12 + rr() * 0.75;
      const sp = curve.getPointAt(f);
      const dir = rr() < 0.5 ? -1 : 1;
      growRoot(sp, dir * (0.55 + rr() * 0.6), length * (0.28 + rr() * 0.3), radius * 0.6,
        depth + 1, t0 + f * span, span * 0.6, rr);
    }
  }
  {
    const rr = mulberry32(7);
    // A muda fica atrás da face frontal; desloca a origem das raízes para que,
    // vistas da câmera, elas pareçam nascer logo abaixo do caule.
    const rootX = (D / 2 - PLANT_Z) * Math.tan(camAzimuth);
    const startY = boundaryY(N, rootX, D / 2) - 0.03;
    [[-0.55, 0.9], [0.0, 1.25], [0.5, 0.95], [-0.25, 0.75], [0.28, 0.8]].forEach(([ang, len], i) => {
      growRoot(new THREE.Vector3(rootX + (i - 2) * 0.012, startY, FRONT_Z), ang, len,
        i < 3 ? 0.013 : 0.01, i < 3 ? 0 : 1, i * 0.04, 0.6, rr);
    });
  }
  const rootGeo = track(mergeIndexed(rootPieces, ['position', 'normal', 'aBirth', 'aLayer']));
  { // normaliza aBirth para 0..1
    const b = rootGeo.attributes.aBirth;
    for (let i = 0; i < b.count; i++) b.setX(i, b.getX(i) / maxBirth);
  }
  const rootMat = track(new THREE.MeshStandardMaterial({
    color: PALETTE.root, roughness: 0.65, emissive: new THREE.Color(PALETTE.accent), emissiveIntensity: 0,
  }));
  rootMat.onBeforeCompile = (shader) => {
    shader.uniforms.uGrowth = rootGrowthU;
    shader.uniforms.uSep = sepU;
    shader.uniforms.uTip = rootTipU;
    shader.vertexShader = `attribute float aBirth;\nattribute float aLayer;\nuniform float uSep;\nvarying float vBirth;\n`
      + shader.vertexShader.replace('#include <begin_vertex>',
        `#include <begin_vertex>
         vBirth = aBirth;
         transformed.y += uSep * (aLayer - 0.5 - ${((N - 1) / 2).toFixed(1)});`);
    shader.fragmentShader = 'uniform float uGrowth;\nuniform float uTip;\nvarying float vBirth;\n'
      + shader.fragmentShader
        .replace('#include <clipping_planes_fragment>', '#include <clipping_planes_fragment>\n if (vBirth > uGrowth) discard;')
        .replace('#include <emissivemap_fragment>',
          `#include <emissivemap_fragment>
           // pontas em crescimento brilham (verde da marca)
           float tip = smoothstep(uGrowth - 0.05, uGrowth, vBirth);
           totalEmissiveRadiance += vec3(0.55, 0.89, 0.25) * tip * uTip;`);
  };
  rootMat.customProgramCacheKey = () => 'siras-roots';
  const roots = new THREE.Mesh(rootGeo, rootMat);
  roots.frustumCulled = false;
  root.add(roots);

  /* ================================================================ */
  /* 5. Efeitos: linha de análise, marcadores, partículas, halo       */
  /* ================================================================ */
  const accent = new THREE.Color(PALETTE.accent);

  // Contorno em retângulo arredondado que "abraça" o bloco (linha de análise)
  const outlinePts = [];
  {
    const m = 0.06, hw = W / 2 + m, hd = D / 2 + m, r = R + m;
    const corners = [[hw - r, hd - r, 0], [-hw + r, hd - r, 0.5], [-hw + r, -hd + r, 1], [hw - r, -hd + r, 1.5]];
    corners.forEach(([cx, cz, a0]) => {
      for (let i = 0; i <= 8; i++) {
        const a = (a0 + i / 16) * Math.PI;
        outlinePts.push(new THREE.Vector3(cx + Math.cos(a) * r, 0, cz + Math.sin(a) * r));
      }
    });
  }
  const scanGroup = new THREE.Group();
  const scanLineMat = track(new THREE.LineBasicMaterial({ color: accent, transparent: true, opacity: 0, depthWrite: false }));
  const scanLine = new THREE.LineLoop(track(new THREE.BufferGeometry().setFromPoints(outlinePts)), scanLineMat);
  const scanSheetMat = track(new THREE.MeshBasicMaterial({
    color: accent, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide,
    alphaMap: track(radialTexture([[0, '#444'], [0.7, '#888'], [1, '#000']])),
  }));
  const scanSheet = new THREE.Mesh(track(new THREE.PlaneGeometry(W * 1.25, D * 1.25)), scanSheetMat);
  scanSheet.rotation.x = -Math.PI / 2;
  scanGroup.add(scanLine, scanSheet);
  root.add(scanGroup);

  // Um único contorno sutil pontua a entrada e o fechamento de cada etapa.
  const cueOutlineMat = track(new THREE.LineBasicMaterial({ color: accent, transparent: true, opacity: 0, depthWrite: false }));
  const cueOutline = new THREE.LineLoop(track(new THREE.BufferGeometry().setFromPoints(outlinePts)), cueOutlineMat);
  cueOutline.visible = effects;
  root.add(cueOutline);

  const dotTex = track(radialTexture([[0, 'rgba(255,255,255,1)'], [0.25, 'rgba(255,255,255,0.9)'], [0.5, 'rgba(255,255,255,0.15)'], [1, 'rgba(255,255,255,0)']]));

  /* ---------- Pontos de leitura (um por atributo da análise) ---------- */
  // DECISÃO DE NARRATIVA: atributos (pH, P, K, CTC, textura...) NÃO são
  // camadas do solo. As camadas do bloco representam só estratigrafia
  // ilustrativa; associar um atributo químico a uma faixa de profundidade
  // sugeriria um horizonte ou profundidade que a análise não mede.
  // Por isso os atributos aparecem num ANEL HORIZONTAL acima do bloco, todos
  // na mesma altura (sem leitura de profundidade), ligados por linhas finas a
  // um único ponto de amostra na superfície: "estes valores vêm da amostra".
  //
  // Estados (forma + cor, nunca só cor):
  //   lido       -> anel vazado, neutro            (atributo medido, sem juízo)
  //   limitante  -> círculo cheio âmbar, pulsando  (a análise revela limitação)
  //   corrigido  -> círculo verde com "check"      (limitação corrigível tratada)
  //   permanente -> losango terroso, sem pulsar    (limitação que manejo não remove)
  //   ausente    -> anel tracejado, apagado        (atributo não informado na análise)
  const ESTADOS = ['lido', 'limitante', 'corrigido', 'permanente', 'ausente'];
  const ESTADO_COR = {
    dark:  { lido: '#d4e6c8', limitante: '#f0a73a', corrigido: '#8ce23f', permanente: '#d9804a', ausente: '#7f8c81' },
    light: { lido: '#4d6350', limitante: '#a86400', corrigido: '#3c8a18', permanente: '#9a4f22', ausente: '#8a958b' },
  };
  function markerTexture(estado) {
    return canvasTexture(128, (ctx, s) => {
      const c = s / 2;
      ctx.fillStyle = '#fff'; ctx.strokeStyle = '#fff';
      if (estado === 'lido') {
        ctx.lineWidth = 14; ctx.beginPath(); ctx.arc(c, c, 40, 0, Math.PI * 2); ctx.stroke();
      } else if (estado === 'ausente') {
        ctx.lineWidth = 10; ctx.setLineDash([14, 12]);
        ctx.beginPath(); ctx.arc(c, c, 40, 0, Math.PI * 2); ctx.stroke();
      } else if (estado === 'limitante') {
        ctx.globalAlpha = 0.28; ctx.beginPath(); ctx.arc(c, c, 60, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 1; ctx.beginPath(); ctx.arc(c, c, 38, 0, Math.PI * 2); ctx.fill();
      } else if (estado === 'corrigido') {
        ctx.beginPath(); ctx.arc(c, c, 46, 0, Math.PI * 2); ctx.fill();
        ctx.globalCompositeOperation = 'destination-out'; // "recorta" o check
        ctx.lineWidth = 13; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.beginPath(); ctx.moveTo(c - 22, c + 2); ctx.lineTo(c - 6, c + 18); ctx.lineTo(c + 24, c - 16); ctx.stroke();
      } else { // permanente: losango com miolo vazado
        ctx.beginPath(); ctx.moveTo(c, c - 62); ctx.lineTo(c + 62, c); ctx.lineTo(c, c + 62); ctx.lineTo(c - 62, c); ctx.closePath(); ctx.fill();
        ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath(); ctx.moveTo(c, c - 22); ctx.lineTo(c + 22, c); ctx.lineTo(c, c + 22); ctx.lineTo(c - 22, c); ctx.closePath(); ctx.fill();
      }
    }, { srgb: false });
  }
  const markerTex = Object.fromEntries(ESTADOS.map((e) => [e, track(markerTexture(e))]));

  const RING_R = 1.75;
  const ringY = () => boundaryY(N, 0, 0) + 0.62;
  const SAMPLE = new THREE.Vector3(-0.32, 0, 0.12);
  SAMPLE.y = boundaryY(N, SAMPLE.x, SAMPLE.z) + 0.02;
  const markerGroup = new THREE.Group();   // acompanha a camada do topo
  root.add(markerGroup);
  const sampleMat = track(new THREE.MeshStandardMaterial({ color: accent, emissive: accent, emissiveIntensity: 0.6, transparent: true, opacity: 0 }));
  const sampleCore = new THREE.Mesh(track(new THREE.CylinderGeometry(0.045, 0.045, 0.1, 16)), sampleMat);
  sampleCore.position.copy(SAMPLE);
  markerGroup.add(sampleCore);

  const markers = []; // { id, estado, alvo, k, spriteMat, sprite, line, lineMat, phase }
  function layoutMarkers() {
    // Distribui igualmente no anel; começa à frente-direita (visível na câmera)
    markers.forEach((m, i) => {
      const a = camAzimuth - Math.PI / 2 + (i / markers.length) * Math.PI * 2 + 0.35;
      const pos = new THREE.Vector3(Math.cos(a) * RING_R, ringY(), Math.sin(a) * RING_R * 0.82);
      m.sprite.position.copy(pos);
      m.line.geometry.setFromPoints([pos, SAMPLE]);
    });
  }
  function setMarkers(list = []) {
    const ids = new Set(list.map((m) => m.id));
    // remove os que saíram
    for (let i = markers.length - 1; i >= 0; i--) {
      if (!ids.has(markers[i].id)) {
        const m = markers[i];
        markerGroup.remove(m.sprite, m.line);
        m.spriteMat.dispose(); m.lineMat.dispose(); m.line.geometry.dispose();
        markers.splice(i, 1);
      }
    }
    list.forEach(({ id, estado }, idx) => {
      const est = ESTADOS.includes(estado) ? estado : 'lido';
      let m = markers.find((x) => x.id === id);
      if (!m) {
        const spriteMat = new THREE.SpriteMaterial({ map: markerTex[est], transparent: true, opacity: 0, depthWrite: false });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.scale.setScalar(0.15);
        const lineMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });
        const line = new THREE.Line(new THREE.BufferGeometry(), lineMat);
        markerGroup.add(line, sprite);
        m = { id, estado: est, alvo: est, k: 1, spriteMat, sprite, line, lineMat, phase: idx * 0.9 };
        markers.splice(idx, 0, m);
      }
      m.alvo = est;
      if (reducedMotion || userPaused) { m.estado = est; m.k = 1; }
    });
    // mantém a ordem da lista recebida
    markers.sort((a, b) => list.findIndex((x) => x.id === a.id) - list.findIndex((x) => x.id === b.id));
    layoutMarkers(); // reposiciona sempre: a ordem pode ter mudado
    applyMarkerColors();
    requestRender();
  }
  function applyMarkerColors() {
    const pal = ESTADO_COR[theme === 'dark' ? 'dark' : 'light'];
    markers.forEach((m) => {
      m.spriteMat.map = markerTex[m.estado];
      m.spriteMat.color.set(pal[m.estado]);
      m.spriteMat.needsUpdate = true;
      m.lineMat.color.set(pal[m.estado]);
    });
  }
  /** Atualiza transições de estado: encolhe, troca o ícone, cresce. */
  function updateMarkers(t, dt, animate) {
    const vis = params.leitura ?? 0;
    sampleMat.opacity = Math.min(1, vis * 1.5) * 0.9;
    markerGroup.position.y = layerOffsets.value[N - 1];
    markers.forEach((m, i) => {
      if (m.estado !== m.alvo) {
        if (!animate) { m.estado = m.alvo; m.k = 1; applyMarkerColors(); }
        else {
          m.k = Math.max(0, m.k - dt * 5);
          if (m.k === 0) { m.estado = m.alvo; applyMarkerColors(); }
        }
      } else if (m.k < 1) m.k = animate ? Math.min(1, m.k + dt * 4) : 1;
      // aparecimento escalonado: cada troca de etapa redesenha a leitura,
      // evitando que todos os marcadores "estourem" ao mesmo tempo.
      const stageReveal = animate ? smoothstep(i * 0.07, i * 0.07 + 0.55, stageElapsed) : 1;
      const appear = smoothstep(0, 1, vis * 1.6 - i * 0.06) * stageReveal;
      const pulse = animate && m.estado === 'limitante'
        ? 1 + MOTION.markerPulse * Math.sin(t * 2.2 + m.phase)
        : 1;
      m.sprite.scale.setScalar(0.15 * m.k * pulse * (0.6 + 0.4 * appear));
      m.spriteMat.opacity = appear;
      m.lineMat.opacity = appear * (m.estado === 'lido' ? 0.22 : m.estado === 'ausente' ? 0.08 : 0.4);
      if (m.estado === 'ausente') m.spriteMat.opacity = appear * 0.75;
    });
  }

  // Partículas ambientais
  const PCOUNT = Q.particles;
  const pPos = new Float32Array(PCOUNT * 3), pVel = new Float32Array(PCOUNT);
  const pPhase = new Float32Array(PCOUNT), pBaseX = new Float32Array(PCOUNT), pBaseZ = new Float32Array(PCOUNT);
  for (let i = 0; i < PCOUNT; i++) {
    pPos[i * 3] = pBaseX[i] = (rand() * 2 - 1) * 2.6;
    pPos[i * 3 + 1] = -1.3 + rand() * 3.6;
    pPos[i * 3 + 2] = pBaseZ[i] = (rand() * 2 - 1) * 1.8;
    pVel[i] = 0.025 + rand() * 0.075;
    pPhase[i] = rand() * Math.PI * 2;
  }
  const pGeo = track(new THREE.BufferGeometry());
  pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  const pMat = track(new THREE.PointsMaterial({
    size: 0.05, map: dotTex, color: accent, transparent: true, opacity: 0,
    depthWrite: false, sizeAttenuation: true,
  }));
  const points = new THREE.Points(pGeo, pMat);
  points.visible = effects;
  root.add(points);

  // Halo atrás do bloco
  const glowMat = track(new THREE.SpriteMaterial({
    map: track(radialTexture([[0, 'rgba(140,226,63,0.55)'], [0.4, 'rgba(90,170,40,0.18)'], [1, 'rgba(0,0,0,0)']])),
    transparent: true, depthWrite: false, opacity: 0,
  }));
  const glow = new THREE.Sprite(glowMat);
  glow.scale.set(6.5, 6.5, 1);
  glow.position.set(-0.4, 0.3, -1.6);
  glow.visible = effects;
  root.add(glow);

  // Sombra de contato
  const shadowMat = track(new THREE.MeshBasicMaterial({
    map: track(radialTexture([[0, 'rgba(0,0,0,0.55)'], [0.55, 'rgba(0,0,0,0.22)'], [1, 'rgba(0,0,0,0)']])),
    transparent: true, depthWrite: false,
  }));
  const shadow = new THREE.Mesh(track(new THREE.PlaneGeometry(3.8, 3.8)), shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  root.add(shadow);

  /* ---------- Tema ---------- */
  let theme = initialTheme;
  function applyTheme(t) {
    theme = t;
    const dark = t === 'dark';
    // Fundo claro: blending aditivo some; use normal e verde mais escuro.
    const blend = dark ? THREE.AdditiveBlending : THREE.NormalBlending;
    [pMat, glowMat, scanSheetMat].forEach((m) => { m.blending = blend; m.needsUpdate = true; });
    const fx = new THREE.Color(dark ? PALETTE.accent : PALETTE.accentDeep);
    [pMat, scanLineMat, scanSheetMat, cueOutlineMat].forEach((m) => m.color.copy(fx));
    applyMarkerColors();
    shadowMat.opacity = dark ? 1 : 0.55;
    hemi.intensity = dark ? 1.1 : 1.35;
    rim.intensity = dark ? 1.6 : 0.6;
    requestRender();
  }

  /* ================================================================ */
  /* 6. Atualização por frame                                         */
  /* ================================================================ */
  const tmpColor = new THREE.Color(), tmpColor2 = new THREE.Color();
  const dryTop = new THREE.Color('#8f7a66'), richTop = new THREE.Color('#4a3524');
  const leafDry = new THREE.Color(PALETTE.leafDry), leafRich = new THREE.Color(PALETTE.leaf);
  const mossDry = new THREE.Color(PALETTE.mossDry), mossRich = new THREE.Color(PALETTE.moss);
  const rootDull = new THREE.Color('#b8a994'), rootRich = new THREE.Color(PALETTE.root);
  const dust = new THREE.Color('#cdb48c');

  let lastDt = 0;
  function applyParams(t, animate) {
    const p = params;
    const v = p.vitality;
    const cue = stageChoreography(stages[stageIndex], stageElapsed, animate);

    // separação das camadas (centralizada: topo sobe, base desce)
    const sep = p.layerSeparation * 0.13;
    layers.forEach((L, k) => {
      const off = sep * (k - (N - 1) / 2);
      L.group.position.y = off;
      layerOffsets.value[k] = off;
      L.sideMat.color.lerpColors(L.dull, L.rich, v);
      L.sideMat.emissiveIntensity = L.hover * 0.07; // destaque sutil no hover
      L.crumbMat.color.lerpColors(L.dull, L.rich, v).multiplyScalar(0.82);
    });
    strawMat.color.lerpColors(tmpColor.set('#c2bcae'), tmpColor2.set('#ffffff'), v); // tons por instância
    const limeTarget = (p.calagem ?? 0) * cue.limeGate;
    const fertTarget = (p.adubacao ?? 0) * cue.fertGate;
    const groupTarget = (p.agrupar ?? 0) * cue.groupGate;
    updateGranules(lime, limeTarget, lastDt, animate);
    updateGranules(fert, fertTarget, lastDt, animate, groupTarget, cue.npkWaves);
    updateRotulos(t, lastDt, animate, cue);
    cloverMat.color.lerpColors(mossDry, tmpColor.set('#5aa83a'), v);
    sepU.value = sep;
    topLayer.topMat.color.lerpColors(dryTop, richTop, v);
    pebbleMat.color.setRGB(0.27 + 0.04 * v, 0.245, 0.22);

    grassMat.color.lerpColors(mossDry, mossRich, v);
    updateGrass(p.grassDensity);

    leafMat.color.lerpColors(leafDry, leafRich, Math.min(1, v * 1.3 + 0.15));
    leafMat.emissiveIntensity = 0.14 + 0.12 * v;
    stemMat.color.lerpColors(leafDry, tmpColor.set(0x8fd35a), Math.min(1, v * 1.3 + 0.15));
    mainPlant.update(p.plantGrowth, t, animate);
    mainPlant.plant.position.y = surfaceY(0, PLANT_Z);
    sprouts.forEach((s) => {
      const k = smoothstep(s.thr, s.thr + 0.3, p.sprouts);
      s.update(k * 0.9, t, animate);
      s.plant.visible = k > 0.01;
      s.plant.scale.multiplyScalar(Math.max(k, 0.001));
    });

    rootGrowthU.value = p.rootGrowth;
    const effectiveRootGlow = Math.max(p.rootGlow, cue.rootFocus);
    rootTipU.value = 0.25 + effectiveRootGlow * 0.9;
    rootMat.color.lerpColors(rootDull, rootRich, v);
    const rootBreath = animate ? 0.93 + 0.07 * Math.sin(t * 1.1) : 1;
    rootMat.emissiveIntensity = effectiveRootGlow * 0.13 * rootBreath;

    // Linha de análise v6: uma varredura com pausa curta entre ciclos.
    // Parece uma leitura deliberada, não um scanner rodando sem parar.
    const top = boundaryY(N, 0, 0) + sep * (N - 1) / 2 + 0.1;
    const bottom = bases[0] - sep * (N - 1) / 2 - 0.05;
    const cycleLen = 4.6;
    const moveLen = 2.55;
    const phase = animate ? (stageElapsed % cycleLen) : moveLen * 0.38;
    const raw = Math.min(1, phase / moveLen);
    const cyc = smoothstep(0, 1, raw);
    const activeWindow = phase <= moveLen ? 1 : smoothstep(cycleLen, moveLen + 0.18, phase);
    scanGroup.position.y = THREE.MathUtils.lerp(top, bottom, cyc);
    const edgeFade = smoothstep(0, 0.09, raw) * smoothstep(1, 0.9, raw) * activeWindow;
    const scanStrength = p.scan * cue.scanGain;
    scanLineMat.opacity = scanStrength * edgeFade * 0.88;
    scanSheetMat.opacity = scanStrength * edgeFade * (theme === 'dark' ? 0.15 : 0.085);

    cueOutline.position.y = top + 0.012;
    cueOutline.scale.setScalar(cue.outlineScale * (1 + scenarioAccent * 0.010));
    cueOutlineMat.opacity = Math.min(0.42, cue.outline + scenarioAccent * 0.10)
      * (theme === 'dark' ? 1 : 0.72);

    updateMarkers(t, lastDt, animate);

    pMat.opacity = p.particles * cue.particleFactor * (theme === 'dark' ? 0.82 : 0.56);
    pMat.color.lerpColors(dust, theme === 'dark' ? accent : tmpColor.set(PALETTE.accentDeep), Math.min(1, v + scanStrength));
    const accentPulse = animate ? stageAccent : 0;
    glowMat.opacity = p.glow * (theme === 'dark' ? 0.56 : 0.27)
      + accentPulse * (theme === 'dark' ? 0.06 : 0.03)
      + cue.lightLift * (theme === 'dark' ? 0.16 : 0.08)
      + scenarioAccent * (theme === 'dark' ? 0.045 : 0.022);
    const glowScale = 6.5 * (1 + accentPulse * 0.028 + cue.lightLift * 0.04 + scenarioAccent * 0.016);
    glow.scale.set(glowScale, glowScale, 1);
    rim.intensity = (theme === 'dark' ? 1.6 : 0.6) + cue.lightLift * 0.55 + scenarioAccent * 0.10;
    shadow.position.y = bases[0] - sep * (N - 1) / 2 - 0.03;
  }

  /* ---------- Interação ---------- */
  const pointer = { x: 0, y: 0, inside: false, mouse: false };
  const parallax = { x: 0, y: 0 };
  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  let hoveredLayer = -1;

  function updatePointer(ev) {
    const r = container.getBoundingClientRect();
    pointer.x = ((ev.clientX - r.left) / r.width) * 2 - 1;
    pointer.y = -(((ev.clientY - r.top) / r.height) * 2 - 1);
    pointer.inside = Math.abs(pointer.x) <= 1 && Math.abs(pointer.y) <= 1;
    pointer.mouse = ev.pointerType === 'mouse';
  }
  function pick() {
    ndc.set(pointer.x, pointer.y);
    raycaster.setFromCamera(ndc, camera);
    const hit = raycaster.intersectObjects(layers.map((l) => l.mesh), false)[0];
    return hit ? hit.object.userData.layerIndex : -1;
  }
  const INTERACTIVE_SEL = 'a,button,input,select,textarea,label,summary,[role="button"],[contenteditable]';
  const onPointerMove = (ev) => {
    updatePointer(ev);
    if (!pointer.mouse || !pointer.inside || reducedMotion) return;
    // Sobre um botão/link da página, a cena não reage (evita destaque "fantasma")
    const h = ev.target.closest?.(INTERACTIVE_SEL) ? -1 : pick();
    if (h !== hoveredLayer) {
      hoveredLayer = h;
      onLayerHover(h >= 0 ? { index: h, ...SOIL_LAYERS[h] } : null);
    }
    requestRender();
  };
  const onPointerLeave = () => {
    pointer.inside = false;
    if (hoveredLayer !== -1) { hoveredLayer = -1; onLayerHover(null); }
  };
  const onClick = (ev) => {
    // nunca rouba cliques de elementos interativos da página
    if (ev.target.closest?.(INTERACTIVE_SEL)) return;
    updatePointer(ev);
    if (pointer.inside && pick() >= 0) setStage((stageIndex + 1) % stages.length, { source: 'click' });
  };
  if (interactive) {
    window.addEventListener('pointermove', onPointerMove, { passive: true });
    document.addEventListener('pointerleave', onPointerLeave);
    if (clickToAdvance) window.addEventListener('click', onClick);
  }

  /* ---------- Estágios ---------- */
  let stageIndex = initialStage;
  let stageClock = 0;
  let stageElapsed = 0;
  let stageAccent = 0;
  let scenarioAccent = 0;
  let autoplayPausedUntil = 0;
  let elapsed = 0;
  const stageView = { yaw: 0, pitch: 0, scale: 1 };

  function primeStageChoreography(stage) {
    if (reducedMotion || userPaused) return;
    const id = stage?.id;
    if (id === 'calagem') {
      lime.vis = 0;
      lime.items.forEach((it) => { it.g = 0; });
      rot.mol = 0;
    } else if (id === 'adubacao') {
      fert.vis = 0;
      fert.agrupado = 0;
      fert.items.forEach((it) => { it.g = 0; });
      rot.npk = 0;
    } else if (id === 'formulacao') {
      fert.agrupado = 0;
    }
  }

  function setStage(i, { source = 'api' } = {}) {
    const idx = ((i % stages.length) + stages.length) % stages.length;
    stageIndex = idx;
    stageClock = 0;
    stageElapsed = 0;
    stageAccent = reducedMotion ? 0 : 1;
    scenarioAccent = 0;
    primeStageChoreography(stages[idx]);
    Object.assign(targets, stages[idx].targets);
    if (source !== 'autoplay') autoplayPausedUntil = elapsed + 20; // usuário interagiu: pausa autoplay 20 s
    if (reducedMotion || userPaused) Object.assign(params, targets); // sem transição
    onStageChange(idx, stages[idx], { source });
    requestRender();
  }

  /* ---------- Layout responsivo ---------- */
  function defaultLayout(w, h) {
    // desktop: bloco à direita, deixando espaço para título/CTA à esquerda
    if (w >= 900) return { offsetX: 0.22, offsetY: 0.02, zoom: Math.min(1.15, h / 640) };
    if (w >= 600) return { offsetX: 0.12, offsetY: 0.05, zoom: 0.9 };
    // celular: espera-se um contêiner próprio abaixo do texto (~340-400px de
    // altura), então a cena fica centralizada e ocupa esse espaço.
    return { offsetX: 0, offsetY: 0.02, zoom: Math.min(1.4, 1.25 * Math.min(w / h, 1.15)) };
  }
  let dpr = Math.min(window.devicePixelRatio || 1, Q.dpr);
  function resize() {
    const w = Math.max(1, container.clientWidth), h = Math.max(1, container.clientHeight);
    const L = layout(w, h);
    renderer.setPixelRatio(dpr);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.zoom = L.zoom;
    // setViewOffset desloca o enquadramento sem distorcer a perspectiva
    camera.setViewOffset(w, h, -L.offsetX * w, L.offsetY * h, w, h);
    camera.updateProjectionMatrix();
    requestRender();
  }
  const ro = new ResizeObserver(resize);
  ro.observe(container);

  /* ---------- Loop: pausa fora da tela / aba oculta ---------- */
  let visible = true, running = false, rafId = 0, last = 0, needsRender = true, disposed = false;
  let frameTimes = [], dprLocked = false;
  const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; syncLoop(); }, { threshold: 0.01 });
  io.observe(container);
  const onVisibility = () => syncLoop();
  document.addEventListener('visibilitychange', onVisibility);
  const onMotionChange = (e) => {
    reducedMotion = e.matches || forcedReduced;
    if (reducedMotion) { autoplay = false; Object.assign(params, targets); }
    else autoplay = baseAutoplay;
    syncLoop(); requestRender();
  };
  motionQuery?.addEventListener?.('change', onMotionChange);

  let userPaused = false; // botão "pausar animação" (WCAG 2.2.2)
  function shouldRun() { return !disposed && visible && !document.hidden && !reducedMotion && !userPaused; }
  function syncLoop() {
    if (shouldRun() && !running) { running = true; last = performance.now(); rafId = requestAnimationFrame(frame); }
    else if (!shouldRun() && running) { running = false; cancelAnimationFrame(rafId); }
    if (!running && needsRender && !disposed) renderStatic();
  }
  function requestRender() {
    needsRender = true;
    if (!running && !disposed) renderStatic();
  }
  function renderStatic() {
    needsRender = false;
    layers.forEach((L, k) => { L.hover = k === hoveredLayer ? 1 : 0; });
    applyParams(elapsed, false);
    renderer.render(scene, camera);
  }

  function frame(now) {
    if (!running) return;
    rafId = requestAnimationFrame(frame);
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    elapsed += dt;
    stageElapsed += dt;
    stageAccent = damp(stageAccent, 0, MOTION.settleDamp, dt);
    scenarioAccent = damp(scenarioAccent, 0, 3.8, dt);
    lastDt = dt;
    timeUniform.value = elapsed;

    // autoplay
    if (autoplay && elapsed > autoplayPausedUntil) {
      stageClock += dt * 1000;
      if (stageClock > (stages[stageIndex].durationMs || 6000)) setStage(stageIndex + 1, { source: 'autoplay' });
    }
    // Interpolação v6: transições visuais têm velocidades diferentes.
    // Estrutura (camadas/plantas) assenta mais devagar; efeitos informativos
    // (scan/marcadores) respondem mais rápido.
    for (const k in targets) {
      const speed = k === 'layerSeparation' ? 2.35
        : (k === 'scan' || k === 'leitura' ? 3.0
          : (k === 'calagem' || k === 'adubacao' || k === 'agrupar' ? 2.1 : 1.55));
      params[k] = damp(params[k], targets[k], speed, dt);
    }
    layers.forEach((L, k) => { L.hover = damp(L.hover, k === hoveredLayer ? 1 : 0, 8, dt); });

    // Movimento de câmera/objeto v6: enquadramento por etapa + paralaxe leve.
    // O bloco deixa de parecer "flutuante" e passa a se comportar como um
    // objeto de produto em estúdio, com micro-movimento ambiental.
    const px = pointer.mouse && interactive ? pointer.x : 0;
    const py = pointer.mouse && interactive ? pointer.y : 0;
    parallax.x = damp(parallax.x, px, 3.0, dt);
    parallax.y = damp(parallax.y, py, 3.0, dt);
    const viewTarget = stageMotion(stages[stageIndex]);
    const frameCue = stageChoreography(stages[stageIndex], stageElapsed, true);
    stageView.yaw = damp(stageView.yaw, viewTarget.yaw + frameCue.cameraYaw, MOTION.stageDamp, dt);
    stageView.pitch = damp(stageView.pitch, viewTarget.pitch + frameCue.cameraPitch, MOTION.stageDamp, dt);
    stageView.scale = damp(stageView.scale, viewTarget.scale + frameCue.cameraScale, MOTION.stageDamp, dt);
    root.rotation.y = stageView.yaw + parallax.x * MOTION.parallaxYaw + Math.sin(elapsed * 0.19) * MOTION.idleYaw;
    root.rotation.x = stageView.pitch - parallax.y * MOTION.parallaxPitch;
    root.position.y = Math.sin(elapsed * 0.42) * MOTION.idleBob;
    root.scale.setScalar(stageView.scale * (1 + stageAccent * 0.005 + scenarioAccent * 0.0025));

    // Partículas v6: poeira suspensa lenta, com deriva lateral quase imperceptível.
    const arr = pGeo.attributes.position.array;
    for (let i = 0; i < PCOUNT; i++) {
      arr[i * 3 + 1] += pVel[i] * dt * (0.35 + params.particles * 0.55);
      const drift = MOTION.particleDrift * (0.012 + pVel[i] * 0.05);
      arr[i * 3] = pBaseX[i] + Math.sin(elapsed * 0.32 + pPhase[i]) * drift;
      arr[i * 3 + 2] = pBaseZ[i] + Math.cos(elapsed * 0.27 + pPhase[i]) * drift * 0.7;
      if (arr[i * 3 + 1] > 2.25) arr[i * 3 + 1] = -1.25;
    }
    pGeo.attributes.position.needsUpdate = true;

    applyParams(elapsed, true);
    renderer.render(scene, camera);
    needsRender = false;

    // DPR adaptativo: se ficar pesado, reduz a resolução uma vez por vez
    if (!dprLocked) {
      frameTimes.push(dt);
      if (frameTimes.length === 90) {
        const avg = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
        frameTimes = [];
        if (avg > 1 / 40 && dpr > 1) { dpr = Math.max(1, dpr - 0.25); resize(); }
        else if (avg < 1 / 55) dprLocked = true; // está fluido: para de medir
      }
    }
  }

  /* ---------- Perda de contexto WebGL ---------- */
  const onContextLost = (e) => {
    e.preventDefault();
    running = false; cancelAnimationFrame(rafId);
    onError(new Error('Contexto WebGL perdido'));
  };
  canvas.addEventListener('webglcontextlost', onContextLost);

  /* ---------- Inicialização ---------- */
  applyTheme(initialTheme);
  resize();
  setStage(initialStage, { source: 'init' });
  autoplayPausedUntil = 0;
  syncLoop();

  /* ---------- API pública ---------- */
  function dispose() {
    disposed = true;
    running = false; cancelAnimationFrame(rafId);
    ro.disconnect(); io.disconnect();
    document.removeEventListener('visibilitychange', onVisibility);
    motionQuery?.removeEventListener?.('change', onMotionChange);
    window.removeEventListener('pointermove', onPointerMove);
    document.removeEventListener('pointerleave', onPointerLeave);
    window.removeEventListener('click', onClick);
    canvas.removeEventListener('webglcontextlost', onContextLost);
    disposables.forEach((d) => d.dispose?.());
    grass.dispose(); layers.forEach((l) => { l.pebbles.dispose(); l.crumbs.dispose(); });
    layers[N - 1].straw.dispose(); lime.mesh.dispose(); fert.mesh.dispose(); clover.dispose();
    renderer.dispose();
    renderer.forceContextLoss?.();
    canvas.remove();
  }

  return {
    canvas,
    setStage: (i) => setStage(i, { source: 'user' }),
    next: () => setStage(stageIndex + 1, { source: 'user' }),
    getStage: () => stageIndex,
    setTheme: applyTheme,
    setAutoplay: (on) => { autoplay = on && !reducedMotion; autoplayPausedUntil = 0; },
    /** Congela toda a animação (o último frame continua visível). */
    setPaused: (p) => {
      userPaused = !!p;
      if (userPaused) Object.assign(params, targets); // mostra o estado final do estágio
      syncLoop(); requestRender();
    },
    isReducedMotion: () => reducedMotion,
    /**
     * Liga/desliga o modo sem movimento em tempo de execução (ex.: controle
     * "menos movimento" do próprio SIRAS, além de prefers-reduced-motion).
     */
    setReducedMotion: (on) => {
      forcedReduced = !!on;
      reducedMotion = forcedReduced || !!motionQuery?.matches;
      if (reducedMotion) { autoplay = false; Object.assign(params, targets); }
      else autoplay = baseAutoplay;
      syncLoop(); requestRender();
    },
    /** Pontos de leitura: [{ id: 'ph', estado: 'lido'|'limitante'|'corrigido'|'permanente'|'ausente' }] */
    setMarkers,
    /**
     * Proporção dos montes na formulação: null = ilustrativa (montes iguais);
     * [n, p, k] = formulação REAL vinda do servidor (ex.: [5, 20, 20]).
     */
    setNPK,
    /** Sobrescreve alvos diretamente (ex.: dirigir a cena por dados/estados reais). */
    setTargets: (partial) => {
      Object.assign(targets, partial);
      if (stages[stageIndex]?.id === 'aptidao' && !reducedMotion && !userPaused) scenarioAccent = 1;
      if (reducedMotion) Object.assign(params, targets);
      requestRender();
    },
    dispose,
  };
}
