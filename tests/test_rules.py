"""Rule baseline, with the public synthetic set only (never the real rows)."""
import pytest

from baseline import rules
from data import synthetic
from labels import LABELS


def test_todas_las_sinteticas_con_su_clase():
    # Tuning set: 100 % here is by construction, and results.md says so.
    for x in synthetic.rows():
        assert rules.classify(x["reply_text"], x["outbound_text"]).label == x["label"], x["id"]


@pytest.mark.parametrize("reply,outbound,label", [
    ("te ofrecemos... no, le ofrecemos nuestro software", "", "fuera_de_tema"),
    ("no me interesa, no me vuelvan a escribir", "", "no_interesado"),
    ("no atiendo llamadas pero dime el precio", "", "prefiere_escrito"),      # refusal beats info (priority 3)
    ("por aqui mandame el precio", "", "pide_informacion"),                   # channel incidental (5.3)
    ("si", "¿Te llamamos mañana?", "quiere_contacto"),                        # 5.1
    ("si", "Gracias por escribir", "sin_intencion"),                          # 5.1, no question
    ("es que tenia el celular apagado", "", "sin_intencion"),                 # 5.2 past
])
def test_prioridad_y_casos_frontera(reply, outbound, label):
    assert rules.classify(reply, outbound).label == label


def test_baja_solo_con_peticion_explicita():
    assert rules.classify("borrenme de su lista").baja_explicita is True
    assert rules.classify("no gracias").baja_explicita is False


def test_siempre_una_clase_de_la_guia():
    for text in ["", "???", "🙂", "12345"]:
        assert rules.classify(text).label in LABELS
