from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.services.report_service import (
    generate_evaluation_report,
    get_available_report_batches,
)

router = APIRouter(
    prefix="/api/report",
    tags=["Evaluation Report"],
)


@router.get("/batches")
def report_batches():
    try:
        return {
            "status": "success",
            "batches": get_available_report_batches(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load report batches: {str(exc)}",
        )


@router.get("/export")
def export_report(batch_id: str = "single"):
    try:
        pdf = generate_evaluation_report(batch_id=batch_id)

        filename = (
            f"AI_Response_Validation_Report_"
            f"{batch_id.replace(' ', '_')}.pdf"
        )

        return StreamingResponse(
            pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate evaluation report: {str(exc)}",
        )
