/*
 * cena-solo.js — adaptador da cena 3D do perfil de solo.
 *
 * POR QUE ESTE ARQUIVO EXISTE: o motor da cena (cena-solo/soilScene.js) é um
 * módulo ES que não sabe nada do SIRAS. Este IIFE faz a ponte com o padrão do
 * projeto: acha o contêiner por atributo de dado, carrega o motor só quando
 * a página já está na tela, segue o tema e o "menos movimento" da aplicação,
 * e lê do DOM tudo o que a cena mostra. O DOM é a fonte da verdade: a cena
 * apenas espelha a legenda em texto, nunca o contrário.
 *
 * CONTRATO COM OS TEMPLATES
 *   [data-cena-solo="inicio"|"gerando"]   contêiner (aria-hidden, nao-imprime)
 *       data-cena-motor="<url de soilScene.js>"  (via url_for, sem caminho fixo)
 *       contém img.cena-solo__fallback, visível até a cena assumir
 *   [data-cena-escopo]                     ancestral que agrupa contêiner,
 *                                          controles e legenda
 *   [data-cena-controles]                  (hero) botões [data-cena-estagio="i"]
 *                                          com data-descricao, [data-cena-descricao]
 *                                          e [data-cena-pausar]; começa hidden
 *   [data-cena-legenda]                    lista de li[data-atributo] com
 *                                          data-limitacao="" | "corrigivel" |
 *                                          "permanente"; começa hidden
 *   (gerando) data-cena-etapa-de="<seletor>"  elemento cujo data-etapa="N"
 *                                          (1..N) gerando.js já mantém
 *   (gerando) [data-cena-npk="05-20-20"]  OPCIONAL: formulação REAL vinda do
 *                                          servidor. Sem ela, os montes N, P, K
 *                                          da formulação têm o mesmo tamanho e
 *                                          [data-cena-npk-texto] diz "proporção
 *                                          ilustrativa".
 *   (formulario) data-cena-campos="<seletor do form>"  campos com
 *                                          data-cena-atributo="ph" etc.:
 *                                          preenchido => "lido"; vazio =>
 *                                          "ausente". Nenhuma interpretação.
 *
 * ESCOPO: só interface ATÉ a geração do laudo. O laudo não tem 3D.
 *
 * Sem JavaScript, ou sem WebGL, nada disso aparece além da imagem estática:
 * a página continua inteira e navegável.
 */
(function () {
  "use strict";

  const raizes = document.querySelectorAll("[data-cena-solo]");
  if (!raizes.length) return; // página sem cena: não baixa nem um byte do three

  /* ------------------------------------------------------------------
   * Conferido contra o projeto em 11/10/2026 (ADR 0012):
   *
   * tema.js escreve document.documentElement.dataset.tema = "escuro" | "claro",
   * e o <script> do <head> aplica o tema salvo antes da primeira pintura. O
   * MutationObserver do adaptador acompanha esse atributo, então a cena troca
   * junto com a aplicação sem depender do nome de nenhum evento.
   *
   * O SIRAS NÃO TEM controle próprio de "menos movimento": ele respeita
   * prefers-reduced-motion do sistema, em CSS e em interacoes.js. O atributo
   * abaixo fica declarado para o dia em que esse controle existir; até lá
   * menosMovimentoNaApp() devolve false e quem decide é a consulta de mídia,
   * que o motor já observa.
   * ------------------------------------------------------------------ */
  const ATRIBUTO_TEMA = "data-tema";
  const VALORES_TEMA_ESCURO = ["escuro", "dark"];
  const ATRIBUTO_MENOS_MOVIMENTO = "data-movimento";
  const VALOR_MENOS_MOVIMENTO = "reduzido";
  // Fechamento da tela de espera: alterna os dois cenários neste intervalo.
  const ALTERNANCIA_CENARIOS_MS = 3200;

  const ROTULO_ESTADO = {
    ausente: "não informado na análise",
    lido: "lido",
    limitante: "limitação identificada",
    corrigido: "limitação corrigível, tratada na recomendação",
    permanente: "limitação permanente, não removida pelo manejo",
  };
  const ROTULO_CENARIO = { diagnostico: "Cenário atual", potencial: "Cenário potencial" };

  const raizDoc = document.documentElement;

  function temaAtual() {
    const v = raizDoc.getAttribute(ATRIBUTO_TEMA);
    if (v) return VALORES_TEMA_ESCURO.indexOf(v) >= 0 ? "dark" : "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function menosMovimentoNaApp() {
    return raizDoc.getAttribute(ATRIBUTO_MENOS_MOVIMENTO) === VALOR_MENOS_MOVIMENTO;
  }

  /** Lê a legenda (texto real) e devolve os atributos na ordem do DOM. */
  function lerAtributos(legenda) {
    if (!legenda) return [];
    return Array.prototype.map.call(legenda.querySelectorAll("li[data-atributo]"), function (li) {
      return { li: li, id: li.getAttribute("data-atributo"), limitacao: li.getAttribute("data-limitacao") || "" };
    });
  }

  /**
   * Aplica um modo ('leitura' | 'diagnostico' | 'potencial') à legenda E à
   * cena, nesta ordem: o texto muda primeiro, a cena acompanha.
   */
  function aplicarModo(ctx, modo) {
    const itens = lerAtributos(ctx.legenda).map(function (a) {
      const estado = ctx.mod.estadoDoAtributo(a.limitacao, modo);
      if (a.li.getAttribute("data-estado") !== estado) a.li.setAttribute("data-estado", estado);
      const alvo = a.li.querySelector("[data-cena-estado-texto]");
      if (alvo && alvo.textContent !== ROTULO_ESTADO[estado]) alvo.textContent = ROTULO_ESTADO[estado];
      return { id: a.id, estado: estado };
    });
    ctx.cena.setMarkers(itens);
  }

  function pararAlternancia(ctx) {
    if (ctx.alternancia) { clearInterval(ctx.alternancia); ctx.alternancia = null; }
  }

  /** Reage à troca de estágio: legenda, cenário e controles. */
  function aoMudarEstagio(ctx, i) {
    if (ctx.raiz.getAttribute("data-cena-solo") === "formulario") return; // o form manda
    const estagio = ctx.estagios && ctx.estagios[i];
    // Durante createSoilScene o motor já avisa o estágio inicial, antes de
    // ctx.cena existir; iniciar() chama de novo logo depois.
    if (!estagio || !ctx.cena) return;
    ctx.estagioAtual = i;
    pararAlternancia(ctx);

    if (estagio.marcadores === "dois-cenarios") {
      // Os dois cenários são dados que o laudo acabou de calcular (vêm do DOM).
      // Com menos movimento, mostra o potencial parado; o texto traz ambos.
      let cenario = "potencial";
      const mostrar = function () {
        aplicarModo(ctx, cenario);
        ctx.cena.setTargets(ctx.mod.CENARIO_TARGETS[cenario]);
        if (ctx.legenda) ctx.legenda.setAttribute("data-cenario-ativo", cenario);
        const rotulo = ctx.escopo.querySelector("[data-cena-cenario]");
        if (rotulo) rotulo.textContent = ROTULO_CENARIO[cenario];
      };
      mostrar();
      if (!ctx.cena.isReducedMotion()) {
        ctx.alternancia = setInterval(function () {
          cenario = cenario === "potencial" ? "diagnostico" : "potencial";
          mostrar();
        }, ALTERNANCIA_CENARIOS_MS);
      }
    } else {
      aplicarModo(ctx, estagio.marcadores || "leitura");
    }

    if (ctx.controles) {
      ctx.controles.querySelectorAll("[data-cena-estagio]").forEach(function (b) {
        b.setAttribute("aria-pressed", String(Number(b.getAttribute("data-cena-estagio")) === i));
      });
      const desc = ctx.controles.querySelector("[data-cena-descricao]");
      const ativo = ctx.controles.querySelector('[data-cena-estagio="' + i + '"]');
      if (desc && ativo) desc.textContent = ativo.getAttribute("data-descricao") || "";
    }
  }

  /**
   * Formulário da análise: cada campo preenchido acende o seu ponto de
   * leitura ("lido"); campo vazio fica "ausente". Usa só o dado digitado:
   * a classificação (limitante etc.) é do motor agronômico, no servidor.
   */
  function seguirFormulario(ctx, seletor) {
    const form = document.querySelector(seletor);
    if (!form) return;
    const atualizar = function () {
      const vistos = {};
      const itens = [];
      form.querySelectorAll("[data-cena-atributo]").forEach(function (campo) {
        const id = campo.getAttribute("data-cena-atributo");
        const cheio = String(campo.value || "").trim() !== "";
        if (!(id in vistos)) { vistos[id] = itens.length; itens.push({ id: id, estado: cheio ? "lido" : "ausente" }); }
        else if (cheio) itens[vistos[id]].estado = "lido"; // vários campos, um atributo
      });
      ctx.cena.setMarkers(itens);
    };
    form.addEventListener("input", atualizar);
    form.addEventListener("change", atualizar);
    ctx.limpezas.push(function () {
      form.removeEventListener("input", atualizar);
      form.removeEventListener("change", atualizar);
    });
    atualizar();
  }

  /**
   * Formulação: lê data-cena-npk ("05-20-20") se o servidor (ou gerando.js)
   * informou a formulação calculada. Sem dado, montes iguais + texto dizendo
   * que a proporção é ilustrativa. A cena nunca inventa proporção.
   */
  function aplicarNPK(ctx) {
    const el = ctx.escopo.querySelector("[data-cena-npk]");
    const bruto = el ? el.getAttribute("data-cena-npk") : "";
    const m = /^\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*$/.exec(bruto || "");
    const texto = ctx.escopo.querySelector("[data-cena-npk-texto]");
    if (m) {
      ctx.cena.setNPK([m[1], m[2], m[3]].map(function (x) { return parseFloat(x.replace(",", ".")); }));
      if (texto) texto.textContent = "Montes N, P e K na proporção da formulação calculada: " + bruto.trim() + ".";
    } else {
      ctx.cena.setNPK(null);
      if (texto) texto.textContent = "Montes N, P e K de mesmo tamanho: proporção ilustrativa.";
    }
  }

  /** Tela de espera: segue o data-etapa que gerando.js já mantém. */
  function seguirEtapas(ctx, seletor) {
    const alvo = document.querySelector(seletor);
    if (!alvo) return;
    const ler = function () {
      const n = parseInt(alvo.getAttribute("data-etapa"), 10);
      if (!isNaN(n)) {
        const i = Math.max(0, Math.min(ctx.estagios.length - 1, n - 1));
        if (i !== ctx.estagioAtual) ctx.cena.setStage(i);
      }
    };
    ctx.observadores.push(observar(alvo, { attributes: true, attributeFilter: ["data-etapa", "class"] }, ler));
    ler();
  }

  function observar(alvo, opcoes, fn) {
    const mo = new MutationObserver(fn);
    mo.observe(alvo, opcoes);
    return mo;
  }

  function iniciar(raiz) {
    const modo = raiz.getAttribute("data-cena-solo");
    const urlMotor = raiz.getAttribute("data-cena-motor");
    if (!urlMotor) return;
    const escopo = raiz.closest("[data-cena-escopo]") || document;
    const ctx = {
      raiz: raiz, escopo: escopo, cena: null, mod: null, estagios: null,
      estagioAtual: -1, alternancia: null, observadores: [], limpezas: [],
      controles: escopo.querySelector("[data-cena-controles]"),
      legenda: escopo.querySelector("[data-cena-legenda]"),
    };

    // import() funciona dentro de script clássico; "three" resolve pelo
    // import map declarado em base.html (arquivo local, nada de rede).
    // URL absoluta: import() em script clássico resolve caminhos relativos a
    // partir do PRÓPRIO script, não da página. Absoluto evita a surpresa.
    const urlAbs = new URL(urlMotor, document.baseURI).href;
    const urlEstagios = new URL("stages.js", urlAbs).href;
    Promise.all([import(urlAbs), import(urlEstagios)]).then(function (mods) {
      const motor = mods[0];
      ctx.mod = mods[1];
      if (!motor.isWebGLAvailable()) return; // fica a imagem estática
      // WebGL só por software (máquina sem aceleração) trava computadores
      // antigos: fica a imagem estática. "?cena-software=1" força a cena
      // (útil para testar em VMs e no navegador headless).
      const forcar = /[?&]cena-software=1\b/.test(location.search) || raiz.hasAttribute("data-cena-permitir-software");
      if (motor.isSoftwareRenderer() && !forcar) return;

      ctx.estagios = modo === "gerando" ? ctx.mod.PROCESSING_STAGES
        : modo === "formulario" ? [ctx.mod.HERO_STAGES[0]]
        : ctx.mod.HERO_STAGES;
      const host = document.createElement("div");
      host.className = "cena-solo__canvas";
      raiz.appendChild(host);

      try {
        ctx.cena = motor.createSoilScene(host, {
          stages: ctx.estagios,
          initialStage: 0,
          theme: temaAtual(),
          reducedMotion: menosMovimentoNaApp(),
          // Na espera, quem manda é o estado real: sem autoplay, sem clique.
          autoplay: modo === "inicio",
          clickToAdvance: modo === "inicio",
          onStageChange: function (i) { aoMudarEstagio(ctx, i); },
          onError: function () { desligar(ctx); },
        });
      } catch (e) {
        desligar(ctx);
        return;
      }
      raiz.classList.add("cena-solo--ativa"); // CSS esconde o fallback
      if (modo === "formulario") seguirFormulario(ctx, raiz.getAttribute("data-cena-campos"));
      else aoMudarEstagio(ctx, 0);

      if (ctx.legenda) ctx.legenda.hidden = false;
      if (ctx.controles && modo === "inicio") {
        ctx.controles.hidden = false;
        ctx.controles.addEventListener("click", function (ev) {
          const b = ev.target.closest("[data-cena-estagio]");
          if (b) ctx.cena.setStage(Number(b.getAttribute("data-cena-estagio")));
          const p = ev.target.closest("[data-cena-pausar]");
          if (p) {
            const pausado = p.getAttribute("aria-pressed") !== "true";
            p.setAttribute("aria-pressed", String(pausado));
            p.textContent = pausado ? "Retomar animação" : "Pausar animação";
            ctx.cena.setPaused(pausado);
          }
        });
        atualizarBotaoPausa(ctx);
      }
      if (modo === "gerando") {
        seguirEtapas(ctx, raiz.getAttribute("data-cena-etapa-de"));
        aplicarNPK(ctx);
        // a formulação pode chegar depois (resposta de gerar_laudo)
        ctx.observadores.push(observar(ctx.escopo === document ? document.body : ctx.escopo,
          { attributes: true, subtree: true, attributeFilter: ["data-cena-npk"] }, function () { if (ctx.cena) aplicarNPK(ctx); }));
      }

      // Tema e "menos movimento": observa o atributo em vez de depender do
      // nome do evento que tema.js dispara (funciona com qualquer um).
      ctx.observadores.push(observar(raizDoc, { attributes: true }, function () {
        if (!ctx.cena) return;
        ctx.cena.setTheme(temaAtual());
        ctx.cena.setReducedMotion(menosMovimentoNaApp());
        atualizarBotaoPausa(ctx);
      }));
      // Legenda preenchida depois (ex.: resultado do laudo): reaplica o modo.
      // Compara uma "assinatura" (ids + limitações) para ignorar as mudanças
      // de texto que este próprio arquivo faz na legenda (evita laço).
      if (ctx.legenda) {
        const assinatura = function () {
          return lerAtributos(ctx.legenda).map(function (a) { return a.id + ":" + a.limitacao; }).join("|");
        };
        let ultima = assinatura();
        ctx.observadores.push(observar(ctx.legenda, { childList: true, subtree: true, attributes: true, attributeFilter: ["data-limitacao", "data-atributo"] }, function () {
          const agora = assinatura();
          if (agora === ultima || !ctx.cena) return;
          ultima = agora;
          aoMudarEstagio(ctx, ctx.estagioAtual);
        }));
      }
      ativos.push(ctx);
    }).catch(function () { /* sem módulos/sem import map: fica o fallback */ });
  }

  function atualizarBotaoPausa(ctx) {
    const p = ctx.controles && ctx.controles.querySelector("[data-cena-pausar]");
    if (p) p.hidden = ctx.cena.isReducedMotion(); // nada se move: botão desnecessário
  }

  function desligar(ctx) {
    pararAlternancia(ctx);
    ctx.observadores.forEach(function (o) { o.disconnect(); });
    ctx.observadores = [];
    ctx.limpezas.forEach(function (fn) { fn(); });
    ctx.limpezas = [];
    if (ctx.cena) { ctx.cena.dispose(); ctx.cena = null; }
    ctx.raiz.classList.remove("cena-solo--ativa");
    const host = ctx.raiz.querySelector(".cena-solo__canvas");
    if (host) host.remove();
    if (ctx.controles) ctx.controles.hidden = true;
    if (ctx.legenda) ctx.legenda.hidden = true;
  }

  const ativos = [];
  function iniciarTodas() { raizes.forEach(iniciar); }

  // Só depois que a página carregou e o navegador ficou ocioso: o texto da
  // hero nunca espera pelo three.js.
  function agendar() {
    if ("requestIdleCallback" in window) requestIdleCallback(iniciarTodas, { timeout: 1500 });
    else setTimeout(iniciarTodas, 200);
  }
  if (document.readyState === "complete") agendar();
  else window.addEventListener("load", agendar, { once: true });

  // Saída da página: libera GPU e listeners. Voltando pelo histórico (bfcache),
  // recria a cena.
  window.addEventListener("pagehide", function () {
    while (ativos.length) desligar(ativos.pop());
  });
  window.addEventListener("pageshow", function (ev) {
    if (ev.persisted) agendar();
  });
})();
