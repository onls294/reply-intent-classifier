"""Sub-agent evaluation plumbing, with synthetic data only."""
import json

import pytest

from eval import subagent_batch as sb


def test_valida_como_llm_y_tolera_bom():
    ok = sb.validate('\ufeff{"id": "syn_001", "label": "pospone", "explicit_opt_out": false}')
    assert ok == {"id": "syn_001", "label": "pospone", "explicit_opt_out": False}


@pytest.mark.parametrize("line", [
    '{"id": "x", "label": "otra", "explicit_opt_out": false}',     # class outside the guide
    '{"id": "x", "label": "pospone", "explicit_opt_out": "no"}',   # opt-out not boolean
    'no es json',
])
def test_en_negativo_respuestas_invalidas(line):
    with pytest.raises((ValueError, json.JSONDecodeError)):
        sb.validate(line)


def test_baja_solo_si_no_interesado():
    assert sb.validate('{"id": "x", "label": "pospone", "explicit_opt_out": true}')["explicit_opt_out"] is False


def test_el_lote_muestra_el_prompt_de_llm_y_sin_etiquetas(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"S01": ["syn_001", "syn_018"]}), encoding="utf-8")
    sb.show(None, plan, "S01")
    out = capsys.readouterr().out
    from classifier import llm
    assert llm.SYSTEM_PROMPT in out and "### syn_001" in out
    assert "sin_intencion\n" not in out.split("=== BATCH")[1].replace("sin_intencion,", "")  # no gold labels after the prompt
    assert "label_source" not in out
