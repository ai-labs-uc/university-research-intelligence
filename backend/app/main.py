from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.auth_routes import router as auth_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="1.0.0-simple",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        item.strip()
        for item in settings.cors_origins.split(",")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "system": settings.app_name,
        "version": "1.0.0-simple",
    }
