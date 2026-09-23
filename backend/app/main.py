import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_routes import router as auth_router
from app.api.routes import router as api_router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="University Research Call for Paper Opportunity and Grants",
    version="1.1.0",
)


# CORS.
#
# The previous configuration was allow_origins=["*"] together with
# allow_credentials=True. That pair is invalid per the CORS spec: a
# browser rejects a credentialed response whose
# Access-Control-Allow-Origin is the "*" wildcard. It happened to work
# only because this frontend sends its JWT in an Authorization header
# rather than a cookie. Listing the real origins keeps it correct either
# way, and stops any site from calling this API from a user's browser.
_default_origins = [
    "https://university-research-intelligence-fr.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

_configured = [
    origin.strip()
    for origin in (settings.cors_origins or "").split(",")
    if origin.strip()
]

allowed_origins = sorted(set(_configured) | set(_default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Preview deployments get a generated subdomain per commit, so match
    # them by pattern rather than pinning every one.
    allow_origin_regex=r"https://university-research-intelligence.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(api_router, prefix="/api")
app.include_router(auth_router)


@app.get("/health")
def health():
    """Also used as a keep-warm target.

    This service runs on a free instance that spins down when idle; the
    first request after a sleep can take 50 seconds or more, which the
    frontend used to surface as a login failure. Pinging this endpoint on
    a schedule (or from the login page on mount) keeps the instance warm.
    """
    return {
        "status": "ok",
        "system": "University Research Call for Paper Opportunity and Grants",
        "version": "1.1.0",
    }
