"""Seudonimizacion generica de mensajes cortos (WhatsApp, espanol).

Portado de la extraccion original. La marca, el diccionario de nombres y las palabras
comunes medidas son ARCHIVOS DE ENTRADA que viven FUERA de este repositorio: nunca se
escriben en el codigo ni en data/.

Uso:
  python data/prepare.py --input mensajes.csv --names nombres.csv [--brands marca.txt]
                         [--common comunes.tsv] --output limpio.csv
  mensajes.csv: columnas id, text y opcionalmente outbound_text.
  nombres.csv:  columna name.   marca.txt: lineas 'COMPANY|termino' o 'PRODUCT|termino'.

Lo que NO atrapa: un nombre ajeno a la base escrito en minuscula, y la reidentificacion
por contenido. Por eso el texto seudonimizado no se publica.
"""
import argparse
import csv
import re
import sys
import unicodedata

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL = re.compile(r"(?:https?://|www\.)\S+", re.I)
PHONE_CANDIDATE = re.compile(r"\+?\(?\d[\d\s().-]{5,}\d")
AMOUNT = re.compile(
    r"(?:\$\s?\d[\d.,]*(?:\s?(?:mil|millones|k)\b)?"
    r"|\b(?:usd|cop)\s?\d[\d.,]*"
    r"|\b\d[\d.,]*\s?(?:mil|millones|pesos|cop|usd|d[oó]lares)\b)",
    re.I,
)
ADDRESS = re.compile(
    r"\b(?:calle|cll|cl|carrera|cra|kr|avenida|av|diagonal|dg|transversal|tv)\.?\s*\d+\w*"
    r"(?:\s*(?:#|no\.?|n°)\s*\d+\w*(?:\s*-\s*\d+)?)?",
    re.I,
)

# Nombres que tambien son palabras comunes: se sustituyen igual (manda la privacidad),
# pero se marcan porque pueden haber borrado una palabra con sentido.
NAME_WORD_COLLISIONS = {
    "luz", "paz", "rosa", "sol", "mar", "angel", "cruz", "flor", "blanca", "gloria",
    "victoria", "esperanza", "consuelo", "amparo", "pilar", "leon", "reyes", "santos",
    "julio", "abril", "clara",
}

# Nunca cuentan como nombre aunque aparezcan en el diccionario. El diccionario sale de
# columnas de la base que incluyen el nombre de PERFIL de WhatsApp, que puede ser
# "Mama de Sofi" o "Dios es amor": sin este filtro, "de", "los" o "gracias" se borrarian
# de todos los mensajes. Solo particulas y palabras comunes; los nombres que tambien son
# palabra (Luz, Paz, Gloria) NO van aqui: van en NAME_WORD_COLLISIONS y se sustituyen.
COMMON_WORDS = {
    "del", "las", "los", "san", "santa", "van", "von", "que", "con", "por", "para", "una",
    "uno", "sin", "muy", "mas", "todo", "todos", "bien", "hoy", "aqui", "alla", "mis", "sus",
    "hola", "gracias", "buenas", "buenos", "dias", "tardes", "noches", "amor", "dios", "mama",
    "mami", "papa", "papi", "bebe", "casa", "familia", "senora", "senor", "sra", "dra",
    "doctor", "doctora", "profe", "profesora", "bendiciones", "feliz", "vida", "cita", "clase",
    "clases", "nino", "nina", "ninos", "hijo", "hija", "hijos", "abuela", "abuelo", "tia",
    "tio", "esposo", "esposa", "amiga", "amigo", "iphone", "samsung", "whatsapp", "business",
    "oficial", "tienda", "mom", "dad", "baby", "love", "the", "and", "family", "home",
    "name", "phone", "email", "amount", "address", "url",   # los propios marcadores
    "enero", "febrero", "marzo", "mayo", "junio", "agosto", "septiembre", "setiembre",
    "octubre", "noviembre", "diciembre", "lunes", "martes", "miercoles", "jueves",
    "viernes", "sabado", "domingo",   # julio y abril NO: son nombres frecuentes
    # Preposiciones: nunca son nombre. Van SIN tilde: se comparan despues de fold().
    "ante", "bajo", "contra", "desde", "durante", "entre", "hacia", "hasta", "mediante",
    "segun", "sobre", "tras",
    "hogar", "pos",   # vistas borradas en [A] (26 sep): perfiles de tienda en el diccionario
}

# Palabras que suelen ir en mayuscula a mitad de frase sin ser un nombre.
CAPITALIZED_OK = {
    "whatsapp", "zoom", "meet", "google", "dios", "ok", "si", "no", "hola", "gracias",
    "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
}


def fold(text):
    """Minuscula y sin tildes, pero CONSERVA la ñ: en español es otra letra (Peña no es pena)."""
    text = text.lower().replace("ñ", "\ue000")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return text.replace("\ue000", "ñ")


ACCENTS = {"a": "[aáàä]", "e": "[eéèë]", "i": "[iíìï]", "o": "[oóòö]", "u": "[uúùü]"}


def build_brand_patterns(lines):
    """Lineas 'PLACEHOLDER|termino'. Sin tildes, sin mayusculas, y traga la palabra pegada
    ('Acmebuenas'). La lista de marca es un ARCHIVO DE ENTRADA: nunca va en el codigo."""
    pats = []
    for line in lines:
        if "|" not in line:
            continue
        tag, term = (x.strip() for x in line.split("|", 1))
        body = r"\s*".join("".join(ACCENTS.get(c, re.escape(c)) for c in fold(w)) for w in term.split())
        pats.append((len(term), re.compile(rf"(?<!\w){body}\w*", re.I), f"[{tag}]"))
    return [(p, tag) for _, p, tag in sorted(pats, key=lambda x: -x[0])]


def build_name_pattern(names, corpus_common=()):
    """Conjunto de tokens de nombre, ya plegados (sin tildes, en minuscula).

    Se compara palabra a palabra contra un conjunto: con miles de nombres, una
    expresion regular con una alternativa por nombre es inviable.
    """
    tokens = set()
    for full in names:
        for tok in re.split(r"[\s\-]+", full.strip()):
            tok = fold(tok)
            if len(tok) >= 3 and tok.isalpha() and tok not in COMMON_WORDS:
                tokens.add(tok)
    # Medidas en los datos: token escrito en minuscula en muchos mensajes = palabra.
    # Las colisiones (julio, pilar, luz...) se quedan: son nombres aunque sean frecuentes.
    tokens -= {fold(w) for w in corpus_common} - NAME_WORD_COLLISIONS
    return (frozenset(tokens) or None), tokens


def scrub(text, name_pattern, brand_patterns=()):
    flags = []
    for pat, tag in brand_patterns:
        text = pat.sub(tag, text)
    text = EMAIL.sub("[EMAIL]", text)
    text = URL.sub("[URL]", text)

    def phone(m):
        return "[PHONE]" if sum(c.isdigit() for c in m.group()) >= 7 else m.group()

    text = PHONE_CANDIDATE.sub(phone, text)
    text = AMOUNT.sub("[AMOUNT]", text)
    text = ADDRESS.sub("[ADDRESS]", text)

    if name_pattern:
        n = 0

        # Toda sustitucion queda en flags. La de un nombre, por su posicion (wN = palabra N
        # del texto resultante), nunca por su valor: copiarlo devolveria el dato al CSV.
        def name(m):
            nonlocal n
            n += 1
            if fold(m.group()) not in name_pattern:
                return m.group()
            if fold(m.group()) in NAME_WORD_COLLISIONS:
                flags.append(f"name_collision:{m.group()}")
            else:
                flags.append(f"name:w{n}")
            return "[NAME]"
        text = re.sub(r"\w+", name, text)

        # Firma de vendedora: la inicial del apellido detras de un nombre ("[NAME] S,").
        # Sin punto no se absorben a/e/o/u/y: en español son palabras ("[NAME] Y [NAME]").
        def initial(m):
            flags.append("firma_inicial")
            return "[NAME]"
        text = re.sub(r"\[NAME\](?:\s+(?:[A-ZÑ]\.|[B-DF-NP-TV-XZÑ])(?=[\s,;:!?]|$))+", initial, text)

    # Mayuscula a mitad de frase que no es un marcador ni una palabra conocida:
    # se MARCA para revision humana, no se sustituye a ciegas.
    for m in re.finditer(r"(?<![.!?¡¿]\s)(?<!^)\b([A-ZÁÉÍÓÚÑ][a-záéíóúñü]{2,})\b", text):
        if fold(m.group(1)) not in CAPITALIZED_OK:
            flags.append(f"cap:{m.group(1)}")
    return text, flags



def leak_check(rows, columns, name_tokens, brand_patterns=()):
    """Lista de problemas en filas que se van a publicar. Vacia = se puede escribir."""
    problems = []
    for i, row in enumerate(rows, 1):
        if list(row) != list(columns):
            problems.append(f"fila {i}: columnas fuera de la lista blanca")
        for col, val in row.items():
            val = str(val)
            if "@" in val:
                problems.append(f"fila {i} {col}: contiene '@'")
            if any(sum(ch.isdigit() for ch in m.group()) >= 7 for m in PHONE_CANDIDATE.finditer(val)):
                problems.append(f"fila {i} {col}: tramo con forma de telefono")
            if any(w in name_tokens for w in re.findall(r"\w+", fold(val))):
                problems.append(f"fila {i} {col}: contiene un nombre del diccionario")
            if any(pat.search(val) for pat, _ in brand_patterns):
                problems.append(f"fila {i} {col}: contiene la marca o un producto")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True)
    ap.add_argument("--names", required=True)
    ap.add_argument("--brands")
    ap.add_argument("--common")
    ap.add_argument("--output", required=True)
    a = ap.parse_args(argv)

    def lines(path):
        return open(path, encoding="utf-8").read().splitlines() if path else []

    brands = build_brand_patterns(lines(a.brands))
    with open(a.names, encoding="utf-8") as f:
        pattern, _ = build_name_pattern((r["name"] for r in csv.DictReader(f)),
                                        [x.split("	")[0] for x in lines(a.common)])
    with open(a.input, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        text, flags = scrub(r["text"], pattern, brands)
        o_text, o_flags = scrub(r.get("outbound_text", ""), pattern, brands)
        out.append({"id": r["id"], "text": text, "outbound_text": o_text,
                    "scrub_flags": ";".join(flags + [f"out:{x}" for x in o_flags])})
    with open(a.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "text", "outbound_text", "scrub_flags"])
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} filas seudonimizadas -> {a.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
