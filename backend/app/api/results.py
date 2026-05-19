from fastapi import APIRouter

router = APIRouter()

@router.get('/dashboard')
def dashboard_stats():
    return {
        'total_papers': 200,
        'ai_graded': 131,
        'pending_review': 47,
        'approved': 84,
        'flagged': 9,
    }
