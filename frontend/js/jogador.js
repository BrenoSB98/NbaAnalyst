var jogadorId = obterParametroUrl("id");
 
var POSICOES_PT = {
    "PG": "Armador",
    "SG": "Ala-armador",
    "SF": "Ala",
    "PF": "Ala-pivô",
    "C": "Pivô",
    "G": "Armador/Ala-armador",
    "F": "Ala/Ala-pivô",
    "GF": "Ala-armador/Ala",
    "FC": "Ala-pivô/Pivô"
};
 
function traduzirPosicao(abreviacao) {
    if (!abreviacao) {
        return "";
    }
    var pos = POSICOES_PT[abreviacao.toUpperCase()];
    if (pos) {
        return pos;
    }
    return abreviacao;
}
 
function calcularIdade(dataNascimentoStr) {
    if (!dataNascimentoStr) {
        return null;
    }
    var hoje = new Date();
    var nascimento = new Date(dataNascimentoStr);
    var idade = hoje.getFullYear() - nascimento.getFullYear();
    var mesAtual = hoje.getMonth();
    var diaAtual = hoje.getDate();
    var mesNasc = nascimento.getMonth();
    var diaNasc = nascimento.getDate();
 
    if (mesAtual < mesNasc) {
        idade = idade - 1;
    } else if (mesAtual === mesNasc && diaAtual < diaNasc) {
        idade = idade - 1;
    }
    return idade;
}
 
document.addEventListener("DOMContentLoaded", function() {
    inicializarPagina();
 
    if (!jogadorId) {
        document.getElementById("pagina-carregando").style.display = "none";
        document.getElementById("pagina-erro").style.display = "block";
        return;
    }
 
    carregarJogador();
});
 
 
async function carregarJogador() {
    try {
        var dados = await chamarApi("/jogadores/" + jogadorId);
 
        var nomeCompleto = dados.nome + " " + dados.sobrenome;
        document.title = "NbaAnalyst — " + nomeCompleto;
 
        var iniciais = dados.nome.charAt(0) + dados.sobrenome.charAt(0);
        document.getElementById("jogador-avatar").textContent = iniciais.toUpperCase();
        document.getElementById("jogador-nome").textContent = nomeCompleto;
        var timeAtualObj = null;
        if (dados.historico_times && dados.historico_times.length > 0) {
            timeAtualObj = dados.historico_times[dados.historico_times.length - 1];
        }
 
        var posicaoAtual = "";
        if (timeAtualObj) {
            posicaoAtual = timeAtualObj.posicao || "";
        }
        var posicaoPT = traduzirPosicao(posicaoAtual);
        if (posicaoPT) {
            document.getElementById("jogador-posicao-pt").textContent = posicaoPT;
        }
 
        var infoHtml = "";
        if (timeAtualObj) {
            infoHtml = infoHtml
                + '<span>'
                + '<i class="bi bi-shield-fill"></i>'
                + '<a href="time.html?id=' + timeAtualObj.time_id + '" style="color:#555570;text-decoration:none;">' + timeAtualObj.nome_time + '</a>'
                + '</span>';
        }
        if (dados.inicio_nba) {
            infoHtml = infoHtml + '<span><i class="bi bi-calendar2"></i>NBA desde ' + dados.inicio_nba + '</span>';
        }
        if (dados.pais_nascimento) {
            infoHtml = infoHtml + '<span><i class="bi bi-globe2"></i>' + dados.pais_nascimento + '</span>';
        }
        document.getElementById("jogador-info-basica").innerHTML = infoHtml;
        document.getElementById("btn-perfil-avancado").href = "jogador_avancado.html?id=" + jogadorId;
 
        renderizarDadosFisicos(dados);
        renderizarHistorico(dados.historico_times || []);
 
        document.getElementById("pagina-carregando").style.display = "none";
        document.getElementById("pagina-conteudo").style.display = "block";
        carregarMedias();
 
    } catch (erro) {
        document.getElementById("pagina-carregando").style.display = "none";
        document.getElementById("pagina-erro").style.display = "block";
    }
}
 
 
function renderizarDadosFisicos(dados) {
    var container = document.getElementById("dados-fisicos");
    var itens = [];
 
    if (dados.altura_metros) {
        itens.push({ icone: "bi-arrow-up", valor: dados.altura_metros.toFixed(2) + " m", rotulo: "Altura" });
    }
    if (dados.peso_kg) {
        itens.push({ icone: "bi-speedometer", valor: dados.peso_kg.toFixed(1) + " kg", rotulo: "Peso" });
    }
 
    if (dados.data_nascimento) {
        var idade = calcularIdade(dados.data_nascimento);
        if (idade !== null) {
            itens.push({ icone: "bi-person-fill", valor: idade + " anos", rotulo: "Idade" });
        }
    }
 
    if (dados.pais_nascimento) {
        itens.push({ icone: "bi-globe2", valor: dados.pais_nascimento, rotulo: "País" });
    }
    if (dados.faculdade) {
        itens.push({ icone: "bi-mortarboard", valor: dados.faculdade, rotulo: "Faculdade" });
    }
    if (dados.inicio_nba) {
        itens.push({ icone: "bi-trophy", valor: dados.inicio_nba, rotulo: "Entrada na NBA" });
    }
 
    if (itens.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="texto-suave" style="font-size:0.88rem;">Dados físicos não disponíveis.</p></div>';
        return;
    }
 
    var html = "";
    for (var i = 0; i < itens.length; i++) {
        var item = itens[i];
        html = html
            + '<div class="col-6 col-sm-4 col-md-3 col-lg-2">'
            +   '<div class="card-dado">'
            +     '<i class="bi ' + item.icone + ' dado-icone"></i>'
            +     '<div>'
            +       '<div class="dado-valor">' + item.valor + '</div>'
            +       '<div class="dado-rotulo">' + item.rotulo + '</div>'
            +     '</div>'
            +   '</div>'
            + '</div>';
    }
    container.innerHTML = html;
}
 
 
function renderizarHistorico(historico) {
    document.getElementById("historico-carregando").style.display = "none";
 
    if (historico.length === 0) {
        document.getElementById("historico-vazio").style.display = "block";
        return;
    }
 
    var html = "";
    for (var i = 0; i < historico.length; i++) {
        var item = historico[i];
        var camisa = (item.camisa !== null && item.camisa !== undefined) ? "#" + item.camisa : "";
        var posicao = item.posicao ? traduzirPosicao(item.posicao) : "";
        var periodoHtml = "";
        if (item.mes_ingresso) {
            periodoHtml = '<div class="time-temporada">' + item.mes_ingresso + '</div>';
        } else {
            periodoHtml = '<div class="time-temporada">' + item.temporada + '</div>';
        }
 
        html = html
            + '<div class="linha-time">'
            +   periodoHtml
            +   '<a href="time.html?id=' + item.time_id + '" class="time-nome-link">' + item.nome_time + '</a>'
            +   '<div class="time-posicao">' + posicao + '</div>'
            +   '<div class="time-camisa">' + camisa + '</div>'
            + '</div>';
    }
 
    document.getElementById("historico-lista").innerHTML = html;
    document.getElementById("historico-lista").style.display = "block";
}
 
 
async function carregarMedias() {
    try {
        var anos = [2025, 2024, 2023, 2022, 2021];
        var dados = null;
 
        for (var ai = 0; ai < anos.length; ai++) {
            var resp = await chamarApi("/jogadores/" + jogadorId + "/estatisticas/temporada?temporada=" + anos[ai]);
            if (!resp.mensagem && resp.medias) {
                dados = resp;
                break;
            }
        }
 
        document.getElementById("medias-carregando").style.display = "none";
 
        if (!dados || !dados.medias) {
            document.getElementById("medias-sem-dados").style.display = "block";
            return;
        }
 
        document.getElementById("medias-jogos-texto").textContent =
            "Temporada " + dados.temporada + " — " + dados.jogos_disputados + " jogos";
 
        var medias = dados.medias;
        var itens = [
            { valor: medias.pontos,rotulo: "PTS", cor: "#F75C03" },
            { valor: medias.assistencias, rotulo: "AST", cor: "#3B9EFF" },
            { valor: medias.rebotes,rotulo: "REB", cor: "#00C896" },
            { valor: medias.roubos, rotulo: "STL", cor: "#FFD600" },
            { valor: medias.bloqueios,rotulo: "BLK", cor: "#555570" },
            { valor: medias.plus_minus, rotulo: "+/-", cor: "#1A1A2E" }
        ];
 
        var html = "";
        for (var i = 0; i < itens.length; i++) {
            var item = itens[i];
            var valorExibido = (item.valor !== null && item.valor !== undefined) ? item.valor : "—";
            html = html
                + '<div class="col-6 col-sm-4 col-md-2">'
                +   '<div class="card-media">'
                +     '<div class="media-valor" style="color:' + item.cor + ';">' + valorExibido + '</div>'
                +     '<div class="media-rotulo">' + item.rotulo + '</div>'
                +   '</div>'
                + '</div>';
        }
 
        document.getElementById("medias-grid").innerHTML = html;
        document.getElementById("medias-dados").style.display = "block";
 
    } catch (erro) {
        document.getElementById("medias-carregando").style.display = "none";
        document.getElementById("medias-sem-dados").style.display = "block";
    }
}