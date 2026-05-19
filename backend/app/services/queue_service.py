def push_to_review_queue(graded_answer: dict) -> dict:
    """
    Integration point for pushing AI-graded answers into the TA dashboard queue.
    Later this should write to PostgreSQL/MongoDB and notify via WebSocket.
    """
    return graded_answer
