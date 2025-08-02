import os
import itertools
from pathlib import Path
from collections import defaultdict
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

def expandir_cifrado_a_corcheas(
    cifrado_texto,
    total_corcheas=256,
    corcheas_por_compas=8,
    return_indices=False,
):
    """Expande un cifrado para obtener el acorde de cada corchea.

    Cuando ``return_indices`` es ``True`` también se devuelve una lista con el
    índice del acorde correspondiente a cada corchea.  Este índice coincide con
    el orden en que aparecen los acordes al recorrer el cifrado de izquierda a
    derecha, independientemente de si dos acordes consecutivos comparten el
    mismo nombre.
    """

    compases = [c.strip() for c in cifrado_texto.split('|') if c.strip()]
    resultado = []
    indices = []
    acorde_idx = 0
    for compas in compases:
        acordes_compas = [a.strip() for a in compas.split() if a.strip()]
        n_acordes = len(acordes_compas)
        if n_acordes == 0:
            raise ValueError("Compás vacío en cifrado.")
        corcheas_por_acorde = corcheas_por_compas // n_acordes
        resto = corcheas_por_compas - corcheas_por_acorde * n_acordes
        for i, acorde in enumerate(acordes_compas):
            extra = 1 if i < resto else 0
            repeticiones = corcheas_por_acorde + extra
            resultado += [acorde] * repeticiones
            if return_indices:
                indices += [acorde_idx] * repeticiones
            acorde_idx += 1
    if len(resultado) < total_corcheas:
        resultado += [resultado[-1]] * (total_corcheas - len(resultado))
        if return_indices:
            indices += [indices[-1]] * (total_corcheas - len(indices))
    if len(resultado) > total_corcheas:
        resultado = resultado[:total_corcheas]
        if return_indices:
            indices = indices[:total_corcheas]
    if return_indices:
        return resultado, indices
    return resultado

def notas_midi_acorde(fundamental, grados, base_octava=4, prev_bajo=None, inversion=0):
    """Devuelve las notas MIDI del acorde.

    Si ``prev_bajo`` es ``None`` se utiliza la inversión indicada por
    ``inversion`` (0=fundamental, 1=1ª inversión, ...).  Para los acordes
    siguientes se elige automáticamente la inversión y el desplazamiento de
    octava cuya nota más grave quede lo más cercana posible a ``prev_bajo``.
    El resultado siempre contiene cuatro notas en posición cerrada dentro del
    registro D3–C5. ``grados`` debe describir exactamente cuatro alturas
    distintas del acorde.
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
        candidatos = []
        for sh in range(-2, 3):
            cand = [base + g + 12 * sh for g in inv]
            if cand[0] < 50 or max(cand) > 72:
                continue
            candidatos.append(cand)
        if candidatos:
            mejor_inversion = candidatos[0]
        else:
            mejor_inversion = [base + g for g in inv]
    else:
        for k in range(len(grados)):
            inv = grados[k:] + [g + 12 for g in grados[:k]]
            for sh in range(-2, 3):
                cand = [base + g + 12 * sh for g in inv]
                if cand[0] < 50 or max(cand) > 72:
                    continue
                dist = abs(cand[0] - prev_bajo)
                if dist > 5:
                    continue
                if mejor_dist is None or dist < mejor_dist:
                    mejor_dist = dist
                    mejor_inversion = cand
        if mejor_inversion is None:
            for k in range(len(grados)):
                inv = grados[k:] + [g + 12 for g in grados[:k]]
                for sh in range(-2, 3):
                    cand = [base + g + 12 * sh for g in inv]
                    if cand[0] < 50 or max(cand) > 72:
                        continue
                    dist = abs(cand[0] - prev_bajo)
                    if mejor_dist is None or dist < mejor_dist:
                        mejor_dist = dist
                        mejor_inversion = cand

    # Ajustar para que el bajo no salte más de cinco semitonos
    if mejor_inversion and prev_bajo is not None:
        bajo = mejor_inversion[0]
        visitados = set()
        # En algunos casos no es posible reducir la distancia a cinco
        # semitonos únicamente desplazando por octavas.  El bucle original
        # intentaba hacerlo indefinidamente, provocando un bucle infinito
        # cuando la diferencia se alternaba entre dos valores (por ejemplo
        # 6 y -6).  Para evitarlo, registramos las alturas visitadas y
        # abandonamos si no se logra mejorar.
        while abs(bajo - prev_bajo) > 5:
            if bajo in visitados:
                break
            visitados.add(bajo)
            if bajo < prev_bajo:
                mejor_inversion = [n + 12 for n in mejor_inversion]
            else:
                mejor_inversion = [n - 12 for n in mejor_inversion]
            bajo = mejor_inversion[0]

    # Limitar el registro de los acordes.
    # El bajo no debe caer por debajo de D3 (50) y la voz superior
    # no debe superar C5 (72).  Cualquier ajuste de octava respeta además
    # la restricción de que el bajo solo puede moverse un máximo de cinco
    # semitonos respecto al acorde anterior.
    if mejor_inversion:
        bajo = mejor_inversion[0]
        if bajo < 50:
            candidato = [n + 12 for n in mejor_inversion]
            if prev_bajo is None or abs(candidato[0] - prev_bajo) <= 5:
                mejor_inversion = candidato
                bajo = mejor_inversion[0]

        alto = max(mejor_inversion)
        if alto > 72:
            candidato = [n - 12 for n in mejor_inversion]
            if candidato[0] >= 50 and (
                prev_bajo is None or abs(candidato[0] - prev_bajo) <= 5
            ):
                mejor_inversion = candidato
                bajo = mejor_inversion[0]

        # Tras los posibles ajustes de registro, garantizar nuevamente que el
        # salto del bajo no exceda cinco semitonos.
        if prev_bajo is not None:
            bajo = mejor_inversion[0]
            visitados = set()
            while abs(bajo - prev_bajo) > 5:
                if bajo in visitados:
                    break
                visitados.add(bajo)
                if bajo < prev_bajo:
                    mejor_inversion = [n + 12 for n in mejor_inversion]
                else:
                    mejor_inversion = [n - 12 for n in mejor_inversion]
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


def evitar_solapamientos(notas, margen=0.01):
    """Acorta una nota si la siguiente tiene la misma altura.

    Recorre ``notas`` en orden temporal y, cuando dos notas consecutivas
    comparten ``pitch`` y la primera se extiende más allá del inicio de la
    segunda, reduce la duración de la primera para que finalice un pequeño
    margen antes de la siguiente.  El ``margen`` se expresa en segundos.
    """
    notas.sort(key=lambda n: n.start)
    for actual, siguiente in zip(notas, notas[1:]):
        if actual.pitch == siguiente.pitch and actual.end > siguiente.start:
            nuevo_fin = min(actual.end, siguiente.start - margen)
            if nuevo_fin < actual.start:
                nuevo_fin = actual.start
            actual.end = nuevo_fin


def recortar_notas_a_segmento(notas, inicio, fin):
    """Recorta notas para que se mantengan dentro del segmento ``[inicio, fin]``.

    Solo se acortan las notas; nunca se extienden. Si el inicio queda por
    encima del final tras el recorte, se ajusta el final para que coincida con
    el inicio.
    """
    for n in notas:
        if n.start < inicio:
            n.start = inicio
        if n.end > fin:
            n.end = fin
        if n.end < n.start:
            n.end = n.start
    return notas


def aplicar_rotaciones(
    notas,
    rotacion=0,
    rotaciones=None,
    octavas=None,
    indices=None,
    dur_corchea=0.25,
    tiempo_inicio=0,
):
    """Aplica rotaciones de inversión a listas de notas.

    ``rotacion`` es la rotación global que se aplica a todos los acordes.
    ``rotaciones`` es un diccionario opcional cuyo índice corresponde al orden
    del acorde (empezando en ``0``) y cuyo valor indica rotaciones adicionales
    para ese acorde.  Si ``indices`` es proporcionado, debe ser una lista cuyo
    elemento ``i`` indica el índice del acorde activo en la corchea ``i``; en
    ese caso, las rotaciones forzadas se aplicarán a todas las notas que caigan
    dentro de la duración del acorde correspondiente.  ``tiempo_inicio``
    representa el instante de inicio de la primera corchea (en segundos).  Cuando
    ``indices`` es ``None`` se mantiene el comportamiento anterior, interpretando
    que cada grupo de notas representa un nuevo acorde consecutivo.
    """

    grupos = defaultdict(list)
    for n in notas:
        grupos[n.start].append(n)

    if not grupos:
        return notas

    if indices is None:
        for idx, start in enumerate(sorted(grupos)):
            rot = rotacion
            if rotaciones and idx in rotaciones:
                rot += rotaciones[idx]
            oct = octavas.get(idx, 0) if octavas else 0

            g = grupos[start]
            if oct:
                for n in g:
                    n.pitch += 12 * oct
            if rot > 0:
                for _ in range(rot):
                    bajo = min(g, key=lambda n: n.pitch)
                    bajo.pitch += 12
            elif rot < 0:
                for _ in range(-rot):
                    alto = max(g, key=lambda n: n.pitch)
                    alto.pitch -= 12
    else:
        for start in sorted(grupos):
            corchea_idx = int(round((start - tiempo_inicio) / dur_corchea))
            rot = rotacion
            oct = 0
            if (
                rotaciones
                and 0 <= corchea_idx < len(indices)
            ):
                acorde_idx = indices[corchea_idx]
                rot += rotaciones.get(acorde_idx, 0)
                if octavas:
                    oct = octavas.get(acorde_idx, 0)

            g = grupos[start]
            if oct:
                for n in g:
                    n.pitch += 12 * oct
            if rot > 0:
                for _ in range(rot):
                    bajo = min(g, key=lambda n: n.pitch)
                    bajo.pitch += 12
            elif rot < 0:
                for _ in range(-rot):
                    alto = max(g, key=lambda n: n.pitch)
                    alto.pitch -= 12

    return notas


def Spread(notas):
    """Duplica notas del acorde para crear un voicing abierto.

    Se duplica la segunda nota del acorde una y dos octavas arriba y se
    agrega una de las notas del acorde una octava arriba, ubicada entre las
    dos notas duplicadas anteriores.
    """

    grupos = defaultdict(list)
    for n in notas:
        grupos[n.start].append(n)

    nuevas = []
    for grupo in grupos.values():
        if len(grupo) < 2:
            continue
        ordenado = sorted(grupo, key=lambda n: n.pitch)
        segunda = ordenado[1]
        # Selecciona la nota más aguda del acorde para el agregado intermedio.
        extra = ordenado[-1]

        cls = segunda.__class__
        duplicados = (
            (segunda, 12),
            (extra, 12),
            (segunda, 24),
        )
        for nota, desplazamiento in duplicados:
            nueva = cls(
                velocity=getattr(nota, "velocity", 0),
                pitch=nota.pitch + desplazamiento,
                start=nota.start,
                end=nota.end,
            )
            nuevas.append(nueva)
    notas.extend(nuevas)
    return notas

def procesa_midi(
    reference_midi_path="reference_comping.mid",
    cifrado="",
    corcheas_por_compas=8,
    dur_corchea=0.25,
    rotacion=0,
    rotaciones=None,
    octavas=None,
    spread=False,
    save=True,
):
    """Genera un archivo MIDI con el cifrado indicado.

    Si ``spread`` es ``True`` se duplica la segunda nota de cada acorde una y dos
    octavas por encima.  Cuando ``save`` es ``True`` (valor por defecto) el
    resultado se escribe en un archivo dentro de ``~/Desktop/output`` y se
    devuelve la ruta al mismo.  Si ``save`` es ``False`` se devuelve el objeto
    ``PrettyMIDI`` resultante sin persistirlo en disco, lo cual permite
    previsualizar el MIDI antes de exportarlo definitivamente.
    """
    import pretty_midi

    midi = pretty_midi.PrettyMIDI(reference_midi_path)
    pista = midi.instruments[0]
    notas = pista.notes

    compases = [c.strip() for c in cifrado.split('|') if c.strip()]
    total_corcheas = len(compases) * corcheas_por_compas
    tiempo_inicio = min(n.start for n in notas)
    tiempo_fin = tiempo_inicio + total_corcheas * dur_corchea

    acordes_corchea, indices_acordes = expandir_cifrado_a_corcheas(
        cifrado, total_corcheas, corcheas_por_compas, return_indices=True
    )
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

        # Evitar legato forzando las notas a encajar en los límites del segmento
        recortar_notas_a_segmento(notas_corchea, t0, t1)

        fundamental, grados = acordes_analizados[i]
        if i == 0:
            nuevas_alturas = None
            for inv in range(4):
                cand = notas_midi_acorde(
                    fundamental, grados, base_octava=4, prev_bajo=None, inversion=inv
                )
                if cand[0] >= 57:
                    nuevas_alturas = cand
                    break
            if nuevas_alturas is None:
                nuevas_alturas = cand
        else:
            nuevas_alturas = notas_midi_acorde(
                fundamental, grados, base_octava=4, prev_bajo=bajo_anterior
            )
        bajo_anterior = nuevas_alturas[0]
        alturas_previas = [n.pitch for n in notas_corchea]
        nuevas = enlazar_notas(alturas_previas, nuevas_alturas)
        for nota, altura in zip(notas_corchea, nuevas):
            nota.pitch = altura

    notas_finales = [n for n in notas if tiempo_inicio <= n.start < tiempo_fin]
    evitar_solapamientos(notas_finales)

    aplicar_rotaciones(
        notas_finales,
        rotacion,
        rotaciones,
        octavas,
        indices_acordes,
        dur_corchea,
        tiempo_inicio,
    )
    if spread:
        Spread(notas_finales)

    pista.notes = notas_finales

    if save:
        out_dir = Path.home() / "Desktop" / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        indices = [int(p.stem) for p in out_dir.glob("*.mid") if p.stem.isdigit()]
        next_idx = max(indices, default=0) + 1
        out_path = out_dir / f"{next_idx}.mid"
        midi.write(str(out_path))
        print(f"Archivo exportado: {out_path}")
        archivos = sorted(out_dir.glob("*.mid"), key=lambda p: int(p.stem))
        for p in archivos:
            print(p.name)
        return str(out_path)
    else:
        return midi
