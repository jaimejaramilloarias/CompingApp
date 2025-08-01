import re

acordes = {
    "m7(b5)": [0,3,6,10],
    "7": [0,4,7,10],
    "m7": [0,3,7,10],
    "∆": [0,4,7,11],
}

def alias_a_clave_acordes(resto):
    semidim_pat = r'^(m7\(b5\)|m7b5|min7b5|mi7b5|\-7b5|ø7|ø)'
    if re.match(semidim_pat, resto, re.IGNORECASE):
        return "m7(b5)", re.sub(semidim_pat, '', resto, flags=re.IGNORECASE)
    menor_pat = r'^(min|mi|m|\-)'
    if re.match(menor_pat, resto, re.IGNORECASE):
        return "m7", re.sub(menor_pat, '', resto, flags=re.IGNORECASE)
    mayor_pat = r'^(maj|major|Maj|M|∆)'
    if re.match(mayor_pat, resto, re.IGNORECASE):
        return "∆", re.sub(mayor_pat, '', resto, flags=re.IGNORECASE)
    return None, resto

def analizar_cifrado(cifrado):
    resultado = []
    tokens = cifrado.split()
    for token in tokens:
        m = re.match(r'^([A-G][#b]?)(.*)$', token)
        if not m:
            print(f"NO MATCH: {token}")
            continue
        fundamental, resto = m.groups()
        resto = resto.strip()
        base, resto2 = alias_a_clave_acordes(resto)
        print(f"TOKEN: '{token}' | Base: '{base}' | resto2: '{resto2}'")
        if not base:
            base = "7"
        grados = acordes[base]
        print(f"--> Grados: {grados}")
        resultado.append((fundamental, grados))
    return resultado

# TESTEA ESTO:
cifrado = "Bø Bø7 Bm7(b5) Bmin7b5 B-7b5 Bmi7b5"
analizar_cifrado(cifrado)
