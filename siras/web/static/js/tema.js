/* ============================================================================
   SIRAS - alternador de tema
   ----------------------------------------------------------------------------
   O par. 14 do plano previa este botao: tema escuro e otimo em monitor e ruim sob
   sol direto, e parte do publico usa tablet em campo. A escolha fica no navegador
   de quem usa - nao ha conta, nao ha servidor guardando preferencia.

   O <script> que aplica o tema salvo roda no <head>, antes da primeira pintura;
   se rodasse aqui, a pagina piscaria escura antes de virar clara.
   ========================================================================= */
(function () {
  "use strict";

  var botao = document.getElementById("alternar-tema");
  if (!botao) {
    return;
  }

  function aplicar(tema) {
    document.documentElement.dataset.tema = tema;
    botao.setAttribute("aria-pressed", String(tema === "claro"));
    botao.setAttribute(
      "aria-label", tema === "claro" ? "Mudar para o modo escuro" : "Mudar para o modo claro"
    );
    try {
      window.localStorage.setItem("siras-tema", tema);
    } catch (erro) {
      /* Navegacao privada ou armazenamento bloqueado: a troca vale para esta
         sessao e nada quebra. */
    }
  }

  botao.addEventListener("click", function () {
    aplicar(document.documentElement.dataset.tema === "claro" ? "escuro" : "claro");
  });

  aplicar(document.documentElement.dataset.tema || "escuro");
})();
