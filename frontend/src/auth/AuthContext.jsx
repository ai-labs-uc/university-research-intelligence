import { createContext, useContext, useEffect, useState } from "react"
import api from "../api/client"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // "ready" distinguishes "still checking a stored token" from
  // "checked, and there's no user" — without it, ProtectedRoute would
  // redirect to /login for a split second on every page load/refresh
  // even when a valid token is sitting in localStorage.
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("auth_token")
    if (!token) {
      setReady(true)
      return
    }
    api.get("/api/auth/me")
      .then(r => setUser(r.data))
      .catch(() => {
        localStorage.removeItem("auth_token")
        localStorage.removeItem("auth_user")
      })
      .finally(() => setReady(true))
  }, [])

  function persist(data) {
    localStorage.setItem("auth_token", data.access_token)
    localStorage.setItem("auth_user", JSON.stringify(data.user))
    setUser(data.user)
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
    localStorage.removeItem("auth_token")
    localStorage.removeItem("auth_user")
    setUser(null)
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
