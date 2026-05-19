from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_database, serialize_mongo_doc, utc_now

router = APIRouter()

DEMO_REVIEW_QUEUE = [
    {
        "id": 1,
        "student": "Student #A-047",
        "exam": "CS301 — Midterm",
        "question": "Q2: Explain the time complexity of merge sort.",
        "aiScore": 8,
        "maxScore": 10,
        "confidence": 0.91,
        "justification": "Correct recurrence and complexity, missing space complexity.",
        "flagged": False,
    }
]


class OverrideRequest(BaseModel):
    score: float
    note: str


class FlagRequest(BaseModel):
    reason: str = "Needs instructor review"


@router.get("/queue")
async def queue():
    db = get_database()
    pending = await db.review_queue.find({"review_status": "pending"}).sort("created_at", -1).to_list(length=100)

    # Until the real grading pipeline inserts queue records, keep one demo item visible.
    if not pending:
        return {"queue": DEMO_REVIEW_QUEUE}

    return {"queue": serialize_mongo_doc(pending)}


@router.get("/completed")
async def completed_reviews():
    db = get_database()
    completed = await db.reviews.find().sort("created_at", -1).to_list(length=100)
    return {"completed": serialize_mongo_doc(completed)}


@router.post("/{paper_id}/approve")
async def approve(paper_id: int):
    return await _complete(paper_id, action="approved")


@router.post("/{paper_id}/override")
async def override(paper_id: int, payload: OverrideRequest):
    return await _complete(paper_id, action="overridden", final_score=payload.score, note=payload.note)


@router.post("/{paper_id}/flag")
async def flag(paper_id: int, payload: FlagRequest):
    return await _complete(paper_id, action="flagged", note=payload.reason)


async def _complete(paper_id: int, action: str, final_score=None, note: str = ""):
    db = get_database()

    paper = await db.review_queue.find_one({"id": paper_id, "review_status": "pending"})
    if paper is None:
        paper = next((p for p in DEMO_REVIEW_QUEUE if p["id"] == paper_id), None)

    if not paper:
        return {"message": "Paper not found or already reviewed"}

    review = {
        **paper,
        "action": action,
        "finalScore": final_score if final_score is not None else paper.get("aiScore"),
        "note": note,
        "created_at": utc_now(),
    }
    review.pop("_id", None)

    await db.reviews.insert_one(review)
    await db.review_queue.update_one(
        {"id": paper_id},
        {"$set": {"review_status": action, "updated_at": utc_now()}},
    )

    return {"message": f"Paper {action} and stored in MongoDB", "review": serialize_mongo_doc(review)}
