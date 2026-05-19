from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import settings
from app.database import get_database, serialize_mongo_doc, utc_now
from app.pipelines.full_pipeline import process_exam_pdf

router = APIRouter()
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("")
async def list_exams():
    db = get_database()
    exams = await db.exams.find().sort("created_at", -1).to_list(length=100)
    return {"exams": serialize_mongo_doc(exams)}


@router.post("/upload")
async def upload_exam(
    exam_name: str = Form(...),
    course: str = Form(...),
    semester: str = Form("Fall 2024"),
    grading_model: str = Form("qwen-vl"),
    files: List[UploadFile] = File(...),
):
    db = get_database()
    saved_files = []
    pipeline_outputs = []

    for uploaded_file in files:
        safe_name = uploaded_file.filename.replace("/", "_").replace("\\", "_")
        target = UPLOAD_DIR / safe_name
        target.write_bytes(await uploaded_file.read())
        saved_files.append(str(target))

        # Stub pipeline call. In production, move this to a background worker.
        pipeline_result = process_exam_pdf(str(target), rubric={})
        pipeline_outputs.append({"file_path": str(target), "result": pipeline_result})

    exam = {
        "exam_name": exam_name,
        "course": course,
        "semester": semester,
        "grading_model": grading_model,
        "files": saved_files,
        "status": "processing",
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    insert_result = await db.exams.insert_one(exam)
    saved_exam = await db.exams.find_one({"_id": insert_result.inserted_id})

    if pipeline_outputs:
        await db.processing_results.insert_one({
            "exam_id": insert_result.inserted_id,
            "outputs": pipeline_outputs,
            "created_at": utc_now(),
        })

    return {
        "message": "Upload received, saved to MongoDB, and processing started",
        "exam": serialize_mongo_doc(saved_exam),
    }
