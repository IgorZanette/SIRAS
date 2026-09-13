/* ============================================================================
   SIRAS - apresentacao de primeira visita
   ----------------------------------------------------------------------------
   Tres passos, dispensavel, e que nao volta. A marca de "ja vi" fica no navegador
   de quem usa: nao ha conta nem servidor guardando preferencia.

   O painel nasce com o atributo hidden no HTML e so e revelado aqui. Assim, sem
   JavaScript a pagina simplesmente nao o mostra - em vez de mostra-lo sem meio de
   fechar, que seria pior que nao ter guia nenhum.
   ========================================================================= */
(function () {
  "use strict";

  var CHAVE = "siras-guia-visto";

  var guia = document.getElementById("guia");
  if (!guia) {
    return;
  }

  var passos = Array.prototype.slice.call(guia.querySelectorAll("[data-guia-passo]"));
  var pontos = Array.prototype.slice.call(guia.querySelectorAll("[data-guia-ponto]"));
  var avancar = guia.querySelector("[data-guia-avancar]");
  var atual = 0;

  function jaViu() {
    try {
      return window.localStorage.getItem(CHAVE) === "1";
    } catch (erro) {
      /* Navegacao privada: a guia aparece uma vez por sessao, e nada quebra. */
      return false;
    }
  }

  function marcarVisto() {
    try {
      window.localStorage.setItem(CHAVE, "1");
    } catch (erro) { /* idem */ }
  }

  function mostrar(indice) {
    passos.forEach(function (passo, posicao) {
      passo.hidden = posicao !== indice;
    });
    pontos.forEach(function (ponto, posicao) {
      ponto.classList.toggle("is-ativo", posicao === indice);
    });
    if (avancar) {
      avancar.firstChild.nodeValue = indice === passos.length - 1 ? "Começar " : "Entendi ";
    }
  }

  function fechar() {
    guia.hidden = true;
    guia.setAttribute("aria-hidden", "true");
    marcarVisto();
    document.removeEventListener("keydown", aoTeclar);
  }

  function aoTeclar(evento) {
    if (evento.key === "Escape") {
      fechar();
    }
  }

  Array.prototype.forEach.call(guia.querySelectorAll("[data-guia-fechar]"), function (alvo) {
    alvo.addEventListener("click", fechar);
  });

  if (avancar) {
    avancar.addEventListener("click", function () {
      atual += 1;
      if (atual >= passos.length) {
        fechar();
        return;
      }
      mostrar(atual);
    });
  }

  if (!jaViu() && passos.length) {
    guia.hidden = false;
    guia.setAttribute("aria-hidden", "false");
    mostrar(0);
    document.addEventListener("keydown", aoTeclar);
    if (avancar) {
      avancar.focus();
    }
  }
})();
