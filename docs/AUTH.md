# Authentication

The app has real login, logout, and self-service registration —
email/password and "Sign in with Google," either one. Every `/api/*`
endpoint except `/health` and `/api/auth/*` itself now requires a valid
session token; the frontend redirects anyone without one to `/login`.

## How it works

- **Email/password.** `POST /api/auth/register` hashes the password
  with `bcrypt` (directly — not `passlib`; see "Why not passlib" below)
  and stores it in `users.password_hash`. `POST /api/auth/login` checks
  it and returns a JWT.
- **Google.** The frontend renders Google's own "Sign in with Google"
  button (Google Identity Services) and gets back a signed ID token —
  this is *not* the OAuth redirect/callback dance, so there's no client
  secret involved anywhere. That token is sent to
  `POST /api/auth/google`, which verifies it against Google's public
  keys using the `google-auth` library and your configured
  `GOOGLE_CLIENT_ID`, then looks up or creates a `users` row by email
  and stores Google's `sub` claim in `users.google_sub`.
- **Account linking.** One person, one row: if you register with a
  password and later sign in with Google using the same email, the
  existing account gets `google_sub` attached rather than a duplicate
  account being created (and the reverse — registering a password on an
  email that first signed up via Google — works the same way). A row
  can have a password, a `google_sub`, or both.
- **Sessions.** A successful login/register/Google sign-in returns a
  JWT (`access_token`), valid for `ACCESS_TOKEN_EXPIRE_MINUTES` (default
  1440 = 24h), signed with `SECRET_KEY`. The frontend stores it in
  `localStorage` and sends it as `Authorization: Bearer <token>` on
  every API call (see `frontend/src/api/client.js`). There is no
  server-side session store or refresh token — the token is the session,
  and it simply stops working when it expires. A 401 response anywhere
  clears the stored token and bounces the frontend to `/login`.
- **Logout** (`POST /api/auth/logout`) doesn't need to invalidate
  anything server-side, since there's nothing stateful to invalidate —
  the frontend just deletes its stored token. The endpoint exists so
  there's one consistent call to make, and so a token blacklist could
  be added behind it later without changing the frontend.

## Setting up Google sign-in

Email/password works with zero configuration. Google sign-in needs one
thing only you can create — an OAuth Client ID from Google Cloud
Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/) →
   create or select a project.
2. **APIs & Services → OAuth consent screen** — configure it (internal
   if you're on Google Workspace and want to restrict this to UC
   accounts only, external otherwise) and add the scopes `email`,
   `profile`, `openid` (these are the defaults).
3. **APIs & Services → Credentials → Create Credentials → OAuth client
   ID** — type **Web application**. Add your frontend's origin(s) under
   **Authorized JavaScript origins** (e.g. `http://localhost:5173` for
   local dev, and your real domain once deployed). You do **not** need
   to add a redirect URI — this flow doesn't use one.
4. Copy the **Client ID** (looks like
   `1234567890-abc123.apps.googleusercontent.com`). You do not need the
   client secret for this flow at all.
5. Put the same Client ID in two places:
   - `backend/.env` → `GOOGLE_CLIENT_ID=...` (server verifies tokens
     against this)
   - `frontend/.env` → `VITE_GOOGLE_CLIENT_ID=...` (frontend passes this
     to Google's button)
6. Restart both the backend and the frontend dev server.

Until this is set up, the Google button on the Login/Register pages
quietly doesn't render (a small note explains why) and
`POST /api/auth/google` returns `501` — email/password keeps working
either way.

This deployment does **not** restrict Google sign-in to the
`uc-bcf.edu.ph` domain — any Google account can register. If you want
to restrict it later, the check is one line in
`backend/app/api/auth_routes.py`'s `google_login()`: compare
`claims["hd"]` (the "hosted domain" claim Google Workspace accounts
carry) against `"uc-bcf.edu.ph"` and reject anything else with a 403.
Google Workspace accounts carry `hd`; personal `@gmail.com` accounts
don't, so this also naturally excludes those if you want it to.

## Roles

`users.role` is `RESEARCHER`, `RESEARCH_ADMIN`, or `SYSTEM_ADMIN`. Every
self-registered account (password or Google) defaults to `RESEARCHER`.
**Nothing in the API currently checks role** — there's no admin-only
endpoint yet, so promoting someone today just means running:

```sql
UPDATE users SET role='SYSTEM_ADMIN' WHERE email='someone@uc-bcf.edu.ph';
```

Building real role-gated endpoints (e.g. only `SYSTEM_ADMIN` can manage
`opportunity_sources`) is straightforward — a `require_role("SYSTEM_ADMIN")`
dependency alongside `get_current_user` in `security.py` — but wasn't
built because nothing in this app is admin-only yet.

## What's intentionally not built

Matching the rest of this codebase's "simple first" philosophy — these
are real gaps, not oversights, and are reasonable Phase 2 work
(`docs/NEXT_STEPS.md`):

- **No password reset / forgot-password flow.** A locked-out
  password-only user currently has no self-service way back in; someone
  with database access has to reset it manually, or the person just
  uses Google sign-in on the same email if they have one.
- **No email verification** on password registration — anyone can
  register with any email address they type in. Google sign-in doesn't
  have this problem since Google already verifies `email_verified`.
- **No rate limiting** on `/api/auth/login` or `/api/auth/register` —
  nothing currently slows down repeated password guesses.
- **No refresh tokens** — sessions just expire after
  `ACCESS_TOKEN_EXPIRE_MINUTES` and the person logs in again. Fine for
  an internal tool; would want a proper refresh flow before this faces
  the public internet at scale.
- **JWT lives in `localStorage`**, not an `httpOnly` cookie — simpler to
  wire up (matches this app's plain `Authorization: Bearer` REST client)
  but readable by any JavaScript running on the page, which matters more
  if this app ever embeds third-party scripts. Worth revisiting before
  a security-sensitive deployment.

## Why not `passlib`

`requirements.txt` used to list `passlib[bcrypt]` (unused scaffolding
from before this feature existed). It was dropped: `passlib` is
unmaintained, and its `bcrypt` backend is broken against current
`bcrypt` releases (it reads a `bcrypt.__about__.__version__` attribute
that newer `bcrypt` versions removed, so every hash/verify call throws).
Hashing directly with the `bcrypt` library (already a `passlib[bcrypt]`
dependency, so nothing new to install) sidesteps the whole problem and
is fewer moving parts besides.
