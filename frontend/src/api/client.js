import axios from "axios"

// The API runs on a free instance that spins down when idle. A measured
// cold start took 36.7 seconds, and the platform's own warning says it
// "can delay requests by 50 seconds or more". axios defaults to no
// timeout but the browser and any proxy in between do not, and the login
// form gave up long before the server answered — which is what users
// reported as "login is broken". The auth endpoints therefore get a
// generous budget, and the login page pings /health on mount so the
// instance is usually already awake by the time anyone submits.
const COLD_START_TIMEOUT_MS = 90000
const NORMAL_TIMEOUT_MS = 25000

const baseURL =
  import.meta.env.VITE_API_URL || "http://localhost:8000"

const client = axios.create({
  baseURL,
  timeout: NORMAL_TIMEOUT_MS,
})

const SLOW_ENDPOINTS = [
  "/api/auth/login",
  "/api/auth/register",
  "/api/auth/google",
  "/api/pipeline/run",
]

// AuthContext registers a callback here so a 401 can clear the session
// and let React Router navigate. The interceptor sits outside React and
// previously did `window.location.href = "/login"` — a full page load,
// which hit the server for a path that has no file behind it and
// returned the host's 404 page instead of the app. That is what users
// saw as the dashboard "crashing" instead of redirecting to login.
let onUnauthorized = null

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

client.interceptors.request.use(config => {
  const token = localStorage.getItem("auth_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (SLOW_ENDPOINTS.some(path => (config.url || "").startsWith(path))) {
    config.timeout = COLD_START_TIMEOUT_MS
  }
  return config
})

client.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config || {}

    // Retry once on a cold-start failure: a timeout, a network-level
    // error, or the HTML 502/503 the platform serves while booting. Only
    // for idempotent-enough calls — never blindly re-POST a login that
    // already got a real answer, which is why 4xx is excluded here.
    const status = error.response?.status
    const isColdStart =
      error.code === "ECONNABORTED" ||
      (!error.response && error.request) ||
      status === 502 ||
      status === 503 ||
      status === 504

    if (isColdStart && !config.__retried) {
      config.__retried = true
      await new Promise(resolve => setTimeout(resolve, 3000))
      return client(config)
    }

    if (status === 401) {
      localStorage.removeItem("auth_token")
      localStorage.removeItem("auth_user")

      if (onUnauthorized) {
        // Preferred path: AuthContext clears the user, ProtectedRoute
        // renders <Navigate to="/login">, and React Router handles it
        // client-side. No page load, so nothing can 404.
        onUnauthorized()
      } else if (window.location.pathname !== "/login") {
        // Fallback only — before AuthProvider has mounted.
        window.location.assign("/login")
      }
    }

    return Promise.reject(error)
  }
)

/**
 * Human-readable message for a failed request.
 *
 * The API returns FastAPI's {detail: "..."} on handled errors, but the
 * hosting platform returns an HTML error page while the service boots —
 * reading .detail off that yields undefined and the UI showed nothing.
 */
export function errorMessage(error, fallback = "Something went wrong.") {
  const detail = error?.response?.data?.detail
  if (typeof detail === "string" && detail.trim()) return detail

  if (error?.code === "ECONNABORTED") {
    return "The server took too long to respond — it may be waking up. Please try again."
  }
  if (!error?.response) {
    return "Cannot reach the server. Check your connection and try again."
  }
  switch (error.response.status) {
    case 401: return "Incorrect email or password."
    case 403: return "Your account does not have access to this."
    case 429: return "Too many attempts. Please wait a moment and try again."
    case 502:
    case 503:
    case 504: return "The server is starting up. Please try again in a few seconds."
    default: return fallback
  }
}

/**
 * Fire-and-forget ping to wake the backend. Call on login page mount so
 * the instance is warm before the user finishes typing.
 */
export function warmBackend() {
  fetch(`${baseURL}/health`).catch(() => {})
}

export default client
