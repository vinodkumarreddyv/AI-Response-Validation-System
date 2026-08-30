from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.evaluation import router as evaluation_router
from backend.app.database import initialize_database


initialize_database()


app = FastAPI(
    title="AI Response Validation System",
    description="AI response evaluation and hallucination detection system",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(evaluation_router)


@app.get("/")
def root():
    return {
        "message": "AI Response Validation System API is running."
    }