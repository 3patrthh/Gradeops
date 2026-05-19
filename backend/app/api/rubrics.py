import json
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.database import get_database, serialize_mongo_doc, utc_now

router = APIRouter()


class RubricRequest(BaseModel):
    name: str = Field(..., min_length=1)
    exam_id: str | None = None
    questions: List[Dict[str, Any]]


def normalize_rubric(raw: Any, fallback_name: str = "Uploaded Rubric") -> dict:
    """
    Accepts either:
    1. { "name": "...", "questions": [...] }
    2. { "exam_name": "...", "questions": [...] }
    3. [ {question...}, {question...} ]
    """
    if isinstance(raw, list):
        return {"name": fallback_name, "exam_id": None, "questions": raw}

    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="Rubric JSON must be an object or a list")

    questions = raw.get("questions") or raw.get("rubric")
    if not isinstance(questions, list) or not questions:
        raise HTTPException(status_code=400, detail="Rubric JSON must contain a non-empty questions list")

    name = raw.get("name") or raw.get("rubric_name") or raw.get("exam_name") or fallback_name

    return {
        "name": str(name),
        "exam_id": raw.get("exam_id"),
        "questions": questions,
    }


@router.post("")
async def save_rubric(payload: RubricRequest):
    db = get_database()
    rubric = payload.model_dump()
    rubric.update({
        "source": "builder",
        "created_at": utc_now(),
        "updated_at": utc_now(),
    })

    result = await db.rubrics.insert_one(rubric)
    saved = await db.rubrics.find_one({"_id": result.inserted_id})

    return {"message": "Rubric saved to MongoDB", "rubric": serialize_mongo_doc(saved)}


@router.post("/upload-json")
async def upload_json_rubric(
    file: UploadFile = File(...),
    linked_exam: str | None = Form(None),
):
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Please upload a .json rubric file")

    try:
        content = await file.read()
        raw = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {exc.msg}") from exc

    rubric = normalize_rubric(raw, fallback_name=file.filename.replace(".json", ""))
    rubric.update({
        "source": "json_upload",
        "original_filename": file.filename,
        "linked_exam": linked_exam,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    })

    db = get_database()
    result = await db.rubrics.insert_one(rubric)
    saved = await db.rubrics.find_one({"_id": result.inserted_id})

    return {"message": "JSON rubric uploaded and saved to MongoDB", "rubric": serialize_mongo_doc(saved)}


@router.get("")
async def list_rubrics():
    db = get_database()
    rubrics = await db.rubrics.find().sort("created_at", -1).to_list(length=100)
    return {"rubrics": serialize_mongo_doc(rubrics)}
