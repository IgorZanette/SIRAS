/* ============================================================================
   SIRAS - escolha de tema: claro, escuro ou o do sistema
   ----------------------------------------------------------------------------
   O par. 14 do plano previa um alternador: tema escuro e otimo em monitor e ruim
   sob sol direto, e parte do publico usa tablet em campo. A escolha fica no
   navegador de quem usa -- nao ha conta, nao ha servidor guardando preferencia.

   TRES ESTADOS, E NAO DOIS. O botao antigo alternava claro <-> escuro, e nao
   havia como dizer "siga o meu sistema". Quem tem o computador em modo claro de
   dia e escuro de noite precisava trocar a mao duas vezes por dia. O controle
   segmentado tem a terceira opcao, que passa a ser o PADRAO: sem escolha
   gravada, o SIRAS segue prefers-color-scheme.

   O QUE FICA GRAVADO E A ESCOLHA, E NAO O TEMA RESULTANTE. Gravar "claro" quando
   a pessoa escolheu "sistema" e o sistema estava claro congelaria a decisao: a
   troca do sistema a noite nao chegaria mais. Entao o localStorage guarda
   "claro", "escuro" ou "sistema", e `data-tema` recebe sempre um dos dois reais.

   O <script> que aplica a escolha gravada roda no <head>, antes da primeira
   pintura; se rodasse aqui, a pagina piscaria escura antes de virar clara.
   ========================================================================= */
(function () {
  "use strict";

  var CHAVE = "siras-tema";
  var MODOS = ["claro", "escuro", "sistema"];
  var ROTULO = {
    claro: "Modo claro",
    escuro: "Modo escuro",
    sistema: "Seguir o sistema"
  };

  var controle = document.getElementById("escolha-de-tema");
  if (!controle) {
    return;
  }
  var botoes = controle.querySelectorAll("[data-tema-modo]");
  var consulta = window.matchMedia("(prefers-color-scheme: light)");

  function escolhaGravada() {
    try {
      var salvo = window.localStorage.getItem(CHAVE);
      return MODOS.indexOf(salvo) >= 0 ? salvo : "sistema";
    } catch (erro) {
      /* Navegacao privada ou armazenamento bloqueado: vale o padrao. */
      return "sistema";
    }
  }

  /* O tema REAL que um modo produz agora. Para "sistema", quem decide e a
     consulta de midia -- e ela pode mudar com a pagina aberta. */
  function temaDoModo(modo) {
    if (modo === "claro" || modo === "escuro") {
      return modo;
    }
    return consulta.matches ? "claro" : "escuro";
  }

  function pintar(modo) {
    document.documentElement.dataset.tema = temaDoModo(modo);
    Array.prototype.forEach.call(botoes, function (botao) {
      var meu = botao.getAttribute("data-tema-modo");
      /* aria-checked, e nao aria-pressed: sao opcoes mutuamente exclusivas de um
         grupo, e nao tres interruptores independentes. */
      botao.setAttribute("aria-checked", String(meu === modo));
      botao.setAttribute("tabindex", meu === modo ? "0" : "-1");
    });
    controle.setAttribute("data-modo", modo);
  }

  function escolher(modo) {
    pintar(modo);
    try {
      window.localStorage.setItem(CHAVE, modo);
    } catch (erro) {
      /* A troca vale para esta sessao e nada quebra. */
    }
  }

  Array.prototype.forEach.call(botoes, function (botao) {
    botao.addEventListener("click", function () {
      escolher(botao.getAttribute("data-tema-modo"));
    });
    botao.setAttribute("title", ROTULO[botao.getAttribute("data-tema-modo")]);
  });

  /* Setas navegam o grupo, como num radiogroup nativo (WAI-ARIA). Sem isto, o
     Tab pararia tres vezes num controle que e uma escolha so. */
  controle.addEventListener("keydown", function (evento) {
    var passo = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[evento.key];
    if (!passo) {
      return;
    }
    evento.preventDefault();
    var atual = MODOS.indexOf(controle.getAttribute("data-modo"));
    var proximo = MODOS[(atual + passo + MODOS.length) % MODOS.length];
    escolher(proximo);
    controle.querySelector('[data-tema-modo="' + proximo + '"]').focus();
  });

  /* Com "sistema" escolhido, mudar o tema do sistema operacional muda a pagina
     na hora, sem recarregar. `addEventListener` nao existe no Safari antigo, que
     ainda usa addListener. */
  function aoTrocarOSistema() {
    if (escolhaGravada() === "sistema") {
      pintar("sistema");
    }
  }
  if (consulta.addEventListener) {
    consulta.addEventListener("change", aoTrocarOSistema);
  } else if (consulta.addListener) {
    consulta.addListener(aoTrocarOSistema);
  }

  pintar(escolhaGravada());
})();
