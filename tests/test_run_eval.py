"""Evaluation metrics and stop conditions, with synthetic data and a mocked LLM."""
import pytest

from eval import run_eval as ev


def test_macro_f1_y_bootstrap_deterministas():
    gold = ["pide_informacion", "pospone", "pospone", "sin_intencion"]
    pred = ["pide_informacion", "pospone", "sin_intencion", "sin_intencion"]
    assert ev.macro_f1(gold, pred) == pytest.approx((1 + 2 / 3 + 2 / 3) / 3)
    assert ev.bootstrap_ci(gold, pred, ev.agreement) == ev.bootstrap_ci(gold, pred, ev.agreement)


def test_costo_de_errores_caros_y_bajas():
    c = ev.error_cost(["quiere_contacto", "no_interesado", "pospone"],
                      ["sin_intencion", "pospone", "pospone"], [False, True, False])
    assert c == {"mean_cost": (5 + 5 + 0) / 3, "expensive_errors": 2}


def test_costo_por_llamada_usa_el_archivo_de_precios():
    log = {"input_tokens": 1_000_000, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
    assert ev.call_cost("claude-sonnet-5", log) == ev.PRICING["models"]["claude-sonnet-5"]["input"]


def test_resumen_publicable_sin_texto():
    rows = [{"id": "syn_1", "reply": "TEXTO PRIVADO", "outbound": "", "gold": "pospone", "hard_v1": True, "hard_v2": False}]
    s = ev.summarize("x", rows, [{"id": "syn_1", "label": "pospone"}])
    assert "TEXTO PRIVADO" not in str(s) and s["hard_v1"]["agree_rows"] == 1


def test_en_negativo_se_para_si_fallan_mas_del_5_por_ciento(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "COUNTER", tmp_path / "c.json")
    from classifier import llm
    def boom(*a, **k):
        raise RuntimeError("api down")
    monkeypatch.setattr(llm, "classify_with_log", boom)
    rows = ev.load_synthetic()[:25]
    with pytest.raises(SystemExit, match="STOP"):
        ev.classify_rows(rows, "claude-sonnet-5", client=object(), workers=1)


def test_en_negativo_se_para_antes_de_pasar_de_1000_llamadas(monkeypatch, tmp_path):
    c = tmp_path / "c.json"
    c.write_text('{"calls": 990, "cost_usd": 0}', encoding="utf-8")
    monkeypatch.setattr(ev, "COUNTER", c)
    with pytest.raises(SystemExit, match="exceed"):
        ev.classify_rows(ev.load_synthetic()[:20], "claude-sonnet-5", client=object())


def test_reglas_sobre_el_sintetico():
    rows = ev.load_synthetic()
    preds, logs = ev.classify_rows(rows, "rules")
    assert logs is None and ev.agreement([r["gold"] for r in rows], [p["label"] for p in preds]) == 1.0


def _repo_snapshot():
    skip = {".venv", "__pycache__", ".pytest_cache", ".git"}
    return {f: (f.stat().st_mtime_ns, f.stat().st_size) for f in ev.REPO.rglob("*")
            if f.is_file() and not skip & set(f.relative_to(ev.REPO).parts)}


def test_en_negativo_run_y_report_solo_escriben_en_out(tmp_path):
    # 28 sep: --out se ignoraba y run/report reescribian eval/metrics y eval/results.md del repo.
    # Compara mtime y tamano: detecta tambien una reescritura con el mismo contenido.
    before = _repo_snapshot()
    ev.main(["run", "--model", "rules", "--set", "synthetic", "--out", str(tmp_path)])
    ev.main(["report", "--out", str(tmp_path)])
    assert _repo_snapshot() == before
    assert (tmp_path / "run-rules-synthetic.json").exists() and (tmp_path / "results.md").exists()
