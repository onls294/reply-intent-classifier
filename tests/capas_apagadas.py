"""Apaga cada capa de data/prepare.py en una COPIA del repo y comprueba que falla alguna prueba.

Uso: python tests/capas_apagadas.py   (sale con 1 si alguna capa no la detecta ninguna prueba)
No lo recoge pytest (no empieza por test_).
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAPAS = {
    "marca": ("for pat, tag in brand_patterns:\n        text = pat.sub", "for pat, tag in []:\n        text = pat.sub"),
    "marca pegada": (r'body = r"\s*".join(', r'body = r"\s+".join('),
    "correo": ('text = EMAIL.sub("[EMAIL]", text)', "pass"),
    "url": ('text = URL.sub("[URL]", text)', "pass"),
    "telefono": ("text = PHONE_CANDIDATE.sub(phone, text)", "pass"),
    "importes": ('text = AMOUNT.sub("[AMOUNT]", text)', "pass"),
    "direcciones": ('text = ADDRESS.sub("[ADDRESS]", text)', "pass"),
    "diccionario de nombres": ("    if name_pattern:\n        n = 0", "    if False:\n        n = 0"),
    "marca de colision": ('flags.append(f"name_collision:{m.group()}")', "pass"),
    "registro name:wN": ('flags.append(f"name:w{n}")', "pass"),
    "inicial de firma": (r'text = re.sub(r"\[NAME\](?:\s+(?:', r'text = text or re.sub(r"\[NAME\](?:\s+(?:'),
    "iniciales encadenadas": (r'(?=[\s,;:!?]|$))+", initial', r'(?=[\s,;:!?]|$))", initial'),
    "marca de mayusculas": ('flags.append(f"cap:{m.group(1)}")', "pass"),
    "palabras comunes fijas": ("and tok not in COMMON_WORDS", ""),
    "palabras comunes medidas": ("tokens -= {fold(w) for w in corpus_common} - NAME_WORD_COLLISIONS", "pass"),
    "colision gana a lo medido": ("- NAME_WORD_COLLISIONS\n", "\n"),
    "fugas: columnas": ("if list(row) != list(columns):", "if False:"),
    "fugas: arroba": ('if "@" in val:', "if False:"),
    "fugas: telefono": ("if any(sum(ch.isdigit() for ch in m.group()) >= 7 for m in PHONE_CANDIDATE.finditer(val)):", "if False:"),
    "fugas: nombres": ("if any(w in name_tokens for w in re.findall(", "if False and any(w in name_tokens for w in re.findall("),
    "fugas: marca": ("if any(pat.search(val) for pat, _ in brand_patterns):", "if False:"),
    "cli: scrub del saliente": ('o_text, o_flags = scrub(r.get("outbound_text", ""), pattern, brands)',
                                'o_text, o_flags = r.get("outbound_text", ""), []'),
}
fallos = 0
for capa, (old, new) in CAPAS.items():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "repo"
        shutil.copytree(REPO, d, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache"))
        f = d / "data" / "prepare.py"
        code = f.read_text(encoding="utf-8")
        if code.count(old) != 1:
            print(f"PATRON NO ENCONTRADO  {capa}"); fallos += 1; continue
        f.write_text(code.replace(old, new), encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        last = (r.stdout.strip().splitlines() or ["?"])[-1]
        ok = r.returncode != 0
        fallos += not ok
        print(f"{'DETECTADA' if ok else 'NO DETECTADA':<13} {capa:<28} {last}")
print(f"\n{len(CAPAS) - fallos}/{len(CAPAS)} capas detectadas al apagarlas")
sys.exit(1 if fallos else 0)
