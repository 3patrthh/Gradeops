import json
import re
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.core.config import GRADING_MAX_TOKENS, GRADING_MODEL_ID, OCR_MODEL_ID, OUTPUT_DIR
from app.services.answer_key_service import get_answer_key_for_question
from app.services.common import extract_json_from_model_output, safe_float, write_json


_grading_model = None
_grading_tokenizer = None


GRADING_PROMPT_TEMPLATE = """You are a strict but fair university exam grader.
Grade EXACTLY ONE student answer against the provided rubric.

=== GRADING RULES ===
1. For EACH rubric criterion, find a DIRECT QUOTE from the student answer that satisfies it.
2. Only award marks if the quote correctly satisfies that specific criterion.
   - Correct keyword in the wrong sentence = 0 marks for that criterion.
   - Swapped/reversed concept (e.g. supervised↔unsupervised) = 0 for that criterion.
3. Accept reasonable spelling mistakes and paraphrasing if meaning is correct.
4. Award PARTIAL marks (e.g. 0.5 out of 1.5) when the student partially addresses a criterion.
5. Do NOT award marks based on what you know — only based on what the student WROTE.
6. Grammar/spelling errors alone do not reduce marks if the meaning is clear.
7. The final awarded_marks MUST equal the exact sum of all rubric_breakdown awarded_marks.
8. awarded_marks cannot exceed max_marks.

=== INPUT ===
Question number  : __QUESTION_NUMBER__
Question text    : __QUESTION_TEXT__
Maximum marks    : __MAX_MARKS__
Model answer     : __MODEL_ANSWER__

Rubric (grade EACH criterion separately):
__RUBRIC_FORMATTED__

Student answer:
<student_answer>
__STUDENT_ANSWER__
</student_answer>

=== OUTPUT ===
Return ONLY a valid JSON object. No markdown, no explanation outside the JSON.
For each rubric_breakdown item, the "reason" field MUST include a short quote from
the student answer (or state "Not found in student answer" if missing).

JSON format:
{
  "question_number": "__QUESTION_NUMBER__",
  "max_marks": __MAX_MARKS__,
  "awarded_marks": <sum of all rubric awarded_marks>,
  "rubric_breakdown": [
    {
      "criterion": "<exact criterion text>",
      "max_marks": <criterion max>,
      "awarded_marks": <0 to criterion max>,
      "evidence": "<direct quote from student answer, or 'Not found'>",
      "reason": "<why marks were awarded or not>"
    }
  ],
  "overall_explanation": "<2-3 sentence summary of what student got right/wrong>",
  "missing_points": ["<concept/point the student missed>"],
  "confidence": <0.0 to 1.0>
}""".strip()


CONCEPT_SWAP_CHECKS = [
    ("supervised", "supervised", "unsupervised", "labelled"),
    ("unsupervised", "unsupervised", "supervised", "unlabelled"),
]

KEYWORD_MENTION_CHECKS = [
    (
        "mentions at least one ai task",
        ["speech", "recogni", "image", "problem", "solv", "decision", "translat", "diagnos", "classif"],
    ),
    (
        "gives at least one correct example of supervised",
        ["example", "e.g", "such as", "like", "classif", "cluster", "grouping", "spam", "cancer", "customer", "image"],
    ),
]


def load_grading_model(model_id: str = GRADING_MODEL_ID):
    """
    Load Qwen2.5 text model once and reuse it for grading.
    """
    global _grading_model, _grading_tokenizer

    if _grading_model is not None and _grading_tokenizer is not None:
        return _grading_model, _grading_tokenizer

    start = time.time()
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    _grading_tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    _grading_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        device_map="auto",
        trust_remote_code=True,
    )
    _grading_model.eval()

    print(f"Grading model loaded in {time.time() - start:.2f}s: {model_id}")
    return _grading_model, _grading_tokenizer


def unload_grading_model() -> None:
    global _grading_model, _grading_tokenizer

    try:
        del _grading_model
        del _grading_tokenizer
    except Exception:
        pass

    _grading_model = None
    _grading_tokenizer = None

    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def run_qwen_text_model(prompt: str, max_new_tokens: int = GRADING_MAX_TOKENS) -> str:
    model, tokenizer = load_grading_model()

    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = output_ids[0][inputs.input_ids.shape[-1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def format_rubric_for_prompt(rubric_list: list[dict]) -> str:
    lines = []
    for i, item in enumerate(rubric_list, 1):
        criterion = item.get("criterion", "")
        marks = item.get("marks", 0)
        lines.append(f"  {i}. [{marks} marks] {criterion}")
    return "\n".join(lines)


def build_grading_prompt(student_answer_obj: dict, answer_key_obj: dict) -> str:
    return GRADING_PROMPT_TEMPLATE \
        .replace("__QUESTION_NUMBER__", str(student_answer_obj.get("question_number", ""))) \
        .replace("__MAX_MARKS__", str(answer_key_obj.get("max_marks", 0))) \
        .replace("__QUESTION_TEXT__", str(answer_key_obj.get("question_text", ""))) \
        .replace("__MODEL_ANSWER__", str(answer_key_obj.get("model_answer", ""))) \
        .replace("__RUBRIC_FORMATTED__", format_rubric_for_prompt(answer_key_obj.get("rubric", []))) \
        .replace("__STUDENT_ANSWER__", str(student_answer_obj.get("answer_text", "")).strip())


def check_keyword_mention(criterion_text: str, student_answer: str, awarded: float) -> float:
    criterion_lower = criterion_text.lower()
    answer_lower = student_answer.lower()

    for crit_phrase, required_keywords in KEYWORD_MENTION_CHECKS:
        if crit_phrase not in criterion_lower:
            continue
        any_found = any(kw in answer_lower for kw in required_keywords)
        if not any_found:
            return 0.0

    return awarded


def check_concept_ownership(criterion_text: str, student_answer: str, awarded: float) -> float:
    criterion_lower = criterion_text.lower()
    answer_lower = student_answer.lower()

    for crit_kw, correct_concept, wrong_concept, property_kw in CONCEPT_SWAP_CHECKS:
        if crit_kw not in criterion_lower:
            continue
        if property_kw not in criterion_lower:
            continue

        correct_pos = answer_lower.find(correct_concept)
        if correct_pos == -1:
            continue

        student_context = answer_lower[correct_pos: correct_pos + 150]

        # Supervised should not be associated with unlabelled data.
        if correct_concept == "supervised":
            if "unlabel" in student_context or "without label" in student_context:
                return 0.0

        # Unsupervised should not be associated with labelled data.
        if correct_concept == "unsupervised":
            if "labelled" in student_context or "labeled" in student_context or "with label" in student_context:
                if "unlabelled" not in student_context and "unlabeled" not in student_context:
                    return 0.0

    return awarded


def validate_and_fix_grading_result(
    grading_json: dict,
    student_answer_obj: dict,
    answer_key_obj: dict,
) -> dict:
    """
    Normalize model JSON and enforce:
    - exact rubric criteria
    - awarded marks within limits
    - total equals sum of breakdown
    - lightweight hallucination/concept-swap checks
    """
    student_answer = student_answer_obj.get("answer_text", "") or ""
    rubric = answer_key_obj.get("rubric", [])
    max_marks = safe_float(answer_key_obj.get("max_marks"), 0.0)

    fixed_breakdown: list[dict] = []
    model_breakdown = grading_json.get("rubric_breakdown", [])
    if not isinstance(model_breakdown, list):
        model_breakdown = []

    for i, rubric_item in enumerate(rubric):
        criterion = rubric_item.get("criterion", "")
        criterion_max = safe_float(rubric_item.get("marks"), 0.0)

        model_item = model_breakdown[i] if i < len(model_breakdown) and isinstance(model_breakdown[i], dict) else {}
        awarded = safe_float(model_item.get("awarded_marks"), 0.0)

        awarded = max(0.0, min(awarded, criterion_max))
        awarded = check_keyword_mention(criterion, student_answer, awarded)
        awarded = check_concept_ownership(criterion, student_answer, awarded)

        fixed_breakdown.append({
            "criterion": criterion,
            "max_marks": criterion_max,
            "awarded_marks": round(awarded, 2),
            "evidence": model_item.get("evidence", "Not found"),
            "reason": model_item.get("reason", "Evaluated against rubric."),
        })

    awarded_total = round(sum(safe_float(x["awarded_marks"]) for x in fixed_breakdown), 2)
    awarded_total = min(awarded_total, max_marks)

    grading_json["question_number"] = str(student_answer_obj.get("question_number", ""))
    grading_json["max_marks"] = max_marks
    grading_json["rubric_breakdown"] = fixed_breakdown
    grading_json["awarded_marks"] = awarded_total
    grading_json["overall_explanation"] = grading_json.get("overall_explanation", "")
    grading_json["missing_points"] = grading_json.get("missing_points", [])
    grading_json["confidence"] = max(0.0, min(safe_float(grading_json.get("confidence"), 0.75), 1.0))

    return grading_json


def grade_single_answer_with_text_model(
    student_answer_obj: dict,
    answer_key_obj: dict,
    retry: bool = True,
) -> tuple[dict, str]:
    prompt = build_grading_prompt(student_answer_obj, answer_key_obj)
    raw_output = run_qwen_text_model(prompt, max_new_tokens=GRADING_MAX_TOKENS)

    try:
        grading_json = extract_json_from_model_output(raw_output)
    except Exception as e:
        grading_json = {
            "question_number": student_answer_obj.get("question_number", ""),
            "max_marks": answer_key_obj.get("max_marks", 0),
            "awarded_marks": 0,
            "rubric_breakdown": [],
            "overall_explanation": f"Model did not return valid JSON: {str(e)}",
            "missing_points": [],
            "confidence": 0.0,
        }

    grading_json = validate_and_fix_grading_result(grading_json, student_answer_obj, answer_key_obj)

    # Retry only when model gives true 0 to a non-empty answer.
    if retry:
        student_answer_text = (student_answer_obj.get("answer_text") or "").strip()
        if student_answer_text and safe_float(grading_json.get("awarded_marks")) == 0:
            retry_prompt = prompt + """

IMPORTANT RETRY:
The student answer is not empty. Re-check for any correct partial credit.
Still be strict. Do not invent evidence. Return valid JSON only.
"""
            raw_retry = run_qwen_text_model(retry_prompt, max_new_tokens=GRADING_MAX_TOKENS)
            try:
                retry_json = extract_json_from_model_output(raw_retry)
                retry_json = validate_and_fix_grading_result(retry_json, student_answer_obj, answer_key_obj)

                if safe_float(retry_json.get("awarded_marks")) > safe_float(grading_json.get("awarded_marks")):
                    return retry_json, raw_retry
            except Exception:
                pass

    return grading_json, raw_output


def grade_all_answers(ocr_result: dict, answer_key_json: dict) -> dict:
    start = time.time()
    grading_results: list[dict] = []

    for student_answer_obj in ocr_result.get("question_answers", []):
        qnum = str(student_answer_obj.get("question_number", "")).strip()
        answer_key_obj = get_answer_key_for_question(answer_key_json, qnum)

        if answer_key_obj is None:
            grading_results.append({
                "question_number": qnum,
                "status": "answer_key_not_found",
                "max_marks": 0,
                "awarded_marks": 0,
                "student_answer": student_answer_obj.get("answer_text", ""),
                "overall_explanation": "No matching answer key question found.",
            })
            continue

        grading_json, raw_output = grade_single_answer_with_text_model(student_answer_obj, answer_key_obj, retry=True)

        grading_json["question_number"] = qnum
        grading_json["student_answer"] = student_answer_obj.get("answer_text", "")
        grading_json["start_page"] = student_answer_obj.get("start_page")
        grading_json["end_page"] = student_answer_obj.get("end_page")
        grading_json["status"] = "graded"
        grading_json["raw_model_output"] = raw_output
        grading_results.append(grading_json)

    total_awarded = round(sum(safe_float(q.get("awarded_marks")) for q in grading_results), 2)
    total_max = round(sum(safe_float(q.get("max_marks")) for q in grading_results), 2)

    return {
        "student_id": ocr_result.get("student_id"),
        "exam_id": ocr_result.get("exam_id"),
        "grading_model": GRADING_MODEL_ID,
        "ocr_model": OCR_MODEL_ID,
        "total_awarded_marks": total_awarded,
        "total_max_marks": total_max,
        "grading_results": grading_results,
        "grading_time_seconds": round(time.time() - start, 2),
    }


def save_grading_result(result: dict, student_id: str, output_dir: str | Path = OUTPUT_DIR) -> Path:
    out_path = Path(output_dir) / f"{student_id}_grading_output.json"
    write_json(out_path, result)
    return out_path



def grade_answer(answer_text: str, rubric: dict) -> dict:
    """
    Backward-compatible wrapper used by the older GradeOps pipeline.

    For the real notebook-derived grading flow, prefer grade_all_answers(ocr_result, answer_key_json).
    This wrapper keeps existing APIs from breaking when a simple transcript + rubric is passed.
    """
    if not answer_text or not answer_text.strip():
        return {
            "score": 0,
            "max_score": 0,
            "justification": "No answer text was available for grading.",
            "confidence": 0.0,
            "criteria_breakdown": [],
        }

    # If a structured single-question rubric is supplied, grade through the text model.
    try:
        question_obj = {
            "question_number": rubric.get("question_number", "Q1"),
            "answer_text": answer_text,
        }
        answer_key_obj = {
            "question_number": rubric.get("question_number", "Q1"),
            "question_text": rubric.get("question_text", rubric.get("question", "")),
            "model_answer": rubric.get("model_answer", rubric.get("answer", "")),
            "max_marks": rubric.get("max_marks", rubric.get("max_score", 0)),
            "rubric": rubric.get("rubric", rubric.get("criteria", [])),
        }
        if answer_key_obj["rubric"] and answer_key_obj["max_marks"]:
            graded, _raw = grade_single_answer_with_text_model(question_obj, answer_key_obj, retry=True)
            return {
                "score": graded.get("awarded_marks", 0),
                "max_score": graded.get("max_marks", 0),
                "justification": graded.get("overall_explanation", ""),
                "confidence": graded.get("confidence", 0.75),
                "criteria_breakdown": graded.get("rubric_breakdown", []),
            }
    except Exception as exc:
        return {
            "score": 0,
            "max_score": rubric.get("max_marks", rubric.get("max_score", 0)) if isinstance(rubric, dict) else 0,
            "justification": f"Grading wrapper failed: {exc}",
            "confidence": 0.0,
            "criteria_breakdown": [],
        }

    # Safe fallback for upload smoke tests when no real rubric has been attached yet.
    return {
        "score": 0,
        "max_score": rubric.get("max_marks", rubric.get("max_score", 0)) if isinstance(rubric, dict) else 0,
        "justification": "OCR text was produced, but no structured rubric/answer key was supplied for model grading.",
        "confidence": 0.0,
        "criteria_breakdown": [],
    }
