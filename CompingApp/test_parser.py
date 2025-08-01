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


def test_extensiones_reemplazan_notas():
    nombres = {0: 'C', 1: 'Db', 2: 'D', 3: 'Eb', 4: 'E', 5: 'F', 6: 'Gb', 7: 'G', 8: 'Ab', 9: 'A', 10: 'Bb', 11: 'B'}
    cifrados = ["Dm7(9)", "G13", "C∆(9)", "C6(9)"]
    esperados = [
        ['E', 'F', 'A', 'C'],
        ['A', 'B', 'E', 'F'],
        ['D', 'E', 'G', 'B'],
        ['D', 'E', 'G', 'A'],
    ]
    for cif, notas_esp in zip(cifrados, esperados):
        fund, grados = analizar_cifrado(cif)[0]
        midi = notas_midi_acorde(fund, grados)
        notas = [nombres[n % 12] for n in midi]
        assert sorted(notas) == sorted(notas_esp)


def test_enlazar_notas_minimo_movimiento():
    previas = [72, 60, 64, 67]
    nuevas = [60, 64, 67, 71]
    assert enlazar_notas(previas, nuevas) == [71, 60, 64, 67]


def test_inversion_limita_salto_de_bajo():
    primero = notas_midi_acorde("C", [0, 4, 7, 10])
    segundo = notas_midi_acorde("B", [0, 4, 7, 10], prev_bajo=primero[0])
    assert primero == [60, 64, 67, 70]
    assert abs(segundo[0] - primero[0]) <= 5
    assert segundo == [59, 63, 66, 69]


def test_rango_de_voces():
    """La voz superior no debe superar C5 y la inferior no debe bajar de D3."""
    primero = notas_midi_acorde("C", [0, 4, 7, 11])
    assert primero[0] >= 50
    assert max(primero) <= 72

    # Forzar un bajo previo alto para comprobar el límite superior
    segundo = notas_midi_acorde("F", [0, 4, 7, 11], prev_bajo=65)
    assert abs(segundo[0] - 65) <= 5
    assert segundo[0] >= 50
    assert max(segundo) <= 72
