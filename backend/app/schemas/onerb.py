from typing import List, Optional

from pydantic import BaseModel


class EntradaHistorico(BaseModel):
    papel: str
    conteudo: str


class RequisicaoChat(BaseModel):
    pergunta: str
    historico: Optional[List[EntradaHistorico]] = []
    tokens_sessao: Optional[int] = 0


class RespostaChat(BaseModel):
    resposta: str
    tokens_sessao: Optional[int] = 0
