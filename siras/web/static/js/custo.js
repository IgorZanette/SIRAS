/* ============================================================================
   SIRAS - quanto vai custar: calcario e adubo formulado
   ----------------------------------------------------------------------------
   Compara as formulas que a revenda oferece contra a recomendacao do laudo, com
   os precos, pesos de saca e formulas QUE A PESSOA DIGITA. Nenhuma formula,
   nenhum peso de saca e nenhum preco vem do sistema.

   Criterio de dose (decisao do autor, 13/09/2026): a formula tem proporcao fixa,
   e a recomendacao raramente sai na mesma proporcao. Para cada formula ha duas
   quantidades que resolvem cada nutriente isoladamente:

     kg_para_P = P2O5_recomendado / (%P2O5 / 100)
     kg_para_K = K2O_recomendado  / (%K2O  / 100)

   A dose e a MAIOR das duas: assim nem P nem K ficam devendo, e o que sobra e
   excesso do outro, nunca falta. O N que a formula entrega e descontado da
   recomendacao; o que faltar vai para o complemento, cujo custo so entra na
   conta quando a pessoa informa o adubo de complemento. O SIRAS nao diz quando
   aplicar o complemento.

   A formula "mais barata" so e apontada entre as que atendem P e K em todos os
   talhoes e cujo custo esta completo - uma formula pobre em N sem o preco do
   complemento pareceria barata por nao pagar o N que falta.

   Doses publicadas como teto ou intervalo chegam como null (insumos_para_custo,
   siras/relatorio/apresentacao.py) e ficam fora da conta, com aviso.

   Nada e guardado: os precos vivem so nesta tela.
   ========================================================================= */
(function () {
  "use strict";

  var raiz = document.querySelector("[data-custo]");
  var fonte = document.getElementById("custo-dados");
  if (!raiz || !fonte) {
    return;
  }

  var dados;
  try {
    dados = JSON.parse(fonte.textContent);
  } catch (erro) {
    return;
  }

  var moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  var numero = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
  var saida = raiz.querySelector("[data-custo-saida]");
  var NOMES = { n: "N", p: "P<sub>2</sub>O<sub>5</sub>", k: "K<sub>2</sub>O" };
  var MARGEM = 1e-9;

  /* --- leitura ----------------------------------------------------------- */

  function lerNumero(campo) {
    if (!campo) {
      return null;
    }
    var texto = String(campo.value || "").trim().replace(/\./g, "").replace(",", ".");
    if (texto === "") {
      return null;
    }
    var valor = Number(texto);
    return isFinite(valor) && valor >= 0 ? valor : NaN;
  }

  function valor(seletor, contexto) {
    return lerNumero((contexto || raiz).querySelector(seletor));
  }

  function escapar(texto) {
    var div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
  }

  /* A formula como no rotulo: tres numeros, em qualquer separador ("05-20-20",
     "5 20 20", "4-14-8"). Garantias de 0 a 100, somando no maximo 100. */
  function lerFormula(opcao) {
    var texto = String(opcao.querySelector("[data-formula]").value || "").trim();
    if (texto === "") {
      return null;
    }
    var partes = texto.split(/[^0-9.,]+/).filter(Boolean);
    var garantias = partes.map(function (parte) { return Number(parte.replace(",", ".")); });
    var invalida = partes.length !== 3 || garantias.some(function (g) {
      return !isFinite(g) || g < 0 || g > 100;
    }) || garantias[0] + garantias[1] + garantias[2] > 100;
    if (invalida) {
      return { rotulo: texto, erro: "Escreva a fórmula como no rótulo, com os três números (N-P₂O₅-K₂O)." };
    }
    var peso = valor("[data-saca-peso]", opcao);
    var preco = valor("[data-saca-preco]", opcao);
    if (isNaN(peso) || isNaN(preco) || peso === 0) {
      return { rotulo: texto, erro: "O peso da saca precisa ser maior que zero, e o preço não pode ser negativo." };
    }
    return { rotulo: texto, n: garantias[0], p: garantias[1], k: garantias[2], peso: peso, preco: preco };
  }

  function lerComplemento() {
    var bloco = raiz.querySelector("[data-complemento]");
    if (!bloco) {
      return null;
    }
    var teor = valor("[data-comp-teor]", bloco);
    var peso = valor("[data-comp-peso]", bloco);
    var preco = valor("[data-comp-preco]", bloco);
    if (teor === null && peso === null && preco === null) {
      return null;
    }
    if (teor === null || peso === null || preco === null) {
      return { erro: "Para o complemento entrar no custo, preencha teor, peso e preço da saca." };
    }
    if (isNaN(teor) || isNaN(peso) || isNaN(preco) || teor <= 0 || teor > 100 || peso <= 0) {
      return { erro: "Confira o complemento: teor de 0 a 100%, peso maior que zero, preço não negativo." };
    }
    return { teor: teor, peso: peso, preco: preco };
  }

  /* --- conta --------------------------------------------------------------- */

  /* A formula aplicada a um talhao: quanto aplicar, o que entrega, o que falta de
     N e o que sobra. So aritmetica sobre as doses do motor e a formula digitada. */
  function aplicarFormula(doses, formula) {
    var p = doses.p2o5;
    var k = doses.k2o;
    var n = doses.n;
    if (p === null || k === null) {
      return { semValor: true };
    }
    var faltam = [];
    if (p > 0 && formula.p === 0) { faltam.push(NOMES.p); }
    if (k > 0 && formula.k === 0) { faltam.push(NOMES.k); }
    if (faltam.length) {
      return { naoAtende: faltam };
    }
    var paraP = p > 0 ? p / (formula.p / 100) : 0;
    var paraK = k > 0 ? k / (formula.k / 100) : 0;
    var kg = Math.max(paraP, paraK);
    var entrega = { n: kg * formula.n / 100, p: kg * formula.p / 100, k: kg * formula.k / 100 };
    return {
      kg: kg,
      define: kg === 0 ? null : (paraP >= paraK ? NOMES.p : NOMES.k),
      entrega: entrega,
      recomendado: { n: n, p: p, k: k },
      faltaN: n === null ? null : Math.max(0, n - entrega.n),
    };
  }

  function custoComplemento(faltaN, complemento) {
    if (!faltaN || faltaN <= MARGEM) {
      return { kg: 0, sacas: 0, custo: 0 };
    }
    if (!complemento || complemento.erro) {
      return null;
    }
    var kg = faltaN / (complemento.teor / 100);
    var sacas = kg / complemento.peso;
    return { kg: kg, sacas: sacas, custo: sacas * complemento.preco };
  }

  /* --- apresentacao ---------------------------------------------------------- */

  function linha(rotulo, valorTexto, classe) {
    return '<div class="custo__linha' + (classe ? " " + classe : "") + '">' +
      "<span>" + rotulo + "</span><strong>" + valorTexto + "</strong></div>";
  }

  function diferenca(recomendado, entregue, nutriente) {
    if (recomendado === null) {
      return "—";
    }
    var d = entregue - recomendado;
    if (Math.abs(d) < 0.05) {
      return "atende";
    }
    if (d > 0) {
      return "sobra " + numero.format(d);
    }
    return '<span class="formula__falta">falta ' + numero.format(-d) +
      (nutriente === "n" ? " (complemento)" : "") + "</span>";
  }

  function tabelaEntrega(r) {
    var corpo = ["n", "p", "k"].map(function (chave) {
      return "<tr><th scope=\"row\">" + NOMES[chave] + "</th>" +
        "<td>" + (r.recomendado[chave] === null ? "—" : numero.format(r.recomendado[chave])) + "</td>" +
        "<td>" + numero.format(r.entrega[chave]) + "</td>" +
        "<td>" + diferenca(r.recomendado[chave], r.entrega[chave], chave) + "</td></tr>";
    }).join("");
    return '<table class="formula__tabela"><thead><tr><th scope="col">kg/ha</th>' +
      '<th scope="col">Recomendado</th><th scope="col">Entrega</th><th scope="col">Diferença</th>' +
      "</tr></thead><tbody>" + corpo + "</tbody></table>";
  }

  function blocoCalcario(multiplos) {
    var preco = valor("[data-calcario-preco]");
    if (preco === null) {
      return { html: "", porTalhao: null };
    }
    if (isNaN(preco)) {
      return { html: '<p class="custo__aviso">O preço do calcário não pode ser negativo.</p>', porTalhao: null };
    }
    var html = '<article class="formula formula--calcario"><div class="formula__cab"><strong>Calcário</strong></div>';
    var porTalhao = [];
    dados.talhoes.forEach(function (talhao) {
      var dose = talhao.doses.calagem;
      if (multiplos) {
        html += '<div class="custo__talhao-nome">' + escapar(talhao.rotulo) + "</div>";
      }
      if (dose === null) {
        porTalhao.push(null);
        html += '<p class="custo__aviso">Dose sem valor único neste talhão: fora da conta.</p>';
        return;
      }
      var custoHa = dose * preco;
      porTalhao.push(custoHa);
      html += linha(numero.format(dose) + " t/ha", moeda.format(custoHa) + "/ha");
      if (talhao.area_ha !== null) {
        html += linha("Em " + numero.format(talhao.area_ha) + " ha · " + numero.format(dose * talhao.area_ha) + " t",
                      moeda.format(custoHa * talhao.area_ha));
      }
    });
    return { html: html + "</article>", porTalhao: porTalhao };
  }

  function calcular() {
    var multiplos = dados.talhoes.length > 1;
    var todasComArea = dados.talhoes.every(function (t) { return t.area_ha !== null; });
    var complemento = lerComplemento();
    var html = "";

    var calcario = blocoCalcario(multiplos);
    html += calcario.html;

    if (complemento && complemento.erro) {
      html += '<p class="custo__aviso">' + complemento.erro + "</p>";
    }

    var opcoes = Array.prototype.slice.call(raiz.querySelectorAll("[data-formula-opcao]"));
    var resultados = [];

    opcoes.forEach(function (opcao) {
      var formula = lerFormula(opcao);
      if (!formula) {
        return;
      }
      if (formula.erro) {
        resultados.push({ formula: formula, html: '<article class="formula"><div class="formula__cab"><strong>' +
          escapar(formula.rotulo) + '</strong></div><p class="custo__aviso">' + formula.erro + "</p></article>" });
        return;
      }

      var corpo = "";
      var atendeTudo = true;
      var custoCompleto = formula.preco !== null && formula.peso !== null;
      var comparavel = 0;
      var totalArea = 0;

      dados.talhoes.forEach(function (talhao) {
        var r = aplicarFormula(talhao.doses, formula);
        if (multiplos) {
          corpo += '<div class="custo__talhao-nome">' + escapar(talhao.rotulo) + "</div>";
        }
        if (r.semValor) {
          atendeTudo = false;
          corpo += '<p class="custo__aviso">Fósforo ou potássio sem valor único neste talhão: fora da conta.</p>';
          return;
        }
        if (r.naoAtende) {
          atendeTudo = false;
          corpo += '<p class="formula__nao">Não atende: a fórmula não tem ' + r.naoAtende.join(" nem ") + ".</p>";
          return;
        }

        var aplicar = numero.format(r.kg) + " kg/ha";
        if (formula.peso !== null) {
          aplicar += " · " + numero.format(r.kg / formula.peso) + " sacas/ha";
        }
        corpo += linha("Aplicar" + (r.define ? " <small>(dose definida pelo " + r.define + ")</small>" : ""), aplicar);
        corpo += tabelaEntrega(r);

        var comp = custoComplemento(r.faltaN, complemento);
        if (r.faltaN === null) {
          custoCompleto = false;
        } else if (r.faltaN > MARGEM) {
          if (comp) {
            corpo += linha("Complemento de N", numero.format(comp.kg) + " kg/ha de produto · " +
                           numero.format(comp.sacas) + " sacas/ha");
          } else {
            custoCompleto = false;
            corpo += linha("Complemento de N", numero.format(r.faltaN) + " kg/ha de N, sem preço informado");
          }
        }

        if (formula.preco !== null && formula.peso !== null) {
          var custoHa = (r.kg / formula.peso) * formula.preco + (comp ? comp.custo : 0);
          corpo += linha("Custo por hectare" + (comp && comp.custo ? " <small>(com complemento)</small>" : ""),
                         moeda.format(custoHa) + "/ha", "custo__linha--total");
          comparavel += custoHa;
          if (talhao.area_ha !== null) {
            var sacasArea = (r.kg * talhao.area_ha) / formula.peso;
            totalArea += custoHa * talhao.area_ha;
            corpo += linha("Em " + numero.format(talhao.area_ha) + " ha · " + Math.ceil(sacasArea - MARGEM) + " sacas",
                           moeda.format(custoHa * talhao.area_ha), "custo__linha--total");
          }
        }
      });

      if (multiplos && todasComArea && formula.preco !== null && formula.peso !== null && atendeTudo) {
        corpo += '<div class="custo__propriedade">' +
          linha("Custo total da fórmula", moeda.format(totalArea), "custo__linha--total") + "</div>";
      }

      resultados.push({
        formula: formula,
        corpo: corpo,
        elegivel: atendeTudo && custoCompleto,
        chave: todasComArea ? totalArea : comparavel,
      });
    });

    var elegiveis = resultados.filter(function (r) { return r.elegivel; });
    var melhor = null;
    if (elegiveis.length > 1) {
      melhor = elegiveis.reduce(function (a, b) { return b.chave < a.chave ? b : a; });
    }

    resultados.forEach(function (r) {
      if (r.html) {
        html += r.html;
        return;
      }
      var destaque = r === melhor;
      html += '<article class="formula' + (destaque ? " formula--melhor" : "") + '">' +
        '<div class="formula__cab"><strong>' + escapar(r.formula.rotulo) + "</strong>" +
        (destaque ? '<span class="formula__selo">Mais barata</span>' : "") + "</div>" + r.corpo + "</article>";
    });

    if (resultados.length > 1 && elegiveis.length < resultados.length) {
      html += '<p class="custo__vazio">A mais barata só é apontada entre as fórmulas que atendem fósforo e ' +
        "potássio e têm o custo completo — com peso e preço da saca e, se faltar N, o complemento.</p>";
    }

    if (!html) {
      html = '<p class="custo__vazio">Informe o preço do calcário ou digite uma fórmula da revenda para ver ' +
        "quanto aplicar e quanto custa.</p>";
    }
    saida.innerHTML = html;
  }

  raiz.addEventListener("input", calcular);
  calcular();
})();
