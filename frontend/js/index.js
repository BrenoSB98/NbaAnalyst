document.addEventListener("DOMContentLoaded", function () {
  inicializarPagina();
  carregarDesempenhoModelo();
  carregarKpisHoje();

  if (estaLogado()) {
    document.getElementById("hero-nav-auth").style.display = "none";
    document.getElementById("secao-cta").style.display = "none";
  }
});

async function carregarDesempenhoModelo() {
  try {
    var dados = await chamarApi("/win_rate/desempenho");

    document.getElementById("kpi-winrate").textContent =
      dados.win_rate_geral + "%";
    document.getElementById("modelo-winrate-geral").textContent =
      dados.win_rate_geral + "%";
    document.getElementById("modelo-total-pred").textContent =
      dados.total_predicoes_avaliadas + " palpites avaliados";
    renderizarCardsModelo(dados);
    document.getElementById("modelo-carregando").style.display = "none";
    document.getElementById("modelo-conteudo").style.display = "block";
  } catch (erro) {
    document.getElementById("modelo-carregando").style.display = "none";
    document.getElementById("modelo-erro").style.display = "block";
    document.getElementById("kpi-winrate").textContent = "—";
  }
}

function renderizarCardsModelo(dados) {
  var container = document.getElementById("modelo-cards-stats");
  var html = "";

  var campos = ["pontos", "assistencias", "rebotes", "roubos", "bloqueios"];
  var labels = ["Pontos", "Assistências", "Rebotes", "Roubos", "Bloqueios"];
  var sufixos = ["pts", "ast", "reb", "stl", "blk"];

  for (var i = 0; i < campos.length; i++) {
    var campo = campos[i];
    var label = labels[i];
    var sufixo = sufixos[i];
    var info = dados[campo];

    if (!info) {
      continue;
    }

    var wr = info.win_rate;
    var cor = "#FF3B5C";
    if (wr >= 70) {
      cor = "#00C896";
    } else if (wr >= 55) {
      cor = "#FFD600";
    }

    var margem = "—";
    if (info.mae_medio !== null && info.mae_medio !== undefined) {
      margem = "± " + parseFloat(info.mae_medio).toFixed(1) + " " + sufixo;
    }

    html = html + '<div class="col-6 col-sm-4 col-xl">';
    html = html + '<div class="card-stat-modelo">';
    html =
      html +
      '<div class="stat-valor" style="color:' +
      cor +
      ';">' +
      wr +
      "%</div>";
    html = html + '<div class="stat-nome">' + label + "</div>";
    html = html + '<div class="stat-margem">' + margem + "</div>";
    html = html + "</div>";
    html = html + "</div>";
  }

  container.innerHTML = html;
}

async function carregarKpisHoje() {
  document.getElementById("kpi-jogos-hoje").textContent = "...";
  document.getElementById("kpi-predicoes-hoje").textContent = "...";

  try {
    var dadosJogos = await chamarApi("/jogos/contagem-hoje");
    document.getElementById("kpi-jogos-hoje").textContent =
      dadosJogos.total_jogos || 0;
  } catch (erro) {
    document.getElementById("kpi-jogos-hoje").textContent = "—";
  }

  try {
    var dadosPalpites = await chamarApi("/predicoes/contagem-hoje");
    document.getElementById("kpi-predicoes-hoje").textContent =
      dadosPalpites.total_palpites || 0;
  } catch (erro) {
    document.getElementById("kpi-predicoes-hoje").textContent = "—";
  }
}
