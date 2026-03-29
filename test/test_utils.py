import pytest

from app.etl.func_normalize import _normalizar_string, _normalizar_inteiro, _normalizar_decimal, _normalizar_boolean, _processar_datetime
from app.services.analytics_service import converter_para_int, converter_para_float

class TestNormalizarString:
    def test_string_normal(self):
        resultado = _normalizar_string("Celtics")
        assert resultado == "Celtics"

    def test_string_com_espacos(self):
        resultado = _normalizar_string("  Lakers  ")
        assert resultado == "Lakers"

    def test_string_nula_none(self):
        resultado = _normalizar_string(None)
        assert resultado is None

    def test_string_vazia(self):
        resultado = _normalizar_string("")
        assert resultado is None

    def test_string_tracos(self):
        resultado = _normalizar_string("--")
        assert resultado is None

    def test_string_na(self):
        resultado = _normalizar_string("N/A")
        assert resultado is None

    def test_string_null_texto(self):
        resultado = _normalizar_string("null")
        assert resultado is None

class TestNormalizarInteiro:
    def test_inteiro_normal(self):
        resultado = _normalizar_inteiro(42)
        assert resultado == 42

    def test_string_numerica(self):
        resultado = _normalizar_inteiro("15")
        assert resultado == 15

    def test_none(self):
        resultado = _normalizar_inteiro(None)
        assert resultado is None

    def test_string_vazia(self):
        resultado = _normalizar_inteiro("")
        assert resultado is None

    def test_string_invalida(self):
        resultado = _normalizar_inteiro("abc")
        assert resultado is None

    def test_string_na(self):
        resultado = _normalizar_inteiro("NA")
        assert resultado is None

class TestNormalizarDecimal:
    def test_float_normal(self):
        resultado = _normalizar_decimal(3.14)
        assert resultado == 3.14

    def test_string_decimal(self):
        resultado = _normalizar_decimal("27.5")
        assert resultado == 27.5

    def test_none(self):
        resultado = _normalizar_decimal(None)
        assert resultado is None

    def test_string_vazia(self):
        resultado = _normalizar_decimal("")
        assert resultado is None

    def test_string_invalida(self):
        resultado = _normalizar_decimal("abc")
        assert resultado is None

class TestNormalizarBoolean:
    def test_true_booleano(self):
        resultado = _normalizar_boolean(True)
        assert resultado is True

    def test_false_booleano(self):
        resultado = _normalizar_boolean(False)
        assert resultado is False

    def test_string_true(self):
        resultado = _normalizar_boolean("true")
        assert resultado is True

    def test_string_false(self):
        resultado = _normalizar_boolean("false")
        assert resultado is False

    def test_string_1(self):
        resultado = _normalizar_boolean("1")
        assert resultado is True

    def test_string_0(self):
        resultado = _normalizar_boolean("0")
        assert resultado is False

    def test_none(self):
        resultado = _normalizar_boolean(None)
        assert resultado is None

    def test_inteiro_1(self):
        resultado = _normalizar_boolean(1)
        assert resultado is True

    def test_inteiro_0(self):
        resultado = _normalizar_boolean(0)
        assert resultado is False

class TestProcessarDatetime:
    def test_formato_iso_z(self):
        resultado = _processar_datetime("2025-01-15T20:30:00Z")
        assert resultado is not None
        assert resultado.year == 2025
        assert resultado.month == 1
        assert resultado.day == 15

    def test_formato_iso_sem_z(self):
        resultado = _processar_datetime("2025-03-10T18:00:00")
        assert resultado is not None
        assert resultado.year == 2025

    def test_none(self):
        resultado = _processar_datetime(None)
        assert resultado is None

    def test_string_vazia(self):
        resultado = _processar_datetime("")
        assert resultado is None

    def test_formato_invalido(self):
        resultado = _processar_datetime("nao-e-uma-data")
        assert resultado is None


class TestConverterParaInt:
    def test_inteiro_normal(self):
        resultado = converter_para_int(25)
        assert resultado == 25

    def test_none_retorna_zero(self):
        resultado = converter_para_int(None)
        assert resultado == 0

    def test_string_numerica(self):
        resultado = converter_para_int("12")
        assert resultado == 12

    def test_string_vazia_retorna_zero(self):
        resultado = converter_para_int("")
        assert resultado == 0

class TestConverterParaFloat:
    def test_float_normal(self):
        resultado = converter_para_float(29.5)
        assert resultado == 29.5

    def test_none_retorna_zero(self):
        resultado = converter_para_float(None)
        assert resultado == 0.0

    def test_string_decimal(self):
        resultado = converter_para_float("14.2")
        assert resultado == 14.2

    def test_string_vazia_retorna_zero(self):
        resultado = converter_para_float("")
        assert resultado == 0.0