/* ============================================================================
   SIRAS - leitura ao vivo
   ----------------------------------------------------------------------------
   Este arquivo NAO interpreta nada. Ele junta o que esta no formulario, manda ao
   servidor e troca o conteudo do painel pela marcacao que voltou pronta.

   E deliberado (PLANO-FRONTEND par. 9.4, opcao B): a interpretacao roda no mesmo
   motor Python que os casos de teste validam. Reimplementar aqui a classificacao
   de teor pareceria mais simples e criaria uma segunda implementacao da mesma
   regra, nao testada, justamente da regra que a hipotese H1.1 mede.

   Se alguem um dia precisar acrescentar uma classe, uma faixa ou um limiar a este
   arquivo, o lugar certo e a base de conhecimento, nao aqui.
   ========================================================================= */
(function () {
  "use strict";

  var ESPERA_MS = 300;

  var formulario = document.querySelector("[data-formulario-analise]");
  var painel = document.getElementById("leitura");
  if (!formulario || !painel) {
    return;
  }

  var endereco = painel.dataset.url;
  var temporizador = null;
  /* Ordem de chegada nao e garantida: uma requisicao disparada antes pode voltar
     depois e sobrescrever uma leitura mais nova com uma mais velha. O contador
     descarta qualquer resposta que nao seja a da ultima requisicao enviada. */
  var ultimaRequisicao = 0;

  function coletar() {
    var dados = {};
    new FormData(formulario).forEach(function (valor, nome) {
      dados[nome] = valor;
    });
    return dados;
  }

  function interpretar() {
    var requisicao = ++ultimaRequisicao;

    fetch(endereco, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletar())
    })
      .then(function (resposta) {
        return resposta.ok ? resposta.json() : null;
      })
      .then(function (corpo) {
        if (corpo && requisicao === ultimaRequisicao) {
          painel.innerHTML = corpo.html;
        }
      })
      .catch(function () {
        /* Sem rede ou servidor fora do ar: mantem a ultima leitura na tela em vez
           de apagar o que o usuario ja conseguiu ler. O laudo tem validacao
           propria e nao depende deste painel. */
      });
  }

  function agendar() {
    window.clearTimeout(temporizador);
    temporizador = window.setTimeout(interpretar, ESPERA_MS);
  }

  /* 'input' cobre digitacao; 'change' cobre os seletores e o colar com o mouse. */
  formulario.addEventListener("input", agendar);
  formulario.addEventListener("change", agendar);
})();
