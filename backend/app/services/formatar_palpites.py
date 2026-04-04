def calcular_linha(valor_previsto):
    if valor_previsto is None:
        return None

    base = int(float(valor_previsto))
    linha = base + 0.5
    return linha

def calcular_direcao(valor_previsto):
    if valor_previsto is None:
        return None

    linha = calcular_linha(valor_previsto)
    valor_float = float(valor_previsto)

    if valor_float >= linha:
        return "+ de"
    else:
        return "- de"

def formatar_palpite(valor_previsto):
    if valor_previsto is None:
        return None

    linha = calcular_linha(valor_previsto)
    direcao = calcular_direcao(valor_previsto)

    resultado = {}
    resultado["linha"] = linha
    resultado["direcao"] = direcao
    resultado["label"] = direcao + " " + str(linha)
    return resultado

def verificar_acerto_linha(valor_previsto, valor_real):
    if valor_previsto is None or valor_real is None:
        return None

    linha = calcular_linha(valor_previsto)
    direcao = calcular_direcao(valor_previsto)
    valor_real_float = float(valor_real)

    if direcao == "mais de":
        return valor_real_float >= linha
    else:
        return valor_real_float < linha