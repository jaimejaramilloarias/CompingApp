from cifrado_utils import analizar_cifrado


def test_m7b5_aliases():
    aliases = ["Bø", "Bø7", "Bm7(b5)", "Bmin7b5", "B-7b5", "Bmi7b5"]
    esperado = ("B", [0, 3, 6, 10])
    for cif in aliases:
        assert analizar_cifrado(cif) == [esperado]
