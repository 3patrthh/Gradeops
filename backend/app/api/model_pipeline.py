import json
import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import ANSWER_KEY_PDF_DIR, OUTPUT_DIR, STUDENT_PDF_DIR, STUDENT_IMAGE_DIR
from app.pipelines.model_pipeline import run_full_gradeops_pipeline
from app.services.answer_key_service import create_answer_key_json_fast
from app.services.grading_service import grade_all_answers, save_grading_result
from app.services.ocr_service import create_student_ocr_json, run_ocr_on_answer_image
from app.services.pdf_service import pdf_to_images
from app.services.common import read_json, write_json

router = APIRouter(prefix="/model", tags=["Model Pipeline"])


def _save_upload(upload_file: UploadFile, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return destination


@router.post("/pdf-to-images")
async def pdf_to_images_endpoint(
    file: UploadFile = File(...),
    exam_id: str = Form("exam_001"),
    dpi: int = Form(140),
):
    """
    Endpoint for Step 2:
    Convert uploaded PDF pages into PNG images.
    """
    pdf_path = STUDENT_PDF_DIR / exam_id / file.filename
    _save_upload(file, pdf_path)

    image_dir = STUDENT_IMAGE_DIR / exam_id / Path(file.filename).stem
    image_paths = pdf_to_images(pdf_path, image_dir, dpi=dpi, force_recreate=True)

    return {
        "status": "success",
        "pdf_path": str(pdf_path),
        "image_count": len(image_paths),
        "image_paths": image_paths,
    }


@router.post("/ocr-image")
async def ocr_image_endpoint(
    file: UploadFile = File(...),
):
    """
    Endpoint for one image OCR.
    Useful for testing your Qwen-VL OCR model before full PDF pipeline.
    """
    image_path = OUTPUT_DIR / "single_image_ocr" / file.filename
    _save_upload(file, image_path)

    text = run_ocr_on_answer_image(str(image_path))

    return {
        "status": "success",
        "image_path": str(image_path),
        "ocr_text": text,
    }


@router.post("/student-ocr")
async def student_ocr_endpoint(
    student_pdf: UploadFile = File(...),
    exam_id: str = Form("exam_001"),
    student_id: str = Form("student_001"),
    force_recreate: bool = Form(True),
):
    """
    Endpoint for Steps 2, 3, 4, 5:
    Student PDF -> images -> OCR -> question-wise OCR JSON.
    """
    pdf_path = STUDENT_PDF_DIR / exam_id / student_id / student_pdf.filename
    _save_upload(student_pdf, pdf_path)

    result, out_path = create_student_ocr_json(
        pdf_path=pdf_path,
        student_id=student_id,
        exam_id=exam_id,
        force_recreate=force_recreate,
    )

    return {
        "status": "success",
        "ocr_json_path": str(out_path),
        "result": result,
    }


@router.post("/answer-key-json")
async def answer_key_json_endpoint(
    answer_key_pdf: UploadFile = File(...),
    exam_id: str = Form("exam_001"),
    force_recreate: bool = Form(False),
):
    """
    Endpoint for answer-key PDF extraction:
    direct PDF text first, OCR fallback if scanned.
    """
    pdf_path = ANSWER_KEY_PDF_DIR / exam_id / answer_key_pdf.filename
    _save_upload(answer_key_pdf, pdf_path)

    result, out_path = create_answer_key_json_fast(
        pdf_path=pdf_path,
        exam_id=exam_id,
        force_recreate=force_recreate,
    )

    return {
        "status": "success",
        "answer_key_json_path": str(out_path),
        "result": result,
    }


@router.post("/grade-json")
async def grade_json_endpoint(
    ocr_json_file: UploadFile = File(...),
    answer_key_json_file: UploadFile = File(...),
    student_id: str = Form("student_001"),
):
    """
    Endpoint for Steps 6 and 7:
    OCR JSON + answer-key JSON -> marks + justification JSON.
    """
    ocr_path = OUTPUT_DIR / "uploaded_json" / ocr_json_file.filename
    ak_path = OUTPUT_DIR / "uploaded_json" / answer_key_json_file.filename
    _save_upload(ocr_json_file, ocr_path)
    _save_upload(answer_key_json_file, ak_path)

    ocr_result = read_json(ocr_path)
    answer_key_file = read_json(ak_path)
    answer_key_json = answer_key_file.get("answer_key_json", answer_key_file)

    grading_result = grade_all_answers(ocr_result, answer_key_json)
    out_path = save_grading_result(grading_result, student_id=student_id)

    return {
        "status": "success",
        "grading_output_path": str(out_path),
        "result": grading_result,
    }


@router.post("/full-pipeline")
async def full_pipeline_endpoint(
    student_pdf: UploadFile = File(...),
    answer_key_pdf: UploadFile = File(...),
    exam_id: str = Form("exam_001"),
    student_id: str = Form("student_001"),
    force_recreate_student_ocr: bool = Form(True),
    force_recreate_answer_key_json: bool = Form(False),
):
    """
    Complete notebook pipeline as one backend endpoint:
    student PDF + answer key PDF -> OCR JSON + answer-key JSON + grading JSON.
    """
    student_pdf_path = STUDENT_PDF_DIR / exam_id / student_id / student_pdf.filename
    answer_key_pdf_path = ANSWER_KEY_PDF_DIR / exam_id / answer_key_pdf.filename

    _save_upload(student_pdf, student_pdf_path)
    _save_upload(answer_key_pdf, answer_key_pdf_path)

    try:
        result = run_full_gradeops_pipeline(
            student_pdf_path=student_pdf_path,
            answer_key_pdf_path=answer_key_pdf_path,
            exam_id=exam_id,
            student_id=student_id,
            force_recreate_student_ocr=force_recreate_student_ocr,
            force_recreate_answer_key_json=force_recreate_answer_key_json,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        **result,
    }
