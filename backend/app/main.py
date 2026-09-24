from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.batch_evaluation import router as batch_evaluation_router
from backend.app.database import initialize_database


app = FastAPI(
    title="AI Response Validation System",
    description="AI Response Validation System with RAG-based evaluation and batch evaluation",
    version="3.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


initialize_database()


app.include_router(evaluation_router)
app.include_router(batch_evaluation_router)


@app.get("/")
def root():
    return {
        "message": "AI Response Validation System backend is running.",
        "docs": "/docs",
        "evaluation_endpoint": "/api/evaluation/submit",
        "batch_endpoint": "/api/batch/evaluate"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Response Validation System"
    }