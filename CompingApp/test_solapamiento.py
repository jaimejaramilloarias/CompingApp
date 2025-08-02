import types
from procesa_midi import evitar_solapamientos

class DummyNote:
    def __init__(self, start, end, pitch):
        self.start = start
        self.end = end
        self.pitch = pitch

def test_evitar_solapamientos():
    n1 = DummyNote(0.0, 1.0, 60)
    n2 = DummyNote(0.9, 1.5, 60)
    notas = [n1, n2]
    evitar_solapamientos(notas)
    assert n1.end <= n2.start and n1.end >= n1.start

def test_no_cambio_sin_solapamiento():
    n1 = DummyNote(0.0, 0.5, 60)
    n2 = DummyNote(0.6, 1.0, 60)
    notas = [n1, n2]
    evitar_solapamientos(notas)
    assert n1.end == 0.5
