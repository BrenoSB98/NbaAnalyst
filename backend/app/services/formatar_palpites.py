def calcular_linha(valor_previsto):
    if valor_previsto is None:
        return None
    base = int(float(valor_previsto))
    return base + 0.5
 
def calcular_direcao(valor_previsto):
    if valor_previsto is None:
        return None
    linha = calcular_linha(valor_previsto)
    if float(valor_previsto) >= linha:
        return "mais de"
    else:
        return "menos de"
 
def formatar_palpite(valor_previsto):
    if valor_previsto is None:
        return None
    linha = calcular_linha(valor_previsto)
    direcao = calcular_direcao(valor_previsto)
    return {
        "linha": linha,
        "direcao": direcao,
        "label": direcao + " " + str(linha),
    }
 
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