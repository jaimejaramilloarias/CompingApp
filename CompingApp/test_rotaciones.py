from procesa_midi import aplicar_rotaciones

class Note:
    def __init__(self, pitch, start):
        self.pitch = pitch
        self.start = start


def group_pitches(notes):
    groups = {}
    for n in notes:
        groups.setdefault(n.start, []).append(n.pitch)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def test_rotacion_global():
    notas = [
        Note(60, 0), Note(64, 0), Note(67, 0), Note(72, 0),
        Note(61, 1), Note(65, 1), Note(68, 1), Note(73, 1),
    ]
    aplicar_rotaciones(notas, rotacion=1)
    grupos = group_pitches(notas)
    assert grupos[0] == [64, 67, 72, 72]
    assert grupos[1] == [65, 68, 73, 73]


def test_rotacion_por_acorde():
    notas = [
        Note(60, 0), Note(64, 0), Note(67, 0), Note(72, 0),
        Note(61, 1), Note(65, 1), Note(68, 1), Note(73, 1),
    ]
    aplicar_rotaciones(notas, rotaciones={1: 1})
    grupos = group_pitches(notas)
    assert grupos[0] == [60, 64, 67, 72]
    assert grupos[1] == [65, 68, 73, 73]
