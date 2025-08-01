from cifrado_utils import analizar_cifrado
from procesa_midi import notas_midi_acorde, enlazar_notas


def test_m7b5_aliases():
    aliases = ["Bø", "Bø7", "Bm7(b5)", "Bmin7b5", "B-7b5", "Bmi7b5"]
    esperado = ("B", [0, 3, 6, 10])
    for cif in aliases:
        assert analizar_cifrado(cif) == [esperado]


def test_6_9_parsing_and_midi():
    cifrado = "C6(9)"
    esperado = ("C", [2, 4, 7, 9])
    assert analizar_cifrado(cifrado) == [esperado]
    assert notas_midi_acorde(*esperado) == [50, 52, 55, 57]


def test_enlazar_notas_minimo_movimiento():
    previas = [72, 60, 64, 67]
    nuevas = [60, 64, 67, 71]
    assert enlazar_notas(previas, nuevas) == [71, 60, 64, 67]


def test_inversion_limita_salto_de_bajo():
    primero = notas_midi_acorde("C", [0, 4, 7])
    segundo = notas_midi_acorde("B", [0, 4, 7], prev_bajo=primero[0])
    assert abs(segundo[0] - primero[0]) <= 5
    assert segundo == [47, 51, 54]
