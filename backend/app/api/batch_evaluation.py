from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.services.batch_evaluation_service import evaluate_batch_csv


router = APIRouter(
    prefix="/api/batch",
    tags=["Batch Evaluation"]
)


@router.post("/evaluate")
async def evaluate_batch(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    try:
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded CSV file is empty."
            )

        csv_content = content.decode("utf-8-sig")

        result = evaluate_batch_csv(csv_content)

        return result

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The CSV file must use UTF-8 encoding."
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Batch evaluation failed: {str(exc)}"
        )