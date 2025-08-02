from procesa_midi import recortar_notas_a_segmento

class DummyNote:
    def __init__(self, start, end, pitch=60):
        self.start = start
        self.end = end
        self.pitch = pitch


def test_recorta_nota_larga():
    n = DummyNote(0.0, 0.5)
    recortar_notas_a_segmento([n], 0.0, 0.25)
    assert n.start == 0.0
    assert n.end == 0.25


def test_no_alarga_nota_corta():
    n = DummyNote(0.05, 0.20)
    recortar_notas_a_segmento([n], 0.0, 0.25)
    assert n.start == 0.05
    assert n.end == 0.20


def test_recorta_inicio_fuera_segmento():
    n = DummyNote(-0.1, 0.2)
    recortar_notas_a_segmento([n], 0.0, 0.25)
    assert n.start == 0.0
    assert n.end == 0.2
