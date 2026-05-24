document.addEventListener("DOMContentLoaded", function () {
  if (estaLogado()) {
    window.location.href = "/index.html";
    return;
  }

  var sessaoExpirada = obterParametroUrl("sessao_expirada");
  if (sessaoExpirada === "1") {
    document.getElementById("area-sessao-expirada").innerHTML =
      '<div class="alerta-nba aviso mb-3">' +
      '<i class="bi bi-exclamation-circle-fill"></i>' +
      "<span>Sua sessão expirou. Faça login novamente.</span>" +
      "</div>";
  }

  document
    .getElementById("campo-senha")
    .addEventListener("keydown", function (evento) {
      if (evento.key === "Enter") {
        fazerLogin();
      }
    });
});

function validarFormulario() {
  var tudo_ok = true;

  var email = document.getElementById("campo-email").value.trim();
  var senha = document.getElementById("campo-senha").value;

  document.getElementById("erro-email").textContent = "";
  document.getElementById("erro-senha").textContent = "";
  document.getElementById("campo-email").classList.remove("erro");
  document.getElementById("campo-senha").classList.remove("erro");

  if (email === "") {
    document.getElementById("erro-email").textContent = "Informe o seu e-mail.";
    document.getElementById("campo-email").classList.add("erro");
    tudo_ok = false;
  }

  if (senha === "") {
    document.getElementById("erro-senha").textContent = "Informe a sua senha.";
    document.getElementById("campo-senha").classList.add("erro");
    tudo_ok = false;
  }

  return tudo_ok;
}

function mostrarPainelRecuperacao() {
  document.getElementById("area-alerta").innerHTML = "";
  document.getElementById("area-sessao-expirada").innerHTML = "";
  document.getElementById("painel-login").style.display = "none";
  document.getElementById("painel-recuperacao").style.display = "block";
  document.getElementById("campo-email-recuperacao").focus();
}

function mostrarPainelLogin() {
  document.getElementById("painel-recuperacao").style.display = "none";
  document.getElementById("area-alerta-recuperacao").innerHTML = "";
  document.getElementById("erro-email-recuperacao").textContent = "";
  document.getElementById("campo-email-recuperacao").value = "";
  document.getElementById("painel-login").style.display = "block";
}

async function solicitarReset() {
  var email = document.getElementById("campo-email-recuperacao").value.trim();
  var erroEl = document.getElementById("erro-email-recuperacao");
  var alertaEl = document.getElementById("area-alerta-recuperacao");
  var botao = document.getElementById("btn-recuperar");

  erroEl.textContent = "";
  alertaEl.innerHTML = "";

  if (email === "") {
    erroEl.textContent = "Informe o seu e-mail.";
    document.getElementById("campo-email-recuperacao").classList.add("erro");
    return;
  }

  document.getElementById("campo-email-recuperacao").classList.remove("erro");
  botao.disabled = true;
  botao.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Enviando...';

  try {
    await chamarApi("/autenticacao/solicitar-reset-senha", "POST", {
      email: email,
    });

    alertaEl.innerHTML =
      '<div class="alerta-nba sucesso mb-3">' +
      '<i class="bi bi-envelope-check-fill"></i>' +
      "<span>Se o e-mail estiver cadastrado, você receberá as instruções em breve. Verifique sua caixa de entrada.</span>" +
      "</div>";

    botao.disabled = true;
    botao.innerHTML = '<i class="bi bi-check-circle me-2"></i>E-mail enviado';
  } catch (erro) {
    alertaEl.innerHTML =
      '<div class="alerta-nba erro mb-3">' +
      '<i class="bi bi-exclamation-triangle-fill"></i>' +
      "<span>Erro ao processar a solicitação. Tente novamente.</span>" +
      "</div>";

    botao.disabled = false;
    botao.innerHTML =
      '<i class="bi bi-envelope me-2"></i>Enviar link de redefinição';
  }
}

async function fazerLogin() {
  if (!validarFormulario()) {
    return;
  }

  var email = document.getElementById("campo-email").value.trim();
  var senha = document.getElementById("campo-senha").value;
  var botao = document.getElementById("btn-entrar");

  botao.disabled = true;
  botao.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Entrando...';

  document.getElementById("area-alerta").innerHTML = "";

  try {
    var redirect = obterParametroUrl("redirect");
    await realizarLogin(email, senha, redirect);
  } catch (erro) {
    document.getElementById("area-alerta").innerHTML =
      '<div class="alerta-nba erro mb-3">' +
      '<i class="bi bi-exclamation-triangle-fill"></i>' +
      "<span>" +
      erro.message +
      "</span>" +
      "</div>";

    botao.disabled = false;
    botao.innerHTML = '<i class="bi bi-box-arrow-in-right me-2"></i>Entrar';
  }
}
