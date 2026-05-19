from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, exams, rubrics, reviews, results, model_pipeline
from app.database import close_mongo_connection, connect_to_mongo

app = FastAPI(title="GradeOps Backend", version="0.3.0")

# CORS settings for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(exams.router, prefix="/exams", tags=["Exams"])
app.include_router(rubrics.router, prefix="/rubrics", tags=["Rubrics"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
app.include_router(results.router, prefix="/results", tags=["Results"])

# Notebook model endpoints. Router already has prefix="/model".
app.include_router(model_pipeline.router)


@app.get("/")
def root():
    return {
        "message": "GradeOps FastAPI backend is running with MongoDB storage and model pipeline endpoints",
        "docs": "/docs",
        "model_endpoints_prefix": "/model",
    }