import json
import logging
import os
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


def _desenhar_rodape(c, width, numero_pagina, season=None):
    from reportlab.lib.colors import Color

    c.setFillColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
    c.rect(0, 0, width, 36, fill=1, stroke=0)

    c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
    c.setFont("Helvetica", 8)
    rodape_texto = "NbaAnalyst — Documento gerado automaticamente apos retreinamento"
    if season:
        rodape_texto = rodape_texto + "  |  Temporada " + str(season)
    c.drawString(40, 13, rodape_texto)
    c.drawRightString(width - 40, 13, f"Pagina {numero_pagina}")


def _bloco_metrica(
    c,
    x,
    y,
    largura,
    altura,
    rotulo,
    valor,
    subtexto=None,
    cor_valor=None,
    progresso=None,
):
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

    if progresso is not None:
        barra_x = x + 12
        barra_y = y + 22
        barra_larg = largura - 24
        barra_alt = 5

        c.setFillColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
        c.roundRect(barra_x, barra_y, barra_larg, barra_alt, 2, fill=1, stroke=0)

        pct_clamp = max(0, min(100, progresso))
        fill_larg = barra_larg * pct_clamp / 100
        if fill_larg > 0:
            c.setFillColor(Color(cor_valor[0], cor_valor[1], cor_valor[2]))
            c.roundRect(barra_x, barra_y, fill_larg, barra_alt, 2, fill=1, stroke=0)

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

    colunas = [
        "Estatistica",
        "Total Prev.",
        "Acertos",
        "Win-Rate",
        "MAE",
        "RMSE",
        "vs Anterior",
    ]
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

        if win_rate >= 58:
            cor_wr = VERDE
        elif win_rate >= 54:
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
                    comparacao = f"▲ +{diff}%"
                    cor_comp = VERDE
                elif diff < 0:
                    comparacao = f"▼ {diff}%"
                    cor_comp = VERMELHO
                else:
                    comparacao = "= 0.00%"
                    cor_comp = CINZA_MEDIO

        if mae is not None:
            mae_str = str(mae)
        else:
            mae_str = "—"
        if rmse is not None:
            rmse_str = str(rmse)
        else:
            rmse_str = "—"

        valores = [
            label,
            str(total),
            str(acertos),
            f"{win_rate}%",
            mae_str,
            rmse_str,
            comparacao,
        ]
        cores = [
            CINZA_ESCURO,
            CINZA_ESCURO,
            CINZA_ESCURO,
            cor_wr,
            CINZA_ESCURO,
            CINZA_ESCURO,
            cor_comp,
        ]
        fontes = [
            "Helvetica",
            "Helvetica",
            "Helvetica",
            "Helvetica-Bold",
            "Helvetica",
            "Helvetica",
            "Helvetica-Bold",
        ]

        pos_x = x + 8
        for i in range(len(valores)):
            c.setFillColor(Color(cores[i][0], cores[i][1], cores[i][2]))
            c.setFont(fontes[i], 8)
            c.drawString(pos_x, linha_y + 7, valores[i])
            pos_x = pos_x + larguras_col[i]

    altura_total = altura_header + len(nomes_stats) * altura_linha

    from reportlab.lib.colors import Color

    c.setStrokeColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
    c.setLineWidth(1)
    c.roundRect(x, y - altura_total, largura, altura_total, 4, fill=0, stroke=1)

    return altura_total


def _desenhar_tabela_posicao(c, x, y, largura, cobertura):
    from reportlab.lib.colors import Color

    nomes_pos = ["PG", "SG", "SF", "PF", "C", "N/D"]
    labels_pos = [
        "Armador (PG)",
        "Ala-armador (SG)",
        "Ala (SF)",
        "Ala-pivo (PF)",
        "Pivo (C)",
        "Nao definido",
    ]
    altura_linha = 24
    altura_header = 26

    c.setFillColor(Color(CINZA_ESCURO[0], CINZA_ESCURO[1], CINZA_ESCURO[2]))
    c.rect(x, y - altura_header, largura, altura_header, fill=1, stroke=0)

    c.setFillColor(Color(BRANCO[0], BRANCO[1], BRANCO[2]))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 12, y - altura_header + 9, "POSICAO")
    c.drawString(x + largura - 120, y - altura_header + 9, "JOGADORES COM MODELO")

    for idx in range(len(nomes_pos)):
        pos = nomes_pos[idx]
        label = labels_pos[idx]
        linha_y = y - altura_header - (idx + 1) * altura_linha

        if idx % 2 == 0:
            c.setFillColor(Color(0.97, 0.97, 0.99))
        else:
            c.setFillColor(Color(BRANCO[0], BRANCO[1], BRANCO[2]))
        c.rect(x, linha_y, largura, altura_linha, fill=1, stroke=0)

        c.setStrokeColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
        c.line(x, linha_y, x + largura, linha_y)

        c.setFillColor(Color(CINZA_ESCURO[0], CINZA_ESCURO[1], CINZA_ESCURO[2]))
        c.setFont("Helvetica", 9)
        c.drawString(x + 12, linha_y + 8, label)

        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + largura - 120, linha_y + 8, str(cobertura.get(pos, 0)))

    altura_total = altura_header + len(nomes_pos) * altura_linha
    c.setStrokeColor(Color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2]))
    c.setLineWidth(1)
    c.roundRect(x, y - altura_total, largura, altura_total, 4, fill=0, stroke=1)
    return altura_total


def gerar_relatorio_treinamento(
    season,
    total_registros_db,
    total_jogadores_treino,
    total_modelos_salvos,
    total_erros,
    dados_win_rate,
    dados_win_rate_anterior=None,
    config_treino=None,
):
    from reportlab.lib.colors import Color
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

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
    _desenhar_rodape(c, width, 1, season)

    c.setFillColor(Color(CINZA_ESCURO[0], CINZA_ESCURO[1], CINZA_ESCURO[2]))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margem, y, f"Relatorio de Retreinamento — Temporada {season}")

    y = y - 20
    c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
    c.setFont("Helvetica", 9)
    c.drawString(
        margem,
        y,
        f"Gerado em: {datetime.now(timezone.utc).strftime('%d/%m/%Y as %H:%M UTC')}",
    )

    y = y - 30
    _linha_divisoria(c, margem, y, area_util)

    y = y - 24
    _titulo_secao(c, margem, y, "Configuracao do Treinamento")

    y = y - 20
    c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
    c.setFont("Helvetica", 9)

    if config_treino is not None:
        temporadas = config_treino.get("temporadas", [])
        proporcao = config_treino.get("proporcao_treino", 0.7)
        limiar_min = config_treino.get("limiar_minutos", 0)
        min_amostras = config_treino.get("min_amostras", 0)
        temporadas_str = ", ".join(str(t) for t in temporadas)
        pct_treino = int(proporcao * 100)
        pct_teste = 100 - pct_treino

        linha_cfg1 = (
            "Modelo: XGBoost Regressor (um modelo por jogador e por estatistica)"
        )
        linha_cfg2 = f"Temporadas utilizadas: {temporadas_str}"
        linha_cfg3 = f"Divisao treino/teste: {pct_treino}% treino / {pct_teste}% teste (split temporal por jogador)"
        linha_cfg4 = f"Criterio de inclusao: media >= {limiar_min} minutos nos jogos recentes  |  minimo de {min_amostras} amostras por modelo"

        c.drawString(margem, y, linha_cfg1)
        y = y - 14
        c.drawString(margem, y, linha_cfg2)
        y = y - 14
        c.drawString(margem, y, linha_cfg3)
        y = y - 14
        c.drawString(margem, y, linha_cfg4)
    else:
        c.drawString(margem, y, "Configuracao nao disponivel.")

    y = y - 24
    _linha_divisoria(c, margem, y, area_util)

    y = y - 24
    _titulo_secao(c, margem, y, "Dados do Treinamento")

    y = y - 80
    larg_bloco = (area_util - 16) / 4

    if config_treino is not None:
        limiar_min_bloco = config_treino.get("limiar_minutos", 0)
    else:
        limiar_min_bloco = 0

    blocos = [
        ("Registros Jogador-Jogo", str(total_registros_db), "amostras historicas"),
        (
            "Jogadores Treinados",
            str(total_jogadores_treino),
            f"acima de {limiar_min_bloco} min/jogo",
        ),
        ("Modelos Salvos", str(total_modelos_salvos), "arquivos .pkl gerados"),
        ("Erros de Treino", str(total_erros), "falhas registradas"),
    ]
    for i in range(len(blocos)):
        bx = margem + i * (larg_bloco + 5)
        cor = CINZA_ESCURO
        if i == 3 and total_erros > 0:
            cor = VERMELHO
        _bloco_metrica(
            c, bx, y, larg_bloco, 76, blocos[i][0], blocos[i][1], blocos[i][2], cor
        )

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

        if win_rate_geral >= 58:
            cor_wr = VERDE
        elif win_rate_geral >= 54:
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

        _bloco_metrica(
            c,
            margem,
            y,
            larg_destaque,
            80,
            "Win-Rate Geral",
            f"{win_rate_geral}%",
            f"{total_avaliadas} palpites avaliados",
            cor_wr,
        )

        mae_str = str(mae_geral) if mae_geral is not None else "—"
        rmse_str = str(rmse_geral) if rmse_geral is not None else "—"
        _bloco_metrica(
            c,
            margem + larg_destaque + 5,
            y,
            larg_destaque,
            80,
            "MAE Medio Geral",
            mae_str,
            "erro absoluto medio",
        )
        _bloco_metrica(
            c,
            margem + (larg_destaque + 5) * 2,
            y,
            larg_destaque,
            80,
            "RMSE Medio Geral",
            rmse_str,
            "raiz erro quadratico medio",
        )

        y = y - 20
        c.setFillColor(Color(cor_comp_geral[0], cor_comp_geral[1], cor_comp_geral[2]))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem, y, comparacao_geral)
        if wr_anterior is not None:
            c.setFont("Helvetica", 9)
            c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
            c.drawString(
                margem + 160,
                y,
                f"(anterior: {wr_anterior}%  |  atual: {win_rate_geral}%)",
            )

        y = y - 20

        if win_rate_geral >= 58:
            badge_texto = "MODELO DENTRO DA META  (meta: >= 58%)"
            badge_cor_fundo = (0.9, 0.97, 0.93)
            badge_cor_borda = (0, 0.6, 0.25)
            badge_cor_texto = VERDE
        elif win_rate_geral >= 54:
            badge_texto = "MODELO PROXIMO DA META  (meta: >= 58%)"
            badge_cor_fundo = (1.0, 0.97, 0.88)
            badge_cor_borda = (0.85, 0.55, 0.0)
            badge_cor_texto = LARANJA
        else:
            badge_texto = "MODELO ABAIXO DA META  (meta: >= 58%)"
            badge_cor_fundo = (0.98, 0.92, 0.93)
            badge_cor_borda = (0.7, 0.05, 0.15)
            badge_cor_texto = VERMELHO

        c.setFillColor(
            Color(badge_cor_fundo[0], badge_cor_fundo[1], badge_cor_fundo[2])
        )
        c.setStrokeColor(
            Color(badge_cor_borda[0], badge_cor_borda[1], badge_cor_borda[2])
        )
        c.setLineWidth(1)
        c.roundRect(margem, y - 14, area_util, 22, 4, fill=1, stroke=1)
        c.setFillColor(
            Color(badge_cor_texto[0], badge_cor_texto[1], badge_cor_texto[2])
        )
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margem + 10, y - 6, badge_texto)

        y = y - 16

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
            stats_anteriores_map["stats"]["points"] = {
                "win_rate": dados_win_rate_anterior.get("pontos", {}).get(
                    "win_rate", None
                )
            }
            stats_anteriores_map["stats"]["assists"] = {
                "win_rate": dados_win_rate_anterior.get("assistencias", {}).get(
                    "win_rate", None
                )
            }
            stats_anteriores_map["stats"]["tot_reb"] = {
                "win_rate": dados_win_rate_anterior.get("rebotes", {}).get(
                    "win_rate", None
                )
            }
            stats_anteriores_map["stats"]["steals"] = {
                "win_rate": dados_win_rate_anterior.get("roubos", {}).get(
                    "win_rate", None
                )
            }
            stats_anteriores_map["stats"]["blocks"] = {
                "win_rate": dados_win_rate_anterior.get("bloqueios", {}).get(
                    "win_rate", None
                )
            }

        y = y - 20
        _tabela_stats(c, margem, y, area_util, stats_map, stats_anteriores_map)

        if config_treino is not None:
            cobertura = config_treino.get("cobertura_posicao", None)
            total_com_modelo = config_treino.get("total_jogadores_com_modelo", None)
            if cobertura is not None:
                c.showPage()
                _desenhar_cabecalho(c, width, height)
                _desenhar_rodape(c, width, 2, season)

                y_pag2 = height - 110
                _titulo_secao(c, margem, y_pag2, "Cobertura de Modelos por Posicao")

                y_pag2 = y_pag2 - 18
                c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
                c.setFont("Helvetica", 9)
                if total_com_modelo is not None:
                    c.drawString(
                        margem,
                        y_pag2,
                        f"Total de {total_com_modelo} jogadores com pelo menos um modelo treinado, distribuidos por posicao:",
                    )

                y_pag2 = y_pag2 - 30
                _desenhar_tabela_posicao(c, margem, y_pag2, area_util, cobertura)
    else:
        y = y - 30
        c.setFillColor(Color(CINZA_MEDIO[0], CINZA_MEDIO[1], CINZA_MEDIO[2]))
        c.setFont("Helvetica", 10)
        c.drawString(
            margem, y, "Nenhum dado de desempenho disponivel para esta temporada ainda."
        )

    c.save()
    logger.info(f"Relatorio gerado: {caminho_pdf}")
    return caminho_pdf


def gerar_e_salvar_relatorio(
    db,
    season,
    total_registros_db,
    total_jogadores_treino,
    total_modelos_salvos,
    total_erros,
    config_treino=None,
):
    from app.services.win_rate_service import calcular_win_rate

    dados_win_rate_anterior = carregar_metadados_anterior()

    dados_win_rate = None
    try:
        dados_win_rate = calcular_win_rate(db=db, temporada=season)
    except Exception as erro:
        logger.warning(f"Falha ao calcular win_rate para relatorio: {erro}")

    caminho_pdf = gerar_relatorio_treinamento(
        season=season,
        total_registros_db=total_registros_db,
        total_jogadores_treino=total_jogadores_treino,
        total_modelos_salvos=total_modelos_salvos,
        total_erros=total_erros,
        dados_win_rate=dados_win_rate,
        dados_win_rate_anterior=dados_win_rate_anterior,
        config_treino=config_treino,
    )

    if dados_win_rate is not None:
        metadados = {}
        metadados["temporada"] = season
        metadados["data_geracao"] = datetime.now(timezone.utc).isoformat()
        metadados["win_rate_geral"] = dados_win_rate.get("win_rate_geral", 0.0)
        metadados["mae_medio_geral"] = dados_win_rate.get("mae_medio_geral", None)
        metadados["rmse_geral"] = dados_win_rate.get("rmse_geral", None)
        metadados["total_predicoes_avaliadas"] = dados_win_rate.get(
            "total_predicoes_avaliadas", 0
        )
        metadados["pontos"] = dados_win_rate.get("pontos", {})
        metadados["assistencias"] = dados_win_rate.get("assistencias", {})
        metadados["rebotes"] = dados_win_rate.get("rebotes", {})
        metadados["roubos"] = dados_win_rate.get("roubos", {})
        metadados["bloqueios"] = dados_win_rate.get("bloqueios", {})
        salvar_metadados_relatorio(metadados)

    return caminho_pdf
