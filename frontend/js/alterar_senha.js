verificarAutenticacao();
 
document.addEventListener("DOMContentLoaded", function() {
    inicializarPagina();
});
 
async function alterarSenha() {
    var senhaAtual = document.getElementById("input-senha-atual").value.trim();
    var novaSenha = document.getElementById("input-nova-senha").value.trim();
    var confirmarSenha = document.getElementById("input-confirmar-senha").value.trim();
    var msgEl = document.getElementById("msg-senha");
    var btnEl = document.getElementById("btn-alterar-senha");
 
    msgEl.style.display = "none";
    msgEl.className = "";
    msgEl.textContent = "";
 
    if (!senhaAtual || !novaSenha || !confirmarSenha) {
        msgEl.textContent = "Preencha todos os campos.";
        msgEl.className = "alerta-erro";
        msgEl.style.display = "block";
        return;
    }
 
    if (novaSenha.length < 6) {
        msgEl.textContent = "A nova senha deve ter no mínimo 6 caracteres.";
        msgEl.className = "alerta-erro";
        msgEl.style.display = "block";
        return;
    }
 
    if (novaSenha !== confirmarSenha) {
        msgEl.textContent = "A nova senha e a confirmação não coincidem.";
        msgEl.className = "alerta-erro";
        msgEl.style.display = "block";
        return;
    }
 
    btnEl.disabled = true;
    btnEl.textContent = "Salvando...";
 
    try {
        await chamarApiAutenticada("/autenticacao/eu/senha", "PATCH", {
            senha_atual: senhaAtual,
            nova_senha: novaSenha
        });
 
        document.getElementById("input-senha-atual").value = "";
        document.getElementById("input-nova-senha").value = "";
        document.getElementById("input-confirmar-senha").value = "";
 
        msgEl.textContent = "Senha alterada com sucesso.";
        msgEl.className = "alerta-sucesso";
        msgEl.style.display = "block";
 
    } catch (erro) {
        var mensagem = "Erro ao alterar senha.";
        if (erro && erro.detail) {
            mensagem = erro.detail;
        }
        msgEl.textContent = mensagem;
        msgEl.className = "alerta-erro";
        msgEl.style.display = "block";
    }
 
    btnEl.disabled = false;
    btnEl.innerHTML = '<i class="bi bi-lock-fill me-1"></i> Salvar Nova Senha';
}