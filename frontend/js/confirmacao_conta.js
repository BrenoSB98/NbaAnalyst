var token = obterParametroUrl("token");
 
document.addEventListener("DOMContentLoaded", function() {
    if (!token) {
        mostrarErro("Nenhum token de confirmação encontrado na URL.");
        return;
    }
 
    confirmarEmail();
});
 
async function confirmarEmail() {
    try {
        await chamarApi("/autenticacao/confirmacao_conta/" + token, "GET");
 
        document.getElementById("estado-carregando").style.display = "none";
        document.getElementById("estado-sucesso").style.display = "block";
 
    } catch (erro) {
        var mensagem = "O link de confirmação é inválido ou já foi utilizado.";
 
        if (erro && erro.detail) {
            mensagem = erro.detail;
        }
 
        mostrarErro(mensagem);
    }
}
 
function mostrarErro(mensagem) {
    document.getElementById("estado-carregando").style.display = "none";
    document.getElementById("msg-erro").textContent = mensagem;
    document.getElementById("estado-erro").style.display = "block";
}