var URL_BASE = "http://localhost:8000/api/v1";
var CHAVE_TOKEN = "nba_token";

async function chamarApi(endpoint, metodo, corpo) {
    var url = URL_BASE + endpoint;

    var opcoes = {
        method: metodo || "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    };

    if (corpo) {
        opcoes.body = JSON.stringify(corpo);
    }

    var resposta = await fetch(url, opcoes);

    if (!resposta.ok) {
        var textoErro = "";

        try {
            var dadosErro = await resposta.json();
            textoErro = dadosErro.detail || "Erro desconhecido.";
        } catch (e) {
            textoErro = "Erro " + resposta.status + " ao acessar o servidor.";
        }

        throw new Error(textoErro);
    }

    var dados = await resposta.json();
    return dados;
}

async function chamarApiAutenticada(endpoint, metodo, corpo) {
    var token = localStorage.getItem(CHAVE_TOKEN);

    if (!token) {
        window.location.href = "/login.html?redirect=" + encodeURIComponent(window.location.pathname);
        return;
    }

    var url = URL_BASE + endpoint;

    var opcoes = {
        method: metodo || "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer " + token
        }
    };

    if (corpo) {
        opcoes.body = JSON.stringify(corpo);
    }

    var resposta = await fetch(url, opcoes);

    if (resposta.status === 401) {
        localStorage.removeItem(CHAVE_TOKEN);
        localStorage.removeItem("nba_usuario");
        window.location.href = "/login.html?sessao_expirada=1";
        return;
    }

    if (!resposta.ok) {
        var textoErro = "";

        try {
            var dadosErro = await resposta.json();
            textoErro = dadosErro.detail || "Erro desconhecido.";
        } catch (e) {
            textoErro = "Erro " + resposta.status + " ao acessar o servidor.";
        }

        throw new Error(textoErro);
    }

    var dados = await resposta.json();
    return dados;
}

async function chamarLoginForm(email, senha) {
    var url = URL_BASE + "/autenticacao/login";

    var formulario = new URLSearchParams();
    formulario.append("username", email);
    formulario.append("password", senha);

    var resposta = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        },
        body: formulario.toString()
    });

    if (!resposta.ok) {
        var textoErro = "";

        try {
            var dadosErro = await resposta.json();
            textoErro = dadosErro.detail || "E-mail ou senha inválidos.";
        } catch (e) {
            textoErro = "Erro ao conectar ao servidor.";
        }

        throw new Error(textoErro);
    }

    var dados = await resposta.json();
    return dados;
}

function construirQueryString(parametros) {
    var pares = [];

    for (var chave in parametros) {
        var valor = parametros[chave];

        if (valor === null || valor === undefined || valor === "") {
            continue;
        }

        pares.push(encodeURIComponent(chave) + "=" + encodeURIComponent(valor));
    }

    if (pares.length === 0) {
        return "";
    }

    return "?" + pares.join("&");
}

function obterParametroUrl(nome) {
    var params = new URLSearchParams(window.location.search);
    return params.get(nome);
}