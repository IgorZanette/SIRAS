/* ============================================================================
   SIRAS - barra que encolhe ao rolar
   ----------------------------------------------------------------------------
   A barra abre grande e encolhe 20% quando a pagina desce. No topo ela e a
   apresentacao do sistema; dali para baixo o conteudo e que importa, e devolver
   altura ao conteudo e o que se espera de um cabecalho fixo.

   Este arquivo so poe e tira uma classe. Os tamanhos - altura, icone e palavra -
   sao variaveis CSS na propria .barra, e encolhem juntos na mesma proporcao.
   Nenhuma medida em pixels mora aqui: mexer no tamanho da marca e assunto do
   CSS, nao do JavaScript.

   O LIMIAR e maior que a VOLTA de proposito (48px contra 24px). Com um valor so,
   uma pagina parada exatamente no limite alterna entre os dois estados a cada
   pixel de rolagem - a barra tremeria. A faixa morta entre os dois resolve.
   ========================================================================= */
(function () {
  "use strict";

  var LIMIAR = 48;
  var VOLTA = 24;

  var barra = document.querySelector(".barra");
  if (!barra) {
    return;
  }

  var reduzida = false;
  var agendado = false;

  function avaliar() {
    agendado = false;
    var topo = window.pageYOffset || document.documentElement.scrollTop;

    if (!reduzida && topo > LIMIAR) {
      reduzida = true;
      barra.classList.add("is-reduzida");
    } else if (reduzida && topo < VOLTA) {
      reduzida = false;
      barra.classList.remove("is-reduzida");
    }
  }

  /* A rolagem dispara dezenas de vezes por segundo; medir e escrever a cada
     evento forcaria recalculo de layout no meio do gesto. Um quadro basta. */
  function aoRolar() {
    if (!agendado) {
      agendado = true;
      window.requestAnimationFrame(avaliar);
    }
  }

  window.addEventListener("scroll", aoRolar, { passive: true });

  /* Recarregar a pagina no meio dela nao pode abrir com a barra grande sobre um
     conteudo que ja esta rolado. */
  avaliar();
})();
