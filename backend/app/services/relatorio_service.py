import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

NOME_METADADOS = "metadados_ultimo_treino.json"


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


def _escrever_linha(c, x, y, texto, fonte="Helvetica", tamanho=10):
    c.setFont(fonte, tamanho)
    c.drawString(x, y, texto)


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
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    pasta = _pasta_relatorios()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"relatorio_retreinamento_{season}_{timestamp}.pdf"
    caminho_pdf = os.path.join(pasta, nome_arquivo)

    width, height = A4
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    margem = 50
    y = height - 60

    data_geracao = datetime.now(timezone.utc).strftime("%d/%m/%Y as %H:%M UTC")

    _escrever_linha(c, margem, y, "NBA Analytics", "Helvetica-Bold", 16)
    y = y - 18
    _escrever_linha(
        c, margem, y, "Relatorio de Treinamento do Modelo Preditivo", "Helvetica", 11
    )
    y = y - 14
    _escrever_linha(c, margem, y, f"Temporada: {season}", "Helvetica", 10)
    y = y - 14
    _escrever_linha(c, margem, y, f"Gerado em: {data_geracao}", "Helvetica", 10)

    y = y - 30
    _escrever_linha(c, margem, y, "Configuracao do Treinamento", "Helvetica-Bold", 12)
    y = y - 18

    if config_treino is not None:
        temporadas = config_treino.get("temporadas", [])
        proporcao = config_treino.get("proporcao_treino", 0.7)
        limiar_min = config_treino.get("limiar_minutos", 0)
        min_amostras = config_treino.get("min_amostras", 0)
        temporadas_str = ", ".join(str(t) for t in temporadas)
        pct_treino = int(proporcao * 100)
        pct_teste = 100 - pct_treino

        _escrever_linha(
            c,
            margem,
            y,
            "Modelo: XGBoost Regressor (um modelo por jogador e por estatistica)",
        )
        y = y - 14
        _escrever_linha(c, margem, y, f"Temporadas utilizadas: {temporadas_str}")
        y = y - 14
        _escrever_linha(
            c,
            margem,
            y,
            f"Divisao treino/teste: {pct_treino}% treino / {pct_teste}% teste (split temporal por jogador)",
        )
        y = y - 14
        _escrever_linha(
            c,
            margem,
            y,
            f"Criterio de inclusao: media maior ou igual a {limiar_min} minutos nos jogos recentes",
        )
        y = y - 14
        _escrever_linha(c, margem, y, f"Minimo de amostras por modelo: {min_amostras}")
    else:
        _escrever_linha(c, margem, y, "Configuracao nao disponivel.")

    y = y - 30
    _escrever_linha(c, margem, y, "Dados do Treinamento", "Helvetica-Bold", 12)
    y = y - 18

    if config_treino is not None:
        limiar_min_bloco = config_treino.get("limiar_minutos", 0)
    else:
        limiar_min_bloco = 0

    _escrever_linha(
        c,
        margem,
        y,
        f"Registros jogador-jogo: {total_registros_db} amostras historicas",
    )
    y = y - 14
    _escrever_linha(
        c,
        margem,
        y,
        f"Jogadores treinados: {total_jogadores_treino} (acima de {limiar_min_bloco} min/jogo)",
    )
    y = y - 14
    _escrever_linha(
        c, margem, y, f"Modelos salvos: {total_modelos_salvos} arquivos .pkl gerados"
    )
    y = y - 14
    _escrever_linha(c, margem, y, f"Erros de treino: {total_erros} falhas registradas")

    y = y - 30
    _escrever_linha(
        c, margem, y, "Desempenho do Modelo", "Helvetica-Bold", 12
    )
    y = y - 18

    if dados_win_rate is not None:
        win_rate_geral = dados_win_rate.get("win_rate_geral", 0.0)
        total_avaliadas = dados_win_rate.get("total_predicoes_avaliadas", 0)
        mae_geral = dados_win_rate.get("mae_medio_geral", None)
        rmse_geral = dados_win_rate.get("rmse_geral", None)

        mae_str = str(mae_geral) if mae_geral is not None else "N/D"
        rmse_str = str(rmse_geral) if rmse_geral is not None else "N/D"

        _escrever_linha(
            c,
            margem,
            y,
            f"Win-rate geral: {win_rate_geral}% ({total_avaliadas} palpites avaliados)",
        )
        y = y - 14
        _escrever_linha(
            c, margem, y, f"MAE medio geral: {mae_str} (erro absoluto medio)"
        )
        y = y - 14
        _escrever_linha(
            c, margem, y, f"RMSE medio geral: {rmse_str} (raiz erro quadratico medio)"
        )
        y = y - 14

        wr_anterior = None
        if dados_win_rate_anterior is not None:
            wr_anterior = dados_win_rate_anterior.get("win_rate_geral", None)

        if wr_anterior is not None:
            diff = round(win_rate_geral - wr_anterior, 2)
            if diff > 0:
                comparacao_geral = f"Melhora de +{diff}% (anterior: {wr_anterior}% / atual: {win_rate_geral}%)"
            elif diff < 0:
                comparacao_geral = f"Queda de {diff}% (anterior: {wr_anterior}% / atual: {win_rate_geral}%)"
            else:
                comparacao_geral = f"Sem variacao (anterior: {wr_anterior}% / atual: {win_rate_geral}%)"
        else:
            comparacao_geral = "Comparacao: sem historico anterior"
        _escrever_linha(c, margem, y, comparacao_geral)
        y = y - 14

        if win_rate_geral >= 58:
            badge_texto = "Status: MODELO DENTRO DA META (meta: maior ou igual a 58%)"
        elif win_rate_geral >= 54:
            badge_texto = "Status: MODELO PROXIMO DA META (meta: maior ou igual a 58%)"
        else:
            badge_texto = "Status: MODELO ABAIXO DA META (meta: maior ou igual a 58%)"
        _escrever_linha(c, margem, y, badge_texto, "Helvetica-Bold", 10)

        y = y - 30
        _escrever_linha(
            c, margem, y, "Detalhamento por Estatistica", "Helvetica-Bold", 12
        )
        y = y - 18

        nomes_stats = ["pontos", "assistencias", "rebotes", "roubos", "bloqueios"]
        labels_stats = [
            "Pontos",
            "Assistencias",
            "Rebotes",
            "Roubos de Bola",
            "Bloqueios",
        ]

        stats_anteriores = {}
        if dados_win_rate_anterior is not None:
            for nome in nomes_stats:
                stats_anteriores[nome] = dados_win_rate_anterior.get(nome, {}).get(
                    "win_rate", None
                )

        for idx in range(len(nomes_stats)):
            nome = nomes_stats[idx]
            label = labels_stats[idx]
            dados = dados_win_rate.get(nome, {})
            total = dados.get("total_avaliadas", 0)
            acertos = dados.get("total_acertos", 0)
            win_rate = dados.get("win_rate", 0.0)
            mae = dados.get("mae_medio", None)
            rmse = dados.get("rmse", None)

            mae_s = str(mae) if mae is not None else "N/D"
            rmse_s = str(rmse) if rmse is not None else "N/D"

            comparacao = "sem historico"
            wr_ant = stats_anteriores.get(nome, None)
            if wr_ant is not None:
                diff = round(win_rate - wr_ant, 2)
                if diff > 0:
                    comparacao = f"+{diff}%"
                elif diff < 0:
                    comparacao = f"{diff}%"
                else:
                    comparacao = "0.00%"

            linha = f"{label}: {total} prev. / {acertos} acertos / win-rate {win_rate}% / MAE {mae_s} / RMSE {rmse_s} / vs anterior {comparacao}"
            _escrever_linha(c, margem, y, linha, "Helvetica", 9)
            y = y - 14

        if config_treino is not None:
            cobertura = config_treino.get("cobertura_posicao", None)
            total_com_modelo = config_treino.get("total_jogadores_com_modelo", None)
            if cobertura is not None:
                y = y - 20
                _escrever_linha(
                    c,
                    margem,
                    y,
                    "Cobertura de Modelos por Posicao",
                    "Helvetica-Bold",
                    12,
                )
                y = y - 18

                if total_com_modelo is not None:
                    _escrever_linha(
                        c,
                        margem,
                        y,
                        f"Total de {total_com_modelo} jogadores com pelo menos um modelo treinado:",
                    )
                    y = y - 16

                nomes_pos = ["PG", "SG", "SF", "PF", "C", "N/D"]
                labels_pos = [
                    "Armador (PG)",
                    "Ala-armador (SG)",
                    "Ala (SF)",
                    "Ala-pivo (PF)",
                    "Pivo (C)",
                    "Nao definido",
                ]
                for idx in range(len(nomes_pos)):
                    pos = nomes_pos[idx]
                    label = labels_pos[idx]
                    qtd = cobertura.get(pos, 0)
                    _escrever_linha(
                        c, margem, y, f"{label}: {qtd} jogadores", "Helvetica", 9
                    )
                    y = y - 14
    else:
        _escrever_linha(
            c,
            margem,
            y,
            "Nenhum dado de desempenho disponivel para esta temporada ainda.",
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
        dados_win_rate = calcular_win_rate(db=db, temporada=None)
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
