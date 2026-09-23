import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
import api, { setUnauthorizedHandler } from "../api/client"

const AuthContext = createContext(null)

// Re-check the session when the tab regains focus, but not more often
// than this — a user flicking between tabs shouldn't spam /api/auth/me.
const REVALIDATE_THROTTLE_MS = 60000

/**
 * Read the `exp` claim out of a JWT without verifying it.
 *
 * Client-side only, and only ever used to decide "this token is already
 * dead, don't bother sending it". The server still verifies every token;
 * nothing here grants access.
 */
function tokenExpiry(token) {
  try {
    const [, payload] = token.split(".")
    const decoded = JSON.parse(
      atob(payload.replace(/-/g, "+").replace(/_/g, "/"))
    )
    return typeof decoded.exp === "number" ? decoded.exp * 1000 : null
  } catch {
    return null
  }
}

function isExpired(token) {
  const expiresAt = tokenExpiry(token)
  // Treat an unreadable token as expired: it cannot be used anyway.
  if (!expiresAt) return true
  // 30s skew, so we don't send a token that dies in flight.
  return Date.now() >= expiresAt - 30000
}

function clearStoredSession() {
  localStorage.removeItem("auth_token")
  localStorage.removeItem("auth_user")
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // "ready" distinguishes "still checking a stored token" from
  // "checked, and there's no user" — without it, ProtectedRoute would
  // redirect to /login for a split second on every page load/refresh
  // even when a valid token is sitting in localStorage.
  const [ready, setReady] = useState(false)
  const lastCheck = useRef(0)
  const expiryTimer = useRef(null)

  const endSession = useCallback(() => {
    clearStoredSession()
    setUser(null)
  }, [])

  // The axios interceptor lives outside React, so it cannot navigate.
  // Registering this handler lets a 401 drop the user through React
  // Router instead of a hard window.location reload — which is what used
  // to land on a blank page.
  useEffect(() => {
    setUnauthorizedHandler(endSession)
    return () => setUnauthorizedHandler(null)
  }, [endSession])

  const validate = useCallback(async () => {
    const token = localStorage.getItem("auth_token")

    if (!token) {
      endSession()
      setReady(true)
      return
    }

    // Expired tokens are dropped locally. Previously the app kept a dead
    // token indefinitely: nothing re-checked it while the tab stayed
    // open, so the UI looked signed in until something finally failed.
    if (isExpired(token)) {
      endSession()
      setReady(true)
      return
    }

    try {
      const response = await api.get("/api/auth/me")
      setUser(response.data)
    } catch (error) {
      // Only a genuine 401 means the session is dead. A timeout or a 5xx
      // is the backend waking from sleep — keep the session and let the
      // user retry, rather than logging them out over a cold start.
      if (error?.response?.status === 401) {
        endSession()
      }
    } finally {
      lastCheck.current = Date.now()
      setReady(true)
    }
  }, [endSession])

  useEffect(() => {
    validate()
  }, [validate])

  // Schedule an automatic sign-out for the moment the token expires, so a
  // dashboard left open overnight lands on the login page by itself
  // rather than sitting there with a dead session.
  useEffect(() => {
    clearTimeout(expiryTimer.current)
    if (!user) return

    const token = localStorage.getItem("auth_token")
    const expiresAt = token && tokenExpiry(token)
    if (!expiresAt) return

    const msUntilExpiry = expiresAt - Date.now()
    // setTimeout overflows past ~24.8 days; clamp well below that.
    if (msUntilExpiry > 0 && msUntilExpiry < 2 ** 31 - 1) {
      expiryTimer.current = setTimeout(endSession, msUntilExpiry)
    }

    return () => clearTimeout(expiryTimer.current)
  }, [user, endSession])

  // Re-validate when the tab comes back to the foreground. This is the
  // case the user hit: leave the dashboard open for hours, come back,
  // and the app had no idea the token had died.
  useEffect(() => {
    function onVisible() {
      if (document.visibilityState !== "visible") return
      if (Date.now() - lastCheck.current < REVALIDATE_THROTTLE_MS) return
      validate()
    }

    document.addEventListener("visibilitychange", onVisible)
    window.addEventListener("focus", onVisible)
    return () => {
      document.removeEventListener("visibilitychange", onVisible)
      window.removeEventListener("focus", onVisible)
    }
  }, [validate])

  // Sign-out in one tab should sign out the others.
  useEffect(() => {
    function onStorage(event) {
      if (event.key === "auth_token" && !event.newValue) {
        setUser(null)
      }
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  function persist(data) {
    localStorage.setItem("auth_token", data.access_token)
    localStorage.setItem("auth_user", JSON.stringify(data.user))
    setUser(data.user)
    lastCheck.current = Date.now()
  }

  async function login(email, password) {
    const r = await api.post("/api/auth/login", { email, password })
    persist(r.data)
  }

  async function register(name, email, password) {
    const r = await api.post("/api/auth/register", { name, email, password })
    persist(r.data)
  }

  async function loginWithGoogle(credential) {
    const r = await api.post("/api/auth/google", { credential })
    persist(r.data)
  }

  async function logout() {
    try {
      await api.post("/api/auth/logout")
    } catch {
      // stateless tokens — nothing to undo server-side even on failure
    }
    endSession()
  }

  return (
    <AuthContext.Provider
      value={{ user, ready, login, register, loginWithGoogle, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth() must be used inside an AuthProvider")
  }
  return ctx
}
