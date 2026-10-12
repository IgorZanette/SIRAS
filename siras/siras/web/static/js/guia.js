/* ============================================================================
   SIRAS - apresentacao periodica
   ----------------------------------------------------------------------------
   Tres passos, dispensavel, e que reaparece a cada CICLO visitas.

   Por que periodica e nao "so na primeira vez": o publico do SIRAS nao e de uso
   diario. Um tecnico que abre o sistema em duas safras diferentes volta sem
   lembrar que a cultura precede a analise, e uma guia que nunca mais aparece
   deixa de ajudar exatamente quem mais precisa. Reaparecer a cada cinco entradas
   relembra sem virar obstaculo - quem usa todo dia a ve uma vez a cada semana de
   trabalho, e pode fechar com Esc em um segundo.

   Uma ENTRADA e uma sessao do navegador, nao um carregamento: recarregar a
   pagina cinco vezes seguidas nao faz a guia voltar, porque isso seria contar
   impaciencia como visita.

   O painel nasce com o atributo hidden no HTML e so e revelado aqui. Assim, sem
   JavaScript a pagina simplesmente nao o mostra - em vez de mostra-lo sem meio de
   fechar, que seria pior que nao ter guia nenhum.
   ========================================================================= */
(function () {
  "use strict";

  /* Mostra na 1a, 6a, 11a entrada... Trocar para 1 mostra sempre; para um numero
     muito alto, praticamente so na primeira vez. */
  var CICLO = 5;

  var CHAVE_VISITAS = "siras-guia-visitas";
  var CHAVE_SESSAO = "siras-guia-sessao";

  var guia = document.getElementById("guia");
  if (!guia) {
    return;
  }

  var passos = Array.prototype.slice.call(guia.querySelectorAll("[data-guia-passo]"));
  var pontos = Array.prototype.slice.call(guia.querySelectorAll("[data-guia-ponto]"));
  var avancar = guia.querySelector("[data-guia-avancar]");
  var atual = 0;

  function contarEntrada() {
    /* Retorna o numero desta entrada, contando a sessao uma vez so. Em navegacao
       privada, ou com armazenamento bloqueado, devolve 1: a guia aparece uma vez
       por sessao e nada quebra. */
    try {
      if (window.sessionStorage.getItem(CHAVE_SESSAO)) {
        return parseInt(window.localStorage.getItem(CHAVE_VISITAS), 10) || 1;
      }
      var visitas = (parseInt(window.localStorage.getItem(CHAVE_VISITAS), 10) || 0) + 1;
      window.localStorage.setItem(CHAVE_VISITAS, String(visitas));
      window.sessionStorage.setItem(CHAVE_SESSAO, "1");
      return visitas;
    } catch (erro) {
      return 1;
    }
  }

  function deveMostrar(entrada) {
    return (entrada - 1) % CICLO === 0;
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
    /* Fechar nao marca nada: o contador ja avancou ao abrir a pagina, e e ele que
       decide a proxima aparicao. Assim "Pular" significa "agora nao", e nao
       "nunca mais" - que e o que a guia periodica se propoe a ser. */
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

  if (passos.length && deveMostrar(contarEntrada())) {
    guia.hidden = false;
    guia.setAttribute("aria-hidden", "false");
    mostrar(0);
    document.addEventListener("keydown", aoTeclar);
    if (avancar) {
      avancar.focus();
    }
  }
})();
