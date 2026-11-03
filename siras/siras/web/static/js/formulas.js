/* ============================================================================
   SIRAS - campo "Formulas que a sua revenda tem"
   ----------------------------------------------------------------------------
   Achado do piloto (02/11/2026): o campo era texto livre, o hifen tinha de ser
   digitado, "5 25 25" era recusado, e uma soma impossivel (40-50-60 = 150%) so
   aparecia DEPOIS de enviar, travando o laudo inteiro por um campo opcional.

   Tres coisas aqui, todas de conveniencia:

   1. MASCARA. Digita-se so numero e o hifen entra sozinho a cada dois digitos:
      "052020" vira "05-20-20". Espaco, ponto, barra ou hifen fecham um grupo
      antes da hora, para garantias de um digito: "5 25 25" vira "5-25-25", e ao
      sair do campo, "05-25-25".
   2. CONFERENCIA NA HORA. Ao sair do campo, se a formula estiver incompleta ou
      as tres garantias somarem mais de 100%, o proprio campo diz o que ha de
      errado - antes do envio, e nao depois.
   3. O ENVIO NAO SAI com formula invalida: o foco volta ao campo.

   A regra continua no servidor (motor/formulacao.py, interpretar_formula_do_usuario),
   que aceita os mesmos formatos. Sem JavaScript, o campo funciona como antes.
   ========================================================================= */
(function () {
  "use strict";

  var campos = document.querySelectorAll('input[name="formula_usuario"]');
  if (!campos.length) { return; }
  var formulario = campos[0].form;

  /* Grupos de digitos do que foi digitado. Separador (espaco . / -) fecha o grupo;
     sem separador, a cada dois digitos abre-se um grupo novo. */
  function grupos(texto) {
    var lista = [];
    var atual = "";
    for (var i = 0; i < texto.length; i++) {
      var c = texto.charAt(i);
      if (c >= "0" && c <= "9") {
        if (atual.length === 2) { lista.push(atual); atual = ""; }
        atual += c;
      } else if (/[\s.\/\-]/.test(c) && atual) {
        lista.push(atual);
        atual = "";
      }
    }
    if (atual) { lista.push(atual); }
    return lista.slice(0, 3);
  }

  function mascarar(campo, digitandoSeparador) {
    var g = grupos(campo.value);
    var texto = g.join("-");
    /* O hifen seguinte aparece assim que o grupo atual fecha, para a pessoa ver que
       pode seguir digitando: "05" -> "05-". */
    var ultimo = g[g.length - 1] || "";
    if (g.length && g.length < 3 && (ultimo.length === 2 || digitandoSeparador)) {
      texto += "-";
    }
    campo.value = texto;
  }

  function problema(campo) {
    var texto = campo.value.trim();
    if (!texto) { return ""; }
    var g = grupos(texto);
    if (g.length < 3) {
      return "Faltam garantias: escreva os três números do rótulo, como 05-20-20.";
    }
    var soma = Number(g[0]) + Number(g[1]) + Number(g[2]);
    if (soma > 100) {
      return "As garantias somam " + soma + "%. São porcentagens do mesmo saco de adubo, " +
             "então juntas não passam de 100%. Confira o rótulo.";
    }
    if (soma === 0) {
      return "Essa fórmula não traz N, P₂O₅ nem K₂O.";
    }
    return "";
  }

  function mostrar(campo, mensagem) {
    var rotulo = campo.closest(".campo");
    var rodape = rotulo && rotulo.querySelector(".campo__rodape");
    var aviso = rodape && rodape.querySelector(".campo__erro-formula");
    if (rodape && !aviso) {
      aviso = document.createElement("span");
      aviso.className = "campo__ajuda campo__erro-formula";
      aviso.setAttribute("role", "alert");
      rodape.appendChild(aviso);
    }
    if (aviso) { aviso.textContent = mensagem; aviso.hidden = !mensagem; }
    if (rotulo) { rotulo.classList.toggle("campo--erro", !!mensagem); }
    campo.setCustomValidity(mensagem);
  }

  function completar(campo) {
    /* Ao sair: "5-25-25" vira "05-25-25", e um hifen sobrando no fim sai. */
    var g = grupos(campo.value);
    if (g.length === 3) {
      campo.value = g.map(function (x) { return x.length === 1 ? "0" + x : x; }).join("-");
    } else {
      campo.value = g.join("-");
    }
    mostrar(campo, problema(campo));
  }

  Array.prototype.forEach.call(campos, function (campo) {
    campo.setAttribute("inputmode", "numeric");
    campo.setAttribute("maxlength", "8");
    campo.setAttribute("spellcheck", "false");

    campo.addEventListener("input", function (evento) {
      var tecla = evento.data || "";
      var apagando = evento.inputType && evento.inputType.indexOf("delete") === 0;
      if (!apagando) { mascarar(campo, /[\s.\/\-]/.test(tecla)); }
      /* Enquanto digita, so limpa o erro; acusar no meio da digitacao irrita. */
      if (!problema(campo)) { mostrar(campo, ""); }
    });
    campo.addEventListener("blur", function () { completar(campo); });
    if (campo.value) { completar(campo); }
  });

  if (formulario) {
    formulario.addEventListener("submit", function (evento) {
      var invalido = null;
      Array.prototype.forEach.call(campos, function (campo) {
        completar(campo);
        if (!invalido && problema(campo)) { invalido = campo; }
      });
      if (invalido) {
        evento.preventDefault();
        invalido.scrollIntoView({ behavior: "smooth", block: "center" });
        invalido.focus({ preventScroll: true });
      }
    }, true);
  }
})();
