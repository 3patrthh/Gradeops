def split_answers_by_question(page_images: list[str]) -> list[dict]:
    """
    Future step:
    Detect markers like QUESTION 1, QUESTION 2, etc. and attach answers that
    continue across pages.
    """
    return [{'question_id': 'Q1', 'image_path': image} for image in page_images]
