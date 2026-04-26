import os
import json
import logging

from datetime import datetime, timezone

logger = logging.getLogger(__name__)

NOME_METADADOS = "metadados_ultimo_treino.json"
LARANJA = (0.969, 0.361, 0.012)
CINZA_ESCURO = (0.102, 0.102, 0.173)
CINZA_MEDIO = (0.333, 0.333, 0.467)
CINZA_CLARO = (0.918, 0.918, 0.941)
BRANCO = (1, 1, 1)
VERDE = (0, 0.478, 0.2)
VERMELHO = (0.784, 0.063, 0.18)

def _pasta_relatorios():
    from app.config import config
    pasta = config.PASTA_RELATORIOS
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    return pasta

def _caminho_metadados():
    pasta = _pasta_relatorios()
    return os.path.join(pasta, NOME_METADADOS)

def salvar_metadados_relatorio(dados):
    caminho = _caminho_metadados()
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as erro:
        logger.warning(f"Falha ao salvar metadados do relatorio: {erro}")

def carregar_metadados_anterior():
    caminho = _caminho_metadados()
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as erro:
        logger.warning(f"Falha ao carregar metadados anteriores: {erro}")
        return None

def _cor_rgb(r, g, b):
    return (r, g, b)

def _desenhar_cabecalho(c, width, height):
    from reportlab.lib.colors import Color

    c.setFillColor(Color(CINZA_ESCURO[0], CINZA_ESCURO[1], CINZA_ESCURO[2]))
    c.rect(0, height - 70, width, 70, fill=1, stroke=0)

    c.setFillColor(Color(LARANJA[0], LARANJA[1], LARANJA[2]))
    c.rect(0, height - 74, width, 4, fill=1, stroke=0)

    c.setFillColor(Color(BRANCO[0], BRANCO[1], BRANCO[2]))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 42, "NBA Analytics")

    c.setFont("Helvetica", 10)
    c.setFillColor(Color(0.7, 0.7, 0.85))
    c.drawString(40, height - 58, "Relatorio de Treinamento do Modelo Preditivo")

    agora = datetime.now(timezone.utc)
    data_str = agora.strftime("%d/%m/%Y %H:%M UTC")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 40, height - 42, data_str)

def _desenhar_rodape(c, width, numero_pagina):
    from reportlab.lib.colors import Color

    c.setFillColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
    c.rect(0, 0, width, 36, fill=1, stroke=0)

    c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
    c.setFont("Helvetica", 8)
    c.drawString(40, 13, "NbaAnalyst — Documento gerado automaticamente apos retreinamento")
    c.drawRightString(width - 40, 13, f"Pagina {numero_pagina}")

def _bloco_metrica(c, x, y, largura, altura, rotulo, valor, subtexto=None, cor_valor=None):
    from reportlab.lib.colors import Color

    c.setFillColor(Color(BRANCO[0], BRANCO[1], BRANCO[2]))
    c.setStrokeColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
    c.roundRect(x, y, largura, altura, 6, fill=1, stroke=1)

    c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
    c.setFont("Helvetica", 8)
    c.drawString(x + 12, y + altura - 18, rotulo.upper())

    if cor_valor is None:
        cor_valor = CINZA_ESCURO
    c.setFillColor(Color(cor_valor[0], cor_valor[1], cor_valor[2]))
    c.setFont("Helvetica-Bold", 22)
    c.drawString(x + 12, y + altura - 44, str(valor))

    if subtexto is not None:
        c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
        c.setFont("Helvetica", 8)
        c.drawString(x + 12, y + 10, subtexto)

def _linha_divisoria(c, x, y, largura):
    from reportlab.lib.colors import Color
    c.setStrokeColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
    c.setLineWidth(1)
    c.line(x, y, x + largura, y)

def _titulo_secao(c, x, y, texto):
    from reportlab.lib.colors import Color
    c.setFillColor(Color(LARANJA[0], LARANJA[1], LARANJA[2]))
    c.rect(x, y + 2, 3, 14, fill=1, stroke=0)
    c.setFillColor(Color(CINZA_ESCURO[0], CINZA_ESCURO[1], CINZA_ESCURO[2]))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 10, y + 2, texto)

def _tabela_stats(c, x, y, largura, dados_stats, dados_anteriores=None):
    from reportlab.lib.colors import Color

    colunas = ["Estatistica", "Total Prev.", "Acertos", "Win-Rate", "MAE", "RMSE", "vs Anterior"]
    larguras_col = [90, 70, 60, 70, 55, 55, 80]
    altura_linha = 22
    altura_header = 26

    c.setFillColor(Color(CINZA_ESCURO[0], CINZA_ESCURO[1], CINZA_ESCURO[2]))
    c.rect(x, y - altura_header, largura, altura_header, fill=1, stroke=0)

    c.setFillColor(Color(BRANCO[0], BRANCO[1], BRANCO[2]))
    c.setFont("Helvetica-Bold", 8)
    pos_x = x + 8
    for i in range(len(colunas)):
        c.drawString(pos_x, y - altura_header + 9, colunas[i])
        pos_x = pos_x + larguras_col[i]

    nomes_stats = ["points", "assists", "tot_reb", "steals", "blocks"]
    labels_stats = ["Pontos", "Assistencias", "Rebotes", "Roubos de Bola", "Bloqueios"]

    for idx in range(len(nomes_stats)):
        stat = nomes_stats[idx]
        label = labels_stats[idx]
        linha_y = y - altura_header - (idx + 1) * altura_linha

        if idx % 2 == 0:
            c.setFillColor(Color(0.97, 0.97, 0.99))
        else:
            c.setFillColor(Color(BRANCO[0], BRANCO[1], BRANCO[2]))
        c.rect(x, linha_y, largura, altura_linha, fill=1, stroke=0)

        c.setStrokeColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
        c.line(x, linha_y, x + largura, linha_y)

        dados = dados_stats.get(stat, {})
        total = dados.get("total_avaliadas", 0)
        acertos = dados.get("total_acertos", 0)
        win_rate = dados.get("win_rate", 0.0)
        mae = dados.get("mae_medio", None)
        rmse = dados.get("rmse", None)

        if win_rate >= 60:
            cor_wr = VERDE
        elif win_rate >= 55:
            cor_wr = LARANJA
        else:
            cor_wr = VERMELHO

        comparacao = "—"
        cor_comp = CINZA_MEDIO
        if dados_anteriores is not None:
            stats_anteriores = dados_anteriores.get("stats", {})
            wr_anterior = stats_anteriores.get(stat, {}).get("win_rate", None)
            if wr_anterior is not None:
                diff = round(win_rate - wr_anterior, 2)
                if diff > 0:
                    comparacao = f"+{diff}%"
                    cor_comp = VERDE
                elif diff < 0:
                    comparacao = f"{diff}%"
                    cor_comp = VERMELHO
                else:
                    comparacao = "0.00%"
                    cor_comp = CINZA_MEDIO

        if mae is not None:
            mae_str = str(mae) 
        else:
            mae_str = "—"
        if rmse is not None:
            rmse_str = str(rmse)
        else:
            rmse_str = "—"

        valores = [label, str(total), str(acertos), f"{win_rate}%", mae_str, rmse_str, comparacao]
        cores = [CINZA_ESCURO, CINZA_ESCURO, CINZA_ESCURO, cor_wr, CINZA_ESCURO, CINZA_ESCURO, cor_comp]
        fontes = ["Helvetica", "Helvetica", "Helvetica", "Helvetica-Bold", "Helvetica", "Helvetica", "Helvetica-Bold"]

        pos_x = x + 8
        for i in range(len(valores)):
            c.setFillColor(Color(cores[i][0], cores[i][1], cores[i][2]))
            c.setFont(fontes[i], 8)
            c.drawString(pos_x, linha_y + 7, valores[i])
            pos_x = pos_x + larguras_col[i]

    altura_total = altura_header + len(nomes_stats) * altura_linha
    return altura_total

def gerar_relatorio_treinamento(season, total_registros_db, total_jogadores_treino, total_modelos_salvos, total_erros, dados_win_rate, dados_win_rate_anterior=None):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import Color

    pasta = _pasta_relatorios()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"relatorio_retreinamento_{season}_{timestamp}.pdf"
    caminho_pdf = os.path.join(pasta, nome_arquivo)

    width, height = A4
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    margem = 40
    area_util = width - (margem * 2)
    y = height - 100

    _desenhar_cabecalho(c, width, height)
    _desenhar_rodape(c, width, 1)

    c.setFillColor(Color(CINZA_ESCURO[0], CINZA_ESCURO[1], CINZA_ESCURO[2]))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margem, y, f"Relatorio de Retreinamento — Temporada {season}")

    y = y - 20
    c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
    c.setFont("Helvetica", 9)
    c.drawString(margem, y, f"Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y as %H:%M UTC')}")

    y = y - 30
    _linha_divisoria(c, margem, y, area_util)

    y = y - 24
    _titulo_secao(c, margem, y, "Dados do Treinamento")

    y = y - 80
    larg_bloco = (area_util - 16) / 4
    blocos = [
        ("Registros no Banco", str(total_registros_db), "jogos na temporada"),
        ("Jogadores Treinados", str(total_jogadores_treino), f"acima de {15} min/jogo"),
        ("Modelos Salvos", str(total_modelos_salvos), "arquivos .pkl gerados"),
        ("Erros de Treino", str(total_erros), "falhas registradas"),
    ]
    for i in range(len(blocos)):
        bx = margem + i * (larg_bloco + 5)
        cor = CINZA_ESCURO
        if i == 3 and total_erros > 0:
            cor = VERMELHO
        _bloco_metrica(c, bx, y, larg_bloco, 76, blocos[i][0], blocos[i][1], blocos[i][2], cor)

    y = y - 36
    _linha_divisoria(c, margem, y, area_util)

    y = y - 24
    _titulo_secao(c, margem, y, "Desempenho do Modelo (Win-Rate Over/Under)")

    if dados_win_rate is not None:
        win_rate_geral = dados_win_rate.get("win_rate_geral", 0.0)
        total_avaliadas = dados_win_rate.get("total_predicoes_avaliadas", 0)
        mae_geral = dados_win_rate.get("mae_medio_geral", None)
        rmse_geral = dados_win_rate.get("rmse_geral", None)

        wr_anterior = None
        if dados_win_rate_anterior is not None:
            wr_anterior = dados_win_rate_anterior.get("win_rate_geral", None)

        if win_rate_geral >= 60:
            cor_wr = VERDE
        elif win_rate_geral >= 55:
            cor_wr = LARANJA
        else:
            cor_wr = VERMELHO

        comparacao_geral = "Sem historico"
        cor_comp_geral = CINZA_MEDIO
        if wr_anterior is not None:
            diff = round(win_rate_geral - wr_anterior, 2)
            if diff > 0:
                comparacao_geral = f"Melhora de +{diff}%"
                cor_comp_geral = VERDE
            elif diff < 0:
                comparacao_geral = f"Queda de {diff}%"
                cor_comp_geral = VERMELHO
            else:
                comparacao_geral = "Sem variacao"
                cor_comp_geral = CINZA_MEDIO

        y = y - 90
        larg_destaque = (area_util - 5) / 3

        _bloco_metrica(c, margem, y, larg_destaque, 80, "Win-Rate Geral", f"{win_rate_geral}%", f"{total_avaliadas} palpites avaliados", cor_wr)

        mae_str = str(mae_geral) if mae_geral is not None else "—"
        rmse_str = str(rmse_geral) if rmse_geral is not None else "—"
        _bloco_metrica(c, margem + larg_destaque + 5, y, larg_destaque, 80, "MAE Medio Geral", mae_str, "erro absoluto medio")
        _bloco_metrica(c, margem + (larg_destaque + 5) * 2, y, larg_destaque, 80, "RMSE Medio Geral", rmse_str, "raiz erro quadratico medio")

        y = y - 20
        c.setFillColor(Color(cor_comp_geral[0], cor_comp_geral[1], cor_comp_geral[2]))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem, y, comparacao_geral)
        if wr_anterior is not None:
            c.setFont("Helvetica", 9)
            c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
            c.drawString(margem + 160, y, f"(anterior: {wr_anterior}%  |  atual: {win_rate_geral}%)")

        y = y - 30
        _titulo_secao(c, margem, y, "Detalhamento por Estatistica")

        stats_map = {}
        stats_map["points"] = dados_win_rate.get("pontos", {})
        stats_map["assists"] = dados_win_rate.get("assistencias", {})
        stats_map["tot_reb"] = dados_win_rate.get("rebotes", {})
        stats_map["steals"] = dados_win_rate.get("roubos", {})
        stats_map["blocks"] = dados_win_rate.get("bloqueios", {})

        stats_anteriores_map = None
        if dados_win_rate_anterior is not None:
            stats_anteriores_map = {}
            stats_anteriores_map["stats"] = {}
            stats_anteriores_map["stats"]["points"] = {"win_rate": dados_win_rate_anterior.get("pontos", {}).get("win_rate", None)}
            stats_anteriores_map["stats"]["assists"] = {"win_rate": dados_win_rate_anterior.get("assistencias", {}).get("win_rate", None)}
            stats_anteriores_map["stats"]["tot_reb"] = {"win_rate": dados_win_rate_anterior.get("rebotes", {}).get("win_rate", None)}
            stats_anteriores_map["stats"]["steals"] = {"win_rate": dados_win_rate_anterior.get("roubos", {}).get("win_rate", None)}
            stats_anteriores_map["stats"]["blocks"] = {"win_rate": dados_win_rate_anterior.get("bloqueios", {}).get("win_rate", None)}

        y = y - 20
        _tabela_stats(c, margem, y, area_util, stats_map, stats_anteriores_map)
    else:
        y = y - 30
        c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
        c.setFont("Helvetica", 10)
        c.drawString(margem, y, "Nenhum dado de desempenho disponivel para esta temporada ainda.")

    c.save()
    logger.warning(f"Relatorio gerado: {caminho_pdf}")
    return caminho_pdf

def gerar_e_salvar_relatorio(db, season, total_registros_db, total_jogadores_treino, total_modelos_salvos, total_erros):
    from app.services.win_rate_service import calcular_win_rate

    dados_win_rate_anterior = carregar_metadados_anterior()

    dados_win_rate = None
    try:
        dados_win_rate = calcular_win_rate(db=db, temporada=season)
    except Exception as erro:
        logger.warning(f"Falha ao calcular win_rate para relatorio: {erro}")

    caminho_pdf = gerar_relatorio_treinamento(season=season, total_registros_db=total_registros_db, total_jogadores_treino=total_jogadores_treino, total_modelos_salvos=total_modelos_salvos, total_erros=total_erros, dados_win_rate=dados_win_rate, dados_win_rate_anterior=dados_win_rate_anterior)

    if dados_win_rate is not None:
        metadados = {}
        metadados["temporada"] = season
        metadados["data_geracao"] = datetime.now(timezone.utc).isoformat()
        metadados["win_rate_geral"] = dados_win_rate.get("win_rate_geral", 0.0)
        metadados["mae_medio_geral"] = dados_win_rate.get("mae_medio_geral", None)
        metadados["rmse_geral"] = dados_win_rate.get("rmse_geral", None)
        metadados["total_predicoes_avaliadas"] = dados_win_rate.get("total_predicoes_avaliadas", 0)
        metadados["pontos"] = dados_win_rate.get("pontos", {})
        metadados["assistencias"] = dados_win_rate.get("assistencias", {})
        metadados["rebotes"] = dados_win_rate.get("rebotes", {})
        metadados["roubos"] = dados_win_rate.get("roubos", {})
        metadados["bloqueios"] = dados_win_rate.get("bloqueios", {})
        salvar_metadados_relatorio(metadados)

    return caminho_pdf