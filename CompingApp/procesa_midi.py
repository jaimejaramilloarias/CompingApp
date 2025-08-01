import os
import itertools
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

def notas_midi_acorde(fundamental, grados, base_octava=4, prev_bajo=None, inversion=0):
    """Devuelve las notas MIDI del acorde.

    Si ``prev_bajo`` es ``None`` se utiliza la inversión indicada por
    ``inversion`` (0=fundamental, 1=1ª inversión, ...).  Para los acordes
    siguientes se elige automáticamente la inversión y el desplazamiento de
    octava cuya nota más grave quede lo más cercana posible a ``prev_bajo``.
    El resultado siempre contiene cuatro notas en posición cerrada. ``grados``
    debe describir exactamente cuatro alturas distintas del acorde.
    """
    if fundamental not in notas_naturales:
        fundamental = 'C'
    base = 12 * base_octava + notas_naturales[fundamental]

    grados = list(grados)
    if len(grados) != 4:
        raise ValueError("Se requieren cuatro grados para construir el acorde")

    mejor_inversion = None
    mejor_dist = None

    if prev_bajo is None:
        k = inversion % len(grados)
        inv = grados[k:] + [g + 12 for g in grados[:k]]
        mejor_inversion = [base + g for g in inv]
    else:
        for k in range(len(grados)):
            # Generar inversión moviendo los primeros k grados una octava arriba
            inv = grados[k:] + [g + 12 for g in grados[:k]]
            bajo_base = base + inv[0]

            # Desplazar el acorde por octavas para acercar el bajo al acorde previo
            shift = round((prev_bajo - bajo_base) / 12) * 12
            for sh in (shift - 12, shift, shift + 12):
                bajo = bajo_base + sh
                dist = abs(bajo - prev_bajo)
                if mejor_dist is None or dist < mejor_dist:
                    mejor_dist = dist
                    mejor_inversion = [base + g + sh for g in inv]

    # Ajustar para que el bajo no salte más de cinco semitonos
    if mejor_inversion and prev_bajo is not None:
        bajo = mejor_inversion[0]
        while abs(bajo - prev_bajo) > 5:
            if bajo < prev_bajo:
                mejor_inversion = [n + 12 for n in mejor_inversion]
            else:
                mejor_inversion = [n - 12 for n in mejor_inversion]
            bajo = mejor_inversion[0]

    # Limitar el bajo entre D3 (50) y D4 (62) sin exceder salto de cinco semitonos
    if mejor_inversion:
        bajo = mejor_inversion[0]
        if bajo < 50:
            candidato = [n + 12 for n in mejor_inversion]
            if prev_bajo is None or abs(candidato[0] - prev_bajo) <= 5:
                mejor_inversion = candidato
                bajo = mejor_inversion[0]
        if bajo > 62:
            candidato = [n - 12 for n in mejor_inversion]
            if prev_bajo is None or abs(candidato[0] - prev_bajo) <= 5:
                mejor_inversion = candidato
                bajo = mejor_inversion[0]

    if mejor_inversion:
        mejor_inversion.sort()
        while max(mejor_inversion) - min(mejor_inversion) > 12:
            max_idx = mejor_inversion.index(max(mejor_inversion))
            mejor_inversion[max_idx] -= 12
            mejor_inversion.sort()

    return mejor_inversion

def enlazar_notas(previas, nuevas):
    """Asigna las notas de ``nuevas`` a ``previas`` minimizando el movimiento.

    ``previas`` y ``nuevas`` son listas de alturas MIDI (enteros).  El resultado
    es una nueva lista con la misma longitud que ``previas`` donde cada elemento
    corresponde a la altura del acorde destino más cercana posible a la nota
    previa, evitando reutilizar alturas cuando sea posible.
    """
    if not previas:
        return []

    n_prev = len(previas)
    if len(nuevas) >= n_prev:
        candidatos = itertools.permutations(nuevas, n_prev)
    else:
        candidatos = itertools.product(nuevas, repeat=n_prev)

    mejor_asignacion = None
    mejor_costo = None
    for cand in candidatos:
        costo = sum(abs(p - q) for p, q in zip(cand, previas))
        if mejor_costo is None or costo < mejor_costo:
            mejor_costo = costo
            mejor_asignacion = cand

    return list(mejor_asignacion)

def procesa_midi(reference_midi_path="reference_comping.mid", cifrado="", corcheas_por_compas=8, dur_corchea=0.25, inversion_inicial=0):
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

    bajo_anterior = None
    for i in range(total_corcheas):
        t0 = tiempo_inicio + i * dur_corchea
        t1 = t0 + dur_corchea
        # Nuevo filtrado para incluir notas activas en el segmento (no solo las que inician)
        notas_corchea = [n for n in notas if not (n.end <= t0 or n.start >= t1)]

        # Mantener silencios del midi de referencia
        if not notas_corchea:
            continue

        if len(notas_corchea) > 4:
            notas_corchea = notas_corchea[:4]
        elif len(notas_corchea) < 4:
            # Duplicar notas existentes para garantizar cuatro eventos
            base_nota = notas_corchea[0]
            for _ in range(4 - len(notas_corchea)):
                nueva = pretty_midi.Note(velocity=base_nota.velocity,
                                         pitch=base_nota.pitch,
                                         start=t0,
                                         end=t1)
                notas.append(nueva)
                notas_corchea.append(nueva)

        fundamental, grados = acordes_analizados[i]
        if i == 0:
            nuevas_alturas = notas_midi_acorde(fundamental, grados, base_octava=4,
                                               prev_bajo=bajo_anterior,
                                               inversion=inversion_inicial)
        else:
            nuevas_alturas = notas_midi_acorde(fundamental, grados, base_octava=4,
                                               prev_bajo=bajo_anterior)
        bajo_anterior = nuevas_alturas[0]
        alturas_previas = [n.pitch for n in notas_corchea]
        nuevas = enlazar_notas(alturas_previas, nuevas_alturas)
        for nota, altura in zip(notas_corchea, nuevas):
            nota.pitch = altura

    pista.notes = [n for n in notas if n.start >= tiempo_inicio and n.start < tiempo_fin]

    out_name = os.path.splitext(os.path.basename(reference_midi_path))[0] + "_export.mid"
    midi.write(out_name)
    print(f"Archivo exportado: {out_name}")
    return out_name
