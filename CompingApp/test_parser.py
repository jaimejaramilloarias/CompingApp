from cifrado_utils import analizar_cifrado
from procesa_midi import notas_midi_acorde


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
