import logging

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.routers.auth import obter_usuario_atual

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
def onerb(usuario_atual=Depends(obter_usuario_atual)):
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Oráculo NBA</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { overflow: hidden; background: #0e1117; }
            iframe { width: 100vw; height: 100vh; border: none; display: block; }
        </style>
    </head>
    <body>
        <iframe src="http://localhost:8502" allowfullscreen></iframe>
    </body>
    </html>
    """
    return html