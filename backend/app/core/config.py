import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = "GradeOps"

    # MongoDB settings
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "gradeops")

    # Local file upload storage used by normal portal APIs
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "uploads"))

    # Kept for compatibility with old frontend/settings screen
    model_name: str = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-VL")


settings = Settings()

# Backend/model storage paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BACKEND_DIR / os.getenv("STORAGE_DIR", "storage")

STUDENT_PDF_DIR = STORAGE_DIR / "uploads" / "student_pdfs"
ANSWER_KEY_PDF_DIR = STORAGE_DIR / "uploads" / "answer_key_pdfs"
STUDENT_IMAGE_DIR = STORAGE_DIR / "images" / "student_pages"
ANSWER_KEY_IMAGE_DIR = STORAGE_DIR / "images" / "answer_key_pages"
OUTPUT_DIR = STORAGE_DIR / "outputs"

for path in [
    STORAGE_DIR,
    STUDENT_PDF_DIR,
    ANSWER_KEY_PDF_DIR,
    STUDENT_IMAGE_DIR,
    ANSWER_KEY_IMAGE_DIR,
    OUTPUT_DIR,
    settings.upload_dir,
]:
    path.mkdir(parents=True, exist_ok=True)

# Model IDs copied from GradeOPS notebook pipeline
OCR_MODEL_ID = os.getenv("OCR_MODEL_ID", "JackChew/Qwen2-VL-2B-OCR")
GRADING_MODEL_ID = os.getenv("GRADING_MODEL_ID", "Qwen/Qwen2.5-3B-Instruct")

# Speed / token controls
PDF_DPI = int(os.getenv("PDF_DPI", "140"))
OCR_MAX_TOKENS = int(os.getenv("OCR_MAX_TOKENS", "700"))
ANSWER_KEY_OCR_MAX_TOKENS = int(os.getenv("ANSWER_KEY_OCR_MAX_TOKENS", "1200"))
GRADING_MAX_TOKENS = int(os.getenv("GRADING_MAX_TOKENS", "650"))
UNLOAD_OCR_BEFORE_GRADING = os.getenv("UNLOAD_OCR_BEFORE_GRADING", "true").lower() == "true"

GEN_KWARGS_FAST = {
    "do_sample": False,
    "temperature": None,
    "top_p": None,
}
