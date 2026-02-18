from app.db.db_utils import get_db_session
from app.db.models import Game

with get_db_session() as db:
    total = db.query(Game).count()
    print("Total de jogos:", total)

    # Conferir algumas linhas
    alguns = db.query(Game).limit(5).all()
    for g in alguns:
        print(g.id, g.season, g.date, g.home_team_id, g.away_team_id)