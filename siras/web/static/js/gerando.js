/* ============================================================================
   SIRAS - tela de calculo
   ----------------------------------------------------------------------------
   Mostra a sequencia de modulos do motor enquanto o laudo e gerado, e conduz a
   cena do monolito de solo junto com ela.

   Sobre a duracao: em localhost o motor responde em dezenas de milissegundos, e
   um veu que aparece e some nesse intervalo e pior que veu nenhum - fica so um
   piscar. Por isso o envio real e adiado ate ESPERA_MINIMA_MS, tempo suficiente
   para os cinco passos serem lidos.

   Isso e uma pausa DELIBERADA, e nao progresso simulado: os cinco passos sao os
   modulos que gerar_laudo() realmente percorre, na ordem em que os chama. Quem
   quiser o laudo instantaneo muda a constante para 0 e o comportamento continua
   correto - o veu passa a durar o tempo real da requisicao.

   O QUE ESTE ARQUIVO DIZ A CENA, e so isto:
     data-etapa="N"   o passo que esta acontecendo agora (1 a 5, ou "pronto");
     .passou-N        os passos que ja terminaram, e cujo efeito fica na cena.
   O que cada passo desenha - o calcario caindo, o broto crescendo - mora no CSS.
   Assim a animacao pode ser redesenhada sem tocar na logica do envio.
   ========================================================================= */
(function () {
  "use strict";

  /* 12 s. O numero andou: 4,2 s no comeco, 6 s para dar tempo de ler a regra de cada
     passo, 24 s quando a cena 3D entrou e as coreografias nao cabiam, e 12 s agora --
     24 s era espera exaustiva, e uma tela que demora demais passa falta de desempenho,
     que e o oposto do que ela deveria passar.

     E PAUSA DELIBERADA, e nao progresso simulado: o motor responde em dezenas de
     milissegundos. Esta tela existe para ser vista. */
  var ESPERA_MINIMA_MS = 12000;

  /* O TEMPO NAO E DIVIDIDO POR IGUAL, e e isso que deixa 12 s bastarem.

     As tres etapas do meio -- calagem, adubacao e formulacao -- sao as que tem
     coreografia de verdade: o calcario caindo e ficando na superficie, o fosforo e o
     potassio subindo da camada de referencia, os tres montes se agrupando. Elas
     precisam de tempo para serem lidas como movimento, e nao como corte.

     As duas das pontas nao: a leitura e uma varredura que atravessa o perfil uma vez,
     e a aptidao e uma alternancia que se entende no primeiro ciclo. Dar a elas o mesmo
     tempo das outras tres era alongar a espera sem acrescentar nada para ver.

     Os pesos sao relativos: mexer em ESPERA_MINIMA_MS redistribui tudo sozinho. */
  var PESOS_DAS_ETAPAS = [0.72, 1.3, 1.3, 1.3, 0.88];

  /* A confirmacao ocupa a ultima fatia: o broto precisa de um instante para abrir
     a folha final antes de a pagina trocar. */
  var FATIA_DO_PRONTO_MS = 900;

  var formulario = document.querySelector("[data-formulario-analise]");
  var veu = document.getElementById("calculando");
  if (!formulario || !veu) {
    return;
  }

  var passos = Array.prototype.slice.call(veu.querySelectorAll("[data-passo]"));
  var barra = veu.querySelector(".calculando__barra i");
  var enviando = false;

  /* Duracao de cada etapa em ms, e o instante em que cada uma comeca.
     Se o numero de passos no HTML divergir dos pesos, o excedente entra com peso 1:
     um passo novo no template nao pode quebrar a tela por causa de uma lista aqui. */
  var animado = ESPERA_MINIMA_MS - FATIA_DO_PRONTO_MS;
  var pesos = passos.map(function (_, i) {
    return PESOS_DAS_ETAPAS[i] === undefined ? 1 : PESOS_DAS_ETAPAS[i];
  });
  var somaDosPesos = pesos.reduce(function (a, b) { return a + b; }, 0) || 1;
  var duracoes = pesos.map(function (peso) { return (animado * peso) / somaDosPesos; });
  var inicios = duracoes.reduce(function (acc, d) {
    acc.push(acc[acc.length - 1] + d);
    return acc;
  }, [0]);

  function marcarCena(etapa, concluidos) {
    veu.setAttribute("data-etapa", String(etapa));
    for (var n = 1; n <= passos.length; n++) {
      veu.classList.toggle("passou-" + n, n <= concluidos);
    }
  }

  function acender(indice) {
    passos.forEach(function (passo, posicao) {
      passo.classList.toggle("is-ativo", posicao === indice);
      passo.classList.toggle("is-feito", posicao < indice);
    });
    marcarCena(indice + 1, indice);

    /* A duracao vai ao CSS A CADA ETAPA, e nao uma vez no comeco: com tempos
       diferentes, um valor unico faria a barra e o traco do passo ativo correrem em
       velocidade errada em quatro das cinco etapas. */
    veu.style.setProperty("--passo-ms", Math.round(duracoes[indice]) + "ms");

    if (barra) {
      /* A barra mede TEMPO, e nao passos: com etapas desiguais, encher um quinto por
         etapa a faria parar e disparar. */
      barra.style.width = ((inicios[indice + 1] / animado) * 100).toFixed(2) + "%";
    }
  }

  function concluir() {
    passos.forEach(function (passo) {
      passo.classList.remove("is-ativo");
      passo.classList.add("is-feito");
    });
    marcarCena("pronto", passos.length);
    var pronto = veu.querySelector(".calculando__pronto");
    if (pronto) {
      pronto.hidden = false;
    }
  }

  /* A etapa 0 nao entra aqui: o submit a acende na hora, no mesmo quadro em que o veu
     aparece. Agendada, ela so acenderia no proximo macrotask, e o veu abriria por um
     instante com os cinco passos apagados. */
  function rodarSequencia() {
    passos.slice(1).forEach(function (_, posicao) {
      var indice = posicao + 1;
      window.setTimeout(function () { acender(indice); }, inicios[indice]);
    });
    window.setTimeout(concluir, animado);
  }

  formulario.addEventListener("submit", function (evento) {
    /* checkValidity: se o envio vai ser barrado por campo obrigatorio em branco, o
       veu nao pode aparecer - o usuario ficaria olhando uma tela de calculo sobre
       um formulario que nem foi enviado. novalidate (posto por envio.js) desliga so
       a bolha do navegador; a checagem continua valendo. */
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
      marcarCena(0, 0);
      enviando = false;
    }
  });
})();
