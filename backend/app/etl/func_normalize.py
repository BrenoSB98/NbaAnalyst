from datetime import datetime

STRINGS_NULAS_INVALIDAS = {"", "-", "--", "—", "N/A", "NA", None, "null", "NULL"}

def _normalizar_string(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if valor in STRINGS_NULAS_INVALIDAS:
            return None
    return valor

def _normalizar_inteiro(valor):
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

def _normalizar_decimal(valor):
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

def _processar_datetime(valor):
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(valor, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

def _normalizar_boolean(valor):
    if valor is None:
        return None
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        valor = valor.strip().lower()
        if valor in {"true", "1", "yes"}:
            return True
        if valor in {"false", "0", "no"}:
            return False
    if isinstance(valor, int):
        return bool(valor)
    return None