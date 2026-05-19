verificarAutenticacaoAdmin();

document.addEventListener("DOMContentLoaded", function () {
  inicializarPagina();
  carregarKpis();
  carregarRelatorios();
});

function verificarAutenticacaoAdmin() {
  var token = localStorage.getItem("nba_token");
  if (!token) {
    window.location.href = "login.html";
  }
}

async function carregarKpis() {
  try {
    var info = await chamarApiAutenticada("/admin/info");
    document.getElementById("kpi-modelos").textContent =
      info.total_modelos || 0;
  } catch (e) {
    document.getElementById("kpi-modelos").textContent = "—";
  }

  try {
    var wr = await chamarApiAutenticada("/win_rate/desempenho");
    document.getElementById("kpi-winrate").textContent =
      Math.round(wr.win_rate_geral || 0) + "%";
  } catch (e) {
    document.getElementById("kpi-winrate").textContent = "—";
  }

  try {
    var relatorios = await chamarApiAutenticada("/admin/relatorios");
    document.getElementById("kpi-relatorios").textContent =
      relatorios.total || 0;
  } catch (e) {
    document.getElementById("kpi-relatorios").textContent = "—";
  }
}

async function carregarRelatorios() {
  document.getElementById("relatorios-carregando").style.display = "block";
  document.getElementById("relatorios-vazio").style.display = "none";
  document.getElementById("relatorios-lista").style.display = "none";

  try {
    var dados = await chamarApiAutenticada("/admin/relatorios");
    document.getElementById("relatorios-carregando").style.display = "none";

    if (!dados.relatorios || dados.relatorios.length === 0) {
      document.getElementById("relatorios-vazio").style.display = "block";
      return;
    }

    document.getElementById("kpi-relatorios").textContent = dados.total;

    var html = "";
    for (var i = 0; i < dados.relatorios.length; i++) {
      var rel = dados.relatorios[i];
      var nome = rel.nome;
      var tamanho = rel.tamanho_kb + " KB";
      var dataObj = new Date(rel.data_modificacao * 1000);
      var dataFormatada =
        dataObj.toLocaleDateString("pt-BR") +
        " " +
        dataObj.toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        });
      var ehMaisRecente = i === 0;

      html = html + '<div class="linha-relatorio">';
      html =
        html +
        '<div class="relatorio-icone"><i class="bi bi-file-earmark-pdf-fill"></i></div>';
      html = html + '<div class="relatorio-info">';
      html = html + '<div class="relatorio-nome">' + nome;
      if (ehMaisRecente) {
        html = html + ' <span class="badge-mais-recente">Mais recente</span>';
      }
      html = html + "</div>";
      html =
        html +
        '<div class="relatorio-meta">' +
        dataFormatada +
        " &nbsp;·&nbsp; " +
        tamanho +
        "</div>";
      html = html + "</div>";
      html =
        html +
        '<a href="#" class="btn-baixar" onclick="baixarRelatorio(\'' +
        nome +
        "', event)\">";
      html = html + '<i class="bi bi-download me-1"></i>Baixar</a>';
      html = html + "</div>";
    }

    document.getElementById("relatorios-lista").innerHTML = html;
    document.getElementById("relatorios-lista").style.display = "block";
  } catch (erro) {
    document.getElementById("relatorios-carregando").style.display = "none";
    document.getElementById("relatorios-vazio").style.display = "block";
  }
}

async function baixarRelatorio(nomeArquivo, evento) {
  evento.preventDefault();
  var token = localStorage.getItem("nba_token");
  if (!token) {
    return;
  }

  var btnClicado = evento.currentTarget;
  var htmlOriginal = btnClicado.innerHTML;

  btnClicado.innerHTML =
    '<span class="spinner-border spinner-border-sm me-1"></span>Baixando...';
  btnClicado.style.pointerEvents = "none";

  try {
    var url = URL_BASE + "/admin/relatorios/download/" + nomeArquivo;
    var resposta = await fetch(url, {
      headers: { Authorization: "Bearer " + token },
    });

    if (!resposta.ok) {
      alert("Erro ao baixar o relatório.");
      btnClicado.innerHTML = htmlOriginal;
      btnClicado.style.pointerEvents = "";
      return;
    }

    var blob = await resposta.blob();
    var urlObj = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = urlObj;
    link.download = nomeArquivo;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(urlObj);
  } catch (erro) {
    alert("Erro ao baixar o relatório.");
  }

  btnClicado.innerHTML = htmlOriginal;
  btnClicado.style.pointerEvents = "";
}

async function retreinarModelos() {
  var btn = document.getElementById("btn-retreinar");
  var resultado = document.getElementById("resultado-retreinar");

  btn.disabled = true;
  btn.innerHTML =
    '<span class="spinner-border spinner-border-sm me-2"></span>Iniciando...';
  resultado.style.display = "none";

  try {
    var dados = await chamarApiAutenticada("/admin/retreinar", "POST");

    resultado.style.display = "block";
    resultado.className = "acao-resultado acao-sucesso";
    resultado.innerHTML =
      '<i class="bi bi-clock-history me-2"></i>Retreinamento iniciado. O relatório PDF será gerado ao final e aparecerá na lista abaixo. Isso pode levar alguns minutos.';

    iniciarPollingRelatorios();
  } catch (erro) {
    resultado.style.display = "block";
    resultado.className = "acao-resultado acao-erro";
    resultado.innerHTML =
      '<i class="bi bi-x-circle-fill me-2"></i>Erro ao iniciar o retreinamento.';
  }

  btn.disabled = false;
  btn.innerHTML =
    '<i class="bi bi-arrow-repeat me-2"></i>Iniciar Retreinamento';
}

function iniciarPollingRelatorios() {
  var tentativas = 0;
  var totalTentativas = 40;
  var intervalId = setInterval(function () {
    tentativas = tentativas + 1;
    carregarRelatorios();
    carregarKpis();
    if (tentativas >= totalTentativas) {
      clearInterval(intervalId);
    }
  }, 30000);
}

function confirmarRetroativo() {
  document.getElementById("modal-confirmacao").style.display = "flex";
}

function fecharModal() {
  document.getElementById("modal-confirmacao").style.display = "none";
}

async function executarRetroativo() {
  fecharModal();
  var btn = document.getElementById("btn-retroativo");
  var resultado = document.getElementById("resultado-retroativo");

  btn.disabled = true;
  btn.innerHTML =
    '<span class="spinner-border spinner-border-sm me-2"></span>Processando...';
  resultado.style.display = "none";

  try {
    var dados = await chamarApiAutenticada("/predicoes/retroativo", "POST");
    resultado.style.display = "block";
    resultado.className = "acao-resultado acao-sucesso";
    resultado.innerHTML =
      '<i class="bi bi-check-circle-fill me-2"></i>Predições retroativas geradas: ' +
      (dados.total || 0) +
      " palpites.";
  } catch (erro) {
    resultado.style.display = "block";
    resultado.className = "acao-resultado acao-erro";
    resultado.innerHTML =
      '<i class="bi bi-x-circle-fill me-2"></i>Erro ao gerar predições retroativas.';
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="bi bi-clock-history me-2"></i>Gerar Retroativo';
}
