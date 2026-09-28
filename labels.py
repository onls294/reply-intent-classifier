"""Clases y filtros de data/LABELING_GUIDE.md. Una sola fuente para reglas, LLM y eval."""

LABELS = (
    "pide_informacion",
    "quiere_contacto",
    "prefiere_escrito",
    "pospone",
    "no_interesado",
    "sin_intencion",
    "fuera_de_tema",
)

# Filas que se quedan en el dataset pero no se etiquetan ni se evaluan.
FILTERS = ("respuesta_automatica", "sin_texto")

# Regla de etiqueta unica: si encaja en varias, gana la primera de esta lista.
PRIORITY = (
    "fuera_de_tema",
    "no_interesado",
    "prefiere_escrito",
    "quiere_contacto",
    "pospone",
    "pide_informacion",
    "sin_intencion",
)
