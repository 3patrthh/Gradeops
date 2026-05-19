"""
MongoDB connection helpers for GradeOps.

Collections used by the current backend:
- exams: uploaded exam metadata + saved PDF paths
- rubrics: manually created rubrics and uploaded JSON rubrics
- processing_results: OCR/grading pipeline output per uploaded PDF
- reviews: TA approve/override/flag actions
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def connect_to_mongo() -> None:
    """Create a single MongoDB client for the FastAPI app."""
    global _client, _db

    if _client is not None and _db is not None:
        return

    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_db_name]

    # Fail fast if MongoDB is not reachable.
    await _client.admin.command("ping")


async def close_mongo_connection() -> None:
    global _client, _db

    if _client is not None:
        _client.close()

    _client = None
    _db = None


def get_database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError(
            "MongoDB is not connected. Start MongoDB and check MONGODB_URI."
        )
    return _db


def serialize_mongo_doc(value: Any) -> Any:
    """Convert MongoDB ObjectId/datetime values into JSON-safe values."""
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [serialize_mongo_doc(item) for item in value]

    if isinstance(value, dict):
        return {key: serialize_mongo_doc(val) for key, val in value.items()}

    return value
