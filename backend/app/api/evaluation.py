from fastapi import APIRouter

from backend.app.models.evaluation import EvaluationInput
from backend.app.services.evaluation_service import process_evaluation


router = APIRouter(
    prefix="/api/evaluation",
    tags=["Evaluation"]
)


@router.post("/submit")
def submit_evaluation(
    data: EvaluationInput
):
    return process_evaluation(data)