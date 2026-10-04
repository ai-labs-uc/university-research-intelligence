from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.database import get_db, next_id, utcnow
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth")


class RegisterPayload(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class GooglePayload(BaseModel):
    # The ID token (a signed JWT) returned by Google Identity Services'
    # Sign In With Google button on the frontend. This is NOT an OAuth
    # authorization code — nothing here ever needs a client secret.
    credential: str


def _user_public(user: dict) -> dict:
    return {
        "id": user["_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "has_password": bool(user.get("password_hash")),
        "has_google": bool(user.get("google_sub")),
    }


def _issue_and_touch(db, user_row: dict) -> dict:
    db.users.update_one(
        {"_id": user_row["_id"]},
        {"$set": {"last_login_at": utcnow()}},
    )
    token = create_access_token(user_row["_id"], user_row["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_public(user_row),
    }


@router.post("/register")
def register(payload: RegisterPayload, db=Depends(get_db)):
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters.",
        )

    existing = db.users.find_one({"email": payload.email})

    if existing:
        if existing.get("password_hash"):
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )
        # Account exists from a prior Google sign-in with no password
        # yet — link a password onto it instead of erroring, so the
        # same person can sign in either way going forward.
        new_hash = hash_password(payload.password)
        new_name = payload.name or existing["name"]
        db.users.update_one(
            {"_id": existing["_id"]},
            {"$set": {"password_hash": new_hash, "name": new_name}},
        )
        existing["password_hash"] = new_hash
        existing["name"] = new_name
        return _issue_and_touch(db, existing)

    user_row = {
        "_id": next_id("users"),
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "google_sub": None,
        "role": "RESEARCHER",
        "active": True,
        "last_login_at": None,
        "created_at": utcnow(),
    }
    db.users.insert_one(user_row)

    return _issue_and_touch(db, user_row)


@router.post("/login")
def login(payload: LoginPayload, db=Depends(get_db)):
    user = db.users.find_one({"email": payload.email})

    if not user or not verify_password(payload.password, user.get("password_hash")):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    if not user["active"]:
        raise HTTPException(status_code=403, detail="Account has been deactivated.")

    return _issue_and_touch(db, user)


@router.post("/google")
def google_login(payload: GooglePayload, db=Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(
            status_code=501,
            detail=(
                "Google sign-in is not configured on this server — "
                "set GOOGLE_CLIENT_ID in backend/.env. See docs/AUTH.md."
            ),
        )

    try:
        claims = google_id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google credential.")

    if not claims.get("email_verified", False):
        raise HTTPException(
            status_code=401,
            detail="Google account email is not verified.",
        )

    email = claims["email"]
    google_sub = claims["sub"]
    name = claims.get("name") or email.split("@")[0]

    user = db.users.find_one({"$or": [{"email": email}, {"google_sub": google_sub}]})

    if user:
        if not user.get("google_sub"):
            db.users.update_one({"_id": user["_id"]}, {"$set": {"google_sub": google_sub}})
            user["google_sub"] = google_sub
        if not user["active"]:
            raise HTTPException(
                status_code=403, detail="Account has been deactivated."
            )
    else:
        user = {
            "_id": next_id("users"),
            "name": name,
            "email": email,
            "password_hash": None,
            "google_sub": google_sub,
            "role": "RESEARCHER",
            "active": True,
            "last_login_at": None,
            "created_at": utcnow(),
        }
        db.users.insert_one(user)

    return _issue_and_touch(db, user)


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return _user_public(current_user)


@router.post("/logout")
def logout():
    # JWTs here are stateless and short-lived (see
    # ACCESS_TOKEN_EXPIRE_MINUTES) — there's no server-side session to
    # tear down. The frontend deletes its stored token; this endpoint
    # exists so the frontend has one consistent call to make and so a
    # future token-blacklist can be added here without changing the
    # frontend contract.
    return {"status": "logged_out"}
