var jogadorId = obterParametroUrl("id");
var nAtivo = 9999;
var donutAtivo = "fg";
var dJogos = null;

var POSICOES_PT = {
  PG: "Armador",
  SG: "Ala-armador",
  SF: "Ala",
  PF: "Ala-pivô",
  C: "Pivô",
  G: "Armador/Ala",
  F: "Ala/Ala-pivô",
  GF: "Ala-armador/Ala",
  FC: "Ala-pivô/Pivô",
};

function traduzirPosicao(abrev) {
  if (!abrev) {
    return "";
  }
  return POSICOES_PT[abrev.toUpperCase()] || abrev;
}
var paginaTabela = 1;
var porPagina = 15;

var tt = document.getElementById("tt");

function showTT(event, html) {
  tt.innerHTML = html;
  tt.style.opacity = 1;
  moveTT(event);
}
function moveTT(event) {
  var x = event.clientX + 14;
  var y = event.clientY - 36;
  if (x + 220 > window.innerWidth) {
    x = event.clientX - 220;
  }
  tt.style.left = x + "px";
  tt.style.top = y + "px";
}
function hideTT() {
  tt.style.opacity = 0;
}

document.addEventListener("DOMContentLoaded", function () {
  verificarAutenticacao();
  inicializarPagina();
  if (!jogadorId) {
    document.getElementById("pg-loading").style.display = "none";
    document.getElementById("pg-erro").style.display = "block";
    return;
  }
  carregarCabecalho();
});

async function carregarCabecalho() {
  try {
    var dados = await chamarApi("/jogadores/" + jogadorId);
    var nome = dados.nome + " " + dados.sobrenome;
    document.title = "NbaAnalyst — " + nome;
    document.getElementById("jav-avatar").textContent = (
      dados.nome.charAt(0) + dados.sobrenome.charAt(0)
    ).toUpperCase();
    document.getElementById("jav-nome").textContent = nome;
    document.getElementById("btn-basico").href = "jogador.html?id=" + jogadorId;

    var meta = "";
    if (dados.historico_times && dados.historico_times.length > 0) {
      var t = dados.historico_times[dados.historico_times.length - 1];
      meta =
        meta +
        '<span><i class="bi bi-shield-fill"></i><a href="time.html?id=' +
        t.time_id +
        '" style="color:#555570;text-decoration:none;">' +
        t.nome_time +
        "</a></span>";
      if (t.posicao) {
        meta =
          meta +
          '<span><i class="bi bi-person-fill"></i>' +
          traduzirPosicao(t.posicao) +
          "</span>";
      }
    }
    if (dados.inicio_nba) {
      meta =
        meta +
        '<span><i class="bi bi-trophy"></i>NBA desde ' +
        dados.inicio_nba +
        "</span>";
    }
    document.getElementById("jav-meta").innerHTML = meta;

    document.getElementById("pg-loading").style.display = "none";
    document.getElementById("pg-content").style.display = "block";
    carregarDados();
  } catch (e) {
    document.getElementById("pg-loading").style.display = "none";
    document.getElementById("pg-erro").style.display = "block";
  }
}

async function carregarDados() {
  var temp = document.getElementById("sel-temp").value;
  document.getElementById("data-loading").style.display = "block";
  document.getElementById("data-content").style.display = "none";
  document.getElementById("data-vazio").style.display = "none";

  try {
    var urlJogos = "/jogadores/" + jogadorId + "/estatisticas/ultimos-jogos";
    var params = [];
    if (nAtivo < 9999) {
      params.push("n_jogos=" + nAtivo);
    }
    if (temp !== "") {
      params.push("temporada=" + temp);
    }
    if (params.length > 0) {
      urlJogos = urlJogos + "?" + params.join("&");
    }
    dJogos = await chamarApi(urlJogos);

    var temJogos = dJogos && dJogos.jogos && dJogos.jogos.length > 0;
    document.getElementById("data-loading").style.display = "none";

    if (!temJogos) {
      document.getElementById("data-vazio").style.display = "block";
      return;
    }

    document.getElementById("data-content").style.display = "block";

    requestAnimationFrame(function () {
      renderCards();
      renderLinha();
      renderBotoesDonut();
      renderTendencia();
      renderTabela();
      setTimeout(function () {
        renderDonut(donutAtivo);
      }, 0);
    });
  } catch (e) {
    document.getElementById("data-loading").style.display = "none";
    document.getElementById("data-vazio").style.display = "block";
  }
}

function recarregar() {
  dJogos = null;
  seriesVisiveis = {
    pontos: true,
    assistencias: true,
    rebotes: true,
    roubos: true,
  };
  paginaTabela = 1;
  carregarDados();
}

function aoDigitarN(event) {
  if (event.key !== "Enter") {
    return;
  }
  var inp = document.getElementById("inp-n-jogos");
  var val = parseInt(inp.value);
  if (isNaN(val) || val <= 5) {
    inp.value = "";
    inp.placeholder = "mín. 6";
    return;
  }
  nAtivo = val;
  document.getElementById("bn-todos").classList.remove("ativo");
  dJogos = null;
  paginaTabela = 1;
  carregarDados();
}

function trocarNTodos() {
  nAtivo = 9999;
  document.getElementById("inp-n-jogos").value = "";
  document.getElementById("bn-todos").classList.add("ativo");
  dJogos = null;
  paginaTabela = 1;
  carregarDados();
}

function filtrarLocal() {
  paginaTabela = 1;
  requestAnimationFrame(function () {
    renderCards();
    renderLinha();
    renderBotoesDonut();
    renderDonut(donutAtivo);
    renderTendencia();
    renderTabela();
  });
}

function jogosVisiveis() {
  if (!dJogos || !dJogos.jogos) {
    return [];
  }
  var local = document.getElementById("sel-local").value;
  if (local === "todos") {
    return dJogos.jogos;
  }
  var out = [];
  for (var i = 0; i < dJogos.jogos.length; i++) {
    var j = dJogos.jogos[i];
    if (local === "casa" && j.em_casa === true) {
      out.push(j);
    }
    if (local === "fora" && j.em_casa === false) {
      out.push(j);
    }
  }
  return out;
}

function calcularMedia(jogos, campo) {
  var soma = 0;
  var cont = 0;
  for (var i = 0; i < jogos.length; i++) {
    var v = jogos[i][campo];
    if (v !== null && v !== undefined) {
      soma = soma + v;
      cont = cont + 1;
    }
  }
  if (cont === 0) {
    return "—";
  }
  return (soma / cont).toFixed(1);
}

function renderCards() {
  var jogos = jogosVisiveis();
  document.getElementById("lbl-jogos").textContent =
    jogos.length > 0 ? "(" + jogos.length + " jogos)" : "";

  var defs = [
    { c: "pontos", l: "PTS", cor: "#F75C03" },
    { c: "assistencias", l: "AST", cor: "#3B9EFF" },
    { c: "rebotes", l: "REB", cor: "#00C896" },
    { c: "roubos", l: "STL", cor: "#FFD600" },
    { c: "bloqueios", l: "BLK", cor: "#555570" },
    { c: "plus_minus", l: "+/-", cor: "#1A1A2E" },
  ];

  var html = "";
  for (var i = 0; i < defs.length; i++) {
    var d = defs[i];
    var v = calcularMedia(jogos, d.c);
    html =
      html +
      '<div class="col-6 col-sm-4 col-md-2" style="min-width:95px;">' +
      '<div class="card-kpi-jav" style="border-top:3px solid ' +
      d.cor +
      ';"><div class="kv" style="color:' +
      d.cor +
      ';">' +
      v +
      "</div>" +
      '<div class="kr">' +
      d.l +
      "</div></div></div>";
  }
  document.getElementById("grid-cards").innerHTML = html;
}

var seriesVisiveis = {
  pontos: true,
  assistencias: true,
  rebotes: true,
  roubos: true,
};
var SERIES_DEF = [
  { campo: "pontos", label: "PTS", cor: "#F75C03" },
  { campo: "assistencias", label: "AST", cor: "#3B9EFF" },
  { campo: "rebotes", label: "REB", cor: "#00C896" },
  { campo: "roubos", label: "STL", cor: "#FFD600" },
];

function renderBotoesLinha() {
  var container = document.getElementById("linha-toggles");
  var html = "";
  for (var i = 0; i < SERIES_DEF.length; i++) {
    var s = SERIES_DEF[i];
    var vis = seriesVisiveis[s.campo];
    var bg = vis ? s.cor : "#F5F5FA";
    var cor = vis ? "#fff" : s.cor;
    var borda = vis ? s.cor : "#CCCCDD";
    html =
      html +
      '<button id="btn-linha-' +
      s.campo +
      '" ' +
      "onclick=\"toggleSerie('" +
      s.campo +
      "')\" " +
      'style="background:' +
      bg +
      ";border:1px solid " +
      borda +
      ";color:" +
      cor +
      ";" +
      "font-size:.68rem;font-weight:700;padding:4px 12px;border-radius:6px;cursor:pointer;" +
      'transition:all .2s;text-transform:uppercase;letter-spacing:.05em;">' +
      '<span style="display:inline-block;width:14px;height:2px;background:' +
      (vis ? "#fff" : s.cor) +
      ';vertical-align:middle;margin-right:5px;border-radius:1px;"></span>' +
      s.label +
      "</button>";
  }
  container.innerHTML = html;
}

function toggleSerie(campo) {
  seriesVisiveis[campo] = !seriesVisiveis[campo];
  renderBotoesLinha();
  renderLinha();
}

function renderLinha() {
  var el = document.getElementById("g-linha");
  el.innerHTML = "";
  renderBotoesLinha();

  var jogos = jogosVisiveis().slice().reverse();
  if (jogos.length < 2) {
    return;
  }

  var mg = { t: 16, r: 28, b: 36, l: 36 };
  var W = el.offsetWidth || 640;
  var LW = W - mg.l - mg.r;
  var H = 340;

  var svg = d3
    .select("#g-linha")
    .append("svg")
    .attr("width", W)
    .attr("height", H + mg.t + mg.b);
  var g = svg
    .append("g")
    .attr("transform", "translate(" + mg.l + "," + mg.t + ")");

  var escX = d3
    .scaleLinear()
    .domain([0, jogos.length - 1])
    .range([0, LW]);

  var todosValores = [];
  for (var si = 0; si < SERIES_DEF.length; si++) {
    if (!seriesVisiveis[SERIES_DEF[si].campo]) {
      continue;
    }
    for (var ji = 0; ji < jogos.length; ji++) {
      var v = jogos[ji][SERIES_DEF[si].campo];
      if (v !== null && v !== undefined) {
        todosValores.push(v);
      }
    }
  }
  if (todosValores.length === 0) {
    return;
  }
  var minV = d3.min(todosValores) || 0;
  var maxV = d3.max(todosValores) || 1;
  var escY = d3
    .scaleLinear()
    .domain([Math.max(0, minV * 0.85), maxV * 1.18])
    .range([H, 0]);

  g.append("g")
    .attr("class", "ey")
    .call(d3.axisLeft(escY).ticks(5).tickSize(-LW))
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick line")
        .attr("stroke", "#CCCCDD")
        .attr("stroke-dasharray", "3,3");
      gr.selectAll(".tick text")
        .attr("fill", "#9999B0")
        .attr("font-size", "10px");
    });

  g.append("g")
    .attr("class", "eixo-x")
    .attr("transform", "translate(0," + H + ")")
    .call(
      d3
        .axisBottom(escX)
        .ticks(Math.min(jogos.length, 10))
        .tickFormat(function (idx) {
          var i = Math.round(idx);
          return "R" + (i + 1);
        })
        .tickSize(0),
    )
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick text")
        .attr("fill", "#9999B0")
        .attr("font-size", "9px")
        .attr("dy", "1.3em");
    });

  for (var si = 0; si < SERIES_DEF.length; si++) {
    var s = SERIES_DEF[si];
    var campo = s.campo;
    if (!seriesVisiveis[campo]) {
      continue;
    }

    var linhaFn = d3
      .line()
      .x(function (d, i) {
        return escX(i);
      })
      .y(function (d) {
        return escY(d[campo] !== null && d[campo] !== undefined ? d[campo] : 0);
      })
      .defined(function (d) {
        return d[campo] !== null && d[campo] !== undefined;
      })
      .curve(d3.curveLinear);

    g.append("path")
      .datum(jogos)
      .attr("class", "linha-serie linha-" + campo)
      .attr("fill", "none")
      .attr("stroke", s.cor)
      .attr("stroke-width", 2)
      .attr("opacity", 0.85)
      .attr("d", linhaFn)
      .style("cursor", "pointer")
      .on(
        "mouseover",
        (function (ss) {
          return function () {
            d3.select(this).attr("stroke-width", 4).attr("opacity", 1);
          };
        })(s),
      )
      .on("mouseout", function () {
        d3.select(this).attr("stroke-width", 2).attr("opacity", 0.85);
      })
      .on(
        "click",
        (function (cc) {
          return function () {
            toggleSerie(cc);
          };
        })(campo),
      );

    g.selectAll(".dot-" + campo)
      .data(jogos)
      .enter()
      .append("circle")
      .attr("class", "dot-" + campo)
      .attr("cx", function (d, i) {
        return escX(i);
      })
      .attr("cy", function (d) {
        return d[campo] !== null && d[campo] !== undefined
          ? escY(d[campo])
          : -999;
      })
      .attr("r", 3.5)
      .attr("fill", s.cor)
      .attr("opacity", 0.9)
      .style("cursor", "pointer")
      .on(
        "mouseover",
        (function (ss) {
          return function (event, d) {
            d3.select(this).attr("r", 6);
            var dt = d.data
              ? new Date(d.data).toLocaleDateString("pt-BR", {
                  day: "2-digit",
                  month: "2-digit",
                  year: "2-digit",
                })
              : "";
            showTT(
              event,
              "<strong>" +
                (d.adversario || "—") +
                " · " +
                dt +
                "</strong><br><b style='color:" +
                ss.cor +
                "'>" +
                ss.label +
                ":</b> " +
                (d[ss.campo] !== null && d[ss.campo] !== undefined
                  ? d[ss.campo]
                  : "—"),
            );
          };
        })(s),
      )
      .on("mousemove", moveTT)
      .on("mouseout", function () {
        d3.select(this).attr("r", 3.5);
        hideTT();
      })
      .on(
        "click",
        (function (cc) {
          return function () {
            toggleSerie(cc);
          };
        })(campo),
      );

    g.append("path")
      .datum(jogos)
      .attr("class", "hit-" + campo)
      .attr("fill", "none")
      .attr("stroke", "transparent")
      .attr("stroke-width", 16)
      .attr("d", linhaFn)
      .style("cursor", "pointer")
      .on(
        "mouseover",
        (function (ss) {
          return function () {
            g.select(".linha-" + ss.campo)
              .attr("stroke-width", 4)
              .attr("opacity", 1);
          };
        })(s),
      )
      .on("mouseout", function () {
        g.selectAll(".linha-serie")
          .attr("stroke-width", 2)
          .attr("opacity", 0.85);
      })
      .on(
        "click",
        (function (cc) {
          return function () {
            toggleSerie(cc);
          };
        })(campo),
      );
  }

  var escXZoom = escX.copy();
  var emZoom = false;

  function redesenharLinhas(ex) {
    for (var si = 0; si < SERIES_DEF.length; si++) {
      var campo = SERIES_DEF[si].campo;
      if (!seriesVisiveis[campo]) {
        continue;
      }

      var fn = d3
        .line()
        .x(function (d, i) {
          return ex(i);
        })
        .y(function (d) {
          return escY(
            d[campo] !== null && d[campo] !== undefined ? d[campo] : 0,
          );
        })
        .defined(function (d) {
          return d[campo] !== null && d[campo] !== undefined;
        })
        .curve(d3.curveLinear);

      g.selectAll(".linha-" + campo).attr("d", fn);
      g.selectAll(".hit-" + campo).attr("d", fn);
      g.selectAll(".dot-" + campo).attr("cx", function (d, i) {
        return ex(i);
      });
    }

    g.select(".eixo-x")
      .call(
        d3
          .axisBottom(ex)
          .ticks(Math.min(jogos.length, 10))
          .tickFormat(function (idx) {
            return "R" + (Math.round(idx) + 1);
          })
          .tickSize(0),
      )
      .call(function (gr) {
        gr.select(".domain").remove();
        gr.selectAll(".tick text")
          .attr("fill", "#9999B0")
          .attr("font-size", "9px")
          .attr("dy", "1.3em");
      });
  }

  var containerLinha = document.getElementById("g-linha");
  containerLinha.style.position = "relative";
  var btnReset = document.createElement("button");
  btnReset.id = "btn-reset-zoom";
  btnReset.textContent = "↺ Resetar zoom";
  btnReset.style.cssText =
    "display:none;position:absolute;top:8px;right:8px;background:#F5F5FA;" +
    "border:1px solid #F75C03;color:#F75C03;font-size:.68rem;font-weight:700;" +
    "padding:3px 10px;border-radius:6px;cursor:pointer;z-index:10;";
  btnReset.onclick = function () {
    resetarZoom();
  };
  containerLinha.appendChild(btnReset);

  function resetarZoom() {
    escXZoom = escX.copy();
    emZoom = false;
    redesenharLinhas(escX);
    document.getElementById("btn-reset-zoom").style.display = "none";
  }

  var brush = d3
    .brushX()
    .extent([
      [0, 0],
      [LW, H],
    ])
    .on("end", function (event) {
      hideTT();
      if (!event.selection) {
        return;
      }
      var x0 = Math.max(0, Math.floor(escX.invert(event.selection[0])));
      var x1 = Math.min(
        jogos.length - 1,
        Math.ceil(escX.invert(event.selection[1])),
      );
      if (Math.abs(x1 - x0) < 1) {
        gBrush.call(brush.move, null);
        return;
      }
      escXZoom = d3.scaleLinear().domain([x0, x1]).range([0, LW]);
      emZoom = true;
      redesenharLinhas(escXZoom);
      gBrush.call(brush.move, null);
      document.getElementById("btn-reset-zoom").style.display = "inline-block";
    });

  var gBrush = g.append("g").attr("class", "brush-layer").call(brush);
  gBrush
    .select(".selection")
    .attr("fill", "rgba(247,92,3,0.15)")
    .attr("stroke", "#F75C03")
    .attr("stroke-width", 1);
  gBrush.selectAll(".handle").attr("fill", "#F75C03").attr("opacity", 0.7);
  gBrush.select(".overlay").style("cursor", "crosshair");
  gBrush.select(".overlay").on("dblclick", function () {
    resetarZoom();
  });
  gBrush
    .select(".overlay")
    .on("mousemove.tt", function (event) {
      var escAtiva = emZoom ? escXZoom : escX;
      var xPos = d3.pointer(event)[0];
      var idx = Math.round(escAtiva.invert(xPos));
      idx = Math.max(0, Math.min(idx, jogos.length - 1));
      var j = jogos[idx];
      if (!j) {
        return;
      }
      var dt = j.data
        ? new Date(j.data).toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "2-digit",
          })
        : "";
      var linhas =
        "<strong>R" +
        (idx + 1) +
        " · " +
        (j.adversario || "—") +
        " · " +
        dt +
        "</strong>";
      for (var si = 0; si < SERIES_DEF.length; si++) {
        var s = SERIES_DEF[si];
        if (!seriesVisiveis[s.campo]) {
          continue;
        }
        var v = j[s.campo];
        linhas =
          linhas +
          "<br><b style='color:" +
          s.cor +
          "'>" +
          s.label +
          ":</b> " +
          (v !== null && v !== undefined ? v : "—");
      }
      showTT(event, linhas);
    })
    .on("mouseout.tt", hideTT);
}

// ── DONUT DE PROGRESSO
var DONUT_CFG = {
  fg: { campo: "fg_pct", cor: "#F75C03", label: "FG%" },
  "3p": { campo: "three_pct", cor: "#3B9EFF", label: "3P%" },
  ft: { campo: "ft_pct", cor: "#00C896", label: "FT%" },
};

function calcularPct(jogos, campo) {
  var soma = 0;
  var cont = 0;
  for (var i = 0; i < jogos.length; i++) {
    var v = jogos[i][campo];
    if (v !== null && v !== undefined) {
      soma = soma + v;
      cont = cont + 1;
    }
  }
  if (cont === 0) {
    return 0;
  }
  return parseFloat((soma / cont).toFixed(1));
}

function renderBotoesDonut() {
  var ids = ["fg", "3p", "ft"];
  for (var i = 0; i < ids.length; i++) {
    var id = ids[i];
    var cfg = DONUT_CFG[id];
    var btn = document.getElementById("btn-" + id);
    if (!btn) {
      continue;
    }
    var ativo = id === donutAtivo;
    btn.style.background = ativo ? cfg.cor : "#F5F5FA";
    btn.style.borderColor = ativo ? cfg.cor : "#CCCCDD";
    btn.style.color = ativo ? "#fff" : cfg.cor;
  }
}

function trocarDonut(tipo) {
  donutAtivo = tipo;
  renderBotoesDonut();
  renderDonut(tipo);
}

function renderDonut(tipo) {
  var el = document.getElementById("g-donut");
  el.innerHTML = "";
  var cfg = DONUT_CFG[tipo];
  var jogos = jogosVisiveis();
  var valor = calcularPct(jogos, cfg.campo);
  var prop = Math.min(valor / 100, 1);

  var W = el.offsetWidth || 260;
  var H = 190;
  var cx = W / 2;
  var cy = H / 2 + 8;
  var R = Math.min(W * 0.38, H * 0.42);
  var ri = R * 0.68;

  var svg = d3
    .select("#g-donut")
    .append("svg")
    .attr("width", W)
    .attr("height", H);

  var angI = -Math.PI * 0.75;
  var angF = Math.PI * 0.75;
  var amp = angF - angI;
  var arc = d3.arc().innerRadius(ri).outerRadius(R).cornerRadius(4);

  svg
    .append("path")
    .datum({ startAngle: angI, endAngle: angF })
    .attr("d", arc)
    .attr("transform", "translate(" + cx + "," + cy + ")")
    .attr("fill", "#CCCCDD");

  if (prop > 0) {
    svg
      .append("path")
      .datum({ startAngle: angI, endAngle: angI + amp * prop })
      .attr("d", arc)
      .attr("transform", "translate(" + cx + "," + cy + ")")
      .attr("fill", cfg.cor)
      .attr("opacity", 0.92)
      .style("cursor", "pointer")
      .on("mouseover", function (event) {
        d3.select(this).attr("opacity", 1);
        showTT(
          event,
          "<strong>" +
            cfg.label +
            ": " +
            valor +
            "%</strong><br>" +
            jogos.length +
            " jogos",
        );
      })
      .on("mousemove", moveTT)
      .on("mouseout", function () {
        d3.select(this).attr("opacity", 0.92);
        hideTT();
      });
  }

  svg
    .append("text")
    .attr("x", cx)
    .attr("y", cy - 4)
    .attr("text-anchor", "middle")
    .attr("fill", cfg.cor)
    .attr("font-family", "Oswald, sans-serif")
    .attr("font-size", "2.1rem")
    .attr("font-weight", "700")
    .text(valor + "%");

  svg
    .append("text")
    .attr("x", cx)
    .attr("y", cy + 20)
    .attr("text-anchor", "middle")
    .attr("fill", "#9999B0")
    .attr("font-size", "11px")
    .attr("font-weight", "700")
    .attr("letter-spacing", "0.07em")
    .text(cfg.label);

  svg
    .append("text")
    .attr("x", cx)
    .attr("y", H - 6)
    .attr("text-anchor", "middle")
    .attr("fill", "#9999B0")
    .attr("font-size", "10px")
    .text(jogos.length + " jogos");
}

// TENDÊNCIA DE PONTUAÇÃO
function renderTendencia() {
  var el = document.getElementById("g-tendencia");
  el.innerHTML = "";
  var jogos = jogosVisiveis().slice().reverse();
  if (jogos.length < 2) {
    el.innerHTML =
      '<p style="font-size:.8rem;color:#9999B0;padding:20px 0;">Dados insuficientes.</p>';
    return;
  }

  var mg = { t: 12, r: 80, b: 36, l: 36 };
  var W = el.offsetWidth || 380;
  var LW = W - mg.l - mg.r;
  var H = 200;
  var svg = d3
    .select("#g-tendencia")
    .append("svg")
    .attr("width", W)
    .attr("height", H + mg.t + mg.b);
  var g = svg
    .append("g")
    .attr("transform", "translate(" + mg.l + "," + mg.t + ")");
  var vals = jogos.map(function (d) {
    return d.pontos !== null && d.pontos !== undefined ? d.pontos : 0;
  });
  var maxV = d3.max(vals) || 1;
  var escX = d3
    .scaleLinear()
    .domain([0, jogos.length - 1])
    .range([0, LW]);
  var escY = d3
    .scaleLinear()
    .domain([0, maxV * 1.2])
    .range([H, 0]);

  g.append("g")
    .call(d3.axisLeft(escY).ticks(4).tickSize(-LW))
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick line")
        .attr("stroke", "#CCCCDD")
        .attr("stroke-dasharray", "3,3");
      gr.selectAll(".tick text")
        .attr("fill", "#9999B0")
        .attr("font-size", "10px");
    });

  g.append("g")
    .attr("transform", "translate(0," + H + ")")
    .call(
      d3
        .axisBottom(escX)
        .ticks(Math.min(jogos.length, 8))
        .tickFormat(function (idx) {
          return "R" + (Math.round(idx) + 1);
        })
        .tickSize(0),
    )
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick text")
        .attr("fill", "#9999B0")
        .attr("font-size", "9px")
        .attr("dy", "1.3em");
    });

  var soma = 0;
  for (var i = 0; i < vals.length; i++) {
    soma = soma + vals[i];
  }
  var mediGeral = soma / vals.length;

  var janela = Math.min(5, vals.length);
  var medMovel = vals.map(function (v, i) {
    var inicio = Math.max(0, i - Math.floor(janela / 2));
    var fim = Math.min(vals.length, inicio + janela);
    var s = 0;
    for (var k = inicio; k < fim; k++) {
      s = s + vals[k];
    }
    return s / (fim - inicio);
  });

  var areaFn = d3
    .area()
    .x(function (d, i) {
      return escX(i);
    })
    .y0(H)
    .y1(function (d) {
      return escY(d);
    })
    .curve(d3.curveLinear);

  g.append("path")
    .datum(medMovel)
    .attr("fill", "#F75C03")
    .attr("opacity", 0.12)
    .attr("d", areaFn);

  var linhaMM = d3
    .line()
    .x(function (d, i) {
      return escX(i);
    })
    .y(function (d) {
      return escY(d);
    })
    .curve(d3.curveLinear);

  g.append("path")
    .datum(medMovel)
    .attr("fill", "none")
    .attr("stroke", "#F75C03")
    .attr("stroke-width", 2.5)
    .attr("d", linhaMM);

  g.selectAll(".dot-tend")
    .data(jogos)
    .enter()
    .append("circle")
    .attr("class", "dot-tend")
    .attr("cx", function (d, i) {
      return escX(i);
    })
    .attr("cy", function (d, i) {
      return escY(medMovel[i]);
    })
    .attr("r", 3)
    .attr("fill", "#F75C03")
    .attr("opacity", 0.85)
    .on("mouseover", function (event, d) {
      var idx = jogos.indexOf(d);
      showTT(
        event,
        "R" +
          (idx + 1) +
          " · <strong>" +
          (d.adversario || "—") +
          "</strong><br>PTS: <strong>" +
          (d.pontos !== null && d.pontos !== undefined ? d.pontos : "—") +
          "</strong><br>Méd móvel: <strong>" +
          medMovel[idx].toFixed(1) +
          "</strong>",
      );
    })
    .on("mousemove", moveTT)
    .on("mouseout", hideTT);

  g.append("line")
    .attr("x1", 0)
    .attr("y1", escY(mediGeral))
    .attr("x2", LW)
    .attr("y2", escY(mediGeral))
    .attr("stroke", "#9999B0")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "4,4");

  g.append("text")
    .attr("x", LW + 5)
    .attr("y", escY(mediGeral))
    .attr("dy", "0.35em")
    .attr("fill", "#9999B0")
    .attr("font-size", "9px")
    .text("Média da temporada (" + mediGeral.toFixed(1) + ")");
}

var POSICOES_PT = {
  PG: "Armador",
  SG: "Ala-armador",
  SF: "Ala",
  PF: "Ala-pivô",
  C: "Pivô",
  G: "Armador/Ala",
  F: "Ala/Ala-pivô",
  GF: "Ala-armador/Ala",
  FC: "Ala-pivô/Pivô",
};

function traduzirPosicao(abrev) {
  if (!abrev) {
    return "";
  }
  return POSICOES_PT[abrev.toUpperCase()] || abrev;
}
var paginaTabela = 1;
var porPagina = 15;

var tt = document.getElementById("tt");

function showTT(event, html) {
  tt.innerHTML = html;
  tt.style.opacity = 1;
  moveTT(event);
}
function moveTT(event) {
  var x = event.clientX + 14;
  var y = event.clientY - 36;
  if (x + 220 > window.innerWidth) {
    x = event.clientX - 220;
  }
  tt.style.left = x + "px";
  tt.style.top = y + "px";
}
function hideTT() {
  tt.style.opacity = 0;
}

document.addEventListener("DOMContentLoaded", function () {
  verificarAutenticacao();
  inicializarPagina();
  if (!jogadorId) {
    document.getElementById("pg-loading").style.display = "none";
    document.getElementById("pg-erro").style.display = "block";
    return;
  }
  carregarCabecalho();
});

async function carregarCabecalho() {
  try {
    var dados = await chamarApi("/jogadores/" + jogadorId);
    var nome = dados.nome + " " + dados.sobrenome;
    document.title = "NbaAnalyst — " + nome;
    document.getElementById("jav-avatar").textContent = (
      dados.nome.charAt(0) + dados.sobrenome.charAt(0)
    ).toUpperCase();
    document.getElementById("jav-nome").textContent = nome;
    document.getElementById("btn-basico").href = "jogador.html?id=" + jogadorId;

    var meta = "";
    if (dados.historico_times && dados.historico_times.length > 0) {
      var t = dados.historico_times[dados.historico_times.length - 1];
      meta =
        meta +
        '<span><i class="bi bi-shield-fill"></i><a href="time.html?id=' +
        t.time_id +
        '" style="color:#555570;text-decoration:none;">' +
        t.nome_time +
        "</a></span>";
      if (t.posicao) {
        meta =
          meta +
          '<span><i class="bi bi-person-fill"></i>' +
          traduzirPosicao(t.posicao) +
          "</span>";
      }
    }
    if (dados.inicio_nba) {
      meta =
        meta +
        '<span><i class="bi bi-trophy"></i>NBA desde ' +
        dados.inicio_nba +
        "</span>";
    }
    document.getElementById("jav-meta").innerHTML = meta;

    document.getElementById("pg-loading").style.display = "none";
    document.getElementById("pg-content").style.display = "block";
    carregarDados();
  } catch (e) {
    document.getElementById("pg-loading").style.display = "none";
    document.getElementById("pg-erro").style.display = "block";
  }
}

async function carregarDados() {
  var temp = document.getElementById("sel-temp").value;
  document.getElementById("data-loading").style.display = "block";
  document.getElementById("data-content").style.display = "none";
  document.getElementById("data-vazio").style.display = "none";

  try {
    var urlJogos = "/jogadores/" + jogadorId + "/estatisticas/ultimos-jogos";
    if (temp !== "") {
      urlJogos = urlJogos + "?n_jogos=" + nAtivo + "&temporada=" + temp;
    }
    dJogos = await chamarApi(urlJogos);

    var temJogos = dJogos && dJogos.jogos && dJogos.jogos.length > 0;
    document.getElementById("data-loading").style.display = "none";

    if (!temJogos) {
      document.getElementById("data-vazio").style.display = "block";
      return;
    }

    document.getElementById("data-content").style.display = "block";

    requestAnimationFrame(function () {
      renderCards();
      renderLinha();
      renderDonut(donutAtivo);
      renderTendencia();
      renderTabela();
    });
  } catch (e) {
    document.getElementById("data-loading").style.display = "none";
    document.getElementById("data-vazio").style.display = "block";
  }
}

function renderTabela() {
  var jogos = jogosVisiveis().slice();

  jogos.sort(function (a, b) {
    var va = a.data ? new Date(a.data).getTime() : 0;
    var vb = b.data ? new Date(b.data).getTime() : 0;
    return vb - va;
  });

  var totalJogos = jogos.length;
  var totalPaginas = Math.max(1, Math.ceil(totalJogos / porPagina));
  if (paginaTabela > totalPaginas) {
    paginaTabela = totalPaginas;
  }

  var inicio = (paginaTabela - 1) * porPagina;
  var fim = Math.min(inicio + porPagina, totalJogos);
  var jogosPag = jogos.slice(inicio, fim);

  document.getElementById("lbl-tabela").textContent =
    totalJogos + " jogos · pág " + paginaTabela + "/" + totalPaginas;

  var html = "";
  for (var i = 0; i < jogosPag.length; i++) {
    var j = jogosPag[i];
    var dt = j.data
      ? new Date(j.data).toLocaleDateString("pt-BR", {
          day: "2-digit",
          month: "2-digit",
          year: "2-digit",
        })
      : "—";
    var mn = j.minutos ? String(j.minutos).split(":")[0] + "m" : "—";

    var pm = j.plus_minus;
    var pmHtml = "—";
    if (pm !== null && pm !== undefined) {
      var pmCor = pm > 0 ? "#00C896" : pm < 0 ? "#FF3B5C" : "#555570";
      pmHtml =
        '<span style="color:' +
        pmCor +
        ';">' +
        (pm > 0 ? "+" : "") +
        pm +
        "</span>";
    }

    html =
      html +
      "<tr>" +
      '<td class="td-sec">' +
      (j.adversario || "—") +
      "</td>" +
      '<td class="td-sec">' +
      dt +
      "</td>" +
      '<td class="td-pts">' +
      (j.pontos !== null && j.pontos !== undefined ? j.pontos : "—") +
      "</td>" +
      "<td>" +
      (j.assistencias !== null && j.assistencias !== undefined
        ? j.assistencias
        : "—") +
      "</td>" +
      "<td>" +
      (j.rebotes !== null && j.rebotes !== undefined ? j.rebotes : "—") +
      "</td>" +
      '<td class="td-sec">' +
      (j.roubos !== null && j.roubos !== undefined ? j.roubos : "—") +
      "</td>" +
      '<td class="td-sec">' +
      (j.bloqueios !== null && j.bloqueios !== undefined ? j.bloqueios : "—") +
      "</td>" +
      '<td class="td-sec">' +
      (j.turnovers !== null && j.turnovers !== undefined ? j.turnovers : "—") +
      "</td>" +
      '<td class="td-sec">' +
      (j.fg_pct !== null && j.fg_pct !== undefined ? j.fg_pct + "%" : "—") +
      "</td>" +
      '<td class="td-sec">' +
      (j.three_pct !== null && j.three_pct !== undefined
        ? j.three_pct + "%"
        : "—") +
      "</td>" +
      '<td class="td-sec">' +
      pmHtml +
      "</td>" +
      '<td class="td-sec">' +
      mn +
      "</td>" +
      "</tr>";
  }
  document.getElementById("tbody-jogos").innerHTML = html;

  var navHtml = "";
  if (totalPaginas > 1) {
    navHtml =
      navHtml +
      '<div class="d-flex align-items-center gap-2 mt-3" style="font-size:.8rem;">';
    navHtml =
      navHtml +
      '<button class="btn-nj" onclick="irPagina(' +
      (paginaTabela - 1) +
      ')" ' +
      (paginaTabela <= 1 ? "disabled" : "") +
      ' style="padding:4px 10px;">&lsaquo;</button>';

    var pInicio = Math.max(1, paginaTabela - 2);
    var pFim = Math.min(totalPaginas, paginaTabela + 2);

    if (pInicio > 1) {
      navHtml =
        navHtml +
        '<button class="btn-nj" onclick="irPagina(1)" style="padding:4px 10px;">1</button>';
    }
    if (pInicio > 2) {
      navHtml = navHtml + '<span style="color:#9999B0;">…</span>';
    }

    for (var pg = pInicio; pg <= pFim; pg++) {
      var cls = pg === paginaTabela ? "btn-nj ativo" : "btn-nj";
      navHtml =
        navHtml +
        '<button class="' +
        cls +
        '" onclick="irPagina(' +
        pg +
        ')" style="padding:4px 10px;">' +
        pg +
        "</button>";
    }

    if (pFim < totalPaginas - 1) {
      navHtml = navHtml + '<span style="color:#9999B0;">…</span>';
    }
    if (pFim < totalPaginas) {
      navHtml =
        navHtml +
        '<button class="btn-nj" onclick="irPagina(' +
        totalPaginas +
        ')" style="padding:4px 10px;">' +
        totalPaginas +
        "</button>";
    }

    navHtml =
      navHtml +
      '<button class="btn-nj" onclick="irPagina(' +
      (paginaTabela + 1) +
      ')" ' +
      (paginaTabela >= totalPaginas ? "disabled" : "") +
      ' style="padding:4px 10px;">&rsaquo;</button>';

    var opcoesPP = [10, 15, 25, 50];
    navHtml =
      navHtml +
      '<span style="color:#9999B0;margin-left:8px;">por página</span>';
    navHtml =
      navHtml +
      '<select class="form-control-nba" style="max-width:70px;font-size:.75rem;" onchange="trocarPorPagina(this.value)">';
    for (var op = 0; op < opcoesPP.length; op++) {
      navHtml =
        navHtml +
        '<option value="' +
        opcoesPP[op] +
        '"' +
        (opcoesPP[op] === porPagina ? " selected" : "") +
        ">" +
        opcoesPP[op] +
        "</option>";
    }
    navHtml = navHtml + "</select>";
    navHtml = navHtml + "</div>";
  }
  document.getElementById("paginacao-tabela").innerHTML = navHtml;
}

function irPagina(pg) {
  var jogos = jogosVisiveis();
  var totalPaginas = Math.max(1, Math.ceil(jogos.length / porPagina));
  if (pg < 1 || pg > totalPaginas) {
    return;
  }
  paginaTabela = pg;
  renderTabela();
  document
    .getElementById("tab-jogos")
    .scrollIntoView({ behavior: "smooth", block: "start" });
}

function trocarPorPagina(valor) {
  porPagina = parseInt(valor);
  paginaTabela = 1;
  renderTabela();
}
