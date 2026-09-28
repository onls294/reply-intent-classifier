"""Interfaces y metricas con datos SINTETICOS inventados."""
import re
from pathlib import Path

import pytest

from baseline import rules
from classifier import llm
from eval import run_eval
from labels import FILTERS, LABELS, PRIORITY

GUIDE = (Path(__file__).resolve().parent.parent / "data" / "LABELING_GUIDE.md").read_text(encoding="utf-8")


def test_las_clases_son_las_de_la_guia():
    assert set(re.findall(r"^\| `(\w+)` \|", GUIDE, re.M)) == set(LABELS) | set(FILTERS)
    assert set(PRIORITY) == set(LABELS)


def test_reglas_y_llm_comparten_la_salida():
    assert isinstance(rules.classify("quiero saber el precio", "hola"), rules.Prediction)
    assert llm.Prediction is rules.Prediction
    assert "<guia>" in llm.SYSTEM_PROMPT


def test_metricas_con_un_caso_calculado_a_mano():
    gold = ["pide_informacion", "pide_informacion", "pospone", "sin_intencion"]
    pred = ["pide_informacion", "pospone", "pospone", "sin_intencion"]
    pc = run_eval.per_class(gold, pred)
    assert pc["pide_informacion"] == (1.0, 0.5, 2)
    assert pc["pospone"] == (0.5, 1.0, 1)
    assert pc["fuera_de_tema"] == (None, None, 0)   # sin dato no es 0
    assert run_eval.agreement(gold, pred) == 0.75
    assert run_eval.confusion(gold, pred)["pide_informacion"]["pospone"] == 1


def test_en_negativo_una_clase_fuera_de_la_guia_se_rechaza():
    with pytest.raises(ValueError):
        run_eval.confusion(["pide_informacion"], ["respuesta_automatica"])
    with pytest.raises(ValueError):
        run_eval.confusion(["pide_informacion"], [])


def test_el_informe_se_genera():
    out = run_eval.report(["pospone"], ["pospone"])
    assert "agreement with Claude-generated labels 1.000" in out
    assert "accuracy" not in out.lower()
