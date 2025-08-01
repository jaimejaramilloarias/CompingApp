import signal
import pytest
from procesa_midi import notas_midi_acorde


def test_notas_midi_acorde_no_infinite_loop():
    # Configurar alarma para evitar bucles infinitos
    def handler(signum, frame):
        raise TimeoutError("timeout")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(1)
    try:
        # Este acorde artificial (todas las notas a una distancia de seis
        # semitonos del bajo previo) provocaba un bucle infinito en la versión
        # anterior.
        notas = notas_midi_acorde('C', [6, 18, 30, 42], base_octava=4, prev_bajo=60)
    finally:
        signal.alarm(0)
    assert len(notas) == 4
