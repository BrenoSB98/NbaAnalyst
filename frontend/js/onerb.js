verificarAutenticacao();
var historico = [];
var aguardando = false;

document.addEventListener("DOMContentLoaded", function() {
    renderizarMenu();
    document.getElementById("campo-pergunta").focus();
    carregarLimite();
});

function verificarEnter(evento) {
    if (evento.key === "Enter" && !evento.shiftKey) {
        evento.preventDefault();
        enviarMensagem();
    }
}

function ajustarAltura(elemento) {
    elemento.style.height = "auto";
    elemento.style.height = Math.min(elemento.scrollHeight, 120) + "px";
}

function usarExemplo(elemento) {
    var campo = document.getElementById("campo-pergunta");
    campo.value = elemento.textContent.trim();
    campo.focus();
    ajustarAltura(campo);
}

async function enviarMensagem() {
    if (aguardando) {
        return;
    }

    var campo = document.getElementById("campo-pergunta");
    var pergunta = campo.value.trim();

    if (pergunta === "") {
        return;
    }

    adicionarMensagemUsuario(pergunta);
    historico.push({ papel: "usuario", conteudo: pergunta });

    campo.value = "";
    campo.style.height = "auto";

    aguardando = true;
    document.getElementById("btn-enviar").disabled = true;
    var idDigitando = mostrarDigitando();

    try {
        var corpo = {
            pergunta: pergunta,
            historico: historico.slice(0, -1)
        };

        var resposta = await chamarApiAutenticada("/chat/mensagem", "POST", corpo);
        removerDigitando(idDigitando);
        adicionarMensagemAssistente(resposta.resposta);
        historico.push({ papel: "oraculo", conteudo: resposta.resposta });
        carregarLimite();

    } catch (erro) {
        removerDigitando(idDigitando);
        if (erro.message && erro.message.indexOf("429") !== -1) {
            adicionarMensagemAssistente("Você atingiu o limite diário de perguntas. Volte amanhã! 🏀");
            document.getElementById("btn-enviar").disabled = true;
        } else {
            adicionarMensagemAssistente("Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente.");
        }
        carregarLimite();
    }

    aguardando = false;
    document.getElementById("btn-enviar").disabled = false;
    campo.focus();
}

function adicionarMensagemUsuario(texto) {
    var container = document.getElementById("chat-mensagens");

    var div = document.createElement("div");
    div.className = "msg-usuario";
    div.innerHTML = '<div class="msg-balao">' + escaparHtml(texto) + '</div>';

    container.appendChild(div);
    rolarParaBaixo();
}

function adicionarMensagemAssistente(texto) {
    var container = document.getElementById("chat-mensagens");

    var div = document.createElement("div");
    div.className = "msg-assistente";
    div.innerHTML = ''
        + '<div class="msg-avatar"><i class="bi bi-dribbble"></i></div>'
        + '<div class="msg-balao">' + escaparHtml(texto) + '</div>';

    container.appendChild(div);
    rolarParaBaixo();
}

function mostrarDigitando() {
    var container = document.getElementById("chat-mensagens");
    var id = "digitando-" + Date.now();

    var div = document.createElement("div");
    div.className = "msg-digitando";
    div.id = id;
    div.innerHTML = ''
        + '<div class="msg-avatar"><i class="bi bi-dribbble"></i></div>'
        + '<div class="balao-digitando">'
        +   '<div class="ponto"></div>'
        +   '<div class="ponto"></div>'
        +   '<div class="ponto"></div>'
        + '</div>';

    container.appendChild(div);
    rolarParaBaixo();

    return id;
}

function removerDigitando(id) {
    var elemento = document.getElementById(id);
    if (elemento) {
        elemento.remove();
    }
}

function rolarParaBaixo() {
    var container = document.getElementById("chat-mensagens");
    container.scrollTop = container.scrollHeight;
}

function limparConversa() {
    historico = [];

    var container = document.getElementById("chat-mensagens");
    var mensagens = container.querySelectorAll(".msg-assistente, .msg-usuario, .msg-digitando");
    for (var i = 0; i < mensagens.length; i++) {
        if (mensagens[i].id !== "msg-boas-vindas") {
            mensagens[i].remove();
        }
    }
    document.getElementById("campo-pergunta").focus();
}

async function carregarLimite() {
    try {
        var dados = await chamarApiAutenticada("/chat/limite");
        var texto = dados.usadas_hoje + " / " + dados.limite_diario + " perguntas hoje";
        document.getElementById("contador-texto").textContent = texto;

        if (dados.restantes_hoje === 0) {
            document.getElementById("btn-enviar").disabled = true;
        }
    } catch (erro) {
        document.getElementById("contador-texto").textContent = "— / — perguntas hoje";
    }
}

function escaparHtml(texto) {
    var mapa = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    };
    return texto.replace(/[&<>"']/g, function(c) { return mapa[c]; }).replace(/\n/g, "<br>");
}