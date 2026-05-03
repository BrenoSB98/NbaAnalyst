document.addEventListener("DOMContentLoaded", function() {
    if (estaLogado()) {
        window.location.href = "/index.html";
    }
});

function validarFormulario() {
    var tudo_ok = true;

    var nome = document.getElementById("campo-nome").value.trim();
    var email = document.getElementById("campo-email").value.trim();
    var nascimento = document.getElementById("campo-nascimento").value;
    var senha = document.getElementById("campo-senha").value;
    var confirmarSenha = document.getElementById("campo-confirmar-senha").value;

    document.getElementById("erro-nome").textContent = "";
    document.getElementById("erro-email").textContent = "";
    document.getElementById("erro-nascimento").textContent = "";
    document.getElementById("erro-senha").textContent = "";
    document.getElementById("erro-confirmar-senha").textContent = "";

    document.getElementById("campo-nome").classList.remove("erro");
    document.getElementById("campo-email").classList.remove("erro");
    document.getElementById("campo-nascimento").classList.remove("erro");
    document.getElementById("campo-senha").classList.remove("erro");
    document.getElementById("campo-confirmar-senha").classList.remove("erro");

    if (nome === "") {
        document.getElementById("erro-nome").textContent = "Informe seu nome completo.";
        document.getElementById("campo-nome").classList.add("erro");
        tudo_ok = false;
    }

    if (email === "") {
        document.getElementById("erro-email").textContent = "Informe seu e-mail.";
        document.getElementById("campo-email").classList.add("erro");
        tudo_ok = false;
    }

    if (nascimento === "") {
        document.getElementById("erro-nascimento").textContent = "Informe sua data de nascimento.";
        document.getElementById("campo-nascimento").classList.add("erro");
        tudo_ok = false;
    }

    if (senha === "") {
        document.getElementById("erro-senha").textContent = "Informe uma senha.";
        document.getElementById("campo-senha").classList.add("erro");
        tudo_ok = false;
    } else if (senha.length < 6) {
        document.getElementById("erro-senha").textContent = "A senha precisa ter no mínimo 6 caracteres.";
        document.getElementById("campo-senha").classList.add("erro");
        tudo_ok = false;
    }

    if (confirmarSenha === "") {
        document.getElementById("erro-confirmar-senha").textContent = "Confirme sua senha.";
        document.getElementById("campo-confirmar-senha").classList.add("erro");
        tudo_ok = false;
    } else if (senha !== confirmarSenha) {
        document.getElementById("erro-confirmar-senha").textContent = "As senhas não coincidem.";
        document.getElementById("campo-confirmar-senha").classList.add("erro");
        tudo_ok = false;
    }

    return tudo_ok;
}

async function fazerCadastro() {
    if (!validarFormulario()) {
        return;
    }

    var nome = document.getElementById("campo-nome").value.trim();
    var email = document.getElementById("campo-email").value.trim();
    var nascimento = document.getElementById("campo-nascimento").value;
    var senha = document.getElementById("campo-senha").value;
    var botao = document.getElementById("btn-cadastrar");

    botao.disabled = true;
    botao.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Criando conta...';

    document.getElementById("area-alerta").innerHTML = "";

    var dadosCadastro = {
        full_name: nome,
        email: email,
        birth_date: nascimento,
        password: senha
    };

    try {
        await chamarApi("/autenticacao/registrar", "POST", dadosCadastro);

        document.getElementById("area-alerta").innerHTML =
            '<div class="alerta-nba sucesso mb-3">'
            + '<i class="bi bi-envelope-check-fill"></i>'
            + '<span>Conta criada! Enviamos um e-mail para <strong>' + email + '</strong>. Clique no link para ativar sua conta.</span>'
            + '</div>';

        botao.disabled = true;
        botao.innerHTML = '<i class="bi bi-check-circle me-2"></i>Cadastro realizado';

    } catch (erro) {
        document.getElementById("area-alerta").innerHTML =
            '<div class="alerta-nba erro mb-3">'
            + '<i class="bi bi-exclamation-triangle-fill"></i>'
            + '<span>' + erro.message + '</span>'
            + '</div>';

        botao.disabled = false;
        botao.innerHTML = '<i class="bi bi-person-plus me-2"></i>Criar Conta';
    }
}