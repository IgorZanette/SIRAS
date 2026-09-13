/* ============================================================================
   SIRAS - talhoes adicionais
   ----------------------------------------------------------------------------
   Uma propriedade raramente e uma amostra so. Este arquivo deixa o tecnico
   acrescentar outras areas ao MESMO formulario, para sairem num laudo unico com
   uma recomendacao por talhao.

   O que se repete e so a analise de solo: cultura, sistema de manejo, PRNT,
   cultivo e antecedente sao preenchidos uma vez e valem para todas as areas.

   COMO OS CAMPOS SAO NOMEADOS
   O primeiro talhao mantem os nomes originais - "ph_agua", "talhao", "area_ha".
   Do segundo em diante vem o sufixo "__2", "__3". Nao e detalhe de gosto: e o
   que faz a analise de uma area so continuar exatamente o que sempre foi. A
   leitura ao vivo, o preenchimento por exemplo e a volta do laudo para a edicao
   seguem funcionando sem saber que talhoes multiplos existem.

   O indice CRESCE e nunca e reaproveitado. Remover o talhao 2 e acrescentar
   outro produz o 3, deixando um buraco na numeracao - de proposito: reaproveitar
   o 2 misturaria os valores de um campo com os do que acabou de sair, se o
   navegador tivesse restaurado algum.

   SEM JAVASCRIPT o bloco simplesmente nao ganha cartoes, e a analise de um
   talhao funciona inteira. O servidor tambem sabe redesenhar os cartoes que ja
   vieram, entao um erro de validacao nao apaga o que foi digitado.
   ========================================================================= */
(function () {
  "use strict";

  var bloco = document.querySelector("[data-talhoes]");
  var molde = document.getElementById("molde-talhao");
  if (!bloco || !molde) {
    return;
  }

  var lista = bloco.querySelector("[data-talhoes-lista]");
  var adicionar = bloco.querySelector("[data-adicionar-talhao]");

  function maiorIndice() {
    var maior = 1;
    Array.prototype.forEach.call(lista.querySelectorAll("[data-talhao]"), function (cartao) {
      var valor = parseInt(cartao.getAttribute("data-talhao"), 10);
      if (valor > maior) {
        maior = valor;
      }
    });
    return maior;
  }

  function renumerar() {
    /* O numero do titulo e a POSICAO, e nao o indice do campo: quem le a tela
       conta talhoes, nao sufixos. Os dois divergem assim que um cartao e
       removido, e e a posicao que faz sentido para quem preenche. */
    Array.prototype.forEach.call(lista.querySelectorAll("[data-talhao]"), function (cartao, ordem) {
      var titulo = cartao.querySelector("h3");
      if (titulo) {
        titulo.textContent = "Talhão " + (ordem + 2);
      }
    });
  }

  function aoClicar(evento) {
    var remover = evento.target.closest("[data-remover-talhao]");
    if (!remover) {
      return;
    }
    var cartao = remover.closest("[data-talhao]");
    if (cartao) {
      cartao.remove();
      renumerar();
    }
  }

  adicionar.addEventListener("click", function () {
    var indice = maiorIndice() + 1;

    /* O molde e o MESMO macro que o servidor usa para redesenhar um cartao que
       ja veio preenchido. Assim nao ha como uma das duas versoes ganhar um campo
       e a outra nao. */
    var marcacao = molde.innerHTML.split("__IDX__").join(String(indice));
    var recipiente = document.createElement("div");
    recipiente.innerHTML = marcacao;

    var cartao = recipiente.querySelector("[data-talhao]");
    if (!cartao) {
      return;
    }
    lista.appendChild(cartao);
    renumerar();

    /* O foco vai para o nome da area: e o primeiro campo do cartao e o unico que
       passa a ser obrigatorio por existir mais de um talhao. */
    var nome = cartao.querySelector('input[name^="talhao__"]');
    if (nome) {
      nome.focus();
    }
  });

  lista.addEventListener("click", aoClicar);
  renumerar();
})();
