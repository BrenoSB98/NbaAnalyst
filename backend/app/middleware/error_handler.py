from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

async def tratar_erros_globais(request: Request, call_next):
    try:
        resposta = await call_next(request)
        return resposta

    except SQLAlchemyError as erro:
        return JSONResponse(
            status_code=500,
            content={
                "erro": "Erro interno no banco de dados.",
                "detalhe": str(erro),
            },
        )

    except ValueError as erro:
        return JSONResponse(
            status_code=400,
            content={
                "erro": "Valor inválido na requisição.",
                "detalhe": str(erro),
            },
        )

    except KeyError as erro:
        return JSONResponse(
            status_code=400,
            content={
                "erro": "Campo obrigatório ausente na requisição.",
                "detalhe": str(erro),
            },
        )

    except Exception as erro:
        return JSONResponse(
            status_code=500,
            content={
                "erro": "Erro interno inesperado no servidor.",
                "detalhe": str(erro),
            },
        )