var abaAtiva = "lideres";
var recordesCarregados = false;
var dadosEvolucao = null;
var todasDatas = [];
var seriesPreenchidas = {};
var totalRodasEvolucao = 0;
var playerInterval = null;
var dadosScatterPtsAst = [];
var dadosScatterRebBlk = [];

var CORES_LINHAS = [
  "#C8102E",
  "#1D428A",
  "#007A33",
  "#F9A01B",
  "#552583",
  "#00838A",
  "#E56020",
  "#860038",
  "#006BB6",
  "#008348",
];

var tt = document.getElementById("tt");

var categorias = [
  { id: "pontos", label: "Pontos", cor: "#C8102E" },
  { id: "assistencias", label: "Assistências", cor: "#1D428A" },
  { id: "rebotes", label: "Rebotes", cor: "#007A33" },
  { id: "roubos", label: "Roubos", cor: "#F9A01B" },
  { id: "bloqueios", label: "Bloqueios", cor: "#552583" },
  { id: "turnovers", label: "Turnovers", cor: "#00838A" },
  { id: "arremessos-campo", label: "Arremessos FG", cor: "#006BB6" },
  { id: "arremessos-tres", label: "Arremessos 3P", cor: "#E56020" },
  { id: "lances-livres", label: "Lances Livres", cor: "#008348" },
  { id: "plus-minus", label: "Plus/Minus", cor: "#860038" },
];

var categoriasPrincipais = [
  { id: "pontos", label: "PTS", descricao: "Pontos", cor: "#C8102E" },
  {
    id: "assistencias",
    label: "AST",
    descricao: "Assistências",
    cor: "#1D428A",
  },
  { id: "rebotes", label: "REB", descricao: "Rebotes", cor: "#007A33" },
  { id: "roubos", label: "STL", descricao: "Roubos", cor: "#F9A01B" },
  { id: "bloqueios", label: "BLK", descricao: "Bloqueios", cor: "#552583" },
];

function showTT(evento, html) {
  tt.innerHTML = html;
  tt.style.opacity = 1;
  moveTT(evento);
}

function moveTT(evento) {
  var x = evento.clientX + 14;
  var y = evento.clientY - 36;
  if (x + 240 > window.innerWidth) {
    x = evento.clientX - 240;
  }
  tt.style.left = x + "px";
  tt.style.top = y + "px";
}

function hideTT() {
  tt.style.opacity = 0;
}

function obterLarguraContainer(idContainer) {
  var container = document.getElementById(idContainer);
  if (!container) {
    return 700;
  }
  var pai = container.parentElement;
  if (pai && pai.clientWidth > 0) {
    return pai.clientWidth - 40;
  }
  var avoPai = pai && pai.parentElement;
  if (avoPai && avoPai.clientWidth > 0) {
    return avoPai.clientWidth - 60;
  }
  return Math.max(window.innerWidth - 120, 500);
}

function mapearNomePosicao(pos) {
  if (pos === "G") {
    return "PG";
  }
  if (pos === "F") {
    return "PF";
  }
  return pos;
}

document.addEventListener("DOMContentLoaded", function () {
  inicializarPagina();
  carregarTemporadas();
});

async function carregarTemporadas() {
  try {
    var resposta = await chamarApi("/temporadas");
    var lista = resposta.temporadas || [];

    var selectPrincipal = document.getElementById("select-temporada");
    var selectRecordes = document.getElementById("select-temporada-recordes");

    for (var i = 0; i < lista.length; i++) {
      var ano = lista[i].season;

      var opcao1 = document.createElement("option");
      opcao1.value = ano;
      opcao1.textContent = ano;
      if (i === 0) {
        opcao1.selected = true;
      }
      selectPrincipal.appendChild(opcao1);

      var opcao2 = document.createElement("option");
      opcao2.value = ano;
      opcao2.textContent = ano;
      selectRecordes.appendChild(opcao2);
    }

    carregarLideres();
  } catch (erro) {
    document.getElementById("lideres-carregando").style.display = "none";
    document.getElementById("lideres-vazio").style.display = "block";
  }
}

function aoTrocarFiltroGlobal() {
  recordesCarregados = false;
  dadosEvolucao = null;
  todasDatas = [];
  seriesPreenchidas = {};
  dadosScatterPtsAst = [];
  dadosScatterRebBlk = [];

  if (abaAtiva === "lideres") {
    carregarLideres();
  } else if (abaAtiva === "recordes") {
    carregarRecordes();
  }
}

function trocarAba(aba) {
  abaAtiva = aba;

  var botoes = document.querySelectorAll(".aba-btn");
  for (var i = 0; i < botoes.length; i++) {
    botoes[i].classList.remove("ativo");
  }
  document.getElementById("aba-btn-" + aba).classList.add("ativo");

  var abas = document.querySelectorAll(".conteudo-aba");
  for (var j = 0; j < abas.length; j++) {
    abas[j].style.display = "none";
  }
  document.getElementById("aba-" + aba).style.display = "block";

  if (aba === "recordes" && !recordesCarregados) {
    carregarRecordes();
  }
}

// ============================
// ABA: LÍDERES
// ============================

async function carregarLideres() {
  var temporada = document.getElementById("select-temporada").value;
  var fase = document.getElementById("select-fase").value;

  document.getElementById("lideres-carregando").style.display = "flex";
  document.getElementById("lideres-conteudo").style.display = "none";
  document.getElementById("lideres-vazio").style.display = "none";

  var dadosLideres = [];
  var temDados = false;

  for (var i = 0; i < categoriasPrincipais.length; i++) {
    var cat = categoriasPrincipais[i];
    try {
      var url =
        "/analiticos/lideres?categoria=" +
        cat.id +
        "&temporada=" +
        temporada +
        "&limite=1";
      if (fase !== "") {
        url = url + "&stage=" + fase;
      }
      var resposta = await chamarApi(url);
      if (resposta && resposta.lideres && resposta.lideres.length > 0) {
        var itemLider = {};
        itemLider.cat = cat;
        itemLider.lider = resposta.lideres[0];
        dadosLideres.push(itemLider);
        temDados = true;
      }
    } catch (e) {}
  }

  document.getElementById("lideres-carregando").style.display = "none";

  if (!temDados) {
    document.getElementById("lideres-vazio").style.display = "block";
    return;
  }

  renderizarCardsLideres(dadosLideres);
  document.getElementById("lideres-conteudo").style.display = "block";

  carregarEvolucao();
  carregarScatterPtsAst();
  carregarScatterRebBlk();
}

function renderizarCardsLideres(dadosLideres) {
  var container = document.getElementById("cards-lideres");
  container.innerHTML = "";

  for (var i = 0; i < dadosLideres.length; i++) {
    var item = dadosLideres[i];
    var lider = item.lider;
    var partes = lider.player_name.split(" ");
    var nomeExibido =
      partes.length > 1
        ? partes[0].charAt(0) + ". " + partes[partes.length - 1]
        : lider.player_name;

    var col = document.createElement("div");
    col.className = "col-6 col-md-4 col-lg";

    col.innerHTML =
      '<a href="jogador.html?id=' +
      lider.player_id +
      '" class="card-lider" style="border-top:3px solid ' +
      item.cat.cor +
      ';">' +
      '<div class="card-lider-stat" style="color:' +
      item.cat.cor +
      ';">' +
      item.cat.descricao.toUpperCase() +
      "</div>" +
      '<div class="card-lider-nome">' +
      nomeExibido +
      "</div>" +
      '<div class="card-lider-valor" style="color:' +
      item.cat.cor +
      ';">' +
      lider.avg +
      "</div>" +
      '<div class="card-lider-sub">' +
      lider.games_played +
      " jogos</div>" +
      "</a>";

    container.appendChild(col);
  }
}

// ============================
// GRÁFICO DE LINHAS — Evolução
// ============================

async function carregarEvolucao() {
  var temporada = document.getElementById("select-temporada").value;
  var categoria = document.getElementById("select-cat-evolucao").value;
  var fase = document.getElementById("select-fase").value;

  document.getElementById("grafico-evolucao").innerHTML = "";
  document.getElementById("legenda-evolucao").innerHTML = "";
  document.getElementById("evolucao-slider-area").style.display = "none";
  document.getElementById("evolucao-carregando").style.display = "flex";
  pararPlayer();

  todasDatas = [];
  seriesPreenchidas = {};
  dadosEvolucao = null;

  try {
    var url =
      "/analiticos/evolucao-medias?categoria=" +
      categoria +
      "&temporada=" +
      temporada;
    if (fase !== "") {
      url = url + "&stage=" + fase;
    }
    var resposta = await chamarApi(url);
    var todosJogadores = resposta.jogadores || [];

    document.getElementById("evolucao-carregando").style.display = "none";

    if (todosJogadores.length === 0) {
      document.getElementById("grafico-evolucao").innerHTML =
        '<p style="color:#888899; font-size:0.88rem; padding:16px 0;">Sem dados de evolução para essa seleção.</p>';
      return;
    }

    todasDatas = buildTodasDatas(todosJogadores);

    if (todasDatas.length === 0) {
      document.getElementById("grafico-evolucao").innerHTML =
        '<p style="color:#888899; font-size:0.88rem; padding:16px 0;">Sem dados de evolução para essa seleção.</p>';
      return;
    }

    for (var i = 0; i < todosJogadores.length; i++) {
      var jog = todosJogadores[i];
      seriesPreenchidas[jog.player_id] = buildSerieFilled(
        jog.series,
        todasDatas,
      );
    }

    dadosEvolucao = todosJogadores;

    var sliderFim = document.getElementById("slider-fim");
    var sliderInicio = document.getElementById("slider-inicio");
    sliderInicio.style.display = "none";
    sliderFim.min = 0;
    sliderFim.max = todasDatas.length - 1;
    sliderFim.value = todasDatas.length - 1;
    document.getElementById("slider-min-label").textContent = formatarDataCurta(
      todasDatas[0],
    );
    document.getElementById("slider-max-label").textContent = formatarDataCurta(
      todasDatas[todasDatas.length - 1],
    );
    document.getElementById("evolucao-slider-area").style.display = "block";

    atualizarSliderLabel();
    atualizarTrackFill();
    renderizarGraficoLinhas(todasDatas.length - 1);
  } catch (erro) {
    document.getElementById("evolucao-carregando").style.display = "none";
    document.getElementById("grafico-evolucao").innerHTML =
      '<p style="color:#FF3B5C; font-size:0.88rem; padding:16px 0;">Erro ao carregar evolução.</p>';
  }
}

function buildTodasDatas(todosJogadores) {
  var mapaData = {};
  for (var i = 0; i < todosJogadores.length; i++) {
    var serie = todosJogadores[i].series;
    for (var k = 0; k < serie.length; k++) {
      if (serie[k].data) {
        mapaData[serie[k].data] = true;
      }
    }
  }
  var datas = Object.keys(mapaData);
  datas.sort();
  return datas;
}

function buildSerieFilled(serie, todasDatas) {
  var mapaJogador = {};
  for (var i = 0; i < serie.length; i++) {
    if (serie[i].data) {
      mapaJogador[serie[i].data] = serie[i].media;
    }
  }
  var resultado = [];
  var ultimaMedia = null;
  for (var j = 0; j < todasDatas.length; j++) {
    var data = todasDatas[j];
    if (mapaJogador[data] !== undefined) {
      ultimaMedia = mapaJogador[data];
    }
    resultado.push(ultimaMedia);
  }
  return resultado;
}

function formatarDataCurta(dataStr) {
  if (!dataStr) {
    return "";
  }
  var partes = dataStr.split("-");
  if (partes.length < 3) {
    return dataStr;
  }
  return partes[2] + "/" + partes[1];
}

function aoMoverSlider() {
  pararPlayer();
  var idxAtual = parseInt(document.getElementById("slider-fim").value);
  atualizarSliderLabel();
  atualizarTrackFill();
  renderizarGraficoLinhas(idxAtual);
}

function atualizarSliderLabel() {
  var idx = parseInt(document.getElementById("slider-fim").value);
  var dataStr = todasDatas[idx] || "";
  document.getElementById("slider-label").textContent =
    formatarDataCurta(dataStr);
}

function atualizarTrackFill() {
  var sliderFim = document.getElementById("slider-fim");
  var fill = document.getElementById("slider-track-fill");
  var min = parseInt(sliderFim.min) || 0;
  var max = parseInt(sliderFim.max) || 1;
  var atual = parseInt(sliderFim.value) || 0;
  var pct = ((atual - min) / (max - min)) * 100;
  fill.style.left = "0%";
  fill.style.width = pct + "%";
}

function togglePlayer() {
  if (playerInterval !== null) {
    pararPlayer();
  } else {
    iniciarPlayer();
  }
}

function iniciarPlayer() {
  var btnPlayer = document.getElementById("btn-player");
  if (!btnPlayer) {
    return;
  }

  var sliderFim = document.getElementById("slider-fim");
  var max = parseInt(sliderFim.max);

  if (parseInt(sliderFim.value) >= max) {
    sliderFim.value = 0;
    atualizarSliderLabel();
    atualizarTrackFill();
    renderizarGraficoLinhas(0);
  }

  btnPlayer.innerHTML = '<i class="bi bi-pause-fill"></i>';
  btnPlayer.title = "Pausar";

  playerInterval = setInterval(function () {
    var sliderFimEl = document.getElementById("slider-fim");
    var atual = parseInt(sliderFimEl.value);
    var maximo = parseInt(sliderFimEl.max);

    if (atual >= maximo) {
      pararPlayer();
      return;
    }

    var proximo = Math.min(atual + 2, maximo);
    sliderFimEl.value = proximo;
    atualizarSliderLabel();
    atualizarTrackFill();
    renderizarGraficoLinhas(proximo);
  }, 60);
}

function pararPlayer() {
  if (playerInterval !== null) {
    clearInterval(playerInterval);
    playerInterval = null;
  }
  var btnPlayer = document.getElementById("btn-player");
  if (btnPlayer) {
    btnPlayer.innerHTML = '<i class="bi bi-play-fill"></i>';
    btnPlayer.title = "Reproduzir";
  }
}

function calcularTop10(idxAtual) {
  var candidatos = [];
  for (var i = 0; i < dadosEvolucao.length; i++) {
    var jog = dadosEvolucao[i];
    var serie = seriesPreenchidas[jog.player_id];
    if (!serie) {
      continue;
    }
    var valor = serie[idxAtual];
    if (valor === null) {
      continue;
    }
    var candidato = {};
    candidato.jog = jog;
    candidato.valorAtual = valor;
    candidatos.push(candidato);
  }
  candidatos.sort(function (a, b) {
    return b.valorAtual - a.valorAtual;
  });
  return candidatos.slice(0, 10);
}

function renderizarGraficoLinhas(idxAtual) {
  var container = document.getElementById("grafico-evolucao");
  container.innerHTML = "";
  document.getElementById("legenda-evolucao").innerHTML = "";

  if (!dadosEvolucao || dadosEvolucao.length === 0 || todasDatas.length === 0) {
    return;
  }

  var top10 = calcularTop10(idxAtual);

  if (top10.length === 0) {
    return;
  }

  var CORES_RANK = [
    "#C8102E",
    "#1D428A",
    "#007A33",
    "#F9A01B",
    "#552583",
    "#00838A",
    "#E56020",
    "#860038",
    "#006BB6",
    "#6B6B6B",
  ];

  var margem = { topo: 20, dir: 30, baixo: 60, esq: 55 };
  var largTotal = Math.max(obterLarguraContainer("grafico-evolucao"), 500);
  var altTotal = 380;
  var largDisp = largTotal - margem.esq - margem.dir;
  var altDisp = altTotal - margem.topo - margem.baixo;

  var maiorMedia = 0;
  for (var k = 0; k < top10.length; k++) {
    var serieTmp = seriesPreenchidas[top10[k].jog.player_id];
    for (var r = 0; r <= idxAtual; r++) {
      if (serieTmp[r] !== null && serieTmp[r] > maiorMedia) {
        maiorMedia = serieTmp[r];
      }
    }
  }

  var numTicks = Math.min(8, todasDatas.length);
  var tickIndices = [];
  for (var ti = 0; ti < numTicks; ti++) {
    tickIndices.push(
      Math.round((ti * (todasDatas.length - 1)) / (numTicks - 1)),
    );
  }

  var escX = d3
    .scaleLinear()
    .domain([0, todasDatas.length - 1])
    .range([0, largDisp]);
  var escY = d3
    .scaleLinear()
    .domain([0, maiorMedia * 1.1 || 1])
    .range([altDisp, 0]);

  var svg = d3
    .select("#grafico-evolucao")
    .append("svg")
    .attr("width", largTotal)
    .attr("height", altTotal);
  var g = svg
    .append("g")
    .attr("transform", "translate(" + margem.esq + "," + margem.topo + ")");

  g.append("g")
    .attr("transform", "translate(0," + altDisp + ")")
    .call(
      d3
        .axisBottom(escX)
        .tickValues(tickIndices)
        .tickFormat(function (d) {
          return formatarDataCurta(todasDatas[Math.round(d)] || "");
        })
        .tickSize(-altDisp),
    )
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick line")
        .attr("stroke", "#E8E8F0")
        .attr("stroke-dasharray", "3,3");
      gr.selectAll(".tick text")
        .attr("fill", "#AAAABC")
        .attr("font-size", "11px");
    });

  g.append("g")
    .call(d3.axisLeft(escY).ticks(5).tickSize(-largDisp))
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick line")
        .attr("stroke", "#E8E8F0")
        .attr("stroke-dasharray", "3,3");
      gr.selectAll(".tick text")
        .attr("fill", "#AAAABC")
        .attr("font-size", "11px");
    });

  g.append("line")
    .attr("x1", escX(idxAtual))
    .attr("x2", escX(idxAtual))
    .attr("y1", 0)
    .attr("y2", altDisp)
    .attr("stroke", "#CCCCDD")
    .attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "4,3");

  var gerador = d3
    .line()
    .defined(function (d) {
      return d !== null;
    })
    .x(function (d, i) {
      return escX(i);
    })
    .y(function (d) {
      return escY(d);
    })
    .curve(d3.curveLinear);

  for (var t = 0; t < top10.length; t++) {
    var item = top10[t];
    var jog = item.jog;
    var cor = CORES_RANK[t];
    var eLider = t === 0;

    var espessura = 1.0;
    if (t === 0) {
      espessura = 2.5;
    } else if (t === 1) {
      espessura = 2.0;
    } else if (t <= 4) {
      espessura = 1.5;
    } else {
      espessura = 1.0;
    }

    var opacidade = eLider ? 1.0 : 0.65;

    var serieFull = seriesPreenchidas[jog.player_id];
    var pontosAteAtual = serieFull.slice(0, idxAtual + 1);

    g.append("path")
      .datum(pontosAteAtual)
      .attr("fill", "none")
      .attr("stroke", cor)
      .attr("stroke-width", espessura)
      .attr("opacity", opacidade)
      .attr("d", gerador);

    if (item.valorAtual !== null) {
      g.append("circle")
        .attr("cx", escX(idxAtual))
        .attr("cy", escY(item.valorAtual))
        .attr("r", eLider ? 5 : 3.5)
        .attr("fill", cor)
        .attr("opacity", Math.min(opacidade + 0.2, 1.0))
        .style("cursor", "pointer")
        .on(
          "click",
          (function (pid) {
            return function () {
              window.location.href = "jogador.html?id=" + pid;
            };
          })(jog.player_id),
        );
    }

    if (eLider && item.valorAtual !== null) {
      var partes = jog.player_name.split(" ");
      var nomeAbrev = partes[0].charAt(0) + ". " + partes[partes.length - 1];

      var xCirulo = escX(idxAtual);
      var yCirulo = escY(item.valorAtual);

      var idxLabel = Math.max(
        0,
        idxAtual - Math.floor(todasDatas.length * 0.08),
      );
      var valorLabel = serieFull[idxLabel];
      if (valorLabel === null) {
        valorLabel = item.valorAtual;
        idxLabel = idxAtual;
      }

      var xLabel = escX(idxLabel) - 6;
      var yLabel = escY(valorLabel) - 8;

      g.append("text")
        .attr("x", xLabel)
        .attr("y", yLabel)
        .attr("text-anchor", "end")
        .attr("fill", cor)
        .attr("font-size", "10px")
        .attr("font-weight", "700")
        .text(nomeAbrev + " " + item.valorAtual);
    }
  }

  var overlay = g
    .append("rect")
    .attr("width", largDisp)
    .attr("height", altDisp)
    .attr("fill", "none")
    .attr("pointer-events", "all")
    .style("cursor", "crosshair");

  overlay.on("mousemove", function (evento) {
    var coords = d3.pointer(evento);
    var xPos = coords[0];
    var idxHovered = Math.round(escX.invert(xPos));
    if (idxHovered < 0) {
      idxHovered = 0;
    }
    if (idxHovered > idxAtual) {
      idxHovered = idxAtual;
    }

    var top10Hover = calcularTop10(idxHovered);
    var dataLabel = formatarDataCurta(todasDatas[idxHovered] || "");

    var html = "<strong>" + dataLabel + "</strong>";
    for (var li = 0; li < top10Hover.length; li++) {
      var partesNome = top10Hover[li].jog.player_name.split(" ");
      var nomeAbrevTT =
        partesNome[0].charAt(0) + ". " + partesNome[partesNome.length - 1];
      html =
        html +
        '<br><span style="color:' +
        CORES_RANK[li] +
        ';font-weight:700;">' +
        (li + 1) +
        "º</span> " +
        nomeAbrevTT +
        ": <strong>" +
        top10Hover[li].valorAtual +
        "</strong>";
    }
    showTT(evento, html);
  });

  overlay.on("mouseout", hideTT);

  var legendaHtml = "";
  for (var lk = 0; lk < top10.length; lk++) {
    var itemLeg = top10[lk];
    var corLeg = CORES_RANK[lk];
    var eLiderLeg = lk === 0;
    var partesLeg = itemLeg.jog.player_name.split(" ");
    var nomeAbrevLeg =
      partesLeg[0].charAt(0) + ". " + partesLeg[partesLeg.length - 1];
    legendaHtml =
      legendaHtml +
      '<span class="legenda-item"><span class="legenda-cor" style="background:' +
      corLeg +
      ";height:" +
      (eLiderLeg ? "3px" : "2px") +
      ';"></span><span style="color:' +
      corLeg +
      ';font-weight:700;margin-right:1px;">' +
      (lk + 1) +
      'º</span><span style="' +
      (eLiderLeg ? "font-weight:700;" : "") +
      '">' +
      nomeAbrevLeg +
      " <strong>" +
      itemLeg.valorAtual +
      "</strong></span></span>";
  }
  document.getElementById("legenda-evolucao").innerHTML = legendaHtml;
}

// ============================
// GRÁFICOS SCATTER
// ============================

async function carregarScatterPtsAst() {
  var temporada = document.getElementById("select-temporada").value;
  var fase = document.getElementById("select-fase").value;

  document.getElementById("scatter-pts-ast").innerHTML = "";
  document.getElementById("scatter-pts-ast-loading").style.display = "flex";

  try {
    var urlPts =
      "/analiticos/lideres?categoria=pontos&temporada=" +
      temporada +
      "&limite=500";
    var urlAst =
      "/analiticos/lideres?categoria=assistencias&temporada=" +
      temporada +
      "&limite=500";
    if (fase !== "") {
      urlPts = urlPts + "&stage=" + fase;
      urlAst = urlAst + "&stage=" + fase;
    }

    var respostaPts = await chamarApi(urlPts);
    var respostaAst = await chamarApi(urlAst);

    var mapaPts = {};
    var maiorJogos = 0;

    if (respostaPts && respostaPts.lideres) {
      for (var i = 0; i < respostaPts.lideres.length; i++) {
        var l = respostaPts.lideres[i];
        mapaPts[l.player_id] = { avg: l.avg, games: l.games_played };
        if (l.games_played > maiorJogos) {
          maiorJogos = l.games_played;
        }
      }
    }

    var limiteMinJogos = Math.floor(maiorJogos * 0.3);
    dadosScatterPtsAst = [];

    if (respostaAst && respostaAst.lideres) {
      for (var j = 0; j < respostaAst.lideres.length; j++) {
        var lider = respostaAst.lideres[j];
        if (mapaPts[lider.player_id] === undefined) {
          continue;
        }
        if (lider.games_played < limiteMinJogos) {
          continue;
        }
        var item = {};
        item.player_id = lider.player_id;
        item.player_name = lider.player_name;
        item.pts = mapaPts[lider.player_id].avg;
        item.ast = lider.avg;
        item.games = lider.games_played;
        item.pos = lider.pos || null;
        dadosScatterPtsAst.push(item);
      }
    }

    document.getElementById("scatter-pts-ast-loading").style.display = "none";

    if (dadosScatterPtsAst.length >= 2) {
      popularSelectPosicao("select-pos-pts-ast", dadosScatterPtsAst);
      var pos = document.getElementById("select-pos-pts-ast").value;
      var dadosFiltrados = filtrarDadosPorPos(dadosScatterPtsAst, pos);
      renderizarScatter(
        "scatter-pts-ast",
        dadosFiltrados,
        "pts",
        "Pontos por jogo",
        "Assistências por jogo",
      );
    } else {
      document.getElementById("scatter-pts-ast").innerHTML =
        '<p style="color:#888899; font-size:0.88rem; padding:16px 0;">Dados insuficientes para essa seleção.</p>';
    }
  } catch (erro) {
    document.getElementById("scatter-pts-ast-loading").style.display = "none";
    document.getElementById("scatter-pts-ast").innerHTML =
      '<p style="color:#FF3B5C; font-size:0.88rem; padding:16px 0;">Erro ao carregar dados.</p>';
  }
}

function aoFiltrarScatterPtsAst() {
  var pos = document.getElementById("select-pos-pts-ast").value;
  var dadosFiltrados = filtrarDadosPorPos(dadosScatterPtsAst, pos);
  document.getElementById("scatter-pts-ast").innerHTML = "";
  if (dadosFiltrados.length >= 2) {
    renderizarScatter(
      "scatter-pts-ast",
      dadosFiltrados,
      "pts",
      "Pontos por jogo",
      "Assistências por jogo",
    );
  }
}

async function carregarScatterRebBlk() {
  var temporada = document.getElementById("select-temporada").value;
  var fase = document.getElementById("select-fase").value;

  document.getElementById("scatter-reb-blk").innerHTML = "";
  document.getElementById("scatter-reb-blk-loading").style.display = "flex";

  try {
    var urlReb =
      "/analiticos/lideres?categoria=rebotes&temporada=" +
      temporada +
      "&limite=500";
    var urlBlk =
      "/analiticos/lideres?categoria=bloqueios&temporada=" +
      temporada +
      "&limite=500";
    if (fase !== "") {
      urlReb = urlReb + "&stage=" + fase;
      urlBlk = urlBlk + "&stage=" + fase;
    }

    var respostaReb = await chamarApi(urlReb);
    var respostaBlk = await chamarApi(urlBlk);

    var mapaReb = {};
    var maiorJogosReb = 0;

    if (respostaReb && respostaReb.lideres) {
      for (var m = 0; m < respostaReb.lideres.length; m++) {
        var lr = respostaReb.lideres[m];
        mapaReb[lr.player_id] = { avg: lr.avg, games: lr.games_played };
        if (lr.games_played > maiorJogosReb) {
          maiorJogosReb = lr.games_played;
        }
      }
    }

    var limiteMinJogosReb = Math.floor(maiorJogosReb * 0.3);
    dadosScatterRebBlk = [];

    if (respostaBlk && respostaBlk.lideres) {
      for (var n = 0; n < respostaBlk.lideres.length; n++) {
        var lb = respostaBlk.lideres[n];
        if (mapaReb[lb.player_id] === undefined) {
          continue;
        }
        if (lb.games_played < limiteMinJogosReb) {
          continue;
        }
        var item2 = {};
        item2.player_id = lb.player_id;
        item2.player_name = lb.player_name;
        item2.reb = mapaReb[lb.player_id].avg;
        item2.blk = lb.avg;
        item2.games = lb.games_played;
        item2.pos = lb.pos || null;
        dadosScatterRebBlk.push(item2);
      }
    }

    document.getElementById("scatter-reb-blk-loading").style.display = "none";

    if (dadosScatterRebBlk.length >= 2) {
      popularSelectPosicao("select-pos-reb-blk", dadosScatterRebBlk);
      var posReb = document.getElementById("select-pos-reb-blk").value;
      var dadosFiltradosReb = filtrarDadosPorPos(dadosScatterRebBlk, posReb);
      renderizarScatter(
        "scatter-reb-blk",
        dadosFiltradosReb,
        "reb",
        "Rebotes por jogo",
        "Bloqueios por jogo",
      );
    } else {
      document.getElementById("scatter-reb-blk").innerHTML =
        '<p style="color:#888899; font-size:0.88rem; padding:16px 0;">Dados insuficientes para essa seleção.</p>';
    }
  } catch (erro) {
    document.getElementById("scatter-reb-blk-loading").style.display = "none";
    document.getElementById("scatter-reb-blk").innerHTML =
      '<p style="color:#FF3B5C; font-size:0.88rem; padding:16px 0;">Erro ao carregar dados.</p>';
  }
}

function aoFiltrarScatterRebBlk() {
  var pos = document.getElementById("select-pos-reb-blk").value;
  var dadosFiltrados = filtrarDadosPorPos(dadosScatterRebBlk, pos);
  document.getElementById("scatter-reb-blk").innerHTML = "";
  if (dadosFiltrados.length >= 2) {
    renderizarScatter(
      "scatter-reb-blk",
      dadosFiltrados,
      "reb",
      "Rebotes por jogo",
      "Bloqueios por jogo",
    );
  }
}

function popularSelectPosicao(idSelect, dados) {
  var select = document.getElementById(idSelect);
  var valorAtual = select.value;

  var posicoesUnicas = [];
  for (var i = 0; i < dados.length; i++) {
    var posRaw = dados[i].pos ? dados[i].pos.split("-")[0] : null;
    if (!posRaw) {
      continue;
    }
    var posNorm = mapearNomePosicao(posRaw);
    var jatem = false;
    for (var k = 0; k < posicoesUnicas.length; k++) {
      if (posicoesUnicas[k] === posNorm) {
        jatem = true;
        break;
      }
    }
    if (!jatem) {
      posicoesUnicas.push(posNorm);
    }
  }
  posicoesUnicas.sort();

  select.innerHTML = '<option value="TODOS">Todas</option>';
  for (var j = 0; j < posicoesUnicas.length; j++) {
    var posNormJ = posicoesUnicas[j];
    var option = document.createElement("option");
    option.value = posNormJ;
    option.textContent = posNormJ;
    select.appendChild(option);
  }

  select.value = valorAtual;
  if (select.value !== valorAtual) {
    select.value = "TODOS";
  }
}

function filtrarDadosPorPos(dados, pos) {
  if (pos === "TODOS") {
    return dados;
  }
  var resultado = [];
  for (var i = 0; i < dados.length; i++) {
    var posRaw = dados[i].pos ? dados[i].pos.split("-")[0] : null;
    var posNorm = posRaw ? mapearNomePosicao(posRaw) : null;
    if (posNorm === pos) {
      resultado.push(dados[i]);
    }
  }
  return resultado;
}

function renderizarScatter(idContainer, dados, campoX, tituloX, tituloY) {
  var container = document.getElementById(idContainer);
  if (!container) {
    return;
  }
  container.innerHTML = "";

  var campoY = campoX === "pts" ? "ast" : "blk";
  var margem = { topo: 40, dir: 40, baixo: 80, esq: 75 };
  var largTotal = Math.max(obterLarguraContainer(idContainer), 500);
  var altTotal = 480;
  var largDisp = largTotal - margem.esq - margem.dir;
  var altDisp = altTotal - margem.topo - margem.baixo;

  var CORES_POS = {};
  CORES_POS["PG"] = "#C8102E";
  CORES_POS["SG"] = "#E56020";
  CORES_POS["SF"] = "#007A33";
  CORES_POS["PF"] = "#1D428A";
  CORES_POS["C"] = "#552583";
  CORES_POS["G"] = "#C8102E";
  CORES_POS["G-F"] = "#E56020";
  CORES_POS["F-G"] = "#F9A01B";
  CORES_POS["F"] = "#1D428A";
  CORES_POS["F-C"] = "#552583";
  CORES_POS["C-F"] = "#860038";

  function corPorPosicao(pos) {
    if (!pos) {
      return "#AAAAAA";
    }
    var posNormalizada = pos.split("-")[0];
    var corConhecida = CORES_POS[posNormalizada];
    if (corConhecida) {
      return corConhecida;
    }
    return "#AAAAAA";
  }

  var svg = d3
    .select("#" + idContainer)
    .append("svg")
    .attr("width", largTotal)
    .attr("height", altTotal);
  var g = svg
    .append("g")
    .attr("transform", "translate(" + margem.esq + "," + margem.topo + ")");

  var maiorX =
    d3.max(dados, function (d) {
      return d[campoX] || 0;
    }) || 1;
  var maiorY =
    d3.max(dados, function (d) {
      return d[campoY] || 0;
    }) || 1;
  var escX = d3
    .scaleLinear()
    .domain([0, maiorX * 1.1])
    .range([0, largDisp]);
  var escY = d3
    .scaleLinear()
    .domain([0, maiorY * 1.1])
    .range([altDisp, 0]);

  g.append("g")
    .attr("transform", "translate(0," + altDisp + ")")
    .call(d3.axisBottom(escX).ticks(6).tickSize(-altDisp))
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick line")
        .attr("stroke", "#E0E0E8")
        .attr("stroke-dasharray", "3,3");
      gr.selectAll(".tick text")
        .attr("fill", "#888899")
        .attr("font-size", "13px");
    });

  g.append("g")
    .call(d3.axisLeft(escY).ticks(5).tickSize(-largDisp))
    .call(function (gr) {
      gr.select(".domain").remove();
      gr.selectAll(".tick line")
        .attr("stroke", "#E0E0E8")
        .attr("stroke-dasharray", "3,3");
      gr.selectAll(".tick text")
        .attr("fill", "#888899")
        .attr("font-size", "13px");
    });

  g.selectAll(".ponto")
    .data(dados)
    .enter()
    .append("circle")
    .attr("class", "ponto")
    .attr("cx", function (d) {
      return escX(d[campoX] || 0);
    })
    .attr("cy", function (d) {
      return escY(d[campoY] || 0);
    })
    .attr("r", 7)
    .attr("fill", function (d) {
      return corPorPosicao(d.pos);
    })
    .attr("opacity", 0.8)
    .style("cursor", "pointer")
    .on("mouseover", function (evento, d) {
      d3.select(this).attr("r", 10).attr("opacity", 1);
      var posRaw = d.pos ? d.pos.split("-")[0] : "—";
      var posLabel = posRaw !== "—" ? mapearNomePosicao(posRaw) : "—";
      showTT(
        evento,
        "<strong>" +
          d.player_name +
          "</strong><br>" +
          tituloX +
          ": <strong>" +
          d[campoX] +
          "</strong><br>" +
          tituloY +
          ": <strong>" +
          d[campoY] +
          "</strong><br>Posição: " +
          posLabel +
          "<br>" +
          d.games +
          " jogos",
      );
    })
    .on("mousemove", moveTT)
    .on("mouseout", function () {
      d3.select(this).attr("r", 7).attr("opacity", 0.8);
      hideTT();
    })
    .on("click", function (evento, d) {
      window.location.href = "jogador.html?id=" + d.player_id;
    });

  var ordenadosPorX = dados.slice().sort(function (a, b) {
    return b[campoX] - a[campoX];
  });
  for (var i = 0; i < Math.min(5, ordenadosPorX.length); i++) {
    var d = ordenadosPorX[i];
    var partes = d.player_name.split(" ");
    var nomeAbrev = partes[0].charAt(0) + ". " + partes[partes.length - 1];
    g.append("text")
      .attr("x", escX(d[campoX] || 0) + 11)
      .attr("y", escY(d[campoY] || 0) + 4)
      .attr("fill", "#333355")
      .attr("font-size", "11px")
      .attr("font-weight", "600")
      .text(nomeAbrev);
  }

  g.append("text")
    .attr("x", largDisp / 2)
    .attr("y", altDisp + 55)
    .attr("text-anchor", "middle")
    .attr("fill", "#555570")
    .attr("font-size", "13px")
    .attr("font-weight", "600")
    .text(tituloX);
  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -altDisp / 2)
    .attr("y", -55)
    .attr("text-anchor", "middle")
    .attr("fill", "#555570")
    .attr("font-size", "13px")
    .attr("font-weight", "600")
    .text(tituloY);

  var posicoesUsadas = [];
  for (var j = 0; j < dados.length; j++) {
    var posRaw2 = dados[j].pos ? dados[j].pos : "—";
    var posNorm = posRaw2 !== "—" ? posRaw2.split("-")[0] : "—";
    var jatem = false;
    for (var k = 0; k < posicoesUsadas.length; k++) {
      if (posicoesUsadas[k] === posNorm) {
        jatem = true;
        break;
      }
    }
    if (!jatem) {
      posicoesUsadas.push(posNorm);
    }
  }
  posicoesUsadas.sort();

  var svgLeg = d3.select("#" + idContainer + " svg");
  var legX = margem.esq;
  var legY = margem.topo + altDisp + 68;
  for (var li = 0; li < posicoesUsadas.length; li++) {
    var posNome = posicoesUsadas[li];
    var corLeg = corPorPosicao(posNome === "—" ? null : posNome);
    var labelLeg = posNome === "—" ? "—" : mapearNomePosicao(posNome);
    svgLeg
      .append("circle")
      .attr("cx", legX)
      .attr("cy", legY)
      .attr("r", 6)
      .attr("fill", corLeg);
    svgLeg
      .append("text")
      .attr("x", legX + 14)
      .attr("y", legY + 5)
      .attr("fill", "#555570")
      .attr("font-size", "12px")
      .text(labelLeg);
    legX = legX + 80;
  }
}

// ============================
// ABA: RECORDES
// ============================

async function carregarRecordes() {
  var temporada = document.getElementById("select-temporada-recordes").value;
  var limite = 10;

  document.getElementById("recordes-carregando").style.display = "flex";
  document.getElementById("recordes-conteudo").style.display = "none";
  document.getElementById("recordes-vazio").style.display = "none";
  document.getElementById("recordes-conteudo").innerHTML = "";

  var temDados = false;
  var pares = [];
  var buffer = [];

  for (var i = 0; i < categorias.length; i++) {
    var cat = categorias[i];
    try {
      var paramTemp = temporada !== "" ? "&temporada=" + temporada : "";
      var url =
        "/analiticos/recordes?categoria=" +
        cat.id +
        paramTemp +
        "&limite=" +
        limite;
      var resposta = await chamarApi(url);

      if (resposta && resposta.recordes && resposta.recordes.length > 0) {
        temDados = true;
        var itemBuffer = {};
        itemBuffer.cat = cat;
        itemBuffer.recordes = resposta.recordes;
        buffer.push(itemBuffer);
        if (buffer.length === 2) {
          pares.push([buffer[0], buffer[1]]);
          buffer = [];
        }
      }
    } catch (e) {}
  }

  if (buffer.length === 1) {
    pares.push([buffer[0], null]);
  }

  document.getElementById("recordes-carregando").style.display = "none";

  if (!temDados) {
    document.getElementById("recordes-vazio").style.display = "block";
    return;
  }

  var container = document.getElementById("recordes-conteudo");

  for (var p = 0; p < pares.length; p++) {
    var par = pares[p];
    var row = document.createElement("div");
    row.className = "row g-3 mb-3";

    var col1 = document.createElement("div");
    if (par[1] !== null) {
      col1.className = "col-12 col-md-6";
    } else {
      col1.className = "col-12";
    }
    col1.innerHTML = construirTabelaRecordes(par[0].cat, par[0].recordes);
    row.appendChild(col1);

    if (par[1] !== null) {
      var col2 = document.createElement("div");
      col2.className = "col-12 col-md-6";
      col2.innerHTML = construirTabelaRecordes(par[1].cat, par[1].recordes);
      row.appendChild(col2);
    }

    container.appendChild(row);
  }

  document.getElementById("recordes-conteudo").style.display = "block";
  recordesCarregados = true;
}

function construirTabelaRecordes(cat, recordes) {
  var html = '<div class="grafico-container h-100">';
  html =
    html +
    '<p class="secao-titulo-grafico mb-3" style="color:' +
    cat.cor +
    ';">' +
    cat.label +
    "</p>";
  html = html + '<div class="tabela-recordes">';

  for (var i = 0; i < recordes.length; i++) {
    var r = recordes[i];
    var classePos = "";
    if (i === 0) {
      classePos = "pos-destaque";
    } else {
      classePos = "pos-normal";
    }
    html =
      html +
      '<div class="linha-recorde" onclick="window.location.href=\'jogador.html?id=' +
      r.player_id +
      "'\">";
    html = html + '<div class="recorde-pos ' + classePos + '">';
    if (i === 0) {
      html = html + "👑";
    } else {
      html = html + (i + 1);
    }
    html = html + "</div>";
    html =
      html +
      '<div class="recorde-valor" style="color:' +
      cat.cor +
      ';">' +
      r.valor +
      "</div>";
    html = html + '<div class="recorde-info">';
    html = html + '<div class="recorde-nome">' + r.player_name + "</div>";
    html =
      html +
      '<div class="recorde-detalhes">vs ' +
      r.adversario +
      " · " +
      r.data +
      "</div>";
    html = html + "</div>";
    html = html + "</div>";
  }

  html = html + "</div></div>";
  return html;
}
