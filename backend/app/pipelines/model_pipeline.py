import shutil
import time
from pathlib import Path

from app.core.config import (
    ANSWER_KEY_PDF_DIR,
    OUTPUT_DIR,
    STUDENT_PDF_DIR,
    UNLOAD_OCR_BEFORE_GRADING,
)
from app.services.answer_key_service import create_answer_key_json_fast
from app.services.grading_service import grade_all_answers, save_grading_result
from app.services.ocr_service import create_student_ocr_json, unload_ocr_model


def save_upload_file(upload_file, destination: Path) -> Path:
    """
    Save FastAPI UploadFile to disk.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return destination


def run_full_gradeops_pipeline(
    student_pdf_path: str | Path,
    answer_key_pdf_path: str | Path,
    exam_id: str,
    student_id: str,
    force_recreate_student_ocr: bool = True,
    force_recreate_answer_key_json: bool = False,
) -> dict:
    """
    Full backend pipeline separated from your notebook:

    1. Student PDF -> images -> OCR -> question-wise JSON
    2. Answer key PDF -> structured answer key JSON
    3. Student answers + answer key -> grading JSON
    """
    pipeline_start = time.time()

    student_ocr_result, student_ocr_path = create_student_ocr_json(
        pdf_path=student_pdf_path,
        student_id=student_id,
        exam_id=exam_id,
        force_recreate=force_recreate_student_ocr,
    )

    answer_key_result, answer_key_path = create_answer_key_json_fast(
        pdf_path=answer_key_pdf_path,
        exam_id=exam_id,
        force_recreate=force_recreate_answer_key_json,
    )
    answer_key_json = answer_key_result["answer_key_json"]

    if UNLOAD_OCR_BEFORE_GRADING:
        unload_ocr_model()

    grading_result = grade_all_answers(student_ocr_result, answer_key_json)
    grading_result["total_pipeline_time_seconds"] = round(time.time() - pipeline_start, 2)
    grading_output_path = save_grading_result(grading_result, student_id=student_id)

    return {
        "exam_id": exam_id,
        "student_id": student_id,
        "student_ocr_json_path": str(student_ocr_path),
        "answer_key_json_path": str(answer_key_path),
        "grading_output_path": str(grading_output_path),
        "student_ocr_result": student_ocr_result,
        "answer_key_result": answer_key_result,
        "grading_result": grading_result,
    }
