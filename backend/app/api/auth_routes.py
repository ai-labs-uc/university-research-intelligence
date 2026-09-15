from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
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
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "has_password": bool(user.get("password_hash")),
        "has_google": bool(user.get("google_sub")),
    }


def _issue_and_touch(db: Session, user_row: dict) -> dict:
    db.execute(
        text("UPDATE users SET last_login_at=NOW() WHERE id=:id"),
        {"id": user_row["id"]},
    )
    db.commit()
    token = create_access_token(user_row["id"], user_row["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_public(user_row),
    }


@router.post("/register")
def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters.",
        )

    existing = db.execute(
        text("SELECT * FROM users WHERE email=:email"),
        {"email": payload.email},
    ).mappings().first()

    if existing:
        if existing["password_hash"]:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )
        # Account exists from a prior Google sign-in with no password
        # yet — link a password onto it instead of erroring, so the
        # same person can sign in either way going forward.
        db.execute(
            text('''
                UPDATE users
                SET password_hash=:hash, name=:name
                WHERE id=:id
            '''),
            {
                "hash": hash_password(payload.password),
                "name": payload.name or existing["name"],
                "id": existing["id"],
            },
        )
        db.commit()
        user_row = dict(existing)
        user_row["password_hash"] = "set"
        return _issue_and_touch(db, user_row)

    result = db.execute(
        text('''
            INSERT INTO users (name, email, password_hash, role)
            VALUES (:name, :email, :hash, 'RESEARCHER')
        '''),
        {
            "name": payload.name,
            "email": payload.email,
            "hash": hash_password(payload.password),
        },
    )
    db.commit()

    user_row = db.execute(
        text("SELECT * FROM users WHERE id=:id"),
        {"id": result.lastrowid},
    ).mappings().first()

    return _issue_and_touch(db, dict(user_row))


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.execute(
        text("SELECT * FROM users WHERE email=:email"),
        {"email": payload.email},
    ).mappings().first()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    if not user["active"]:
        raise HTTPException(status_code=403, detail="Account has been deactivated.")

    return _issue_and_touch(db, dict(user))


@router.post("/google")
def google_login(payload: GooglePayload, db: Session = Depends(get_db)):
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

    user = db.execute(
        text("SELECT * FROM users WHERE email=:email OR google_sub=:sub"),
        {"email": email, "sub": google_sub},
    ).mappings().first()

    if user:
        if not user["google_sub"]:
            db.execute(
                text("UPDATE users SET google_sub=:sub WHERE id=:id"),
                {"sub": google_sub, "id": user["id"]},
            )
            db.commit()
        if not user["active"]:
            raise HTTPException(
                status_code=403, detail="Account has been deactivated."
            )
        user_row = dict(user)
    else:
        result = db.execute(
            text('''
                INSERT INTO users (name, email, google_sub, role)
                VALUES (:name, :email, :sub, 'RESEARCHER')
            '''),
            {"name": name, "email": email, "sub": google_sub},
        )
        db.commit()
        user_row = dict(
            db.execute(
                text("SELECT * FROM users WHERE id=:id"),
                {"id": result.lastrowid},
            ).mappings().first()
        )

    return _issue_and_touch(db, user_row)


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
