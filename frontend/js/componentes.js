function renderizarMenu() {
    var elementoNavbar = document.getElementById("navbar-principal");

    if (!elementoNavbar) {
        return;
    }

    var usuarioLogado = estaLogado();
    var dadosUsuario = obterUsuario();
    var paginaAtual = window.location.pathname;

    function classeLinkAtivo(caminhos) {
        for (var i = 0; i < caminhos.length; i++) {
            if (paginaAtual.indexOf(caminhos[i]) !== -1) {
                return "ativo";
            }
        }
        return "";
    }

    var linksLogados = "";
    if (usuarioLogado) {
        linksLogados = `
            <li class="nav-item">
                <a class="nav-link ${classeLinkAtivo(["predicoes"])} d-flex align-items-center gap-2" href="/predicoes.html">
                    <i class="bi bi-graph-up-arrow"></i> Palpites
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link ${classeLinkAtivo(["confrontos"])} d-flex align-items-center gap-2" href="/confrontos.html">
                    <i class="bi bi-bar-chart-steps"></i> Confrontos
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link ${classeLinkAtivo(["onerb"])} d-flex align-items-center gap-2" href="/onerb.html">
                    <i class="bi bi-robot"></i> Onerb IA
                </a>
            </li>
        `;
    }

    var blocoAuth = "";
    if (usuarioLogado && dadosUsuario) {
        var iniciais = obterInicialNome(dadosUsuario.full_name);
        var primeiroNome = obterPrimeiroNome(dadosUsuario.full_name);

        blocoAuth = `
            <div class="dropdown">
                <button class="btn d-flex align-items-center gap-2 btn-nba-ghost btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <div class="avatar-usuario">${iniciais}</div>
                    <span class="d-none d-lg-inline texto-suave" style="font-size:0.85rem; font-weight:600;">${primeiroNome}</span>
                </button>
                <ul class="dropdown-menu dropdown-menu-end">
                    <li>
                        <a class="dropdown-item d-flex align-items-center gap-2" href="/perfil.html">
                            <i class="bi bi-person-circle texto-laranja"></i> Meu Perfil
                        </a>
                    </li>
                    <li><hr class="dropdown-divider"></li>
                    <li>
                        <button class="dropdown-item d-flex align-items-center gap-2 texto-perigo" onclick="encerrarSessao()">
                            <i class="bi bi-box-arrow-right"></i> Sair
                        </button>
                    </li>
                </ul>
            </div>
        `;
    } else {
        blocoAuth = `
            <a href="/login.html" class="btn-nba-ghost btn-nba btn-sm d-flex align-items-center gap-2">
                <i class="bi bi-box-arrow-in-right"></i> Entrar
            </a>
            <a href="/cadastro.html" class="btn-nba btn-sm d-flex align-items-center gap-2">
                <i class="bi bi-person-plus"></i> Cadastrar
            </a>
        `;
    }

    var htmlNavbar = `
        <div class="container-fluid px-3 px-lg-4">

            <a class="navbar-brand" href="/index.html">
                <i class="bi bi-dribbble icone-logo"></i>
                NBA Analytics
            </a>

            <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse"
                data-bs-target="#menuColapsavel" aria-controls="menuColapsavel" aria-expanded="false" aria-label="Abrir menu">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="menuColapsavel">

                <ul class="navbar-nav me-auto ms-3 d-flex gap-1">
                    <li class="nav-item">
                        <a class="nav-link ${classeLinkAtivo(["times", "time.html", "time-avancado"])} d-flex align-items-center gap-2" href="/times.html">
                            <i class="bi bi-shield-fill"></i> Times
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link ${classeLinkAtivo(["estatisticas"])} d-flex align-items-center gap-2" href="/estatisticas.html">
                            <i class="bi bi-bar-chart-fill"></i> Estatísticas
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link ${classeLinkAtivo(["classificacao"])} d-flex align-items-center gap-2" href="/classificacao.html">
                            <i class="bi bi-list-ol"></i> Classificação
                        </a>
                    </li>
                    ${linksLogados}
                </ul>

                <div class="d-flex align-items-center gap-2 mt-2 mt-lg-0">
                    ${blocoAuth}
                </div>

            </div>
        </div>
    `;

    elementoNavbar.innerHTML = htmlNavbar;
    elementoNavbar.classList.add("navbar", "navbar-expand-lg", "fixed-top");
}

function renderizarRodape() {
    var elementoRodape = document.getElementById("rodape-principal");

    if (!elementoRodape) {
        return;
    }

    var anoAtual = new Date().getFullYear();

    var htmlRodape = `
        <div class="container">
            <div class="row gy-4">
                <div class="col-12 col-md-4">
                    <div class="rodape-logo">
                        <i class="bi bi-dribbble icone-logo"></i>
                        NBA Analytics
                    </div>
                    <p class="rodape-tagline">Quem tem dados, domina o jogo.</p>
                </div>
                <div class="col-6 col-md-2">
                    <p class="rodape-titulo-coluna">Explorar</p>
                    <a class="rodape-link" href="/times.html">Times</a>
                    <a class="rodape-link" href="/estatisticas.html">Estatísticas</a>
                    <a class="rodape-link" href="/classificacao.html">Classificação</a>
                    <a class="rodape-link" href="/predicoes.html">Palpites</a>
                    <a class="rodape-link" href="/confrontos.html">Confrontos</a>
                </div>
                <div class="col-6 col-md-2">
                    <p class="rodape-titulo-coluna">Conta</p>
                    <a class="rodape-link" href="/login.html">Entrar</a>
                    <a class="rodape-link" href="/cadastro.html">Cadastrar</a>
                    <a class="rodape-link" href="/perfil.html">Meu Perfil</a>
                    <a class="rodape-link" href="/onerb.html">Onerb IA</a>
                </div>
            </div>

            <div class="rodape-direitos">
                <span class="texto-fraco">
                    &copy; ${anoAtual} NBA Analytics: &mdash; Análise de dados para fãs e apostadores
                </span>
            </div>
        </div>
    `;
    elementoRodape.innerHTML = htmlRodape;
}

function exibirAlerta(idElemento, mensagem, tipo) {
    var elemento = document.getElementById(idElemento);

    if (!elemento) {
        return;
    }

    var tipoFinal = tipo || "erro";

    var icone = "bi-exclamation-triangle-fill";
    if (tipoFinal === "sucesso") {
        icone = "bi-check-circle-fill";
    } else if (tipoFinal === "aviso") {
        icone = "bi-exclamation-circle-fill";
    }

    elemento.innerHTML = `
        <div class="alerta-nba ${tipoFinal}">
            <i class="bi ${icone}"></i>
            <span>${mensagem}</span>
        </div>
    `;

    setTimeout(function() {
        elemento.innerHTML = "";
    }, 5000);
}

function exibirSpinner(idElemento, mensagem) {
    var elemento = document.getElementById(idElemento);

    if (!elemento) {
        return;
    }

    var textoBaixo = mensagem || "Carregando...";

    elemento.innerHTML = `
        <div class="spinner-nba">
            <div class="bola-animada"></div>
            <span>${textoBaixo}</span>
        </div>
    `;
}

function exibirEstadoVazio(idElemento, titulo, descricao, icone) {
    var elemento = document.getElementById(idElemento);

    if (!elemento) {
        return;
    }

    var iconeUsado = icone || "bi-dribbble";
    var descricaoHtml = descricao ? `<p class="desc-vazio">${descricao}</p>` : "";

    elemento.innerHTML = `
        <div class="estado-vazio">
            <i class="bi ${iconeUsado} icone-vazio"></i>
            <p class="titulo-vazio">${titulo}</p>
            ${descricaoHtml}
        </div>
    `;
}

function inicializarPagina() {
    renderizarMenu();
    renderizarRodape();
}