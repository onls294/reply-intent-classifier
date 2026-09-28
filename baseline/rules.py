"""Rule baseline: keyword rules written from data/LABELING_GUIDE.md (v2).

The floor the LLM classifiers are judged against. Rules follow the guide's single-label
priority (section 3) and edge cases (section 5).

TUNING DISCIPLINE: the rules were written from the guide and adjusted ONLY against the public
synthetic set (data/synthetic.py), never against the 164 real rows. Adjustments made while
tuning are listed in ADJUSTMENTS. Because of that, the rules' score on the synthetic set is
optimistic; the real-set score is the honest one.
"""
import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Prediction:
    label: str                # one of labels.LABELS
    baja_explicita: bool      # only True if label == "no_interesado"
    reason: str = ""          # one line: which rule fired


ADJUSTMENTS = [
    "fuera_de_tema: added 'receta' after the only synthetic off-topic example (a recipe request).",
    "no_interesado: added 'descarto' and 'paso' for short refusals in the synthetic set.",
    "prefiere_escrito: added 'no alcanzo a contestar' as an explicit call refusal.",
    "quiere_contacto: added 'esperando la llamada' (claims the promised call).",
]


def _fold(text):
    text = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _any(patterns, text):
    return next((p for p in patterns if re.search(p, text)), None)


OFF_TOPIC = [r"\breceta\b", r"le ofrecemos", r"nuestro (software|sistema|servicio)", r"te mando el pedido",
             r"\bretoc", r"\bcotizacion de\b"]
OPT_OUT = [r"no (me )?(vuelvan|sigan) a? ?(escribir|llamar|contactar)", r"no me (sigan )?escriban mas",
           r"no me llamen mas", r"\bborr(en|ar|enme|arme)\b", r"(sacar|saquen)me de (la|su) (lista|base)",
           r"no (quiero|deseo) (que me )?(contacten|recibir)"]
NOT_INTERESTED = [r"no (me|nos) interesa", r"no estoy interesad", r"\bno,? gracias\b", r"\bya no\b",
                  r"ya (compramos|tenemos|compre)", r"presupuesto", r"\bcaro\b", r"costoso",
                  r"no lo necesito", r"\bcancel", r"dice que no", r"\by no$", r"\bdescarto\b", r"\bpaso\b$",
                  r"^no[.!]*$", r"^nop\b"]
CALL_REFUSAL = [r"no (puedo|contesto|atiendo|alcanzo a contestar)( \w+)* (llamad|telefono|contestar)",
                r"no (contesto|atiendo) llamad", r"no alcanzo a contestar", r"sin llamadas",
                r"no puedo hablar por telefono", r"no me llamen\b", r"solo (puedo )?(leer )?mensaje",
                r"prefiero que me escriban"]
WRITTEN_CHANNEL = [r"\bpor (chat|mensaje|escrito|whatsapp|wpp|aqui|aca|este (medio|chat))\b",
                   r"\bescri(beme|banme|bir|ban)\b", r"sigamos por", r"por este chat"]
INFO = [r"\bcuanto\b", r"precio", r"\bvalor\b", r"costo", r"que (incluye|trae|venden)", r"informacion", r"\binfo\b",
        r"detalles", r"como (funciona|lo pido|pago)", r"\bdonde\b", r"de que (se trata|es)", r"comprar",
        r"\bpago\b", r"descuento", r"video", r"\bsirve\b", r"funciona con", r"idiomas", r"\bdura\b",
        r"sede", r"tarjeta", r"cuotas"]
TIME = [r"\b\d{1,2} ?(am|pm)\b", r"\ba las \d", r"despues de las", r"\b(lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b",
        r"\bmanana (en|a|por)\b", r"\bhoy (despues|en la|a las)\b"]
CONTACT = [r"\bllam(en|ame|enme|ar me)\b", r"\bmarqu(en|enme|ame)\b", r"no me han llamado", r"esperando la llamada",
           r"(puedo|podria) atender", r"estoy disponible", r"estoy libre", r"que numero", r"reprogram",
           r"quiero la llamada", r"agend(ar|emos)"]
AFFIRM = r"^(si|claro|dale|perfecto|listo|ok,? si)\b"
CONTACT_QUESTION = r"(llam|marc|hablamos|reprogram|cita|asesora)"
LATER = [r"\bluego\b", r"mas tarde", r"en un rato", r"mas adelante", r"despues te", r"estoy en (junta|reunion|clase)",
         r"\bocupad", r"\bando a\b", r"te aviso", r"lo consulto", r"tengo que verlo", r"ahorita no puedo",
         r"estoy (manejando|cocinando|trabajando)"]


def classify(reply: str, outbound: str | None = None) -> Prediction:
    """Classify a pseudonymized reply, read together with the last outbound message."""
    r, o = _fold(reply).strip(), _fold(outbound)
    if (p := _any(OFF_TOPIC, r)):
        return Prediction("fuera_de_tema", False, f"off-topic: {p}")
    if (p := _any(OPT_OUT, r)):
        return Prediction("no_interesado", True, f"explicit opt-out: {p}")
    if (p := _any(NOT_INTERESTED, r)):
        return Prediction("no_interesado", False, f"refusal: {p}")
    if (p := _any(CALL_REFUSAL, r)):
        return Prediction("prefiere_escrito", False, f"call refusal: {p}")
    info = _any(INFO, r)
    if (p := _any(WRITTEN_CHANNEL, r)) and not info:
        return Prediction("prefiere_escrito", False, f"channel only: {p}")
    if (p := _any(TIME + CONTACT, r)):
        return Prediction("quiere_contacto", False, f"contact/time: {p}")
    if re.search(AFFIRM, r) and re.search(CONTACT_QUESTION, o):
        return Prediction("quiere_contacto", False, "affirmation to a contact proposal (5.1/5.7)")
    if (p := _any(LATER, r)):
        return Prediction("pospone", False, f"later: {p}")
    if info or "?" in r:
        return Prediction("pide_informacion", False, f"info: {info or 'question mark'}")
    return Prediction("sin_intencion", False, "no actionable intent")
