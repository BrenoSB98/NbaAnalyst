var MAX_JOGADORES_POR_TIME = 8;
var todosOsPalpites = [];
var filtroAtivo = "TODOS";

verificarAutenticacao();

document.addEventListener("DOMContentLoaded", function () {
  inicializarPagina();
  carregarPalpites();
});

function esconderTodos() {
  document.getElementById("pagina-carregando").style.display = "none";
  document.getElementById("pagina-conteudo").style.display = "none";
  document.getElementById("pagina-sem-jogos").style.display = "none";
  document.getElementById("pagina-aguardando").style.display = "none";
  document.getElementById("pagina-erro").style.display = "none";
  document.getElementById("resumo-dia").style.display = "none";
}

function mostrarErro(mensagem) {
  esconderTodos();
  var descEl = document.getElementById("desc-erro-mensagem");
  if (descEl && mensagem) {
    descEl.textContent = mensagem;
  }
  document.getElementById("pagina-erro").style.display = "block";
}

function validarDadosApi(dados) {
  if (!dados || typeof dados !== "object") {
    return false;
  }
  return true;
}

function palpiteEhValido(p) {
  if (!p || typeof p !== "object") {
    return false;
  }
  if (!p.game_id && p.game_id !== 0) {
    return false;
  }
  if (!p.nome_jogador || String(p.nome_jogador).trim() === "") {
    return false;
  }
  if (!p.player_id && p.player_id !== 0) {
    return false;
  }
  return true;
}

function jogoTemTimesIdentificados(jogo) {
  if (!jogo.nome_casa || String(jogo.nome_casa).trim() === "") {
    return false;
  }
  if (!jogo.nome_fora || String(jogo.nome_fora).trim() === "") {
    return false;
  }
  return true;
}

async function carregarPalpites() {
  try {
    var dados = await chamarApiAutenticada("/predicoes/hoje");

    if (!validarDadosApi(dados)) {
      mostrarErro(
        "O servidor retornou uma resposta inesperada. Tente novamente em instantes.",
      );
      return;
    }

    var totalJogos = Number(dados.total_jogos) || 0;
    var totalPredicoes = Number(dados.total_predicoes) || 0;

    esconderTodos();

    document.getElementById("resumo-jogos").textContent = totalJogos;
    document.getElementById("resumo-palpites").textContent = totalPredicoes;
    document.getElementById("resumo-data").textContent = dados.data || "—";
    document.getElementById("resumo-dia").style.display = "flex";

    if (totalJogos === 0) {
      document.getElementById("pagina-sem-jogos").style.display = "block";
      return;
    }

    if (
      !dados.predicoes ||
      !Array.isArray(dados.predicoes) ||
      dados.predicoes.length === 0
    ) {
      document.getElementById("desc-n-jogos").textContent = totalJogos;
      document.getElementById("pagina-aguardando").style.display = "block";
      return;
    }

    var palpitesValidos = [];
    for (var i = 0; i < dados.predicoes.length; i++) {
      if (palpiteEhValido(dados.predicoes[i])) {
        palpitesValidos.push(dados.predicoes[i]);
      }
    }

    if (palpitesValidos.length === 0) {
      document.getElementById("desc-n-jogos").textContent = totalJogos;
      document.getElementById("pagina-aguardando").style.display = "block";
      return;
    }

    todosOsPalpites = palpitesValidos;
    document.getElementById("pagina-conteudo").style.display = "block";
    carregarDesempenhoModelo();
    renderizarJogos(todosOsPalpites);
  } catch (erro) {
    var mensagemErro = "Verifique sua conexão ou tente novamente em instantes.";

    if (erro && erro.message) {
      var msg = String(erro.message);
      var ehMensagemDeRede =
        msg.toLowerCase().indexOf("failed to fetch") !== -1 ||
        msg.toLowerCase().indexOf("networkerror") !== -1 ||
        msg.toLowerCase().indexOf("load failed") !== -1;
      if (!ehMensagemDeRede) {
        mensagemErro = msg;
      }
    }

    mostrarErro(mensagemErro);
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

  if (!wr || typeof wr !== "object") {
    return;
  }

  var wrGeral = Math.round(Number(wr.win_rate_geral) || 0);

  var wrPts = 0;
  if (wr.pontos && wr.pontos.win_rate) {
    wrPts = Math.round(Number(wr.pontos.win_rate) || 0);
  }

  var wrAst = 0;
  if (wr.assistencias && wr.assistencias.win_rate) {
    wrAst = Math.round(Number(wr.assistencias.win_rate) || 0);
  }

  var wrReb = 0;
  if (wr.rebotes && wr.rebotes.win_rate) {
    wrReb = Math.round(Number(wr.rebotes.win_rate) || 0);
  }

  var wrStl = 0;
  if (wr.roubos && wr.roubos.win_rate) {
    wrStl = Math.round(Number(wr.roubos.win_rate) || 0);
  }

  var wrBlk = 0;
  if (wr.bloqueios && wr.bloqueios.win_rate) {
    wrBlk = Math.round(Number(wr.bloqueios.win_rate) || 0);
  }

  var html = "";
  html = html + '<span class="modelo-geral">' + wrGeral + "% geral</span>";
  html = html + construirBarraModelo("PTS", wrPts, "#C8102E");
  html = html + construirBarraModelo("AST", wrAst, "#1D428A");
  html = html + construirBarraModelo("REB", wrReb, "#007A33");
  html = html + construirBarraModelo("STL", wrStl, "#F9A01B");
  html = html + construirBarraModelo("BLK", wrBlk, "#552583");

  container.innerHTML = html;
  painel.style.display = "block";
}

function construirBarraModelo(rotulo, pct, cor) {
  var html = '<div class="modelo-stat-item">';
  html = html + '<span class="modelo-stat-rotulo">' + rotulo + "</span>";
  html =
    html +
    '<div class="modelo-stat-trilha"><div class="modelo-stat-fill" style="width:' +
    pct +
    "%;background:" +
    cor +
    ';"></div></div>';
  html = html + '<span class="modelo-stat-pct">' + pct + "%</span>";
  html = html + "</div>";
  return html;
}

function calcularConfiancaPorcentagem(valorPrevisto, mediaJogador) {
  var previsto = parseFloat(valorPrevisto);
  var media = parseFloat(mediaJogador);

  if (!previsto || !media || isNaN(previsto) || isNaN(media)) {
    return 0;
  }

  if (media === 0 || previsto <= 0) {
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
    var gid = String(p.game_id);

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

  var ids = Object.keys(jogos);

  if (ids.length === 0) {
    container.innerHTML =
      '<p class="texto-suave text-center py-4">Nenhum palpite encontrado para o filtro selecionado.</p>';
    return;
  }

  var html = "";
  var jogosMostrados = 0;

  for (var j = 0; j < ids.length; j++) {
    var gid = ids[j];
    var jogo = jogos[gid];

    if (!jogoTemTimesIdentificados(jogo)) {
      continue;
    }

    jogo.time_casa.sort(function (a, b) {
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

    jogo.time_fora.sort(function (a, b) {
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
    for (
      var k = 0;
      k < jogo.time_casa.length && k < MAX_JOGADORES_POR_TIME;
      k++
    ) {
      jogadoresCasa.push(jogo.time_casa[k]);
    }

    var jogadoresFora = [];
    for (
      var m = 0;
      m < jogo.time_fora.length && m < MAX_JOGADORES_POR_TIME;
      m++
    ) {
      jogadoresFora.push(jogo.time_fora[m]);
    }

    var htmlCasa = renderizarColunaTimes(jogadoresCasa);
    var htmlFora = renderizarColunaTimes(jogadoresFora);

    if (htmlCasa === "" && htmlFora === "") {
      continue;
    }

    jogosMostrados++;

    html = html + '<div class="card-jogo-palpite">';
    html = html + '<div class="jogo-titulo" onclick="toggleJogo(this)">';
    html =
      html +
      '<div class="times-nome">' +
      jogo.nome_casa +
      "<span>vs</span>" +
      jogo.nome_fora +
      "</div>";
    html = html + '<i class="bi bi-chevron-down jogo-seta aberto"></i>';
    html = html + "</div>";
    html = html + '<div class="jogo-corpo">';
    html = html + '<div class="times-grid">';
    html = html + '<div class="time-coluna">';
    html =
      html +
      '<div class="time-coluna-titulo casa">' +
      jogo.nome_casa +
      ' <span class="tag-local">Casa</span></div>';
    html = html + htmlCasa;
    html = html + "</div>";
    html = html + '<div class="time-coluna">';
    html =
      html +
      '<div class="time-coluna-titulo">' +
      jogo.nome_fora +
      ' <span class="tag-local">Fora</span></div>';
    html = html + htmlFora;
    html = html + "</div>";
    html = html + "</div>";
    html = html + "</div>";
    html = html + "</div>";
  }

  if (jogosMostrados === 0) {
    if (filtroAtivo !== "TODOS") {
      container.innerHTML =
        '<p class="texto-suave text-center py-4">Nenhum palpite com confiança <strong>' +
        filtroAtivo.toLowerCase() +
        "</strong> encontrado. Tente o filtro <strong>Todos</strong> para ver todos os palpites do dia.</p>";
    } else {
      container.innerHTML =
        '<p class="texto-suave text-center py-4">Nenhum palpite disponível para exibição no momento.</p>';
    }
    return;
  }

  container.innerHTML = html;
}

function renderizarColunaTimes(jogadores) {
  if (!jogadores || jogadores.length === 0) {
    return "";
  }

  var html = "";

  for (var i = 0; i < jogadores.length; i++) {
    var p = jogadores[i];

    var htmlPts = construirStatPalpite(
      p.palpite_pontos,
      p.pontos_previstos,
      "PTS",
      p.media_pontos,
    );
    var htmlAst = construirStatPalpite(
      p.palpite_assistencias,
      p.assistencias_previstas,
      "AST",
      p.media_assistencias,
    );
    var htmlReb = construirStatPalpite(
      p.palpite_rebotes,
      p.rebotes_previstos,
      "REB",
      p.media_rebotes,
    );
    var htmlStl = construirStatPalpite(
      p.palpite_roubos,
      p.roubos_previstos,
      "STL",
      p.media_roubos,
    );
    var htmlBlk = construirStatPalpite(
      p.palpite_bloqueios,
      p.bloqueios_previstos,
      "BLK",
      p.media_bloqueios,
    );

    var htmlStats = htmlPts + htmlAst + htmlReb + htmlStl + htmlBlk;

    if (htmlStats === "") {
      continue;
    }

    html = html + '<div class="linha-jogador">';
    html = html + '<div class="jogador-nome">';
    html =
      html +
      '<a href="jogador.html?id=' +
      p.player_id +
      '">' +
      p.nome_jogador +
      "</a>";
    html = html + "</div>";
    html = html + '<div class="stats-palpites">';
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
    var valorFloat = parseFloat(valorPrevisto);
    if (isNaN(valorFloat) || valorFloat < 0) {
      return "";
    }
    var baseVal = Math.floor(valorFloat);
    linha = String(baseVal + 0.5);
    if (valorFloat >= baseVal + 0.5) {
      direcao = "mais de";
    } else {
      direcao = "menos de";
    }
  }

  if (
    linha === "" ||
    linha === "null" ||
    valorPrevisto === null ||
    valorPrevisto === undefined
  ) {
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

  var html = '<div class="stat-palpite ' + classeConf + '">';
  html = html + '<div class="stat-palpite-prefixo">' + prefixo + "</div>";
  html = html + '<div class="stat-palpite-valor">' + linha + "</div>";
  html = html + '<div class="stat-palpite-rotulo">' + rotulo + "</div>";
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
