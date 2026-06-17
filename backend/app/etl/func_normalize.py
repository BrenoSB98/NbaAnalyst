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


def normalizar_posicao(pos_crua, media_assists=None, media_rebotes=None):
    if pos_crua is None:
        return None
    pos = str(pos_crua).strip().upper()
    if pos == "":
        return None

    posicoes_diretas = ["PG", "SG", "SF", "PF", "C"]
    if pos in posicoes_diretas:
        return pos

    primeira = pos.split("-")[0]

    if primeira == "C":
        return "C"
    if primeira == "PG":
        return "PG"
    if primeira == "SG":
        return "SG"
    if primeira == "SF":
        return "SF"
    if primeira == "PF":
        return "PF"

    if primeira == "G":
        if media_assists is not None and media_assists >= 4.5:
            return "PG"
        else:
            return "SG"

    if primeira == "F":
        if media_rebotes is not None and media_rebotes >= 6.0:
            return "PF"
        else:
            return "SF"

    return None
