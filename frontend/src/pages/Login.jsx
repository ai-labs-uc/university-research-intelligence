import { useEffect, useRef, useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import { errorMessage, warmBackend } from "../api/client"
import GoogleButton from "../auth/GoogleButton"
import Logo from "../components/Logo"

// How long a sign-in can run before we tell the user the server is
// waking rather than leaving them staring at a spinner. The API is on a
// free instance that sleeps when idle; a cold start was measured at 36.7s.
const WAKE_HINT_AFTER_MS = 4000

export default function Login() {
  const { login, loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectTo = location.state?.from?.pathname || "/"

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [waking, setWaking] = useState(false)
  const wakeTimer = useRef(null)

  // Wake the backend as soon as the page loads, so it is usually already
  // up by the time the user finishes typing their password.
  useEffect(() => {
    warmBackend()
    return () => clearTimeout(wakeTimer.current)
  }, [])

  function startSubmit() {
    setError("")
    setSubmitting(true)
    wakeTimer.current = setTimeout(() => setWaking(true), WAKE_HINT_AFTER_MS)
  }

  function endSubmit() {
    clearTimeout(wakeTimer.current)
    setWaking(false)
    setSubmitting(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    startSubmit()
    try {
      await login(email, password)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(errorMessage(err, "Couldn't sign in. Please try again."))
    } finally {
      endSubmit()
    }
  }

  async function handleGoogleCredential(credential) {
    startSubmit()
    try {
      await loginWithGoogle(credential)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(errorMessage(err, "Google sign-in failed. Please try again."))
    } finally {
      endSubmit()
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <Logo size={48} className="mb-4" />
        <p className="text-xs font-bold uppercase tracking-widest text-uc-700">
          University Research Office
        </p>
        <h1 className="mt-2 text-2xl font-black">Sign in</h1>

        <div className="mt-6">
          <GoogleButton onCredential={handleGoogleCredential} />
        </div>

        <div className="my-6 flex items-center gap-3 text-xs font-semibold uppercase text-slate-400">
          <div className="h-px flex-1 bg-slate-200" />
          or
          <div className="h-px flex-1 bg-slate-200" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full rounded-xl border border-slate-300 px-4 py-3"
          />
          <input
            type="password"
            required
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full rounded-xl border border-slate-300 px-4 py-3"
          />

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          {waking && !error && (
            <p className="text-sm text-slate-500">
              Waking up the server — this can take up to a minute on the
              first sign-in of the day.
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-uc-800 px-5 py-3 font-semibold text-white transition hover:bg-uc-900 disabled:opacity-50"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          No account?{" "}
          <Link to="/register" className="font-semibold text-uc-700">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
