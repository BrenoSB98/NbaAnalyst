from pydantic import BaseModel
from typing import List, Optional

class EntradaHistorico(BaseModel):
    papel: str
    conteudo: str
  
class RequisicaoChat(BaseModel):
    pergunta: str
    historico: Optional[List[EntradaHistorico]] = []
    modelo: Optional[str] = "gpt-4o-mini"
  
class RespostaChat(BaseModel):
    resposta: str