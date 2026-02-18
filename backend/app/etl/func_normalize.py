from typing import Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STRINGS_NULAS_INVALIDAS = {"", "-", "--", "—", "N/A", "NA", None, "null", "NULL"}

def _normalizar_string(valor: Optional[str]) -> Optional[str]:
    """
    Normaliza valores string, convertendo strings vazias ou inválidas em None.
    """
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if valor in STRINGS_NULAS_INVALIDAS:
            return None
    return valor


def _normalizar_inteiro(valor) -> Optional[int]:
    """
    Normaliza valores inteiros, convertendo strings vazias ou inválidas em None.
    """
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if valor in STRINGS_NULAS_INVALIDAS:
            return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _normalizar_decimal(valor) -> Optional[float]:
    """
    Normaliza valores decimais, convertendo strings vazias ou inválidas em None.
    """
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if valor in STRINGS_NULAS_INVALIDAS:
            return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None

def _processar_datetime(valor: Optional[str]) -> Optional[datetime]:
    """
    Converte string de data/hora para objeto datetime.
    """
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(valor, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            logger.warning(f"Formato de data/hora inválido recebido: {valor}")
            return None

def _normalizar_boolean(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {"true", "1", "yes"}:
            return True
        if value in {"false", "0", "no"}:
            return False
    if isinstance(value, int):
        return bool(value)
    return None