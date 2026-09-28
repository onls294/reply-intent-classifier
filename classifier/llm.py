"""LLM classifier: one prompt (guide v2) for every evaluated Claude model.

This is the publishable API classifier. It has NOT been run against the API yet: the numbers in
eval/results.md come from Claude Code sub-agents that received this exact prompt and input
(eval/subagent_batch.py). Results through the API may differ (different harness, effort and
sampling defaults), and cost and latency only exist for this path.

Input = the pseudonymized reply + the last outbound message, the same thing the labelers saw.
Output = structured JSON (one class from the guide + explicit opt-out), validated here.
Every call logs tokens (including cache), latency, attempts and format errors.

Sampling: Claude Opus 5.5 and Claude Sonnet 5 reject `temperature` (400), and Opus 5.5 cannot
turn thinking off. Both models therefore run with the same settings: no sampling parameters,
adaptive thinking (the default when the parameter is omitted) and effort "low". Run-to-run
variation is measured by the stability check in eval/run_eval.py instead.

Few-shot rule: examples, if ever added, come only from data/synthetic.py, never from rows or
leads of the evaluation set.
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from baseline.rules import Prediction
from labels import LABELS

GUIDE_PATH = Path(__file__).resolve().parent.parent / "data" / "LABELING_GUIDE.md"
MAX_TOKENS = 4096          # room for low-effort adaptive thinking plus a short JSON answer
EFFORT = "low"
FORMAT_RETRIES = 1         # one extra attempt when the answer is not valid JSON / not a class

SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": list(LABELS)},
        "explicit_opt_out": {"type": "boolean"},
    },
    "required": ["label", "explicit_opt_out"],
    "additionalProperties": False,
}


def build_system_prompt(guide_text: str) -> str:
    """Frozen system prompt: instructions + the full guide. Byte-stable so it caches."""
    return (
        "Eres un clasificador de intención de respuestas cortas de WhatsApp a mensajes "
        "automáticos de seguimiento comercial. Sigue exactamente la guía de etiquetado de "
        "abajo: una sola etiqueta por respuesta, con la regla de prioridad y los casos "
        "frontera. Los filtros (respuesta_automatica, sin_texto) no son etiquetas: no los uses. "
        "Marca explicit_opt_out = true solo si la etiqueta es no_interesado y la persona pide "
        "explícitamente no ser contactada. Los textos están seudonimizados: [NAME], [PHONE], "
        "[COMPANY] y similares son marcadores. Responde solo con el JSON pedido.\n\n"
        "<guia>\n" + guide_text + "\n</guia>"
    )


SYSTEM_PROMPT = build_system_prompt(GUIDE_PATH.read_text(encoding="utf-8"))


def build_user_message(reply: str, outbound: str | None) -> str:
    return ("Último mensaje de la empresa:\n" + (outbound.strip() if outbound and outbound.strip() else "(vacío)")
            + "\n\nRespuesta de la persona:\n" + reply.strip())


@dataclass
class CallLog:
    model: str
    attempts: int = 0
    format_errors: int = 0
    api_error: str = ""
    latency_s: float = 0.0
    input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    output_tokens: int = 0
    stop_reasons: list = field(default_factory=list)


class ClassificationError(RuntimeError):
    """Raised when no valid class came back after the allowed attempts."""


def parse_answer(response):
    """Validate a Messages API response. Returns (label, opt_out) or raises ValueError."""
    if response.stop_reason != "end_turn":
        raise ValueError(f"stop_reason={response.stop_reason}")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ValueError("no text block")
    data = json.loads(text)
    label, opt = data.get("label"), data.get("explicit_opt_out")
    if label not in LABELS or not isinstance(opt, bool):
        raise ValueError(f"invalid answer: {data!r}")
    return label, bool(opt and label == "no_interesado")


def classify_with_log(reply: str, outbound: str | None, *, model: str, client) -> tuple[Prediction, CallLog]:
    """One classification. API errors are retried by the SDK (client max_retries); a malformed
    answer gets FORMAT_RETRIES extra attempts. Raises ClassificationError if nothing valid."""
    log = CallLog(model=model)
    last = None
    for _ in range(1 + FORMAT_RETRIES):
        log.attempts += 1
        t0 = time.perf_counter()
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": build_user_message(reply, outbound)}],
            output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
        )
        log.latency_s += time.perf_counter() - t0
        u = response.usage
        log.input_tokens += u.input_tokens or 0
        log.cache_creation_input_tokens += getattr(u, "cache_creation_input_tokens", 0) or 0
        log.cache_read_input_tokens += getattr(u, "cache_read_input_tokens", 0) or 0
        log.output_tokens += u.output_tokens or 0
        log.stop_reasons.append(response.stop_reason)
        try:
            label, opt = parse_answer(response)
            return Prediction(label, opt, "llm"), log
        except (ValueError, json.JSONDecodeError) as e:
            log.format_errors += 1
            last = e
    raise ClassificationError(f"{model}: no valid answer after {log.attempts} attempts ({last})")


def classify(reply: str, outbound: str | None = None, *, model: str, client) -> Prediction:
    """Same signature shape and output as baseline.rules.classify (plus model and client)."""
    return classify_with_log(reply, outbound, model=model, client=client)[0]


PROMPT = SYSTEM_PROMPT   # kept for callers that inspect the prompt
