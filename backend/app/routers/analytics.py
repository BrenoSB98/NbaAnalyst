import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Game, GameTeamScore, Player, PlayerGameStats, Team
from app.routers.auth import obter_usuario_atual
from app.schemas.analytics import LideresResponse, MaioresPontuadoresResponse, MediasCasaForaResponse, MediasContraTimeResponse, MediasTemporadaResponse, MediasUltimosJogosResponse, TendenciasTimeResponse
from app.services.analytics_service import (
    buscar_top_assistencias,
    buscar_top_arremessos_campo,
    buscar_top_arremessos_tres,
    buscar_top_bloqueios,
    buscar_top_faltas_pessoais,
    buscar_top_lances_livres,
    buscar_top_plus_minus,
    buscar_top_pontuadores,
    buscar_top_rebotes,
    buscar_top_rebotes_defensivos,
    buscar_top_rebotes_ofensivos,
    buscar_top_roubos_bola,
    buscar_top_turnovers,
    calcular_medias_casa_fora,
    calcular_medias_contra_time,
    calcular_medias_temporada_completa,
    calcular_medias_ultimos_n_jogos,
    calcular_totais_e_medias
)

router = APIRouter()
logger = logging.getLogger(__name__)

CATEGORIAS = {
    "pontos": PlayerGameStats.points,
    "assistencias": PlayerGameStats.assists,
    "rebotes": PlayerGameStats.tot_reb,
    "roubos": PlayerGameStats.steals,
    "bloqueios": PlayerGameStats.blocks,
    "turnovers": PlayerGameStats.turnovers,
    "arremessos-campo": PlayerGameStats.fgm,
    "arremessos-tres": PlayerGameStats.tpm,
    "lances-livres": PlayerGameStats.ftm,
    "plus-minus": PlayerGameStats.plus_minus,
}

def _validar_jogador(db, player_id):
    jogador = db.query(Player).filter(Player.id == player_id).first()
    if not jogador:
        raise HTTPException(status_code=404, detail=f"Jogador {player_id} não encontrado.")
    return jogador

def _validar_time(db, team_id):
    time = db.query(Team).filter(Team.id == team_id).first()
    if not time:
        raise HTTPException(status_code=404, detail=f"Time {team_id} não encontrado.")
    return time

@router.get("/lideres/{temporada}/pontos", response_model=LideresResponse)
def get_top_pontuadores(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_pontuadores(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/assistencias", response_model=LideresResponse)
def get_top_assistencias(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_assistencias(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/rebotes", response_model=LideresResponse)
def get_top_rebotes(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_rebotes(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/roubos-bola", response_model=LideresResponse)
def get_top_roubos_bola(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_roubos_bola(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/bloqueios", response_model=LideresResponse)
def get_top_bloqueios(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_bloqueios(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/turnovers", response_model=LideresResponse)
def get_top_turnovers(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_turnovers(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/arremessos-campo", response_model=LideresResponse)
def get_top_arremessos_campo(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_arremessos_campo(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/arremessos-tres", response_model=LideresResponse)
def get_top_arremessos_tres(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_arremessos_tres(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/lances-livres", response_model=LideresResponse)
def get_top_lances_livres(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_lances_livres(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/rebotes-ofensivos", response_model=LideresResponse)
def get_top_rebotes_ofensivos(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_rebotes_ofensivos(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/rebotes-defensivos", response_model=LideresResponse)
def get_top_rebotes_defensivos(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_rebotes_defensivos(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/faltas-pessoais", response_model=LideresResponse)
def get_top_faltas_pessoais(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_faltas_pessoais(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/plus-minus", response_model=LideresResponse)
def get_top_plus_minus(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_plus_minus(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/jogadores/{jogador_id}/medias/ultimos-jogos", response_model=MediasUltimosJogosResponse)
def get_medias_ultimos_n_jogos(jogador_id: int, n_jogos: int = Query(default=10, ge=1, le=82), temporada: int = Query(default=None), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    resultado = calcular_medias_ultimos_n_jogos(db, jogador_id, n_jogos, temporada)

    if not resultado:
        logger.warning(f"Nenhum dado encontrado —> jogador_id={jogador_id}, n_jogos={n_jogos}, temporada={temporada}")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "mensagem": "Nenhum dado encontrado."}

    resultado["jogador_id"] = jogador_id
    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    return resultado

@router.get("/jogadores/{jogador_id}/medias/casa-fora", response_model=MediasCasaForaResponse)
def get_medias_casa_fora(jogador_id: int, temporada: int = Query(...), local: str = Query(default="casa", pattern="^(casa|fora)$"), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)

    if local == "casa":
        location = "home"
    else:
        location = "away"

    resultado = calcular_medias_casa_fora(db, jogador_id, temporada, location)

    if not resultado:
        logger.warning(f"Nenhum dado encontrado para médias casa/fora — jogador_id={jogador_id}, temporada={temporada}, local={local}")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "mensagem": "Nenhum dado encontrado."}

    resultado["jogador_id"] = jogador_id
    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["local"] = local
    resultado["temporada"] = temporada
    return resultado

@router.get("/jogadores/{jogador_id}/medias/temporada", response_model=MediasTemporadaResponse)
def get_medias_temporada_completa(jogador_id: int, temporada: int = Query(None), db: Session = Depends(get_db)):
    jogador = _validar_jogador(db, jogador_id)
    
    if temporada is not None:
        resultado = calcular_medias_temporada_completa(db, jogador_id, temporada)
    else:
        stats_query = (db.query(PlayerGameStats, Game).join(Game, PlayerGameStats.game_id == Game.id).filter(PlayerGameStats.player_id == jogador_id, Game.status_short == 3).all())
        resultado = calcular_totais_e_medias(stats_query)
        if resultado:
            resultado["games_played"] = resultado.pop("num_jogos")
            
    if not resultado:
        logger.warning(f"Nenhum dado encontrado  —> jogador_id={jogador_id}, temporada={temporada}")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "temporada": temporada, "mensagem": "Nenhum dado encontrado."}

    avgs = resultado.get("averages")
    return {
        "jogador_id": jogador_id,
        "nome_jogador": f"{jogador.firstname} {jogador.lastname}",
        "temporada": temporada,
        "jogos_disputados": resultado.get("games_played", 0),
        "medias": {
            "pontos": avgs.get("points"),
            "assistencias": avgs.get("assists"),
            "rebotes": avgs.get("rebounds"),
            "roubos": avgs.get("steals"),
            "bloqueios": avgs.get("blocks"),
            "turnovers": avgs.get("turnovers"),
            "fg_pct": avgs.get("fg_pct"),
            "three_pct": avgs.get("three_pct"),
            "ft_pct": avgs.get("ft_pct"),
            "minutos": avgs.get("minutes"),
            "plus_minus": avgs.get("plus_minus"),
        },
    }

@router.get("/jogadores/{jogador_id}/medias/contra-time/{time_adversario_id}", response_model=MediasContraTimeResponse)
def get_medias_contra_time(jogador_id: int, time_adversario_id: int, temporada: int = Query(default=None), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    time_adversario = _validar_time(db, time_adversario_id)
    resultado = calcular_medias_contra_time(db, jogador_id, time_adversario_id, temporada)

    if not resultado:
        logger.warning(f"Nenhum dado encontrado para médias contra time — jogador_id={jogador_id}, time_adversario_id={time_adversario_id}, temporada={temporada}")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "mensagem": "Nenhum dado encontrado."}

    resultado["jogador_id"] = jogador_id
    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["time_adversario_id"] = time_adversario_id
    resultado["nome_adversario"] = time_adversario.name

    if temporada:
        resultado["temporada"] = temporada

    return resultado

@router.get("/maiores-pontuadores", response_model=MaioresPontuadoresResponse)
def maiores_pontuadores(temporada: int = Query(2025), limite: int = Query(10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultados = (db.query(Player.id, Player.firstname, Player.lastname, func.count(PlayerGameStats.game_id).label("jogos"), func.sum(PlayerGameStats.points).label("total_pontos"), func.avg(PlayerGameStats.points).label("media_pontos"))
                  .join(PlayerGameStats, Player.id == PlayerGameStats.player_id).join(Game, PlayerGameStats.game_id == Game.id).filter(Game.season == temporada, Game.status_short == 3)
                  .group_by(Player.id, Player.firstname, Player.lastname).order_by(desc("media_pontos")).limit(limite).all())

    lista = []
    for r in resultados:
        lista.append({
            "jogador_id": r.id,
            "nome_jogador": f"{r.firstname} {r.lastname}",
            "jogos_disputados": r.jogos,
            "total_pontos": r.total_pontos,
            "media_pontos": round(float(r.media_pontos), 2),
        })

    return {"temporada": temporada, "total": len(lista), "maiores_pontuadores": lista}

@router.get("/tendencias-time/{time_id}", response_model=TendenciasTimeResponse)
def tendencias_time(time_id: int, temporada: int = Query(2025), ultimos_n_jogos: int = Query(10, ge=1, le=20), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    time = db.query(Team).filter(Team.id == time_id).first()
    if not time:
        logger.warning(f"Time não encontrado ao buscar tendências: id={time_id}")
        raise HTTPException(status_code=404, detail="Time não encontrado.")

    jogos = (db.query(Game, GameTeamScore).join(GameTeamScore, GameTeamScore.game_id == Game.id).filter(Game.season == temporada, GameTeamScore.team_id == time_id, Game.status_short == 3).order_by(Game.date_start.desc()).limit(ultimos_n_jogos).all())

    if len(jogos) == 0:
        logger.warning(f"Sem jogos finalizados para tendências — time_id={time_id}, temporada={temporada}")
        raise HTTPException(status_code=404, detail="Sem jogos finalizados para este time na temporada informada.")

    vitorias = 0
    pontos_feitos = []
    pontos_sofridos = []

    for jogo_data in jogos:
        jogo = jogo_data[0]
        score = jogo_data[1]

        adversario = db.query(GameTeamScore).filter(GameTeamScore.game_id == jogo.id, GameTeamScore.team_id != time_id).first()
        if adversario:
            if score.points is not None:
                pts_feitos = score.points 
            else:
                pts_feitos = 0
            if adversario.points is not None:
                pts_sofridos = adversario.points     
            else:
                pts_sofridos = 0

            pontos_feitos.append(pts_feitos)
            pontos_sofridos.append(pts_sofridos)

            if pts_feitos > pts_sofridos:
                vitorias = vitorias + 1

    num_jogos = len(pontos_feitos)
    derrotas = num_jogos - vitorias
    if num_jogos > 0:
        aproveitamento = round(vitorias / num_jogos * 100, 2) 
    else:
        aproveitamento = 0.0
    if num_jogos > 0:
        media_feitos = round(sum(pontos_feitos) / num_jogos, 2) 
    else:
        media_feitos = 0.0
    if num_jogos > 0:
        media_sofridos = round(sum(pontos_sofridos) / num_jogos, 2) 
    else:
        media_sofridos = 0.0
    if num_jogos > 0:
        diferencial = round((sum(pontos_feitos) - sum(pontos_sofridos)) / num_jogos, 2) 
    else:
        diferencial = 0.0

    tendencia_ofensiva = "estavel"
    if len(pontos_feitos) >= 3:
        if pontos_feitos[0] > pontos_feitos[-1]:
            tendencia_ofensiva = "melhorando"
        else:
            tendencia_ofensiva = "piorando"

    tendencia_defensiva = "estavel"
    if len(pontos_sofridos) >= 3:
        if pontos_sofridos[0] < pontos_sofridos[-1]:
            tendencia_defensiva = "melhorando"
        else:
            tendencia_defensiva = "piorando"

    return {
        "time_id": time_id,
        "nome_time": time.name,
        "temporada": temporada,
        "ultimos_n_jogos": num_jogos,
        "record": f"{vitorias}-{derrotas}",
        "aproveitamento": aproveitamento,
        "media_pontos_feitos": media_feitos,
        "media_pontos_sofridos": media_sofridos,
        "diferencial_pontos": diferencial,
        "tendencia_ofensiva": tendencia_ofensiva,
        "tendencia_defensiva": tendencia_defensiva,
    }

@router.get("/lideres")
def lideres_publico(categoria: str = Query("pontos"), temporada: int = Query(None), limite: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    stat_field = CATEGORIAS.get(categoria)
    if stat_field is None:
        raise HTTPException(status_code=400, detail=f"Categoria inválida: {categoria}. Use: {list(CATEGORIAS.keys())}")
 
    query = (db.query(PlayerGameStats.player_id, func.sum(stat_field).label("total"), func.count(PlayerGameStats.game_id).label("jogos")).join(Game, PlayerGameStats.game_id == Game.id).filter(Game.status_short == 3))
 
    if temporada is not None:
        query = query.filter(Game.season == temporada)
 
    resultados = query.group_by(PlayerGameStats.player_id).order_by(desc("total")).limit(limite).all()
 
    lideres = []
    for row in resultados:
        jogador = db.query(Player).filter(Player.id == row[0]).first()
        if jogador:
            nome_jogador = f"{jogador.firstname} {jogador.lastname}"     
        else:
            nome_jogador = "Desconhecido"
        if row[1] is not None:
            total = row[1] 
        else:
            total = 0
        if row[2] > 0:
            jogos = row[2]     
        else:
            jogos = 1
        media = round(total / jogos, 2)
        lideres.append({"player_id": row[0], "player_name": nome_jogador, "games_played": row[2], "avg": media})
 
    return {"categoria": categoria, "temporada": temporada, "total": len(lideres), "lideres": lideres}
  
@router.get("/recordes")
def recordes_publico(categoria: str = Query("pontos"), temporada: int = Query(None), limite: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    stat_field = CATEGORIAS.get(categoria)
    if stat_field is None:
        raise HTTPException(status_code=400, detail=f"Categoria inválida: {categoria}. Use: {list(CATEGORIAS.keys())}")
 
    query = (db.query(PlayerGameStats.player_id, PlayerGameStats.game_id, stat_field.label("valor"), Game.date_start, Game.home_team_id, Game.away_team_id, PlayerGameStats.team_id)
               .join(Game, PlayerGameStats.game_id == Game.id).filter(Game.status_short == 3, stat_field.isnot(None)))
 
    if temporada is not None:
        query = query.filter(Game.season == temporada)
 
    resultados = query.order_by(desc("valor")).limit(limite).all()
 
    recordes = []
    for row in resultados:
        player_id  = row[0]
        game_id    = row[1]
        valor      = row[2]
        data_jogo  = row[3]
        home_id    = row[4]
        away_id    = row[5]
        team_id    = row[6]
 
        jogador = db.query(Player).filter(Player.id == player_id).first()
        if jogador is not None:
            nome_jogador = f"{jogador.firstname} {jogador.lastname}"     
        else:
            nome_jogador = "Desconhecido"
 
        if team_id == home_id:
            adversario_id = away_id
        else:
            adversario_id = home_id
 
        time_adv = db.query(Team).filter(Team.id == adversario_id).first()
        if time_adv is not None:
            nome_adversario = time_adv.name 
        else:
            nome_adversario = "—"
        if time_adv:
            logo_adversario = time_adv.logo    
        else:
            logo_adversario = None
 
        if data_jogo:
            data_fmt = data_jogo.strftime("%d/%m/%Y") 
        else:
            data_fmt = "—"
 
        recordes.append({
            "player_id": player_id,
            "player_name": nome_jogador,
            "game_id": game_id,
            "valor": valor,
            "data": data_fmt,
            "adversario": nome_adversario,
            "logo_adversario": logo_adversario,
        })
 
    return {"categoria": categoria, "temporada": temporada, "total": len(recordes), "recordes": recordes}