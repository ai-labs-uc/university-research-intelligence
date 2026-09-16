from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


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



app.include_router(
    router,
    prefix="/api"
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