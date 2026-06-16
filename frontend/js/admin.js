verificarAutenticacaoAdmin();

document.addEventListener("DOMContentLoaded", function () {
  inicializarPagina();
  carregarRelatorios();
});

function verificarAutenticacaoAdmin() {
  var token = localStorage.getItem("nba_token");
  if (!token) {
    window.location.href = "login.html";
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
