var token = obterParametroUrl("token");

document.addEventListener("DOMContentLoaded", function () {
  if (!token) {
    document.getElementById("estado-token-invalido").style.display = "block";
    return;
  }

  document.getElementById("estado-formulario").style.display = "block";
});

async function redefinirSenha() {
  var novaSenha = document.getElementById("campo-nova-senha").value.trim();
  var confirmarSenha = document
    .getElementById("campo-confirmar-senha")
    .value.trim();
  var alertaEl = document.getElementById("area-alerta");
  var botao = document.getElementById("btn-redefinir");

  document.getElementById("erro-nova-senha").textContent = "";
  document.getElementById("erro-confirmar-senha").textContent = "";
  document.getElementById("campo-nova-senha").classList.remove("erro");
  document.getElementById("campo-confirmar-senha").classList.remove("erro");
  alertaEl.innerHTML = "";

  var tudo_ok = true;

  if (novaSenha === "") {
    document.getElementById("erro-nova-senha").textContent =
      "Informe a nova senha.";
    document.getElementById("campo-nova-senha").classList.add("erro");
    tudo_ok = false;
  } else if (novaSenha.length < 6) {
    document.getElementById("erro-nova-senha").textContent =
      "A senha deve ter no mínimo 6 caracteres.";
    document.getElementById("campo-nova-senha").classList.add("erro");
    tudo_ok = false;
  }

  if (confirmarSenha === "") {
    document.getElementById("erro-confirmar-senha").textContent =
      "Confirme a nova senha.";
    document.getElementById("campo-confirmar-senha").classList.add("erro");
    tudo_ok = false;
  } else if (novaSenha !== confirmarSenha) {
    document.getElementById("erro-confirmar-senha").textContent =
      "As senhas não coincidem.";
    document.getElementById("campo-confirmar-senha").classList.add("erro");
    tudo_ok = false;
  }

  if (!tudo_ok) {
    return;
  }

  botao.disabled = true;
  botao.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Salvando...';

  try {
    await chamarApi("/autenticacao/redefinir-senha", "POST", {
      token: token,
      nova_senha: novaSenha,
    });

    document.getElementById("estado-formulario").style.display = "none";
    document.getElementById("estado-sucesso").style.display = "block";
  } catch (erro) {
    var mensagem = "Erro ao redefinir senha. Tente novamente.";

    if (erro && erro.detail) {
      mensagem = erro.detail;
    }

    alertaEl.innerHTML =
      '<div class="alerta-nba erro mb-3">' +
      '<i class="bi bi-exclamation-triangle-fill"></i>' +
      "<span>" +
      mensagem +
      "</span>" +
      "</div>";

    botao.disabled = false;
    botao.innerHTML = '<i class="bi bi-lock-fill me-2"></i>Salvar nova senha';
  }
}
