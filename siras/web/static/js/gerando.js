/* ============================================================================
   SIRAS - tela de calculo
   ----------------------------------------------------------------------------
   Mostra a sequencia de modulos do motor enquanto o laudo e gerado.

   Sobre a duracao: em localhost o motor responde em dezenas de milissegundos, e
   um veu que aparece e some nesse intervalo e pior que veu nenhum - fica so um
   piscar. Por isso o envio real e adiado ate ESPERA_MINIMA_MS, tempo suficiente
   para os cinco passos serem lidos.

   Isso e uma pausa DELIBERADA, e nao progresso simulado: os cinco passos sao os
   modulos que gerar_laudo() realmente percorre, na ordem em que os chama. Quem
   quiser o laudo instantaneo muda a constante para 0 e o comportamento continua
   correto - o veu passa a durar o tempo real da requisicao.
   ========================================================================= */
(function () {
  "use strict";

  var ESPERA_MINIMA_MS = 3500;

  var formulario = document.querySelector("[data-formulario-analise]");
  var veu = document.getElementById("calculando");
  if (!formulario || !veu) {
    return;
  }

  var passos = Array.prototype.slice.call(veu.querySelectorAll("[data-passo]"));
  var barra = veu.querySelector(".calculando__barra i");
  var enviando = false;

  function acender(indice) {
    passos.forEach(function (passo, posicao) {
      passo.classList.toggle("is-ativo", posicao === indice);
      passo.classList.toggle("is-feito", posicao < indice);
    });
    if (barra) {
      barra.style.width = Math.round(((indice + 1) / passos.length) * 100) + "%";
    }
  }

  function rodarSequencia() {
    var intervalo = ESPERA_MINIMA_MS / passos.length;
    passos.forEach(function (_, indice) {
      window.setTimeout(function () { acender(indice); }, intervalo * indice);
    });
    window.setTimeout(function () {
      passos.forEach(function (passo) {
        passo.classList.remove("is-ativo");
        passo.classList.add("is-feito");
      });
    }, ESPERA_MINIMA_MS);
  }

  formulario.addEventListener("submit", function (evento) {
    /* checkValidity: se o navegador vai barrar o envio por campo obrigatorio em
       branco, o veu nao pode aparecer - o usuario ficaria olhando uma tela de
       calculo sobre um formulario que nem foi enviado. */
    if (!formulario.checkValidity()) {
      return;
    }
    if (enviando) {
      evento.preventDefault();
      return;
    }

    enviando = true;
    evento.preventDefault();

    veu.hidden = false;
    veu.setAttribute("aria-hidden", "false");
    acender(0);
    rodarSequencia();

    window.setTimeout(function () { formulario.submit(); }, ESPERA_MINIMA_MS);
  });

  /* Voltar pelo historico devolve a pagina do cache com o veu aberto: sem isto o
     usuario encontra a tela de calculo travada sobre um formulario parado. */
  window.addEventListener("pageshow", function (evento) {
    if (evento.persisted) {
      veu.hidden = true;
      veu.setAttribute("aria-hidden", "true");
      enviando = false;
    }
  });
})();
