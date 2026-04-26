// estatisticas.js

var abaAtiva = "lideres";
var analiseCarregada = false;
var recordesCarregados = false;
var dadosEvolucao = null;
var totalRodasEvolucao = 0;
var playerInterval = null;
var dadosScatterPtsAst = [];
var dadosScatterRebBlk = [];
var posicaoFiltroAtiva = "TODOS";

var CORES_LINHAS = ["#C8102E","#1D428A","#007A33","#F9A01B","#552583","#00838A","#E56020","#860038","#006BB6","#008348"];

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
    { id: "assistencias", label: "AST", descricao: "Assistências", cor: "#1D428A" },
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

document.addEventListener("DOMContentLoaded", function() {
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

function aoTrocarTemporada() {
    analiseCarregada = false;
    recordesCarregados = false;
    dadosEvolucao = null;
    dadosScatterPtsAst = [];
    dadosScatterRebBlk = [];
    posicaoFiltroAtiva = "TODOS";
    if (abaAtiva === "lideres") {
        carregarLideres();
    } else if (abaAtiva === "analise") {
        carregarAnalise();
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

    if (aba === "analise" && !analiseCarregada) {
        carregarAnalise();
    }

    if (aba === "recordes" && !recordesCarregados) {
        carregarRecordes();
    }
}

// ============================
// ABA: LÍDERES
// ============================

async function carregarLideres() {
    var temporada = document.getElementById("select-temporada").value;

    document.getElementById("lideres-carregando").style.display = "flex";
    document.getElementById("lideres-conteudo").style.display = "none";
    document.getElementById("lideres-vazio").style.display = "none";

    var dadosLideres = [];
    var temDados = false;

    for (var i = 0; i < categoriasPrincipais.length; i++) {
        var cat = categoriasPrincipais[i];
        try {
            var url = "/analiticos/lideres?categoria=" + cat.id + "&temporada=" + temporada + "&limite=1";
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

    renderizarInsights(dadosLideres, temporada);
    renderizarCardsLideres(dadosLideres);
    document.getElementById("lideres-conteudo").style.display = "block";

    carregarEvolucao();
}

function renderizarInsights(dadosLideres, temporada) {
    var area = document.getElementById("area-insights");

    var html = '<div class="insights-header"><i class="bi bi-lightning-charge-fill me-2" style="color:#FFD600;"></i><strong>Destaques da temporada ' + temporada + '</strong></div>';
    html = html + '<div class="insights-lista">';

    for (var i = 0; i < dadosLideres.length; i++) {
        var item = dadosLideres[i];
        var lider = item.lider;
        html = html + '<span class="insight-item">';
        html = html + '<span class="insight-dot" style="background:' + item.cat.cor + ';"></span>';
        html = html + '<strong>' + lider.player_name + '</strong> lidera em ' + item.cat.descricao + ' com <strong style="color:' + item.cat.cor + ';">' + lider.avg + '</strong>/jogo';
        html = html + '</span>';
    }

    html = html + '</div>';
    area.innerHTML = html;
    area.style.display = "block";
}

function renderizarCardsLideres(dadosLideres) {
    var container = document.getElementById("cards-lideres");
    container.innerHTML = "";

    for (var i = 0; i < dadosLideres.length; i++) {
        var item = dadosLideres[i];
        var lider = item.lider;
        var partes = lider.player_name.split(" ");
        var sobrenome = partes.length > 1 ? partes[partes.length - 1] : lider.player_name;
        var inicial = partes[0] ? partes[0].charAt(0) + "." : "";

        var col = document.createElement("div");
        col.className = "col-6 col-md-4 col-lg";

        col.innerHTML = '<a href="jogador.html?id=' + lider.player_id + '" class="card-lider" style="border-top:3px solid ' + item.cat.cor + ';">'
            + '<div class="card-lider-stat" style="color:' + item.cat.cor + ';">' + item.cat.descricao.toUpperCase() + '</div>'
            + '<div class="card-lider-nome"><span class="card-lider-inicial">' + inicial + '</span> <span class="card-lider-sobrenome">' + sobrenome + '</span></div>'
            + '<div class="card-lider-valor" style="color:' + item.cat.cor + ';">' + lider.avg + '</div>'
            + '<div class="card-lider-sub">' + lider.games_played + ' jogos · <span class="badge-lider">#1</span></div>'
            + '</a>';

        container.appendChild(col);
    }
}

// ============================
// GRÁFICO DE LINHAS — Evolução
// ============================

async function carregarEvolucao() {
    var temporada = document.getElementById("select-temporada").value;
    var categoria = document.getElementById("select-cat-evolucao").value;

    document.getElementById("grafico-evolucao").innerHTML = "";
    document.getElementById("legenda-evolucao").innerHTML = "";
    document.getElementById("evolucao-slider-area").style.display = "none";
    document.getElementById("evolucao-carregando").style.display = "flex";

    try {
        var url = "/analiticos/evolucao-medias?categoria=" + categoria + "&temporada=" + temporada;
        var resposta = await chamarApi(url);

        var todosJogadores = resposta.jogadores || [];
        totalRodasEvolucao = resposta.total_rodadas || 0;

        // Filtra jogadores com ao menos 30% dos jogos da temporada
        var limiteMinJogos = Math.floor(totalRodasEvolucao * 0.3);
        dadosEvolucao = [];
        for (var i = 0; i < todosJogadores.length; i++) {
            if (todosJogadores[i].total_jogos >= limiteMinJogos) {
                dadosEvolucao.push(todosJogadores[i]);
            }
        }

        document.getElementById("evolucao-carregando").style.display = "none";

        if (dadosEvolucao.length === 0 || totalRodasEvolucao === 0) {
            document.getElementById("grafico-evolucao").innerHTML = '<p style="color:#888899; font-size:0.88rem; padding:16px 0;">Sem dados de evolução para essa seleção.</p>';
            return;
        }

        var sliderInicio = document.getElementById("slider-inicio");
        var sliderFim = document.getElementById("slider-fim");
        sliderInicio.min = 1;
        sliderInicio.max = totalRodasEvolucao;
        sliderInicio.value = 1;
        sliderFim.min = 1;
        sliderFim.max = totalRodasEvolucao;
        sliderFim.value = totalRodasEvolucao;

        document.getElementById("slider-max-label").textContent = totalRodasEvolucao;
        document.getElementById("evolucao-slider-area").style.display = "block";

        atualizarSliderLabel();
        renderizarGraficoLinhas(1, totalRodasEvolucao);

    } catch (erro) {
        document.getElementById("evolucao-carregando").style.display = "none";
        document.getElementById("grafico-evolucao").innerHTML = '<p style="color:#FF3B5C; font-size:0.88rem; padding:16px 0;">Erro ao carregar evolução.</p>';
    }
}

function aoMoverSlider() {
    pararPlayer();
    var inicio = parseInt(document.getElementById("slider-inicio").value);
    var fim = parseInt(document.getElementById("slider-fim").value);

    if (inicio > fim) {
        var temp = inicio;
        inicio = fim;
        fim = temp;
        document.getElementById("slider-inicio").value = inicio;
        document.getElementById("slider-fim").value = fim;
    }

    atualizarSliderLabel();
    atualizarTrackFill();
    renderizarGraficoLinhas(inicio, fim);
}

function atualizarSliderLabel() {
    var inicio = document.getElementById("slider-inicio").value;
    var fim = document.getElementById("slider-fim").value;
    document.getElementById("slider-label").textContent = "Rodada " + inicio + " a " + fim;
    atualizarTrackFill();
}

function atualizarTrackFill() {
    var sliderInicio = document.getElementById("slider-inicio");
    var sliderFim = document.getElementById("slider-fim");
    var fill = document.getElementById("slider-track-fill");
    var min = parseInt(sliderInicio.min);
    var max = parseInt(sliderInicio.max);
    var inicio = parseInt(sliderInicio.value);
    var fim = parseInt(sliderFim.value);
    var pctInicio = ((inicio - min) / (max - min)) * 100;
    var pctFim = ((fim - min) / (max - min)) * 100;
    fill.style.left = pctInicio + "%";
    fill.style.width = (pctFim - pctInicio) + "%";
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

    // Se já chegou no final, reinicia do começo
    if (parseInt(sliderFim.value) >= max) {
        sliderFim.value = parseInt(document.getElementById("slider-inicio").value);
        atualizarSliderLabel();
        renderizarGraficoLinhas(parseInt(document.getElementById("slider-inicio").value), parseInt(sliderFim.value));
    }

    btnPlayer.innerHTML = '<i class="bi bi-pause-fill"></i>';
    btnPlayer.title = "Pausar";

    playerInterval = setInterval(function() {
        var sliderFimEl = document.getElementById("slider-fim");
        var atual = parseInt(sliderFimEl.value);
        var maximo = parseInt(sliderFimEl.max);
        var inicio = parseInt(document.getElementById("slider-inicio").value);

        if (atual >= maximo) {
            pararPlayer();
            return;
        }

        sliderFimEl.value = atual + 1;
        atualizarSliderLabel();
        renderizarGraficoLinhas(inicio, atual + 1);
    }, 300);
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

function renderizarGraficoLinhas(rodadaInicio, rodadaFim) {
    var container = document.getElementById("grafico-evolucao");
    container.innerHTML = "";
    document.getElementById("legenda-evolucao").innerHTML = "";

    if (!dadosEvolucao || dadosEvolucao.length === 0) {
        return;
    }

    // Calcula a média na rodada fim para cada jogador e pega top 10
    var jogadoresComMedia = [];
    for (var i = 0; i < dadosEvolucao.length; i++) {
        var jog = dadosEvolucao[i];
        var serie = jog.series;
        if (!serie || serie.length === 0) {
            continue;
        }
        // Se o jogador tem menos jogos que rodadaFim, usa o último valor disponível
        var idxFim = Math.min(rodadaFim, serie.length) - 1;
        if (idxFim < rodadaInicio - 1) {
            continue;
        }
        var mediaNoFim = serie[idxFim];
        var itemMedia = {};
        itemMedia.jog = jog;
        itemMedia.mediaNoFim = mediaNoFim;
        jogadoresComMedia.push(itemMedia);
    }

    jogadoresComMedia.sort(function(a, b) {
        return b.mediaNoFim - a.mediaNoFim;
    });

    var top10 = jogadoresComMedia.slice(0, 10);

    if (top10.length === 0) {
        return;
    }

    // Maior média no top10 para destaque
    var maiorMediaFinal = top10[0].mediaNoFim;

    var margem = { topo: 20, dir: 20, baixo: 50, esq: 55 };
    var largTotal = Math.max(obterLarguraContainer("grafico-evolucao"), 500);
    var altTotal = 420;
    var largDisp = largTotal - margem.esq - margem.dir;
    var altDisp = altTotal - margem.topo - margem.baixo;

    var svg = d3.select("#grafico-evolucao").append("svg")
        .attr("width", largTotal)
        .attr("height", altTotal);

    var g = svg.append("g").attr("transform", "translate(" + margem.esq + "," + margem.topo + ")");

    var numRodadas = rodadaFim - rodadaInicio + 1;
    var escX = d3.scaleLinear().domain([rodadaInicio, rodadaFim]).range([0, largDisp]);

    var maiorMedia = 0;
    for (var k = 0; k < top10.length; k++) {
        var serie = top10[k].jog.series;
        for (var r = rodadaInicio - 1; r < Math.min(rodadaFim, serie.length); r++) {
            if (serie[r] > maiorMedia) {
                maiorMedia = serie[r];
            }
        }
    }

    var escY = d3.scaleLinear().domain([0, maiorMedia * 1.1 || 1]).range([altDisp, 0]);

    g.append("g").attr("transform", "translate(0," + altDisp + ")")
        .call(d3.axisBottom(escX).ticks(Math.min(numRodadas, 10)).tickFormat(d3.format("d")).tickSize(-altDisp))
        .call(function(gr) {
            gr.select(".domain").remove();
            gr.selectAll(".tick line").attr("stroke", "#E0E0E8").attr("stroke-dasharray", "3,3");
            gr.selectAll(".tick text").attr("fill", "#888899").attr("font-size", "12px");
        });

    g.append("g")
        .call(d3.axisLeft(escY).ticks(5).tickSize(-largDisp))
        .call(function(gr) {
            gr.select(".domain").remove();
            gr.selectAll(".tick line").attr("stroke", "#E0E0E8").attr("stroke-dasharray", "3,3");
            gr.selectAll(".tick text").attr("fill", "#888899").attr("font-size", "12px");
        });

    g.append("text").attr("x", largDisp / 2).attr("y", altDisp + 40).attr("text-anchor", "middle").attr("fill", "#555570").attr("font-size", "13px").attr("font-weight", "600").text("Rodada");
    g.append("text").attr("transform", "rotate(-90)").attr("x", -altDisp / 2).attr("y", -42).attr("text-anchor", "middle").attr("fill", "#555570").attr("font-size", "13px").attr("font-weight", "600").text("Média acumulada");

    // Gerador de linha sem suavização
    var gerador = d3.line()
        .x(function(d) { return escX(d.rodada); })
        .y(function(d) { return escY(d.media); })
        .curve(d3.curveLinear);

    var legendaHtml = "";

    for (var t = 0; t < top10.length; t++) {
        var item = top10[t];
        var jog = item.jog;
        var cor = CORES_LINHAS[t % CORES_LINHAS.length];
        var eLider = item.mediaNoFim === maiorMediaFinal;
        var espessura = eLider ? 3.5 : 1.8;
        var opacidade = eLider ? 1.0 : 0.6;
        var pontos = [];

        for (var rd = rodadaInicio; rd <= rodadaFim; rd++) {
            if (rd <= jog.series.length) {
                var ponto = {};
                ponto.rodada = rd;
                ponto.media = jog.series[rd - 1];
                pontos.push(ponto);
            } else {
                // Estende a linha até rodadaFim com o último valor conhecido
                var ultimoValor = jog.series[jog.series.length - 1];
                var pontoExtra = {};
                pontoExtra.rodada = rd;
                pontoExtra.media = ultimoValor;
                pontos.push(pontoExtra);
            }
        }

        if (pontos.length === 0) {
            continue;
        }

        g.append("path")
            .datum(pontos)
            .attr("fill", "none")
            .attr("stroke", cor)
            .attr("stroke-width", espessura)
            .attr("opacity", opacidade)
            .attr("d", gerador);

        // Ponto final
        var ultimoPonto = pontos[pontos.length - 1];
        g.append("circle")
            .attr("cx", escX(ultimoPonto.rodada))
            .attr("cy", escY(ultimoPonto.media))
            .attr("r", eLider ? 7 : 4)
            .attr("fill", cor)
            .style("cursor", "pointer")
            .on("mouseover", (function(nomeJog, ponto) {
                return function(evento) {
                    showTT(evento, "<strong>" + nomeJog + "</strong><br>Média: <strong>" + ponto.media + "</strong><br>Rodada " + ponto.rodada);
                };
            })(jog.player_name, ultimoPonto))
            .on("mousemove", moveTT)
            .on("mouseout", hideTT)
            .on("click", (function(pid) {
                return function() { window.location.href = "jogador.html?id=" + pid; };
            })(jog.player_id));

        // Label do líder
        if (eLider) {
            var partes = jog.player_name.split(" ");
            var nomeAbrev = partes[0].charAt(0) + ". " + partes[partes.length - 1];
            g.append("text")
                .attr("x", escX(ultimoPonto.rodada) + 10)
                .attr("y", escY(ultimoPonto.media) + 4)
                .attr("fill", cor)
                .attr("font-size", "11px")
                .attr("font-weight", "700")
                .text(nomeAbrev + " " + ultimoPonto.media);
        }

        var partesLeg = jog.player_name.split(" ");
        var nomeAbrevLeg = partesLeg[0].charAt(0) + ". " + partesLeg[partesLeg.length - 1];
        var destaqueLeg = eLider ? " font-weight:700;" : "";
        legendaHtml = legendaHtml + '<span class="legenda-item" style="' + destaqueLeg + '"><span class="legenda-cor" style="background:' + cor + ';height:' + (eLider ? "4px" : "2px") + ';"></span>' + nomeAbrevLeg + ' <strong>' + ultimoPonto.media + '</strong></span>';
    }

    document.getElementById("legenda-evolucao").innerHTML = legendaHtml;
}

// ============================
// ABA: ANÁLISE (SCATTER)
// ============================

async function carregarAnalise() {
    var temporada = document.getElementById("select-temporada").value;

    document.getElementById("analise-carregando").style.display = "flex";
    document.getElementById("analise-conteudo").style.display = "none";
    document.getElementById("analise-vazio").style.display = "none";
    document.getElementById("scatter-pts-ast").innerHTML = "";
    document.getElementById("scatter-reb-blk").innerHTML = "";

    try {
        // Busca top 200 para ter jogadores suficientes para o filtro de 30%
        var respostaPts = await chamarApi("/analiticos/lideres?categoria=pontos&temporada=" + temporada + "&limite=500");
        var respostaAst = await chamarApi("/analiticos/lideres?categoria=assistencias&temporada=" + temporada + "&limite=500");

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
        var dadosScatter1 = [];

        if (respostaAst && respostaAst.lideres) {
            for (var j = 0; j < respostaAst.lideres.length; j++) {
                var lider = respostaAst.lideres[j];
                if (mapaPts[lider.player_id] === undefined) {
                    continue;
                }
                if (lider.games_played < limiteMinJogos) {
                    continue;
                }
                var itemScatter1 = {};
                itemScatter1.player_id = lider.player_id;
                itemScatter1.player_name = lider.player_name;
                itemScatter1.pts = mapaPts[lider.player_id].avg;
                itemScatter1.ast = lider.avg;
                itemScatter1.games = lider.games_played;
                itemScatter1.pos = lider.pos || null;
                dadosScatter1.push(itemScatter1);
            }
        }

        if (dadosScatter1.length >= 5) {
            dadosScatterPtsAst = dadosScatter1;
            document.getElementById("analise-conteudo").style.display = "block";
            document.getElementById("analise-carregando").style.display = "none";
            renderizarScatter("scatter-pts-ast", dadosScatter1, "pts", "Pontos por jogo", "Assistências por jogo");
        }

        var respostaReb = await chamarApi("/analiticos/lideres?categoria=rebotes&temporada=" + temporada + "&limite=500");
        var respostaBlk = await chamarApi("/analiticos/lideres?categoria=bloqueios&temporada=" + temporada + "&limite=500");

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
        var dadosScatter2 = [];

        if (respostaBlk && respostaBlk.lideres) {
            for (var n = 0; n < respostaBlk.lideres.length; n++) {
                var lb = respostaBlk.lideres[n];
                if (mapaReb[lb.player_id] === undefined) {
                    continue;
                }
                if (lb.games_played < limiteMinJogosReb) {
                    continue;
                }
                var itemScatter2 = {};
                itemScatter2.player_id = lb.player_id;
                itemScatter2.player_name = lb.player_name;
                itemScatter2.reb = mapaReb[lb.player_id].avg;
                itemScatter2.blk = lb.avg;
                itemScatter2.games = lb.games_played;
                itemScatter2.pos = lb.pos || null;
                dadosScatter2.push(itemScatter2);
            }
        }

        document.getElementById("analise-carregando").style.display = "none";

        if (dadosScatter2.length >= 5) {
            dadosScatterRebBlk = dadosScatter2;
            document.getElementById("analise-conteudo").style.display = "block";
            renderizarScatter("scatter-reb-blk", dadosScatter2, "reb", "Rebotes por jogo", "Bloqueios por jogo");
        }

        if (dadosScatter1.length < 5 && dadosScatter2.length < 5) {
            document.getElementById("analise-vazio").style.display = "block";
        } else {
            construirBotoesPosicoesScatter(dadosScatter1);
        }

        analiseCarregada = true;

    } catch (erro) {
        document.getElementById("analise-carregando").style.display = "none";
        document.getElementById("analise-vazio").style.display = "block";
    }
}

function construirBotoesPosicoesScatter(dados) {
    posicaoFiltroAtiva = "TODOS";

    var posicoesUnicas = [];
    for (var i = 0; i < dados.length; i++) {
        var pos = dados[i].pos ? dados[i].pos.split("-")[0] : null;
        if (!pos) {
            continue;
        }
        var jatem = false;
        for (var k = 0; k < posicoesUnicas.length; k++) {
            if (posicoesUnicas[k] === pos) {
                jatem = true;
                break;
            }
        }
        if (!jatem) {
            posicoesUnicas.push(pos);
        }
    }
    posicoesUnicas.sort();

    var container = document.getElementById("filtro-posicao-botoes");
    container.innerHTML = "";

    for (var j = 0; j < posicoesUnicas.length; j++) {
        var pos = posicoesUnicas[j];
        var btn = document.createElement("button");
        btn.className = "btn-filtro-pos";
        btn.textContent = pos;
        btn.dataset.pos = pos;
        btn.onclick = (function(p) {
            return function() { filtrarPorPosicao(p); };
        })(pos);
        container.appendChild(btn);
    }

    document.getElementById("filtro-posicao-area").style.display = "flex";
    document.getElementById("btn-pos-todos").classList.add("ativo");
}

function filtrarPorPosicao(pos) {
    posicaoFiltroAtiva = pos;

    var btnTodos = document.getElementById("btn-pos-todos");
    var botoesPos = document.querySelectorAll("#filtro-posicao-botoes .btn-filtro-pos");

    btnTodos.classList.remove("ativo");
    for (var i = 0; i < botoesPos.length; i++) {
        botoesPos[i].classList.remove("ativo");
    }

    if (pos === "TODOS") {
        btnTodos.classList.add("ativo");
    } else {
        for (var j = 0; j < botoesPos.length; j++) {
            if (botoesPos[j].dataset.pos === pos) {
                botoesPos[j].classList.add("ativo");
                break;
            }
        }
    }

    var dadosFiltrados1 = filtrarDadosPorPos(dadosScatterPtsAst, pos);
    var dadosFiltrados2 = filtrarDadosPorPos(dadosScatterRebBlk, pos);

    document.getElementById("scatter-pts-ast").innerHTML = "";
    document.getElementById("scatter-reb-blk").innerHTML = "";

    if (dadosFiltrados1.length >= 2) {
        renderizarScatter("scatter-pts-ast", dadosFiltrados1, "pts", "Pontos por jogo", "Assistências por jogo");
    }
    if (dadosFiltrados2.length >= 2) {
        renderizarScatter("scatter-reb-blk", dadosFiltrados2, "reb", "Rebotes por jogo", "Bloqueios por jogo");
    }
}

function filtrarDadosPorPos(dados, pos) {
    if (pos === "TODOS") {
        return dados;
    }
    var resultado = [];
    for (var i = 0; i < dados.length; i++) {
        var posJog = dados[i].pos ? dados[i].pos.split("-")[0] : null;
        if (posJog === pos) {
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
    CORES_POS["F"] = "#007A33";
    CORES_POS["F-C"] = "#1D428A";
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

    var svg = d3.select("#" + idContainer).append("svg").attr("width", largTotal).attr("height", altTotal);
    var g = svg.append("g").attr("transform", "translate(" + margem.esq + "," + margem.topo + ")");

    var maiorX = d3.max(dados, function(d) { return d[campoX] || 0; }) || 1;
    var maiorY = d3.max(dados, function(d) { return d[campoY] || 0; }) || 1;
    var escX = d3.scaleLinear().domain([0, maiorX * 1.1]).range([0, largDisp]);
    var escY = d3.scaleLinear().domain([0, maiorY * 1.1]).range([altDisp, 0]);

    g.append("g").attr("transform", "translate(0," + altDisp + ")")
        .call(d3.axisBottom(escX).ticks(6).tickSize(-altDisp))
        .call(function(gr) {
            gr.select(".domain").remove();
            gr.selectAll(".tick line").attr("stroke", "#E0E0E8").attr("stroke-dasharray", "3,3");
            gr.selectAll(".tick text").attr("fill", "#888899").attr("font-size", "13px");
        });

    g.append("g")
        .call(d3.axisLeft(escY).ticks(5).tickSize(-largDisp))
        .call(function(gr) {
            gr.select(".domain").remove();
            gr.selectAll(".tick line").attr("stroke", "#E0E0E8").attr("stroke-dasharray", "3,3");
            gr.selectAll(".tick text").attr("fill", "#888899").attr("font-size", "13px");
        });

    g.selectAll(".ponto").data(dados).enter().append("circle").attr("class", "ponto")
        .attr("cx", function(d) { return escX(d[campoX] || 0); })
        .attr("cy", function(d) { return escY(d[campoY] || 0); })
        .attr("r", 7)
        .attr("fill", function(d) { return corPorPosicao(d.pos); })
        .attr("opacity", 0.8)
        .style("cursor", "pointer")
        .on("mouseover", function(evento, d) {
            d3.select(this).attr("r", 10).attr("opacity", 1);
            var posLabel = d.pos ? d.pos.split("-")[0] : "—";
            showTT(evento, "<strong>" + d.player_name + "</strong><br>" + tituloX + ": <strong>" + d[campoX] + "</strong><br>" + tituloY + ": <strong>" + d[campoY] + "</strong><br>Posição: " + posLabel + "<br>" + d.games + " jogos");
        })
        .on("mousemove", moveTT)
        .on("mouseout", function() {
            d3.select(this).attr("r", 7).attr("opacity", 0.8);
            hideTT();
        })
        .on("click", function(evento, d) {
            window.location.href = "jogador.html?id=" + d.player_id;
        });

    // Labels dos top 5 em X
    var ordenadosPorX = dados.slice().sort(function(a, b) { return b[campoX] - a[campoX]; });
    for (var i = 0; i < Math.min(5, ordenadosPorX.length); i++) {
        var d = ordenadosPorX[i];
        var partes = d.player_name.split(" ");
        var nomeAbrev = partes[0].charAt(0) + ". " + partes[partes.length - 1];
        g.append("text").attr("x", escX(d[campoX] || 0) + 11).attr("y", escY(d[campoY] || 0) + 4).attr("fill", "#333355").attr("font-size", "11px").attr("font-weight", "600").text(nomeAbrev);
    }

    g.append("text").attr("x", largDisp / 2).attr("y", altDisp + 55).attr("text-anchor", "middle").attr("fill", "#555570").attr("font-size", "13px").attr("font-weight", "600").text(tituloX);
    g.append("text").attr("transform", "rotate(-90)").attr("x", -altDisp / 2).attr("y", -55).attr("text-anchor", "middle").attr("fill", "#555570").attr("font-size", "13px").attr("font-weight", "600").text(tituloY);

    // Legenda de posições
    var posicoesUsadas = [];
    for (var j = 0; j < dados.length; j++) {
        var posRaw = dados[j].pos ? dados[j].pos : "—";
        var posNorm = posRaw !== "—" ? posRaw.split("-")[0] : "—";
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
        svgLeg.append("circle").attr("cx", legX).attr("cy", legY).attr("r", 6).attr("fill", corLeg);
        svgLeg.append("text").attr("x", legX + 14).attr("y", legY + 5).attr("fill", "#555570").attr("font-size", "12px").text(posNome);
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
            var url = "/analiticos/recordes?categoria=" + cat.id + paramTemp + "&limite=" + limite;
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
    html = html + '<p class="secao-titulo-grafico mb-3" style="color:' + cat.cor + ';">' + cat.label + '</p>';
    html = html + '<div class="tabela-recordes">';

    for (var i = 0; i < recordes.length; i++) {
        var r = recordes[i];
        var classePos = "";
        if (i === 0) {
            classePos = "pos-destaque";
        } else {
            classePos = "pos-normal";
        }
        html = html + '<div class="linha-recorde" onclick="window.location.href=\'jogador.html?id=' + r.player_id + '\'">';
        html = html + '<div class="recorde-pos ' + classePos + '">';
        if (i === 0) {
            html = html + '👑';
        } else {
            html = html + (i + 1);
        }
        html = html + '</div>';
        html = html + '<div class="recorde-valor" style="color:' + cat.cor + ';">' + r.valor + '</div>';
        html = html + '<div class="recorde-info">';
        html = html + '<div class="recorde-nome">' + r.player_name + '</div>';
        html = html + '<div class="recorde-detalhes">vs ' + r.adversario + ' · ' + r.data + '</div>';
        html = html + '</div>';
        html = html + '</div>';
    }

    html = html + '</div></div>';
    return html;
}