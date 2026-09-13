/* ============================================================================
   SIRAS - mascara de CPF e CNPJ
   ----------------------------------------------------------------------------
   Pontua o documento do responsavel enquanto ele e digitado. Quem decide qual
   mascara vale e a CONTAGEM DE DIGITOS: onze e CPF, quatorze e CNPJ. Nao ha
   seletor perguntando de qual dos dois se trata, porque o proprio numero ja diz.

   Fora dessas duas contagens o texto fica como foi digitado. Encaixar dez ou
   doze digitos na mascara do CPF a forca produziria um documento que PARECE
   valido e nao e - e num laudo assinado isso e pior que o numero cru.

   Isto e conveniencia, nao a regra: quem pontua o que sai no laudo e o servidor
   (formulario.formatar_documento). Sem JavaScript o campo aceita os digitos
   corridos e o documento sai pontuado do mesmo jeito. As duas implementacoes
   seguem a mesma tabela de mascaras, e o teste compara as duas.

   O CURSOR e reposicionado por contagem de digitos, e nao por posicao de texto:
   ao inserir um ponto antes do cursor, a posicao em caracteres muda e a posicao
   em digitos nao. Sem isso, corrigir um numero no meio do campo jogava o cursor
   para o fim a cada tecla.
   ========================================================================= */
(function () {
  "use strict";

  var MASCARAS = {
    11: "###.###.###-##",
    14: "##.###.###/####-##"
  };

  var campo = document.getElementById("responsavel_documento");
  if (!campo) {
    return;
  }

  function digitos(texto) {
    return String(texto).replace(/\D/g, "");
  }

  function pontuar(texto) {
    var numeros = digitos(texto);
    var mascara = MASCARAS[numeros.length];
    if (!mascara) {
      return texto;
    }
    var saida = "";
    var proximo = 0;
    for (var i = 0; i < mascara.length; i++) {
      saida += mascara[i] === "#" ? numeros[proximo++] : mascara[i];
    }
    return saida;
  }

  function digitosAteOCursor(texto, cursor) {
    return digitos(texto.slice(0, cursor)).length;
  }

  function posicaoDoDigito(texto, quantos) {
    if (quantos === 0) {
      return 0;
    }
    var vistos = 0;
    for (var i = 0; i < texto.length; i++) {
      if (/\d/.test(texto[i])) {
        vistos++;
        if (vistos === quantos) {
          return i + 1;
        }
      }
    }
    return texto.length;
  }

  campo.addEventListener("input", function () {
    var antes = campo.value;
    var cursor = campo.selectionStart;
    var depois = pontuar(antes);

    if (depois === antes) {
      return;
    }
    var quantos = digitosAteOCursor(antes, cursor);
    campo.value = depois;
    campo.setSelectionRange(
      posicaoDoDigito(depois, quantos),
      posicaoDoDigito(depois, quantos)
    );
  });

  /* Ao sair do campo, o valor colado de uma planilha - com espacos, ou ja
     pontuado de outro jeito - fica no formato do laudo. */
  campo.addEventListener("blur", function () {
    campo.value = pontuar(campo.value);
  });

  /* O campo pode chegar preenchido: depois de um erro de validacao, ou vindo do
     "Editar a analise". */
  if (campo.value) {
    campo.value = pontuar(campo.value);
  }
})();
