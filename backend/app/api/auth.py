from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str

@router.post('/login')
def login(payload: LoginRequest):
    # Prototype login. Replace with MongoDB/PostgreSQL user lookup + JWT later.
    return {
        'access_token': 'dev-token',
        'token_type': 'bearer',
        'user': {
            'email': payload.email,
            'role': payload.role,
        },
    }
