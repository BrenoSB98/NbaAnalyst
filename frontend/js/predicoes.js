// predicoes.js

var MAX_JOGADORES_POR_TIME = 8;
var todosOsPalpites = [];
var filtroAtivo = "TODOS";

verificarAutenticacao();

document.addEventListener("DOMContentLoaded", function() {
    inicializarPagina();
    carregarPalpites();
});

function esconderTodos() {
    document.getElementById("pagina-carregando").style.display = "none";
    document.getElementById("pagina-conteudo").style.display = "none";
    document.getElementById("pagina-sem-jogos").style.display = "none";
    document.getElementById("pagina-aguardando").style.display = "none";
}

async function carregarPalpites() {
    try {
        var dados = await chamarApiAutenticada("/predicoes/hoje");

        esconderTodos();

        document.getElementById("resumo-jogos").textContent = dados.total_jogos;
        document.getElementById("resumo-palpites").textContent = dados.total_predicoes;
        document.getElementById("resumo-data").textContent = dados.data || "—";
        document.getElementById("resumo-dia").style.display = "flex";

        if (dados.total_jogos === 0) {
            document.getElementById("pagina-sem-jogos").style.display = "block";
            return;
        }

        if (!dados.predicoes || dados.predicoes.length === 0) {
            document.getElementById("desc-n-jogos").textContent = dados.total_jogos;
            document.getElementById("pagina-aguardando").style.display = "block";
            return;
        }

        todosOsPalpites = dados.predicoes;
        document.getElementById("pagina-conteudo").style.display = "block";
        carregarDesempenhoModelo();
        renderizarJogos(todosOsPalpites);

    } catch (erro) {
        esconderTodos();
        document.getElementById("pagina-sem-jogos").style.display = "block";
    }
}

async function carregarDesempenhoModelo() {
    try {
        var wr = await chamarApi("/desempenho");
        renderizarPainelModelo(wr);
    } catch (e) {}
}

function renderizarPainelModelo(wr) {
    var painel = document.getElementById("painel-modelo");
    var container = document.getElementById("modelo-stats");

    var wrGeral = Math.round(wr.win_rate_geral || 0);

    var wrPts = 0;
    if (wr.pontos) {
        wrPts = Math.round(wr.pontos.win_rate || 0);
    }

    var wrAst = 0;
    if (wr.assistencias) {
        wrAst = Math.round(wr.assistencias.win_rate || 0);
    }

    var wrReb = 0;
    if (wr.rebotes) {
        wrReb = Math.round(wr.rebotes.win_rate || 0);
    }

    var wrStl = 0;
    if (wr.roubos) {
        wrStl = Math.round(wr.roubos.win_rate || 0);
    }

    var wrBlk = 0;
    if (wr.bloqueios) {
        wrBlk = Math.round(wr.bloqueios.win_rate || 0);
    }

    var html = "";
    html = html + "<span class=\"modelo-geral\">" + wrGeral + "% geral</span>";
    html = html + construirBarraModelo("PTS", wrPts, "#C8102E");
    html = html + construirBarraModelo("AST", wrAst, "#1D428A");
    html = html + construirBarraModelo("REB", wrReb, "#007A33");
    html = html + construirBarraModelo("STL", wrStl, "#F9A01B");
    html = html + construirBarraModelo("BLK", wrBlk, "#552583");

    container.innerHTML = html;
    painel.style.display = "block";
}

function construirBarraModelo(rotulo, pct, cor) {
    var html = "<div class=\"modelo-stat-item\">";
    html = html + "<span class=\"modelo-stat-rotulo\">" + rotulo + "</span>";
    html = html + "<div class=\"modelo-stat-trilha\"><div class=\"modelo-stat-fill\" style=\"width:" + pct + "%;background:" + cor + ";\"></div></div>";
    html = html + "<span class=\"modelo-stat-pct\">" + pct + "%</span>";
    html = html + "</div>";
    return html;
}

function calcularConfiancaPorcentagem(valorPrevisto, mediaJogador) {
    var previsto = parseFloat(valorPrevisto);
    var media = parseFloat(mediaJogador);

    if (!previsto || !media || isNaN(previsto) || isNaN(media)) {
        return 0;
    }

    if (media === 0) {
        return 0;
    }

    var menor = previsto;
    var maior = media;
    if (media < previsto) {
        menor = media;
        maior = previsto;
    }

    var pct = (menor / maior) * 100;
    return Math.round(pct);
}

function obterClasseConfianca(pct) {
    if (pct > 75) {
        return "stat-conf-alta";
    }
    if (pct >= 50) {
        return "stat-conf-media";
    }
    return "stat-conf-baixa";
}

function _statPassaFiltro(pct) {
    if (filtroAtivo === "TODOS") {
        return true;
    }
    if (filtroAtivo === "ALTA" && pct > 75) {
        return true;
    }
    if (filtroAtivo === "MEDIA" && pct >= 50 && pct <= 75) {
        return true;
    }
    if (filtroAtivo === "BAIXA" && pct < 50) {
        return true;
    }
    return false;
}

function filtrarConfianca(nivel) {
    filtroAtivo = nivel;

    var botoes = document.querySelectorAll(".btn-filtro-conf");
    for (var i = 0; i < botoes.length; i++) {
        botoes[i].classList.remove("ativo");
    }

    var mapa = {};
    mapa["TODOS"] = "filtro-todos";
    mapa["ALTA"] = "filtro-alta";
    mapa["MEDIA"] = "filtro-media";
    mapa["BAIXA"] = "filtro-baixa";

    var idAtivo = mapa[nivel];
    if (idAtivo) {
        document.getElementById(idAtivo).classList.add("ativo");
    }

    renderizarJogos(todosOsPalpites);
}

function renderizarJogos(palpites) {
    var container = document.getElementById("lista-jogos");
    var jogos = {};

    for (var i = 0; i < palpites.length; i++) {
        var p = palpites[i];
        var gid = p.game_id;

        if (!jogos[gid]) {
            jogos[gid] = {};
            jogos[gid].nome_casa = "";
            jogos[gid].nome_fora = "";
            jogos[gid].time_casa = [];
            jogos[gid].time_fora = [];
        }

        if (p.eh_casa === 1 || p.eh_casa === true) {
            if (!jogos[gid].nome_casa) {
                jogos[gid].nome_casa = p.nome_time || "";
            }
            jogos[gid].time_casa.push(p);
        } else {
            if (!jogos[gid].nome_fora) {
                jogos[gid].nome_fora = p.nome_time || "";
            }
            jogos[gid].time_fora.push(p);
        }
    }

    if (Object.keys(jogos).length === 0) {
        container.innerHTML = "<p class=\"texto-suave text-center py-4\">Nenhum palpite encontrado para o filtro selecionado.</p>";
        return;
    }

    var html = "";
    var ids = Object.keys(jogos);

    for (var j = 0; j < ids.length; j++) {
        var gid = ids[j];
        var jogo = jogos[gid];

        jogo.time_casa.sort(function(a, b) {
            var pa = parseFloat(a.pontos_previstos) || 0;
            var pb = parseFloat(b.pontos_previstos) || 0;
            if (pb > pa) {
                return 1;
            }
            if (pb < pa) {
                return -1;
            }
            return 0;
        });

        jogo.time_fora.sort(function(a, b) {
            var pa = parseFloat(a.pontos_previstos) || 0;
            var pb = parseFloat(b.pontos_previstos) || 0;
            if (pb > pa) {
                return 1;
            }
            if (pb < pa) {
                return -1;
            }
            return 0;
        });

        var jogadoresCasa = [];
        for (var k = 0; k < jogo.time_casa.length && k < MAX_JOGADORES_POR_TIME; k++) {
            jogadoresCasa.push(jogo.time_casa[k]);
        }

        var jogadoresFora = [];
        for (var m = 0; m < jogo.time_fora.length && m < MAX_JOGADORES_POR_TIME; m++) {
            jogadoresFora.push(jogo.time_fora[m]);
        }

        var htmlCasa = renderizarColunaTimes(jogadoresCasa);
        var htmlFora = renderizarColunaTimes(jogadoresFora);

        if (htmlCasa === "" && htmlFora === "") {
            continue;
        }

        html = html + "<div class=\"card-jogo-palpite\">";
        html = html + "<div class=\"jogo-titulo\" onclick=\"toggleJogo(this)\">";
        html = html + "<div class=\"times-nome\">" + jogo.nome_casa + "<span>vs</span>" + jogo.nome_fora + "</div>";
        html = html + "<i class=\"bi bi-chevron-down jogo-seta aberto\"></i>";
        html = html + "</div>";
        html = html + "<div class=\"jogo-corpo\">";
        html = html + "<div class=\"times-grid\">";
        html = html + "<div class=\"time-coluna\">";
        html = html + "<div class=\"time-coluna-titulo casa\">" + jogo.nome_casa + " <span class=\"tag-local\">Casa</span></div>";
        html = html + htmlCasa;
        html = html + "</div>";
        html = html + "<div class=\"time-coluna\">";
        html = html + "<div class=\"time-coluna-titulo\">" + jogo.nome_fora + " <span class=\"tag-local\">Fora</span></div>";
        html = html + htmlFora;
        html = html + "</div>";
        html = html + "</div>";
        html = html + "</div>";
        html = html + "</div>";
    }

    if (html === "") {
        container.innerHTML = "<p class=\"texto-suave text-center py-4\">Nenhum palpite encontrado para o filtro selecionado.</p>";
        return;
    }

    container.innerHTML = html;
}

function renderizarColunaTimes(jogadores) {
    if (jogadores.length === 0) {
        return "";
    }

    var html = "";

    for (var i = 0; i < jogadores.length; i++) {
        var p = jogadores[i];

        var htmlPts = construirStatPalpite(p.palpite_pontos, p.pontos_previstos, "PTS", p.media_pontos);
        var htmlAst = construirStatPalpite(p.palpite_assistencias, p.assistencias_previstas, "AST", p.media_assistencias);
        var htmlReb = construirStatPalpite(p.palpite_rebotes, p.rebotes_previstos, "REB", p.media_rebotes);
        var htmlStl = construirStatPalpite(p.palpite_roubos, p.roubos_previstos, "STL", p.media_roubos);
        var htmlBlk = construirStatPalpite(p.palpite_bloqueios, p.bloqueios_previstos, "BLK", p.media_bloqueios);

        var htmlStats = htmlPts + htmlAst + htmlReb + htmlStl + htmlBlk;

        if (htmlStats === "") {
            continue;
        }

        html = html + "<div class=\"linha-jogador\">";
        html = html + "<div class=\"jogador-nome\">";
        html = html + "<a href=\"jogador.html?id=" + p.player_id + "\">" + p.nome_jogador + "</a>";
        html = html + "</div>";
        html = html + "<div class=\"stats-palpites\">";
        html = html + htmlStats;
        html = html + "</div>";
        html = html + "</div>";
    }

    return html;
}

function construirStatPalpite(palpite, valorPrevisto, rotulo, mediaJogador) {
    var linha = "";
    var direcao = "";
    var prefixo = "";

    if (palpite && palpite.linha !== null && palpite.linha !== undefined) {
        linha = String(palpite.linha);
        direcao = palpite.direcao || "";
    } else if (valorPrevisto !== null && valorPrevisto !== undefined) {
        var baseVal = Math.floor(parseFloat(valorPrevisto));
        linha = String(baseVal + 0.5);
        if (parseFloat(valorPrevisto) >= (baseVal + 0.5)) {
            direcao = "mais de";
        } else {
            direcao = "menos de";
        }
    }

    if (linha === "" || linha === "null" || valorPrevisto === null || valorPrevisto === undefined) {
        return "";
    }

    var pct = calcularConfiancaPorcentagem(valorPrevisto, mediaJogador);

    if (!_statPassaFiltro(pct)) {
        return "";
    }

    if (direcao === "mais de" || direcao === "+ de") {
        prefixo = "+ de";
    } else if (direcao === "menos de" || direcao === "- de") {
        prefixo = "- de";
    }

    var classeConf = obterClasseConfianca(pct);

    var html = "<div class=\"stat-palpite " + classeConf + "\">";
    html = html + "<div class=\"stat-palpite-prefixo\">" + prefixo + "</div>";
    html = html + "<div class=\"stat-palpite-valor\">" + linha + "</div>";
    html = html + "<div class=\"stat-palpite-rotulo\">" + rotulo + "</div>";
    html = html + "</div>";
    return html;
}

function toggleJogo(header) {
    var corpo = header.nextElementSibling;
    var seta = header.querySelector(".jogo-seta");

    if (corpo.style.display === "none") {
        corpo.style.display = "block";
        seta.classList.add("aberto");
    } else {
        corpo.style.display = "none";
        seta.classList.remove("aberto");
    }
}