var CHAVE_TOKEN = "nba_token";
var CHAVE_USUARIO = "nba_usuario";

function salvarSessao(token, usuario) {
    localStorage.setItem(CHAVE_TOKEN, token);
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(usuario));
}

function obterToken() {
    return localStorage.getItem(CHAVE_TOKEN);
}

function obterUsuario() {
    var dadosBrutos = localStorage.getItem(CHAVE_USUARIO);

    if (!dadosBrutos) {
        return null;
    }

    try {
        return JSON.parse(dadosBrutos);
    } catch (e) {
        return null;
    }
}

function estaLogado() {
    var token = obterToken();
    return token !== null && token !== "";
}

async function encerrarSessao() {
    var token = obterToken();
    if (token) {
        try {
            await chamarApiAutenticada("/autenticacao/logout", "POST");
        } catch (e) {
        }
    }

    localStorage.removeItem(CHAVE_TOKEN);
    localStorage.removeItem(CHAVE_USUARIO);

    window.location.href = "/index.html";
}

function verificarAutenticacao() {
    if (!estaLogado()) {
        var paginaAtual = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = "/login.html?redirect=" + paginaAtual;
    }
}

async function realizarLogin(email, senha, redirecionarPara) {
    var dadosToken = await chamarLoginForm(email, senha);
    var token = dadosToken.access_token;

    var dadosUsuario = await fetch(URL_BASE + "/autenticacao/eu", {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + token,
            "Accept": "application/json"
        }
    });

    if (!dadosUsuario.ok) {
        throw new Error("Não foi possível carregar os dados do usuário.");
    }

    var usuario = await dadosUsuario.json();
    salvarSessao(token, usuario);
    if (redirecionarPara && redirecionarPara !== "" && redirecionarPara !== "null") {
        window.location.href = decodeURIComponent(redirecionarPara);
    } else {
        window.location.href = "/index.html";
    }
}

function obterInicialNome(nomeCompleto) {
    if (!nomeCompleto) {
        return "U";
    }

    var partes = nomeCompleto.trim().split(" ");

    if (partes.length === 1) {
        return partes[0].charAt(0).toUpperCase();
    }

    var primeiraLetra = partes[0].charAt(0).toUpperCase();
    var ultimaLetra = partes[partes.length - 1].charAt(0).toUpperCase();
    return primeiraLetra + ultimaLetra;
}

function obterPrimeiroNome(nomeCompleto) {
    if (!nomeCompleto) {
        return "Usuário";
    }

    return nomeCompleto.trim().split(" ")[0];
}