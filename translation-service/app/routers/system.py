from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.translator import translation_engine

router = APIRouter()

@router.get("/")
async def root():
    return {
        "service": "Translation Microservice",
        "status": "running",
        "supported_languages": list(translation_engine.supported_languages.keys())
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": len(translation_engine.models),
        "supported_languages": list(translation_engine.supported_languages.keys())
    }

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = Path("app/templates/dashboard.html")
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    return dashboard_path.read_text(encoding="utf-8")
