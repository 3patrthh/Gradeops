import json
import re
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

try:
    from peft import PeftModel, PeftConfig
    PEFT_AVAILABLE = True
except Exception:
    PEFT_AVAILABLE = False

from app.core.config import (
    OCR_MODEL_ID,
    OCR_MAX_TOKENS,
    PDF_DPI,
    STUDENT_IMAGE_DIR,
    OUTPUT_DIR,
    GEN_KWARGS_FAST,
)
from app.services.common import write_json
from app.services.pdf_service import pdf_to_images


STUDENT_OCR_PROMPT = """
You are a strict OCR transcription system.

Your only task is to read the handwritten or printed text visible in the image and write it exactly as it appears.

Rules:
1. Do NOT solve, grade, explain, summarize, improve, or correct the answer.
2. Do NOT add information that is not visible.
3. Preserve question markers exactly, especially QUESTION 1, QUESTION 2, etc.
4. Preserve line breaks where possible.
5. Preserve equations, symbols, bullet points, and numbering as text.
6. If a word is unclear, write [unclear].
7. Ignore page borders, shadows, scanner noise, and unrelated printed template text when possible.
8. Return only the transcribed text. No JSON, no explanation, no markdown.

Transcribe this page now.
""".strip()


_ocr_model = None
_ocr_processor = None


def load_ocr_model(model_id: str = OCR_MODEL_ID):
    """
    Load JackChew/Qwen2-VL-2B-OCR once and reuse it for OCR calls.

    Supports:
    - direct full model load
    - PEFT/LoRA adapter fallback, copied from your notebook
    """
    global _ocr_model, _ocr_processor

    if _ocr_model is not None and _ocr_processor is not None:
        return _ocr_model, _ocr_processor

    start = time.time()
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    try:
        _ocr_model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=dtype,
            device_map="auto",
            trust_remote_code=True,
        )
        _ocr_processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    except Exception as direct_error:
        if not PEFT_AVAILABLE:
            raise direct_error

        peft_config = PeftConfig.from_pretrained(model_id)
        base_id = peft_config.base_model_name_or_path

        base_model = Qwen2VLForConditionalGeneration.from_pretrained(
            base_id,
            torch_dtype=dtype,
            device_map="auto",
            trust_remote_code=True,
        )
        _ocr_model = PeftModel.from_pretrained(base_model, model_id)
        _ocr_processor = AutoProcessor.from_pretrained(base_id, trust_remote_code=True)

    _ocr_model.eval()
    print(f"OCR model loaded in {time.time() - start:.2f}s: {model_id}")
    return _ocr_model, _ocr_processor


def unload_ocr_model() -> None:
    """
    Free OCR model from GPU before loading grading model.
    Useful for T4/low VRAM GPUs.
    """
    global _ocr_model, _ocr_processor

    try:
        del _ocr_model
        del _ocr_processor
    except Exception:
        pass

    _ocr_model = None
    _ocr_processor = None

    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def run_qwen_vl_ocr_on_image(
    image_path: str | Path,
    prompt: str = STUDENT_OCR_PROMPT,
    max_new_tokens: int = OCR_MAX_TOKENS,
) -> str:
    """
    Run Qwen-VL OCR on one image.

    Input:
    - image_path: page/cropped answer image

    Output:
    - raw OCR transcript text
    """
    model, processor = load_ocr_model()

    image = Image.open(image_path).convert("RGB")
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": prompt},
        ],
    }]

    chat_text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[chat_text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            **GEN_KWARGS_FAST,
        )

    trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, output_ids)]
    text = processor.batch_decode(
        trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]

    return text.strip()


# This is the function your existing backend placeholder should call.
def run_ocr_on_answer_image(image_path: str) -> str:
    return run_qwen_vl_ocr_on_image(image_path, STUDENT_OCR_PROMPT, OCR_MAX_TOKENS)


def parse_student_questions_strict(page_outputs: list[dict]) -> list[dict]:
    """
    Split OCR transcript question-wise.

    Expected markers:
    QUESTION 1
    answer...
    QUESTION 2
    answer...

    This intentionally stays strict, matching your notebook.
    """
    full_blocks: list[str] = []

    for page in page_outputs:
        full_blocks.append(f"\n[PAGE {page['page_number']}]\n{page.get('raw_text', '')}")

    full_text = "\n".join(full_blocks)
    pattern = r"(QUESTION\s+\d+)"
    matches = list(re.finditer(pattern, full_text, flags=re.IGNORECASE))

    question_answers: list[dict] = []

    for i, match in enumerate(matches):
        marker = match.group(1).strip()
        qnum = re.search(r"\d+", marker).group()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        answer_text = full_text[start:end].strip()

        page_nums = [int(x) for x in re.findall(r"\[PAGE\s+(\d+)\]", answer_text)]
        if page_nums:
            start_page = min(page_nums)
            end_page = max(page_nums)
        else:
            previous_pages = [int(x) for x in re.findall(r"\[PAGE\s+(\d+)\]", full_text[:match.start()])]
            start_page = previous_pages[-1] if previous_pages else None
            end_page = start_page

        answer_text = re.sub(r"\[PAGE\s+\d+\]", "", answer_text).strip()

        question_answers.append({
            "question_number": qnum,
            "answer_text": answer_text,
            "start_page": start_page,
            "end_page": end_page,
        })

    return question_answers


def create_student_ocr_json(
    pdf_path: str | Path,
    student_id: str,
    exam_id: str,
    force_recreate: bool = True,
    output_dir: str | Path = OUTPUT_DIR,
) -> tuple[dict, Path]:
    """
    Full student OCR stage:
    PDF -> page images -> OCR each page -> split into question-wise answers -> JSON
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{student_id}_ocr_output.json"

    if out_path.exists() and not force_recreate:
        return json.loads(out_path.read_text(encoding="utf-8")), out_path

    start = time.time()
    page_image_dir = Path(STUDENT_IMAGE_DIR) / exam_id / student_id
    image_paths = pdf_to_images(pdf_path, page_image_dir, dpi=PDF_DPI, force_recreate=force_recreate)

    page_outputs: list[dict] = []
    for idx, image_path in enumerate(image_paths, start=1):
        raw = run_qwen_vl_ocr_on_image(image_path, STUDENT_OCR_PROMPT, OCR_MAX_TOKENS)
        page_outputs.append({
            "page_number": idx,
            "image_path": image_path,
            "raw_text": raw,
        })

    question_answers = parse_student_questions_strict(page_outputs)

    result = {
        "student_id": student_id,
        "exam_id": exam_id,
        "answer_copy_file": pdf_path.name,
        "ocr_model": OCR_MODEL_ID,
        "page_outputs": page_outputs,
        "question_answers": question_answers,
        "processing_time_seconds": round(time.time() - start, 2),
    }

    write_json(out_path, result)
    return result, out_path
