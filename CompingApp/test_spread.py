from procesa_midi import Spread


class Note:
    def __init__(self, pitch, start=0.0, end=1.0, velocity=100):
        self.pitch = pitch
        self.start = start
        self.end = end
        self.velocity = velocity


def test_spread_agrega_nota_intermedia():
    notas = [Note(p) for p in (60, 64, 67, 71)]
    Spread(notas)
    pitches = sorted(n.pitch for n in notas)
    # Se agregan tres notas nuevas
    assert len(notas) == 7
    assert pitches.count(64) == 1
    # Notas duplicadas: E+12, B+12 y E+24
    assert {76, 83, 88}.issubset(set(pitches))

    segunda = [n for n in notas if n.pitch == 64][0]
    for p in (76, 88):
        dup = [n for n in notas if n.pitch == p][0]
        assert dup.start == segunda.start
        assert dup.end == segunda.end
        assert dup.velocity == segunda.velocity

    alto = [n for n in notas if n.pitch == 71][0]
    intermedia = [n for n in notas if n.pitch == 83][0]
    assert intermedia.start == alto.start
    assert intermedia.end == alto.end
    assert intermedia.velocity == alto.velocity
