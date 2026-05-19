from app.services.grading_service import grade_answer
from app.services.plagiarism_service import check_plagiarism

def grade_transcripts(transcripts: list[dict], rubric: dict) -> list[dict]:
    graded = []
    previous_answers = []

    for item in transcripts:
        grade = grade_answer(item['transcript'], rubric)
        plagiarism = check_plagiarism(item['transcript'], previous_answers)
        previous_answers.append(item['transcript'])
        graded.append({**item, 'grade': grade, 'plagiarism': plagiarism})

    return graded
