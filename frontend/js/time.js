var timeId = obterParametroUrl("id");
var dadosTime = null;
var temporadaAtual = 2025;
var stageAtual = "";
var nJogosAtual = 10;

document.addEventListener("DOMContentLoaded", function () {
  inicializarPagina();

  if (!timeId) {
    document.getElementById("pagina-carregando").style.display = "none";
    document.getElementById("pagina-erro").style.display = "block";
    return;
  }

  carregarTime();
});

function obterTemporadaSelecionada() {
  return parseInt(document.getElementById("select-temporada").value);
}

function obterStageSelecionado() {
  return document.getElementById("select-stage").value;
}

function obterNJogosSelecionado() {
  return parseInt(document.getElementById("select-n-jogos").value);
}

function trocarFiltros() {
  temporadaAtual = obterTemporadaSelecionada();
  stageAtual = obterStageSelecionado();

  document.getElementById("cards-estatisticas").innerHTML = "";
  document.getElementById("stats-conteudo").style.display = "none";
  document.getElementById("stats-carregando").style.display = "block";
  document.getElementById("jogos-secao").style.display = "none";

  carregarPerformance(temporadaAtual, stageAtual, nJogosAtual);
}

function trocarNJogos() {
  nJogosAtual = obterNJogosSelecionado();
  carregarPerformance(temporadaAtual, stageAtual, nJogosAtual);
}

async function carregarTime() {
  try {
    dadosTime = await chamarApi("/times/" + timeId);

    document.title = "NbaAnalyst — " + dadosTime.nome;
    document.getElementById("time-nome").textContent = dadosTime.nome;
    document.getElementById("time-cidade").textContent = dadosTime.cidade || "";

    var logoContainer = document.getElementById("time-logo-container");
    if (dadosTime.logo) {
      logoContainer.innerHTML =
        '<img src="' +
        dadosTime.logo +
        '" alt="' +
        dadosTime.nome +
        '" class="time-logo-grande">';
    } else {
      var codigo =
        dadosTime.codigo || dadosTime.nome.substring(0, 3).toUpperCase();
      logoContainer.innerHTML =
        '<div class="time-logo-placeholder">' + codigo + "</div>";
    }

    if (dadosTime.info_liga) {
      document.getElementById("time-conferencia").textContent =
        dadosTime.info_liga.conferencia || "";
      document.getElementById("time-divisao").textContent =
        dadosTime.info_liga.divisao || "";
    }

    document.getElementById("pagina-carregando").style.display = "none";
    document.getElementById("pagina-conteudo").style.display = "block";

    renderizarDadosCadastrais(dadosTime);
    carregarPerformance(temporadaAtual, stageAtual, nJogosAtual);
  } catch (erro) {
    document.getElementById("pagina-carregando").style.display = "none";
    document.getElementById("pagina-erro").style.display = "block";
  }
}

function renderizarDadosCadastrais(dados) {
  var conferencia = "—";
  var divisao = "—";

  if (dados.info_liga) {
    conferencia = dados.info_liga.conferencia || "—";
    divisao = dados.info_liga.divisao || "—";
  }

  var html =
    "" +
    '<div class="col-6 col-md-3">' +
    '<div class="dado-cadastral-rotulo">Apelido</div>' +
    '<div class="dado-cadastral-valor">' +
    (dados.apelido || "—") +
    "</div>" +
    "</div>" +
    '<div class="col-6 col-md-3">' +
    '<div class="dado-cadastral-rotulo">Cidade</div>' +
    '<div class="dado-cadastral-valor">' +
    (dados.cidade || "—") +
    "</div>" +
    "</div>" +
    '<div class="col-6 col-md-3">' +
    '<div class="dado-cadastral-rotulo">Conferência</div>' +
    '<div class="dado-cadastral-valor texto-laranja">' +
    conferencia +
    "</div>" +
    "</div>" +
    '<div class="col-6 col-md-3">' +
    '<div class="dado-cadastral-rotulo">Divisão</div>' +
    '<div class="dado-cadastral-valor">' +
    divisao +
    "</div>" +
    "</div>";

  document.getElementById("dados-cadastrais").innerHTML = html;
}

function trocarAba(nomeAba) {
  var todasAbas = document.querySelectorAll(".conteudo-aba");
  for (var i = 0; i < todasAbas.length; i++) {
    todasAbas[i].classList.remove("ativo");
  }

  var todosBotoes = document.querySelectorAll(".abas-time .nav-link");
  for (var i = 0; i < todosBotoes.length; i++) {
    todosBotoes[i].classList.remove("ativo");
  }

  document.getElementById("aba-" + nomeAba).classList.add("ativo");
  document.getElementById("aba-btn-" + nomeAba).classList.add("ativo");

  if (nomeAba === "elenco") {
    if (document.getElementById("elenco-tbody").innerHTML === "") {
      carregarElenco();
    }
  }
}

async function carregarPerformance(temporada, stage, nJogos) {
  document.getElementById("stats-carregando").style.display = "block";
  document.getElementById("stats-conteudo").style.display = "none";
  document.getElementById("jogos-secao").style.display = "none";

  try {
    var url =
      "/times/" +
      timeId +
      "/performance?temporada=" +
      temporada +
      "&n_jogos=" +
      nJogos;
    if (stage !== "" && stage !== null && stage !== undefined) {
      url = url + "&stage=" + stage;
    }

    var dados = await chamarApi(url);

    var cards = [
      { numero: dados.total_jogos, rotulo: "Jogos", cor: "#1A1A2E" },
      { numero: dados.vitorias, rotulo: "Vitórias", cor: "#00C896" },
      { numero: dados.derrotas, rotulo: "Derrotas", cor: "#FF3B5C" },
      {
        numero: dados.aproveitamento + "%",
        rotulo: "Aproveitamento",
        cor: "#F75C03",
      },
      {
        numero: dados.media_pontos_feitos,
        rotulo: "Média Pts Feitos",
        cor: "#3B9EFF",
      },
      {
        numero: dados.media_pontos_sofridos,
        rotulo: "Média Pts Sofridos",
        cor: "#555570",
      },
    ];

    var html = "";
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      html =
        html +
        '<div class="col-6 col-sm-4 col-md-2">' +
        '<div class="card-stat-time" style="border-top:3px solid ' +
        c.cor +
        ';">' +
        '<div class="stat-numero" style="color:' +
        c.cor +
        ';">' +
        c.numero +
        "</div>" +
        '<div class="stat-rotulo">' +
        c.rotulo +
        "</div>" +
        "</div>" +
        "</div>";
    }

    document.getElementById("cards-estatisticas").innerHTML = html;
    document.getElementById("stats-carregando").style.display = "none";
    document.getElementById("stats-conteudo").style.display = "block";

    renderizarTabelaJogos(dados.ultimos_jogos);
  } catch (erro) {
    document.getElementById("stats-carregando").style.display = "none";
    document.getElementById("cards-estatisticas").innerHTML =
      '<div class="col-12"><p class="texto-suave" style="font-size:0.88rem; padding:8px 0;">Sem dados para esta seleção.</p></div>';
    document.getElementById("stats-conteudo").style.display = "block";
  }
}

function renderizarTabelaJogos(jogos) {
  if (!jogos || jogos.length === 0) {
    document.getElementById("jogos-secao").style.display = "none";
    return;
  }

  var tbody = "";
  for (var i = 0; i < jogos.length; i++) {
    var j = jogos[i];

    var classeRes = j.resultado === "V" ? "vitoria" : "derrota";

    var dataFmt = "—";
    if (j.data) {
      var dt = new Date(j.data);
      dataFmt = dt.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "2-digit",
      });
    }

    var localTexto = j.em_casa ? "Casa" : "Fora";

    var adversarioHtml = "";
    if (j.logo_adversario) {
      adversarioHtml =
        '<img src="' +
        j.logo_adversario +
        '" alt="" style="width:20px;height:20px;object-fit:contain;margin-right:6px;vertical-align:middle;">';
    }
    adversarioHtml = adversarioHtml + (j.nome_adversario || "—");

    tbody =
      tbody +
      "<tr>" +
      '<td><span class="resultado-badge ' +
      classeRes +
      '">' +
      j.resultado +
      "</span></td>" +
      "<td>" +
      adversarioHtml +
      "</td>" +
      '<td class="texto-suave">' +
      localTexto +
      "</td>" +
      "<td style=\"font-family:'Oswald',sans-serif;font-size:1rem;\">" +
      j.pontos_feitos +
      " — " +
      j.pontos_sofridos +
      "</td>" +
      '<td class="texto-suave">' +
      dataFmt +
      "</td>" +
      "</tr>";
  }

  document.getElementById("jogos-tbody").innerHTML = tbody;
  document.getElementById("jogos-secao").style.display = "block";
}

async function carregarElenco() {
  document.getElementById("elenco-carregando").style.display = "block";
  document.getElementById("elenco-conteudo").style.display = "none";
  document.getElementById("elenco-vazio").style.display = "none";

  try {
    var dados = await chamarApi("/times/" + timeId + "/elenco");

    document.getElementById("elenco-carregando").style.display = "none";
    document.getElementById("elenco-titulo").textContent =
      "Temporada " + dados.temporada + " — " + dados.total + " jogadores";

    if (!dados.jogadores || dados.jogadores.length === 0) {
      document.getElementById("elenco-vazio").style.display = "block";
      return;
    }

    var tbody = "";
    for (var i = 0; i < dados.jogadores.length; i++) {
      var j = dados.jogadores[i];

      var altura = j.altura_metros ? j.altura_metros.toFixed(2) + " m" : "—";
      var peso = j.peso_kg ? j.peso_kg.toFixed(1) + " kg" : "—";
      var camisa = j.camisa !== null ? j.camisa : "—";
      var pos = j.posicao || "—";

      tbody =
        tbody +
        "<tr>" +
        '<td class="numero-camisa">' +
        camisa +
        "</td>" +
        '<td><a href="jogador.html?id=' +
        j.id +
        '" class="nome-jogador-link">' +
        j.nome +
        "</a></td>" +
        '<td class="texto-suave">' +
        pos +
        "</td>" +
        '<td class="texto-suave">' +
        altura +
        "</td>" +
        '<td class="texto-suave">' +
        peso +
        "</td>" +
        '<td><span class="badge-status ' +
        (j.ativo ? "ativo" : "inativo") +
        '">' +
        (j.ativo ? "Ativo" : "Inativo") +
        "</span></td>" +
        "</tr>";
    }

    document.getElementById("elenco-tbody").innerHTML = tbody;
    document.getElementById("elenco-conteudo").style.display = "block";
  } catch (erro) {
    document.getElementById("elenco-carregando").style.display = "none";
    document.getElementById("elenco-vazio").style.display = "block";
  }
}
