var STATS_MENOR_MELHOR = ["turnovers", "pontos_sofridos"];

var STATS_EXIBIDAS = [
    { campo: "pontos_feitos", rotulo: "Pontos Feitos" },
    { campo: "pontos_sofridos", rotulo: "Pontos Sofridos" },
    { campo: "rebotes", rotulo: "Rebotes" },
    { campo: "assistencias", rotulo: "Assistências" },
    { campo: "roubos", rotulo: "Roubos" },
    { campo: "bloqueios", rotulo: "Bloqueios" },
    { campo: "turnovers", rotulo: "Turnovers" },
    { campo: "plus_minus", rotulo: "+/-" },
    { campo: "fg_pct", rotulo: "FG%" },
    { campo: "three_pct", rotulo: "3P%" },
    { campo: "ft_pct", rotulo: "FT%" }
];

document.addEventListener("DOMContentLoaded", function() {
    inicializarPagina();
    carregarTimes();
});

async function carregarTimes() {
    try {
        var dados = await chamarApi("/times?nba_franchise=true&page_size=50");
        var times = dados.times || [];

        times.sort(function(a, b) {
            if (a.nome < b.nome) {
                return -1;
            }
            if (a.nome > b.nome) {
                return 1;
            }
            return 0;
        });

        var selectCasa = document.getElementById("select-time-casa");
        var selectFora = document.getElementById("select-time-fora");

        for (var i = 0; i < times.length; i++) {
            var time = times[i];

            var opcaoCasa = document.createElement("option");
            opcaoCasa.value = time.id;
            opcaoCasa.textContent = time.nome;

            var opcaoFora = document.createElement("option");
            opcaoFora.value = time.id;
            opcaoFora.textContent = time.nome;

            selectCasa.appendChild(opcaoCasa);
            selectFora.appendChild(opcaoFora);
        }
    } catch (erro) {
        console.warn("Erro ao carregar times:", erro);
    }
}

function esconderTudo() {
    document.getElementById("pagina-inicial").style.display = "none";
    document.getElementById("pagina-carregando").style.display = "none";
    document.getElementById("pagina-erro").style.display = "none";
    document.getElementById("pagina-conteudo").style.display = "none";
}

async function buscarConfrontos() {
    var timeCasaId = document.getElementById("select-time-casa").value;
    var timeForaId = document.getElementById("select-time-fora").value;
    var ultimosN = document.getElementById("select-ultimos-n").value;

    if (!timeCasaId || !timeForaId) {
        document.getElementById("msg-erro").textContent = "Selecione os dois times antes de analisar.";
        esconderTudo();
        document.getElementById("pagina-erro").style.display = "block";
        return;
    }

    if (timeCasaId === timeForaId) {
        document.getElementById("msg-erro").textContent = "Selecione times diferentes.";
        esconderTudo();
        document.getElementById("pagina-erro").style.display = "block";
        return;
    }

    esconderTudo();
    document.getElementById("pagina-carregando").style.display = "block";

    try {
        var qs = construirQueryString({ time_casa_id: timeCasaId, time_fora_id: timeForaId, ultimos_n: ultimosN });
        var dados = await chamarApiAutenticada("/confrontos/analise" + qs);

        esconderTudo();
        renderizarConfronto(dados);
        document.getElementById("pagina-conteudo").style.display = "block";

    } catch (erro) {
        esconderTudo();
        document.getElementById("msg-erro").textContent = "Não foi possível carregar os dados do confronto.";
        document.getElementById("pagina-erro").style.display = "block";
    }
}

function renderizarCardTime(elementId, infoTime, corBorda) {
    var container = document.getElementById(elementId);
    var logoHtml = "";

    if (infoTime.logo) {
        logoHtml = '<img src="' + infoTime.logo + '" alt="' + infoTime.nome + '" class="time-logo-img">';
    } else {
        var codigo = infoTime.codigo || infoTime.nome.substring(0, 3).toUpperCase();
        logoHtml = '<div class="time-logo-placeholder">' + codigo + '</div>';
    }

    var jogosTexto = "";
    if (infoTime.medias) {
        jogosTexto = '<div class="time-info-jogos">Média dos últimos ' + infoTime.medias.jogos_considerados + ' jogos</div>';
    }

    container.style.borderColor = corBorda;
    container.innerHTML = logoHtml
        + '<div class="time-info">'
        + '<div class="time-info-nome">' + infoTime.nome + '</div>'
        + '<div class="time-info-apelido">' + (infoTime.apelido || "") + '</div>'
        + jogosTexto
        + '</div>';
}

function renderizarConfronto(dados) {
    var casa = dados.time_casa;
    var fora = dados.time_fora;

    var nomeCasa = casa.apelido || casa.nome;
    var nomeFora = fora.apelido || fora.nome;

    document.getElementById("th-casa").textContent = nomeCasa;
    document.getElementById("th-fora").textContent = nomeFora;

    renderizarCardTime("card-time-casa", casa, "#F75C03");
    renderizarCardTime("card-time-fora", fora, "#3B9EFF");
    renderizarTabela(casa, fora, dados.historico_confronto);
}

function renderizarTabela(casa, fora, historico) {
    var tbody = document.getElementById("tbody-confronto");
    var html = "";

    var vitCasa = "—";
    var vitFora = "—";
    var totalJogos = 0;

    if (historico) {
        vitCasa = historico.vitorias_casa;
        vitFora = historico.vitorias_fora;
        totalJogos = historico.total_jogos;
    }

    var classeVitCasa = "td-valor-casa";
    var classeVitFora = "td-valor-fora";

    if (historico) {
        if (historico.vitorias_casa > historico.vitorias_fora) {
            classeVitCasa = "td-valor-casa td-vantagem";
        }
        if (historico.vitorias_fora > historico.vitorias_casa) {
            classeVitFora = "td-valor-fora td-vantagem";
        }
    }

    html = html + '<tr class="tr-vitorias">';
    html = html + '<td class="' + classeVitCasa + '">' + vitCasa + '</td>';
    html = html + '<td class="td-stat">Vitórias (' + totalJogos + ' jogos)</td>';
    html = html + '<td class="' + classeVitFora + '">' + vitFora + '</td>';
    html = html + '</tr>';
    html = html + '<tr class="tr-separador"><td colspan="3"></td></tr>';

    for (var i = 0; i < STATS_EXIBIDAS.length; i++) {
        var stat = STATS_EXIBIDAS[i];

        var valorCasa = "—";
        var valorFora = "—";

        if (casa.medias && casa.medias[stat.campo] !== undefined) {
            valorCasa = casa.medias[stat.campo];
        }
        if (fora.medias && fora.medias[stat.campo] !== undefined) {
            valorFora = fora.medias[stat.campo];
        }

        var classeCasa = "td-valor-casa";
        var classeFora = "td-valor-fora";

        if (valorCasa !== "—" && valorFora !== "—") {
            var menorMelhor = false;
            for (var m = 0; m < STATS_MENOR_MELHOR.length; m++) {
                if (STATS_MENOR_MELHOR[m] === stat.campo) {
                    menorMelhor = true;
                    break;
                }
            }

            if (menorMelhor) {
                if (valorCasa < valorFora) {
                    classeCasa = "td-valor-casa td-vantagem";
                }
                if (valorFora < valorCasa) {
                    classeFora = "td-valor-fora td-vantagem";
                }
            } else {
                if (valorCasa > valorFora) {
                    classeCasa = "td-valor-casa td-vantagem";
                }
                if (valorFora > valorCasa) {
                    classeFora = "td-valor-fora td-vantagem";
                }
            }
        }

        html = html + '<tr>';
        html = html + '<td class="' + classeCasa + '">' + valorCasa + '</td>';
        html = html + '<td class="td-stat">' + stat.rotulo + '</td>';
        html = html + '<td class="' + classeFora + '">' + valorFora + '</td>';
        html = html + '</tr>';
    }

    tbody.innerHTML = html;
}