import os
from acordes_dict import acordes
from cifrado_utils import analizar_cifrado

notas_naturales = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11
}

def expandir_cifrado_a_corcheas(cifrado_texto, total_corcheas=256, corcheas_por_compas=8):
    compases = [c.strip() for c in cifrado_texto.split('|') if c.strip()]
    resultado = []
    for compas in compases:
        acordes_compas = [a.strip() for a in compas.split() if a.strip()]
        n_acordes = len(acordes_compas)
        if n_acordes == 0:
            raise ValueError("Compás vacío en cifrado.")
        corcheas_por_acorde = corcheas_por_compas // n_acordes
        resto = corcheas_por_compas - corcheas_por_acorde * n_acordes
        for i, acorde in enumerate(acordes_compas):
            extra = 1 if i < resto else 0
            resultado += [acorde] * (corcheas_por_acorde + extra)
    if len(resultado) < total_corcheas:
        resultado += [resultado[-1]] * (total_corcheas - len(resultado))
    if len(resultado) > total_corcheas:
        resultado = resultado[:total_corcheas]
    return resultado

def notas_midi_acorde(fundamental, grados, base_octava=4):
    if fundamental not in notas_naturales:
        fundamental = 'C'
    base = 12 * base_octava + notas_naturales[fundamental]
    return [base + intervalo for intervalo in grados]

def procesa_midi(reference_midi_path="reference_comping.mid", cifrado="", corcheas_por_compas=8, dur_corchea=0.25):
    import pretty_midi
    midi = pretty_midi.PrettyMIDI(reference_midi_path)
    pista = midi.instruments[0]
    notas = pista.notes

    compases = [c.strip() for c in cifrado.split('|') if c.strip()]
    total_corcheas = len(compases) * corcheas_por_compas
    tiempo_inicio = min(n.start for n in notas)
    tiempo_fin = tiempo_inicio + total_corcheas * dur_corchea

    acordes_corchea = expandir_cifrado_a_corcheas(cifrado, total_corcheas, corcheas_por_compas)
    cache = {}
    acordes_analizados = []
    for a in acordes_corchea:
        if a not in cache:
            cache[a] = analizar_cifrado(a)[0]
        acordes_analizados.append(cache[a])

    for i in range(total_corcheas):
        t0 = tiempo_inicio + i * dur_corchea
        t1 = t0 + dur_corchea
        # Nuevo filtrado para incluir notas activas en el segmento (no solo las que inician)
        notas_corchea = [n for n in notas if not (n.end <= t0 or n.start >= t1)]
        if not notas_corchea:
            continue
        fundamental, grados = acordes_analizados[i]
        nuevas_alturas = notas_midi_acorde(fundamental, grados, base_octava=4)
        usadas = []
        for nota in notas_corchea:
            disponibles = [p for p in nuevas_alturas if p not in usadas]
            if not disponibles:
                disponibles = nuevas_alturas
            mejor = min(disponibles, key=lambda x: abs(nota.pitch - x))
            nota.pitch = mejor
            usadas.append(mejor)

    pista.notes = [n for n in notas if n.start >= tiempo_inicio and n.start < tiempo_fin]

    out_name = os.path.splitext(os.path.basename(reference_midi_path))[0] + "_export.mid"
    midi.write(out_name)
    print(f"Archivo exportado: {out_name}")
    return out_name
