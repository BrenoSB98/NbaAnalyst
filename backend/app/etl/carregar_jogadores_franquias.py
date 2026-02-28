from app.db.models import Team
from app.db.db_utils import get_db
from app.etl.carregar_jogadores import carregar_jogadores

def carregar_jogadores_franquias(season):
    for db in get_db():
        times = db.query(Team).filter(Team.nba_franchise == True).all()

        if not times:
            return

        for time in times:
            try:
                carregar_jogadores(team_id=time.id, season=season)
            except Exception:
                continue

if __name__ == "__main__":
    carregar_jogadores_franquias(season=2023)