"""
Evaluates a single candidate answer using chain-of-thought prompting,
then parses the trailing JSON block into a structured score.
"""
import json
import re

from coach.llm_client import LLMError
from coach.prompts import EVALUATION_SYSTEM_PROMPT, build_evaluation_prompt

_JSON_RE = re.compile(r"\{[^{}]*\}")


def _parse_json_tail(text: str) -> dict:
    """
    The model is asked to put a JSON object on the last line, but may add
    stray formatting. Pull out the last well-formed {...} block robustly
    instead of assuming the whole string is valid JSON.
    """
    matches = _JSON_RE.findall(text)
    if not matches:
        raise LLMError("Could not parse an evaluation score from the model's response.")
    last = matches[-1]
    try:
        data = json.loads(last)
    except json.JSONDecodeError as e:
        raise LLMError("The evaluation response was malformed.") from e

    for key in ("clarity", "correctness", "confidence"):
        if key not in data:
            raise LLMError(f"Evaluation response is missing '{key}'.")
        try:
            data[key] = max(1, min(5, int(data[key])))
        except (TypeError, ValueError):
            data[key] = 3  # safe default rather than crashing the session
    data.setdefault("overall_comment", "")
    return data


def evaluate_answer(llm_client, role: str, question: str, answer: str) -> dict:
    """
    Returns: {"question": ..., "answer": ..., "clarity": int, "correctness": int,
              "confidence": int, "overall_comment": str, "raw_reasoning": str}
    """
    prompt = build_evaluation_prompt(role, question, answer)
    raw = llm_client.complete(EVALUATION_SYSTEM_PROMPT, prompt)
    parsed = _parse_json_tail(raw)
    return {
        "question": question,
        "answer": answer,
        "clarity": parsed["clarity"],
        "correctness": parsed["correctness"],
        "confidence": parsed["confidence"],
        "overall_comment": parsed["overall_comment"],
        "raw_reasoning": raw,
    }


def aggregate_scores(results: list[dict]) -> dict:
    if not results:
        return {"clarity": 0, "correctness": 0, "confidence": 0, "overall": 0}
    n = len(results)
    clarity = sum(r["clarity"] for r in results) / n
    correctness = sum(r["correctness"] for r in results) / n
    confidence = sum(r["confidence"] for r in results) / n
    overall = (clarity + correctness + confidence) / 3
    return {
        "clarity": round(clarity, 2),
        "correctness": round(correctness, 2),
        "confidence": round(confidence, 2),
        "overall": round(overall, 2),
    }
