from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/onerb", response_class=HTMLResponse, summary="Acesso ao Onerb NBA")
def onerb():
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
        <iframe src="http://localhost:8501" allowfullscreen></iframe>
    </body>
    </html>
    """
    return html