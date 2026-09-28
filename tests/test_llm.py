"""LLM classifier with the Messages API mocked: no network, no key."""
import json
from types import SimpleNamespace as NS

import pytest

from classifier import llm


def _resp(text, stop="end_turn"):
    return NS(stop_reason=stop, content=[NS(type="thinking", thinking=""), NS(type="text", text=text)],
              usage=NS(input_tokens=200, cache_creation_input_tokens=0, cache_read_input_tokens=3400, output_tokens=90))


class FakeClient:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        return self.answers.pop(0)


def test_respuesta_valida_y_registro():
    c = FakeClient([_resp(json.dumps({"label": "pospone", "explicit_opt_out": False}))])
    pred, log = llm.classify_with_log("luego te escribo", "hola", model="claude-sonnet-5", client=c)
    assert pred.label == "pospone" and log.attempts == 1 and log.cache_read_input_tokens == 3400
    kw = c.calls[0]
    assert "temperature" not in kw                                  # rejected by these models
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kw["output_config"]["effort"] == "low"
    assert kw["output_config"]["format"]["schema"]["properties"]["label"]["enum"] == list(llm.LABELS)


def test_en_negativo_formato_malo_se_reintenta_una_vez():
    c = FakeClient([_resp("no es json"), _resp(json.dumps({"label": "pide_informacion", "explicit_opt_out": False}))])
    pred, log = llm.classify_with_log("precio?", None, model="claude-opus-5-5", client=c)
    assert pred.label == "pide_informacion" and log.format_errors == 1 and log.attempts == 2


def test_en_negativo_clase_inventada_o_rechazo_falla():
    c = FakeClient([_resp(json.dumps({"label": "otra", "explicit_opt_out": False})), _resp("{}", stop="refusal")])
    with pytest.raises(llm.ClassificationError):
        llm.classify_with_log("x", None, model="claude-opus-5-5", client=c)


def test_baja_solo_si_no_interesado():
    c = FakeClient([_resp(json.dumps({"label": "pospone", "explicit_opt_out": True}))])
    assert llm.classify("x", None, model="claude-sonnet-5", client=c).baja_explicita is False


def test_el_mensaje_lleva_saliente_y_respuesta():
    m = llm.build_user_message("hola", None)
    assert "(vacío)" in m and "hola" in m
