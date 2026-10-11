/* ============================================================================
   SIRAS - revelacao das secoes ao rolar
   ----------------------------------------------------------------------------
   A landing tinha todas as secoes pintadas de uma vez, e a leitura chegava nelas
   sem nenhuma marcacao de ritmo: o olho percorre dois mil pixels de conteudo
   igualmente presente. A revelacao em cascata nao e enfeite -- ela diz "isto
   aqui comeca agora", que e o que um titulo de secao faz em papel e o que a
   rolagem apaga na tela.

   MOVIMENTO COM PROPOSITO, e nao decorativo:
   - a distancia e curta (14px) e a duracao tambem (420ms): o conteudo CHEGA, nao
     desfila. Animacao longa numa landing e tempo que se cobra de quem le;
   - cada elemento e revelado UMA vez e o observador o solta. Reanimar ao subir e
     voltar transforma a rolagem em brinquedo;
   - o padrao e VISIVEL. A classe so entra se este script rodar, entao sem
     JavaScript a pagina aparece inteira, como sempre apareceu.

   QUEM PEDIU MENOS MOVIMENTO NAO RECEBE NENHUM. A consulta de midia e checada
   aqui, e nao so no CSS: com ela ativa o script marca tudo como revelado de uma
   vez e nem cria o observador.

   Sem IntersectionObserver (navegador antigo), mesmo caminho: tudo visivel.
   ========================================================================= */
(function () {
  "use strict";

  var alvos = document.querySelectorAll("[data-revelar]");
  if (!alvos.length) {
    return;
  }

  function revelarTudo() {
    Array.prototype.forEach.call(alvos, function (alvo) {
      alvo.classList.add("e-visivel");
    });
  }

  var semMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (semMovimento || !("IntersectionObserver" in window)) {
    revelarTudo();
    return;
  }

  /* A margem inferior negativa atrasa um pouco o gatilho: o elemento comeca a
     aparecer quando ja entrou de verdade no campo de visao, e nao no instante em
     que a borda toca a tela. */
  var observador = new IntersectionObserver(function (entradas) {
    entradas.forEach(function (entrada) {
      if (!entrada.isIntersecting) {
        return;
      }
      entrada.target.classList.add("e-visivel");
      observador.unobserve(entrada.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

  Array.prototype.forEach.call(alvos, function (alvo) {
    observador.observe(alvo);
  });

  /* Rede de seguranca: se por algum motivo o observador nao disparar (uma aba em
     segundo plano que nunca ganha foco, por exemplo), o conteudo aparece assim
     mesmo. Um texto invisivel por causa de uma animacao e pior do que nenhuma
     animacao. */
  window.setTimeout(revelarTudo, 3000);
})();
