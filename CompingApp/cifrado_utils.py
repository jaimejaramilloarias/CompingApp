import re
from acordes_dict import acordes

def alias_a_clave_acordes(resto):
    suf = resto.replace(" ", "").replace('[', '(').replace(']', ')').lower()
    for pat in ["m7(b5)", "m7b5", "min7b5", "mi7b5", "-7b5", "ø7", "ø"]:
        if suf.startswith(pat):
            return "m7(b5)", resto[len(pat):]
    for pat in ["min", "mi", "m", "-"]:
        if suf.startswith(pat):
            return "m", resto[len(pat):]
    for pat in ["maj", "major", "maj", "m", "∆"]:
        if suf.startswith(pat):
            return "∆", resto[len(pat):]
    for pat in ["dim", "º", "o"]:
        if suf.startswith(pat):
            return "º", resto[len(pat):]
    for pat in ["aug", "+"]:
        if suf.startswith(pat):
            return "+", resto[len(pat):]
    for pat in ["sus4", "sus"]:
        if suf.startswith(pat):
            return "sus", resto[len(pat):]
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

        # Extraer extensiones en paréntesis
        sufijo_base = sufijo
        if '(' in sufijo:
            parentesis = re.findall(r'\((.*?)\)', sufijo)
            for contenido in parentesis:
                for ext in contenido.split(','):
                    ext = ext.strip()
                    if ext:
                        extensiones.append(ext)
            sufijo_base = re.sub(r'\(.*?\)', '', sufijo).strip()

        # Extraer extensiones pegadas fuera de paréntesis
        for ext_tag in ['b9', '#9', '9', '#11', '11', 'b13', '13']:
            if ext_tag in sufijo_base:
                extensiones.append(ext_tag)
                sufijo_base = sufijo_base.replace(ext_tag, '')

        sufijo_base = sufijo_base.strip()
        base, resto_limpio = alias_a_clave_acordes(sufijo_base)
        if not base or base not in acordes:
            if sufijo_base == '':
                base = '7'
            else:
                print(f"¡Acorde no reconocido: {sufijo_base}! Usando 7 por defecto.")
                base = "7"
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
        if e_11 and e_13:
            grados_final[0] = ext_map.get(e_9 or "9", 2)
            grados_final[1] = ext_map.get(e_11, 5)
            grados_final[2] = ext_map.get(e_13, 9)
        elif e_13:
            grados_final[0] = ext_map.get(e_9 or "9", 2)
            grados_final[2] = ext_map.get(e_13, 9)
        elif e_11:
            grados_final[0] = ext_map.get(e_9 or "9", 2)
            grados_final[2] = ext_map.get(e_11, 5)
        elif e_9:
            grados_final[0] = ext_map.get(e_9, 2)

        resultado.append((fundamental, grados_final))
    return resultado
