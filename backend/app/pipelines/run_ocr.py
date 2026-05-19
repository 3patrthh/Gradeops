from app.services.ocr_service import run_ocr_on_answer_image

def transcribe_answers(answer_regions: list[dict]) -> list[dict]:
    return [
        {
            **answer,
            'transcript': run_ocr_on_answer_image(answer['image_path']),
        }
        for answer in answer_regions
    ]
