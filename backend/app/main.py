from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router


app = FastAPI(
    title="University Research Call for Paper Opportunity and Grants",
    version="1.0.0-simple"
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "*"
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# General API routes
app.include_router(
    api_router,
    prefix="/api"
)


# Authentication routes
app.include_router(
    auth_router
)


@app.get("/health")
def health():

    return {
        "status": "ok",
        "system":
        "University Research Call for Paper Opportunity and Grants",
        "version":
        "1.0.0-simple"
    }