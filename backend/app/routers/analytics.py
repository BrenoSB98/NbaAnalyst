import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.db_utils import get_db
from app.db.models import Player, Team
from app.routers.auth import obter_usuario_atual
from app.services.analytics_service import (
    buscar_top_pontuadores,
    buscar_top_assistencias,
    buscar_top_rebotes,
    buscar_top_roubos_bola,
    buscar_top_bloqueios,
    buscar_top_turnovers,
    buscar_top_arremessos_campo,
    buscar_top_arremessos_tres,
    buscar_top_lances_livres,
    buscar_top_rebotes_ofensivos,
    buscar_top_rebotes_defensivos,
    buscar_top_faltas_pessoais,
    buscar_top_plus_minus,
    calcular_medias_ultimos_n_jogos,
    calcular_medias_casa_fora,
    calcular_medias_temporada_completa,
    calcular_medias_contra_time,
)

router = APIRouter()
logger = logging.getLogger(__name__)

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

@router.get("/lideres/{temporada}/pontos")
def get_top_pontuadores(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_pontuadores(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/assistencias")
def get_top_assistencias(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_assistencias(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/rebotes")
def get_top_rebotes(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_rebotes(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/roubos-bola")
def get_top_roubos_bola(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_roubos_bola(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/bloqueios")
def get_top_bloqueios(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_bloqueios(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/turnovers")
def get_top_turnovers(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_turnovers(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/arremessos-campo")
def get_top_arremessos_campo(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_arremessos_campo(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/arremessos-tres")
def get_top_arremessos_tres(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_arremessos_tres(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/lances-livres")
def get_top_lances_livres(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_lances_livres(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/rebotes-ofensivos")
def get_top_rebotes_ofensivos(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_rebotes_ofensivos(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/rebotes-defensivos")
def get_top_rebotes_defensivos(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_rebotes_defensivos(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/faltas-pessoais")
def get_top_faltas_pessoais(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_faltas_pessoais(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/lideres/{temporada}/plus-minus")
def get_top_plus_minus(temporada: int, limite: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    resultado = buscar_top_plus_minus(db, temporada, limite)
    if not resultado:
        return {"temporada": temporada, "total": 0, "lideres": []}
    return {"temporada": temporada, "total": len(resultado), "lideres": resultado}

@router.get("/jogadores/{jogador_id}/medias/ultimos-jogos")
def get_medias_ultimos_n_jogos(jogador_id: int, n_jogos: int = Query(default=10, ge=1, le=82), temporada: int = Query(default=None), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    resultado = calcular_medias_ultimos_n_jogos(db, jogador_id, n_jogos, temporada)

    if not resultado:
        logger.warning(f"Nenhum dado encontrado para médias dos últimos jogos")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "mensagem": "Nenhum dado encontrado."}

    resultado["jogador_id"] = jogador_id
    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    return resultado

@router.get("/jogadores/{jogador_id}/medias/casa-fora")
def get_medias_casa_fora(jogador_id: int, temporada: int = Query(...), local: str = Query(default="casa", pattern="^(casa|fora)$"), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)

    if local == "casa":
        location = "home"
    else:
        location = "away"

    resultado = calcular_medias_casa_fora(db, jogador_id, temporada, location)
    if not resultado:
        logger.warning(f"Nenhum dado encontrado para médias casa/fora")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "mensagem": "Nenhum dado encontrado."}

    resultado["jogador_id"] = jogador_id
    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["local"] = local
    resultado["temporada"] = temporada
    return resultado

@router.get("/jogadores/{jogador_id}/medias/temporada")
def get_medias_temporada_completa(jogador_id: int, temporada: int = Query(...), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    resultado = calcular_medias_temporada_completa(db, jogador_id, temporada)

    if not resultado:
        logger.warning(f"Nenhum dado encontrado para médias da temporada")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "mensagem": "Nenhum dado encontrado."}

    resultado["jogador_id"] = jogador_id
    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["temporada"] = temporada
    return resultado

@router.get("/jogadores/{jogador_id}/medias/contra-time/{time_adversario_id}")
def get_medias_contra_time(jogador_id: int, time_adversario_id: int, temporada: int = Query(default=None), db: Session = Depends(get_db), usuario_atual=Depends(obter_usuario_atual)):
    jogador = _validar_jogador(db, jogador_id)
    time_adversario = _validar_time(db, time_adversario_id)
    resultado = calcular_medias_contra_time(db, jogador_id, time_adversario_id, temporada)

    if not resultado:
        logger.warning(f"Nenhum dado encontrado para médias contra time")
        return {"jogador_id": jogador_id, "nome_jogador": f"{jogador.firstname} {jogador.lastname}", "mensagem": "Nenhum dado encontrado."}

    resultado["jogador_id"] = jogador_id
    resultado["nome_jogador"] = f"{jogador.firstname} {jogador.lastname}"
    resultado["time_adversario_id"] = time_adversario_id
    resultado["nome_adversario"] = time_adversario.name

    if temporada:
        resultado["temporada"] = temporada
    return resultado