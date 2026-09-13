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
    var valor = decimal(campo.value);
    if (campo.value.trim() === "") {
      return campo.required ? "Campo obrigatório." : null;
    }
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
      rotulo.appendChild(aviso);
    }
    aviso.textContent = erro;
  }

  var numericos = document.querySelectorAll('.campo input[type="number"]');
  Array.prototype.forEach.call(numericos, function (campo) {
    /* Só depois do primeiro blur: avisar enquanto a pessoa digita o primeiro
       dígito acusaria erro em todo valor pela metade. */
    campo.addEventListener("blur", function () {
      campo.dataset.tocado = "1";
      avaliar(campo);
    });
    campo.addEventListener("input", function () {
      var rotulo = campo.closest(".campo");
      if (rotulo) {
        rotulo.classList.toggle("campo--preenchido", campo.value.trim() !== "");
      }
      if (campo.dataset.tocado) {
        avaliar(campo);
      }
    });
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
})();
