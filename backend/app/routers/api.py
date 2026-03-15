from fastapi import APIRouter

from app.routers import analytics, auth, backtest, bet, player, game, league, win_rate, onerb, predictions, season, team, chat

router = APIRouter()

router.include_router(season.router, prefix="/temporadas", tags=["Temporadas"])
router.include_router(league.router, prefix="/ligas", tags=["Ligas"])
router.include_router(team.router, prefix="/times", tags=["Times"])
router.include_router(game.router, prefix="/jogos", tags=["Jogos"])
router.include_router(player.router, prefix="/jogadores", tags=["Jogadores"])
router.include_router(analytics.router, prefix="/analiticos", tags=["Analíticos"])
router.include_router(predictions.router, prefix="/predicoes", tags=["Predições"])
router.include_router(bet.router, prefix="/apostas", tags=["Apostas"])
router.include_router(win_rate.router, prefix="/win_rate", tags=["Desempenho"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(backtest.router, prefix="/backtest", tags=["Backtest"])
router.include_router(onerb.router, prefix="/onerb", tags=["OneRB"])
router.include_router(auth.router, prefix="/autenticacao", tags=["Autenticação"])