def calcular_linha_referencia(media_recente):
    if media_recente is None:
        return None
    base = int(float(media_recente))
    parte_decimal = float(media_recente) - base
    if parte_decimal >= 0.5:
        return base + 0.5
    else:
        if base == 0:
            return 0.5
        return base - 0.5


def calcular_direcao(valor_previsto, linha):
    if valor_previsto is None or linha is None:
        return None
    if float(valor_previsto) >= linha:
        return "mais de"
    else:
        return "menos de"


def formatar_palpite(valor_previsto, linha):
    if valor_previsto is None or linha is None:
        return None
    direcao = calcular_direcao(valor_previsto, linha)
    return {
        "linha": linha,
        "direcao": direcao,
        "label": direcao + " " + str(linha),  # type: ignore
    }


def verificar_acerto_linha(valor_previsto, valor_real, linha):
    if valor_previsto is None or valor_real is None or linha is None:
        return None
    direcao = calcular_direcao(valor_previsto, linha)
    valor_real_float = float(valor_real)
    if direcao == "mais de":
        return valor_real_float >= linha
    else:
        return valor_real_float < linha
