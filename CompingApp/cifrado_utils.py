import re
from acordes_dict import acordes

def alias_a_clave_acordes(resto):
    suf = resto.replace(" ", "").replace('[', '(').replace(']', ')').lower()

    alias_patterns = [
        ("m7(b5)", ["m7(b5)", "m7b5", "min7b5", "mi7b5", "-7b5", "ø7", "ø"]),
        ("m6", ["m6"]),
        ("6", ["6"]),
        ("m", ["min", "mi", "m", "-"]),
        ("∆", ["maj", "major", "maj", "m", "∆"]),
        ("º", ["dim", "º", "o"]),
        ("+", ["aug", "+"]),
        ("sus", ["sus4", "sus"]),
    ]

    for base, pats in alias_patterns:
        for pat in pats:
            if suf.startswith(pat):
                return base, resto[len(pat):]
    return None, resto

def analizar_cifrado(cifrado):
    resultado = []
    tokens = cifrado.split()
    for token in tokens:
        m = re.match(r'^([A-G][#b]?)(.*)$', token)
        if not m:
            print(f"No se pudo analizar el token: {token}")
            continue
        fundamental, sufijo = m.groups()
        sufijo = sufijo.strip()
        extensiones = []

        # Detectar la base del acorde antes de procesar extensiones
        base, resto = alias_a_clave_acordes(sufijo)
        if base == 'm':
            base = 'm7'
        elif base == '+':
            base = '+7'
        elif base == 'º':
            base = 'º7'
        elif base == 'sus':
            base = '7sus4'
        if not base or base not in acordes:
            if sufijo == '' or sufijo.startswith('7'):
                base = '7'
                resto = sufijo[1:] if sufijo.startswith('7') else ''
            else:
                base = '7'
                resto = sufijo
                conocidos = ['b9', '#9', '9', '#11', '11', 'b13', '13']
                if not any(tag in sufijo for tag in conocidos):
                    print(f"¡Acorde no reconocido: {sufijo}! Usando 7 por defecto.")

        if resto.startswith('7'):
            resto = resto[1:]

        # Extraer extensiones en paréntesis del resto
        sufijo_base = resto
        if '(' in sufijo_base:
            parentesis = re.findall(r'\((.*?)\)', sufijo_base)
            for contenido in parentesis:
                for ext in contenido.split(','):
                    ext = ext.strip()
                    if ext:
                        extensiones.append(ext)
            sufijo_base = re.sub(r'\(.*?\)', '', sufijo_base).strip()

        # Extraer extensiones pegadas fuera de paréntesis
        for ext_tag in ['b9', '#9', '9', '#11', '11', 'b13', '13']:
            if ext_tag in sufijo_base:
                extensiones.append(ext_tag)
                sufijo_base = sufijo_base.replace(ext_tag, '')

        sufijo_base = sufijo_base.strip()
        if sufijo_base:
            print(f"¡Acorde no reconocido: {sufijo_base}! Usando 7 por defecto.")

        grados_base = acordes[base][:]

        e_9 = next((e for e in extensiones if '9' in e), None)
        e_11 = next((e for e in extensiones if '11' in e), None)
        e_13 = next((e for e in extensiones if '13' in e), None)

        ext_map = {
            "9": 2, "b9": 1, "#9": 3,
            "11": 5, "#11": 6,
            "13": 9, "b13": 8
        }

        grados_final = grados_base[:]
        if e_13:
            grados_final[2] = ext_map.get(e_13, 9)
            grados_final[0] = ext_map.get(e_9, 2)
        elif e_11:
            grados_final[2] = ext_map.get(e_11, 5)
            grados_final[0] = ext_map.get(e_9, 2)
        elif e_9:
            grados_final[0] = ext_map.get(e_9, 2)

        resultado.append((fundamental, grados_final))
    return resultado
