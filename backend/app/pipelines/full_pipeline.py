from app.services.pdf_service import convert_pdf_to_images
from app.pipelines.extract_answers import split_answers_by_question
from app.pipelines.run_ocr import transcribe_answers
from app.pipelines.grade_answers import grade_transcripts


def process_exam_pdf(pdf_path: str, rubric: dict) -> list[dict]:
    """
    Portal upload pipeline:
    PDF -> page images -> answer regions -> OCR transcript -> grading wrapper -> plagiarism flag.

    For answer-key-PDF based full model grading, use:
    app.pipelines.model_pipeline.run_full_gradeops_pipeline(...)
    """
    page_images = convert_pdf_to_images(pdf_path)
    answer_regions = split_answers_by_question(page_images)
    transcripts = transcribe_answers(answer_regions)
    return grade_transcripts(transcripts, rubric)
