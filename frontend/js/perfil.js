verificarAutenticacao();

var todosOsTimes = [];

document.addEventListener("DOMContentLoaded", function () {
  inicializarPagina();
  carregarPerfil();
});

async function carregarPerfil() {
  try {
    var usuario = await chamarApiAutenticada("/autenticacao/eu");

    var iniciais = obterInicialNome(usuario.full_name);
    document.getElementById("perfil-avatar").textContent = iniciais;
    document.getElementById("perfil-nome").textContent = usuario.full_name;
    document.getElementById("perfil-email").textContent = usuario.email;

    if (usuario.created_at) {
      var dtCriado = new Date(usuario.created_at);
      var membroDesde = dtCriado.toLocaleDateString("pt-BR", {
        month: "long",
        year: "numeric",
      });
      document.getElementById("perfil-membro").textContent =
        "Membro desde " + membroDesde;
    }

    renderizarDadosConta(usuario);

    document.getElementById("pagina-carregando").style.display = "none";
    document.getElementById("pagina-conteudo").style.display = "block";

    carregarTimeFavorito(usuario.favorite_team_id);
    carregarListaTimes();
  } catch (erro) {
    document.getElementById("pagina-carregando").style.display = "none";
    document.getElementById("pagina-conteudo").style.display = "block";
  }
}

function renderizarDadosConta(usuario) {
  var nascimento = "—";
  if (usuario.birth_date) {
    var dt = new Date(usuario.birth_date + "T00:00:00");
    nascimento = dt.toLocaleDateString("pt-BR");
  }

  var html =
    "" +
    '<div class="col-6 col-md-3">' +
    '<div class="dado-cadastral-rotulo">Nome</div>' +
    '<div class="dado-cadastral-valor">' +
    (usuario.full_name || "—") +
    "</div>" +
    "</div>" +
    '<div class="col-6 col-md-3">' +
    '<div class="dado-cadastral-rotulo">E-mail</div>' +
    '<div class="dado-cadastral-valor">' +
    (usuario.email || "—") +
    "</div>" +
    "</div>" +
    '<div class="col-6 col-md-3">' +
    '<div class="dado-cadastral-rotulo">Nascimento</div>' +
    '<div class="dado-cadastral-valor">' +
    nascimento +
    "</div>" +
    "</div>";

  document.getElementById("dados-conta").innerHTML = html;
}

async function carregarListaTimes() {
  try {
    var resposta = await chamarApi("/times?nba_franchise=true&page_size=30");
    var lista = resposta.times || [];

    todosOsTimes = lista;

    var select = document.getElementById("select-time-favorito");
    select.innerHTML = '<option value="">Selecione um time...</option>';

    for (var i = 0; i < lista.length; i++) {
      var time = lista[i];
      var option = document.createElement("option");
      option.value = time.id;
      option.textContent = time.nome || time.name;
      select.appendChild(option);
    }
  } catch (erro) {
    var select = document.getElementById("select-time-favorito");
    if (select) {
      select.innerHTML = "";
      var opcaoErro = document.createElement("option");
      opcaoErro.value = "";
      opcaoErro.textContent = "Erro ao carregar times — recarregue a página";
      opcaoErro.disabled = true;
      select.appendChild(opcaoErro);
      select.disabled = true;
    }
  }
}

async function carregarTimeFavorito(timeId) {
  document.getElementById("time-fav-carregando").style.display = "none";

  if (!timeId) {
    document.getElementById("time-fav-vazio").style.display = "block";
    document.getElementById("btn-trocar-time").style.display = "inline-flex";
    return;
  }

  try {
    var time = await chamarApi("/times/" + timeId);

    var logoHtml = "";
    if (time.logo) {
      logoHtml =
        '<img src="' +
        time.logo +
        '" alt="' +
        time.nome +
        '" class="time-logo-fav">';
    } else {
      var codigo =
        time.codigo || (time.nome || "NBA").substring(0, 3).toUpperCase();
      logoHtml = '<div class="time-placeholder-fav">' + codigo + "</div>";
    }

    var conferencia = "";
    if (time.info_liga) {
      conferencia =
        (time.info_liga.conferencia || "") +
        " · " +
        (time.info_liga.divisao || "");
    }

    var html =
      "" +
      '<a href="time.html?id=' +
      time.id +
      '" class="card-time-favorito">' +
      logoHtml +
      "<div>" +
      '<div class="time-nome-fav">' +
      time.nome +
      "</div>" +
      '<div class="time-label-fav">' +
      conferencia +
      "</div>" +
      "</div>" +
      '<i class="bi bi-chevron-right ms-auto texto-suave"></i>' +
      "</a>";

    document.getElementById("time-fav-conteudo").innerHTML = html;
    document.getElementById("time-fav-conteudo").style.display = "block";
    document.getElementById("btn-trocar-time").style.display = "inline-flex";
  } catch (erro) {
    document.getElementById("time-fav-vazio").style.display = "block";
    document.getElementById("btn-trocar-time").style.display = "inline-flex";
  }
}

function mostrarSeletorTime() {
  document.getElementById("time-fav-seletor").style.display = "block";
  document.getElementById("btn-trocar-time").style.display = "none";
}

function cancelarSelecaoTime() {
  document.getElementById("time-fav-seletor").style.display = "none";
  document.getElementById("msg-time-favorito").innerHTML = "";
  document.getElementById("btn-trocar-time").style.display = "inline-flex";
}

async function salvarTimeFavorito() {
  var select = document.getElementById("select-time-favorito");
  var timeId = select.value;
  var msgEl = document.getElementById("msg-time-favorito");
  var botao = document.getElementById("btn-salvar-time");

  msgEl.innerHTML = "";

  if (!timeId) {
    msgEl.innerHTML =
      '<span style="color:#FF3B5C; font-size:0.85rem;">Selecione um time.</span>';
    return;
  }

  botao.disabled = true;
  botao.textContent = "Salvando...";

  try {
    await chamarApiAutenticada("/autenticacao/eu/time-favorito", "PATCH", {
      favorite_team_id: parseInt(timeId),
    });

    document.getElementById("time-fav-conteudo").innerHTML = "";
    document.getElementById("time-fav-conteudo").style.display = "none";
    document.getElementById("time-fav-vazio").style.display = "none";
    document.getElementById("time-fav-seletor").style.display = "none";

    document.getElementById("time-fav-carregando").style.display = "block";
    document.getElementById("time-fav-carregando").textContent =
      "Carregando...";

    await carregarTimeFavorito(parseInt(timeId));
  } catch (erro) {
    msgEl.innerHTML =
      '<span style="color:#FF3B5C; font-size:0.85rem;">Erro ao salvar. Tente novamente.</span>';
  }

  botao.disabled = false;
  botao.innerHTML = '<i class="bi bi-check-lg me-1"></i>Salvar';
}
