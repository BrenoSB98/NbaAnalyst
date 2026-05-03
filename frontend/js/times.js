var todosTimes = [];

document.addEventListener("DOMContentLoaded", function() {
    inicializarPagina();
    carregarTimes();
});

async function carregarTimes() {
    try {
        var dados = await chamarApi("/times?nba_franchise=true&page_size=35");

        todosTimes = dados.times || [];

        document.getElementById("times-carregando").style.display = "none";

        if (todosTimes.length === 0) {
            document.getElementById("times-vazio").style.display = "block";
            return;
        }

        renderizarTimes(todosTimes);
        document.getElementById("times-lista").style.display = "block";

    } catch (erro) {
        document.getElementById("times-carregando").style.display = "none";
        document.getElementById("times-vazio").style.display = "block";
    }
}

function renderizarTimes(times) {
    var grid = document.getElementById("times-grid");
    var contador = document.getElementById("contador-times");
    var html = "";

    contador.textContent = times.length + " times";

    for (var i = 0; i < times.length; i++) {
        var time = times[i];

        var escudoConteudo = "";
        if (time.logo) {
            escudoConteudo = '<img src="' + time.logo + '" alt="' + time.nome + '" class="time-logo">';
        } else {
            var iniciais = time.codigo || time.nome.substring(0, 3).toUpperCase();
            escudoConteudo = '<div class="time-logo-placeholder">' + iniciais + '</div>';
        }

        html = html
            + '<div class="col-4 col-sm-3 col-md-2">'
            +   '<a href="time.html?id=' + time.id + '" class="card-time">'
            +     '<div class="escudo-wrapper">' + escudoConteudo + '</div>'
            +     '<div class="time-nome">' + time.nome + '</div>'
            +   '</a>'
            + '</div>';
    }

    grid.innerHTML = html;
}

function filtrarTimes() {
    var busca = document.getElementById("campo-busca").value.toLowerCase().trim();

    if (busca === "") {
        renderizarTimes(todosTimes);
        return;
    }

    var timesFiltrados = [];
    for (var i = 0; i < todosTimes.length; i++) {
        var time = todosTimes[i];
        var nome = time.nome.toLowerCase();
        var cidade = (time.cidade || "").toLowerCase();

        if (nome.indexOf(busca) !== -1 || cidade.indexOf(busca) !== -1) {
            timesFiltrados.push(time);
        }
    }

    if (timesFiltrados.length === 0) {
        document.getElementById("times-lista").style.display = "none";
        document.getElementById("times-vazio").style.display = "block";
        document.getElementById("contador-times").textContent = "0 times";
    } else {
        document.getElementById("times-vazio").style.display = "none";
        document.getElementById("times-lista").style.display = "block";
        renderizarTimes(timesFiltrados);
    }
}