import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.batch_evaluation import router as batch_evaluation_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.report import router as report_router
from backend.app.database import initialize_database


app = FastAPI(
    title="AI Response Validation System",
    description=(
        "AI Response Validation System with RAG-based evaluation, "
        "batch evaluation, dashboard, and PDF reporting"
    ),
    version="4.1.0",
)


# Configurable CORS origins
cors_env = os.getenv("CORS_ORIGINS", "*").strip()
if cors_env == "*":
    allow_origins = ["*"]
else:
    allow_origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()]
    for local in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]:
        if local not in allow_origins:
            allow_origins.append(local)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True if "*" not in allow_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


initialize_database()


app.include_router(evaluation_router)
app.include_router(batch_evaluation_router)
app.include_router(dashboard_router)
app.include_router(report_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Response Validation System",
    }


# Frontend static files support (for unified Docker / single-service deployments)
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("docs", "openapi.json", "redoc", "health"):
            return None
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "message": "AI Response Validation System backend is running.",
            "docs": "/docs",
            "evaluation_endpoint": "/api/evaluation/submit",
            "batch_endpoint": "/api/batch/evaluate",
            "dashboard_endpoint": "/api/dashboard/summary",
            "report_endpoint": "/api/report/export",
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)


