import sys

# Prevent uvicorn/fastapi from loading on Streamlit Cloud
sys.modules['uvicorn'] = None
sys.modules['fastapi'] = None

from pathlib import Path
import logging

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
except ImportError:
    uvicorn = None
    FastAPI = None
    CORSMiddleware = None
    FileResponse = None
    StaticFiles = None

from src.api.routes.metadata import router as metadata_router
from src.api.routes.recommendations import router as recommendations_router
from src.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("zomato_ai")
logger.info("Initializing Zomato AI Restaurant Recommendation API...")

if FastAPI:
    app = FastAPI(
        title="Zomato AI Restaurant Recommendation API",
        description=(
            "AI-powered restaurant recommendation service "
            "with hybrid filtering & LLM ranking."
        ),
        version="0.1.0",
    )

    # CORS Middleware setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files directory
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Register routes
    app.include_router(metadata_router)
    app.include_router(recommendations_router)


    @app.get("/", tags=["UI Root"])
    async def root():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Welcome to Zomato AI Restaurant Recommendation API"}


    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}


    if __name__ == "__main__":
        uvicorn.run(
            "src.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=True,
        )
else:
    # Dummy app for Streamlit Cloud (when fastapi is blocked)
    app = None
