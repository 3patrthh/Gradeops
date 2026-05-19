import json
import re
import time
from pathlib import Path

from app.core.config import (
    ANSWER_KEY_IMAGE_DIR,
    ANSWER_KEY_OCR_MAX_TOKENS,
    OUTPUT_DIR,
    PDF_DPI,
)
from app.services.common import has_enough_text, normalize_question_number, safe_float, write_json
from app.services.ocr_service import run_qwen_vl_ocr_on_image
from app.services.pdf_service import extract_text_from_pdf_directly, pdf_to_images


ANSWER_KEY_OCR_PROMPT = """
You are a strict OCR transcription system.
Read the answer key or marking scheme visible in the image and transcribe it exactly.
Preserve QUESTION numbers, Ideal Answer, Grading Rubric, marks, bullets, and equations.
Return only text. No JSON. No explanation.
""".strip()


def normalize_answer_key_markers(text: str) -> str:
    # For answer keys only, normalize Q1:/Q2: into QUESTION 1/QUESTION 2.
    return re.sub(r"\bQ\s*(\d+)\s*[:\.)-]", r"QUESTION \1\n", text, flags=re.IGNORECASE)


def parse_answer_key_text_regex(answer_key_text: str, exam_id: str) -> dict:
    text = normalize_answer_key_markers(answer_key_text)
    pattern = r"(QUESTION\s+\d+)"
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
    questions: list[dict] = []

    for i, m in enumerate(matches):
        label = m.group(1).strip().upper()
        qnum = re.search(r"\d+", label).group()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()

        max_marks_match = re.search(r"\((\d+(?:\.\d+)?)\s*Marks?\)", block, flags=re.IGNORECASE)
        max_marks = safe_float(max_marks_match.group(1), 0.0) if max_marks_match else 0.0

        ideal_match = re.search(r"Ideal\s+Answer\s*:", block, flags=re.IGNORECASE)
        rubric_match = re.search(r"Grading\s+Rubric\s*:", block, flags=re.IGNORECASE)

        if ideal_match:
            question_text = block[:ideal_match.start()].strip()
        else:
            question_text = block.split("\n", 1)[0].strip()

        question_text = re.sub(r"\(\s*\d+(?:\.\d+)?\s*Marks?\s*\)", "", question_text, flags=re.IGNORECASE).strip()
        question_text = re.sub(r"\s+", " ", question_text)

        if ideal_match and rubric_match:
            model_answer = block[ideal_match.end():rubric_match.start()].strip()
        elif ideal_match:
            model_answer = block[ideal_match.end():].strip()
        else:
            model_answer = ""

        model_answer = re.sub(r"\s+", " ", model_answer).strip()

        rubric: list[dict] = []
        if rubric_match:
            rubric_text = block[rubric_match.end():].strip()
            rubric_text = re.sub(r"\s+", " ", rubric_text)
            items = re.findall(r"(.+?)\s*\((\d+(?:\.\d+)?)\s*Marks?\)", rubric_text, flags=re.IGNORECASE)

            for criterion, marks in items:
                criterion = criterion.strip(" •-;\n\t")
                criterion = re.sub(r"^•\s*", "", criterion).strip()
                if criterion:
                    rubric.append({"criterion": criterion, "marks": safe_float(marks)})

        if not rubric and max_marks > 0:
            rubric = [{"criterion": "Correct answer according to the model answer.", "marks": max_marks}]

        if max_marks == 0 and rubric:
            max_marks = sum(safe_float(r.get("marks")) for r in rubric)

        questions.append({
            "question_number": qnum,
            "question_text": question_text,
            "max_marks": float(max_marks),
            "model_answer": model_answer,
            "rubric": rubric,
        })

    return {
        "exam_id": exam_id,
        "total_marks": float(sum(q["max_marks"] for q in questions)),
        "questions": questions,
    }


def extract_answer_key_text(pdf_path: str | Path) -> tuple[str, str]:
    """
    Direct text extraction first. If answer key is scanned, fallback to OCR.
    """
    direct_text = extract_text_from_pdf_directly(pdf_path)

    if has_enough_text(direct_text):
        return normalize_answer_key_markers(direct_text), "direct_pdf_text"

    image_paths = pdf_to_images(pdf_path, ANSWER_KEY_IMAGE_DIR, dpi=PDF_DPI, force_recreate=True)

    blocks: list[str] = []
    for idx, img_path in enumerate(image_paths, start=1):
        raw = run_qwen_vl_ocr_on_image(
            img_path,
            ANSWER_KEY_OCR_PROMPT,
            max_new_tokens=ANSWER_KEY_OCR_MAX_TOKENS,
        )
        blocks.append(f"\n[PAGE {idx}]\n{raw}")

    return normalize_answer_key_markers("\n".join(blocks)), "qwen_vl_ocr"


def validate_answer_key_json(answer_key_json: dict) -> list[str]:
    errors: list[str] = []
    questions = answer_key_json.get("questions", [])

    if not isinstance(questions, list) or not questions:
        return ["No questions found in answer key JSON"]

    total = 0.0

    for i, q in enumerate(questions):
        prefix = f"Question index {i}"

        if not q.get("question_number"):
            errors.append(prefix + ": missing question_number")

        max_marks = safe_float(q.get("max_marks"), 0.0)

        if max_marks <= 0:
            errors.append(prefix + ": max_marks missing or zero")

        total += max_marks

        if not q.get("model_answer"):
            errors.append(prefix + ": missing model_answer")

        rubric = q.get("rubric", [])
        if not isinstance(rubric, list) or not rubric:
            errors.append(prefix + ": missing rubric")
        else:
            rubric_sum = sum(safe_float(r.get("marks")) for r in rubric)
            if abs(rubric_sum - max_marks) > 0.05:
                errors.append(prefix + f": rubric sum {rubric_sum} != max_marks {max_marks}")

    answer_key_json["total_marks"] = round(total, 2)
    return errors


def create_answer_key_json_fast(
    pdf_path: str | Path,
    exam_id: str,
    force_recreate: bool = False,
    output_dir: str | Path = OUTPUT_DIR,
) -> tuple[dict, Path]:
    """
    Answer-key PDF -> structured answer_key_json.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / f"{exam_id}_answer_key_output.json"

    if out_path.exists() and not force_recreate:
        return json.loads(out_path.read_text(encoding="utf-8")), out_path

    start = time.time()
    answer_key_text, method = extract_answer_key_text(pdf_path)
    answer_key_json = parse_answer_key_text_regex(answer_key_text, exam_id=exam_id)
    validation_errors = validate_answer_key_json(answer_key_json)

    result = {
        "exam_id": exam_id,
        "source_pdf": pdf_path.name,
        "extraction_method": method,
        "answer_key_text": answer_key_text,
        "answer_key_json": answer_key_json,
        "validation_errors": validation_errors,
        "processing_time_seconds": round(time.time() - start, 2),
    }

    write_json(out_path, result)
    return result, out_path


def get_answer_key_for_question(answer_key_json: dict, question_number) -> dict | None:
    target = normalize_question_number(question_number)

    for q in answer_key_json.get("questions", []):
        if normalize_question_number(q.get("question_number")) == target:
            return q

    return None
