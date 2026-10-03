from fastapi import APIRouter, HTTPException

from backend.app.services.dashboard_service import (
    get_dashboard_summary,
    get_dashboard_batches,
    get_evaluation_detail
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
def dashboard_summary(
    verdict: str = None,
    min_score: float = None,
    max_score: float = None,
    batch_id: str = None
):
    try:
        return get_dashboard_summary(
            verdict=verdict,
            min_score=min_score,
            max_score=max_score,
            batch_id=batch_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load dashboard summary: {str(exc)}"
        )


@router.get("/batches")
def dashboard_batches():
    try:
        return {
            "status": "success",
            "batches": get_dashboard_batches()
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load dashboard batches: {str(exc)}"
        )


@router.get("/evaluation/{submission_id}")
def evaluation_detail(submission_id: int):
    try:
        result = get_evaluation_detail(
            submission_id
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Evaluation record not found."
            )

        return {
            "status": "success",
            "record": result
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load evaluation detail: {str(exc)}"
        )