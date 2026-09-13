/* ============================================================================
   SIRAS - aviso proprio ao tentar gerar o laudo incompleto
   ----------------------------------------------------------------------------
   Sem isto, quem clica em "Gerar laudo" com um campo em branco recebe a bolha
   nativa do navegador: cinza, com a tipografia do sistema operacional, escrita
   por ele ("Preencha este campo"), mostrando um campo de cada vez e sumindo ao
   primeiro clique. Num sistema que desenhou o proprio conjunto de icones e a
   propria paleta, ela e a unica peca que nao pertence ao produto.

   O que entra no lugar: os campos que faltam marcados TODOS de uma vez, cada um
   com o aviso do proprio sistema no seu rodape, um resumo acima do formulario
   dizendo quantos sao, e o foco levado ao primeiro. Quem preenche corrige de uma
   vez em vez de descobrir um campo por clique.

   O ATRIBUTO novalidate E POSTO AQUI, e nao escrito no HTML. Assim, sem
   JavaScript o formulario continua com a validacao nativa do navegador - feia,
   mas presente. Desligar a validacao no HTML deixaria quem esta sem JavaScript
   sem nenhuma, e o servidor recebendo envio vazio.

   Nenhum limiar agronomico mora aqui: o que este arquivo sabe e o que o HTML
   declara, e o servidor continua sendo quem valida de verdade.
   ========================================================================= */
(function () {
  "use strict";

  var formulario = document.querySelector("[data-formulario-analise]");
  if (!formulario) {
    return;
  }

  formulario.setAttribute("novalidate", "novalidate");

  var SELETOR = "input[required], select[required]";

  function rodape(campo) {
    var rotulo = campo.closest(".campo");
    if (!rotulo) {
      return null;
    }
    return rotulo.querySelector(".campo__rodape") || rotulo;
  }

  function avisar(campo) {
    var rotulo = campo.closest(".campo");
    if (!rotulo) {
      return;
    }
    rotulo.classList.add("campo--invalido");

    var aviso = rotulo.querySelector(".campo__erro");
    if (!aviso) {
      aviso = document.createElement("span");
      aviso.className = "campo__erro";
      aviso.setAttribute("role", "alert");
      rodape(campo).appendChild(aviso);
    }
    aviso.textContent = "Este campo precisa ser preenchido.";
    campo.dataset.tocado = "1";
  }

  function resumo(quantos) {
    var caixa = formulario.querySelector("[data-resumo-envio]");
    if (!caixa) {
      caixa = document.createElement("div");
      caixa.className = "aviso aviso--erro resumo-envio";
      caixa.setAttribute("data-resumo-envio", "");
      caixa.setAttribute("role", "alert");
      formulario.insertBefore(caixa, formulario.firstChild);
    }
    caixa.textContent =
      quantos === 1
        ? "Falta preencher 1 campo obrigatório. Ele está marcado abaixo."
        : "Faltam preencher " + quantos + " campos obrigatórios. Eles estão marcados abaixo.";
    return caixa;
  }

  function limparResumo() {
    var caixa = formulario.querySelector("[data-resumo-envio]");
    if (caixa) {
      caixa.remove();
    }
  }

  formulario.addEventListener("submit", function (evento) {
    var vazios = Array.prototype.filter.call(
      formulario.querySelectorAll(SELETOR),
      function (campo) {
        return campo.value.trim() === "";
      }
    );

    if (!vazios.length) {
      limparResumo();
      return;
    }

    evento.preventDefault();
    /* A tela de "estamos calculando" escuta o mesmo envio, e nao abre aqui
       porque ela propria consulta checkValidity() antes de aparecer. novalidate
       desliga a BOLHA do navegador, nao a checagem: checkValidity() continua
       devolvendo falso, e o veu continua sabendo que nao deve subir. */

    vazios.forEach(avisar);
    var caixa = resumo(vazios.length);

    /* O foco vai para o primeiro campo que falta, e a rolagem para o resumo:
       assim quem usa teclado ja esta no campo a preencher, e quem usa o mouse
       ve de imediato quantos sao. */
    caixa.scrollIntoView({ behavior: "smooth", block: "center" });
    vazios[0].focus({ preventScroll: true });
  }, true);
})();
