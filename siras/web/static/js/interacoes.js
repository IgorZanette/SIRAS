/* ============================================================================
   SIRAS - microinteracoes
   ----------------------------------------------------------------------------
   Tres comportamentos pequenos, nenhum deles com regra agronomica dentro:

   1. VALIDACAO IMEDIATA. As faixas vem dos atributos min e max que o servidor
      escreveu a partir de AnaliseSolo e Contexto - este arquivo nao conhece
      nenhum limiar, so le o que o HTML declara. Quem valida de verdade continua
      sendo o servidor; isto apenas adianta o aviso para o momento da digitacao.

   2. CONTADORES da landing, que sobem quando entram na viewport.

   3. CAMPO PREENCHIDO, que ganha marca visual assim que recebe valor - sem isso
      valor digitado e marcador de posicao ficam com a mesma cara.

   Tudo degrada em silencio: sem JavaScript, o formulario continua validando no
   envio, os numeros aparecem prontos e os campos funcionam.
   ========================================================================= */
(function () {
  "use strict";

  var decimal = function (texto) {
    var numero = parseFloat(String(texto).replace(",", "."));
    return isNaN(numero) ? null : numero;
  };

  /* --- 1. validacao imediata ---------------------------------------------- */
  function mensagemDeErro(campo) {
    if (campo.value.trim() === "") {
      return campo.required ? "Este campo precisa ser preenchido." : null;
    }
    if (campo.tagName === "SELECT" || campo.type === "text") {
      return null;
    }
    var valor = decimal(campo.value);
    if (valor === null) {
      return "Informe um número.";
    }
    var minimo = campo.min === "" ? null : parseFloat(campo.min);
    var maximo = campo.max === "" ? null : parseFloat(campo.max);
    if (minimo !== null && valor < minimo) {
      return "Abaixo da faixa aceita" + (maximo !== null ? " (" + minimo + " a " + maximo + ")" : "") + ".";
    }
    if (maximo !== null && valor > maximo) {
      return "Acima da faixa aceita (" + minimo + " a " + maximo + ").";
    }
    return null;
  }

  function avaliar(campo) {
    var rotulo = campo.closest(".campo");
    if (!rotulo) {
      return;
    }
    var erro = mensagemDeErro(campo);
    var aviso = rotulo.querySelector(".campo__erro");

    rotulo.classList.toggle("campo--preenchido", campo.value.trim() !== "");
    rotulo.classList.toggle("campo--invalido", Boolean(erro));

    if (!erro) {
      if (aviso) {
        aviso.remove();
      }
      return;
    }
    if (!aviso) {
      aviso = document.createElement("span");
      aviso.className = "campo__erro";
      aviso.setAttribute("role", "alert");
      /* DENTRO do rodape, e nao solto no fim do rotulo. A grade alinha os campos
         por subgrid, com uma faixa para o rotulo, uma para a caixa e uma para o
         rodape: um quarto filho nao teria faixa e caia por cima da ajuda. */
      (rotulo.querySelector(".campo__rodape") || rotulo).appendChild(aviso);
    }
    aviso.textContent = erro;
  }

  function avaliavel(alvo) {
    return alvo
      && alvo.matches
      && alvo.matches('.campo input[type="number"], .campo input[type="text"], .campo select');
  }

  /* Delegado no documento, e nao ligado campo a campo na carga. Um talhao
     acrescentado depois nasce com os mesmos campos e precisa da mesma validacao;
     ligando um a um, os cartoes criados pelo botao "Adicionar novo talhao"
     ficavam sem nenhuma - digitava-se -500 de pH ali e nada acusava.

     focusout no lugar de blur porque blur nao sobe na arvore e nao pode ser
     delegado. */
  document.addEventListener("focusout", function (evento) {
    if (!avaliavel(evento.target)) {
      return;
    }
    /* Só depois do primeiro blur: avisar enquanto a pessoa digita o primeiro
       dígito acusaria erro em todo valor pela metade. */
    evento.target.dataset.tocado = "1";
    avaliar(evento.target);
  });

  document.addEventListener("input", function (evento) {
    if (!avaliavel(evento.target)) {
      return;
    }
    var rotulo = evento.target.closest(".campo");
    if (rotulo) {
      rotulo.classList.toggle("campo--preenchido", evento.target.value.trim() !== "");
    }
    if (evento.target.dataset.tocado) {
      avaliar(evento.target);
    }
  });

  document.addEventListener("change", function (evento) {
    if (avaliavel(evento.target) && evento.target.tagName === "SELECT") {
      evento.target.dataset.tocado = "1";
      avaliar(evento.target);
    }
  });

  /* --- 2. contadores ------------------------------------------------------ */
  var contadores = document.querySelectorAll("[data-contador]");
  if (contadores.length) {
    var parado = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var subir = function (elemento) {
      var alvo = parseInt(elemento.dataset.contador, 10);
      if (parado || !alvo) {
        elemento.textContent = elemento.dataset.contador;
        return;
      }
      var duracao = 900;
      var inicio = null;
      var passo = function (agora) {
        inicio = inicio || agora;
        var fracao = Math.min((agora - inicio) / duracao, 1);
        /* Desaceleracao no fim: o numero chega ao valor e para, em vez de bater. */
        var suave = 1 - Math.pow(1 - fracao, 3);
        elemento.textContent = Math.round(alvo * suave);
        if (fracao < 1) {
          window.requestAnimationFrame(passo);
        }
      };
      window.requestAnimationFrame(passo);
    };

    if (!("IntersectionObserver" in window)) {
      Array.prototype.forEach.call(contadores, subir);
    } else {
      var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
          if (entrada.isIntersecting) {
            subir(entrada.target);
            observador.unobserve(entrada.target);
          }
        });
      }, { threshold: 0.6 });
      Array.prototype.forEach.call(contadores, function (elemento) {
        elemento.textContent = "0";
        observador.observe(elemento);
      });
    }
  }

  /* ---------------------------------------------------------------------
     Dica do campo opcional: dispensavel com Esc
     ---------------------------------------------------------------------
     Conteudo que aparece ao passar o mouse precisa poder ser fechado sem
     mover o ponteiro (WCAG 1.4.13) - alguem usando ampliacao de tela pode ter
     o balao cobrindo justamente o campo que ia preencher.

     O CSS abre a dica no :hover e no :focus-visible; nao ha como ensinar Esc a
     uma pseudo-classe. A marca is-dispensada vence as duas por !important, e
     sai assim que o ponteiro deixa a dica ou o foco muda - senao o campo
     ficaria sem dica pelo resto da visita.
     ------------------------------------------------------------------ */
  document.addEventListener("keydown", function (evento) {
    if (evento.key !== "Escape") {
      return;
    }
    Array.prototype.forEach.call(document.querySelectorAll(".dica"), function (dica) {
      dica.classList.add("is-dispensada");
    });
  });

  function reabilitar(evento) {
    var dica = evento.target.closest ? evento.target.closest(".dica") : null;
    Array.prototype.forEach.call(
      document.querySelectorAll(".dica.is-dispensada"),
      function (outra) {
        if (outra !== dica) {
          outra.classList.remove("is-dispensada");
        }
      }
    );
  }

  document.addEventListener("mouseover", reabilitar);
  document.addEventListener("focusin", reabilitar);
})();
