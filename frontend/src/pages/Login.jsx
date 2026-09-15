import { useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import GoogleButton from "../auth/GoogleButton"
import Logo from "../components/Logo"

export default function Login() {
  const { login, loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectTo = location.state?.from?.pathname || "/"

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError("")
    setSubmitting(true)
    try {
      await login(email, password)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(
        err.response?.data?.detail || "Couldn't sign in. Please try again."
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function handleGoogleCredential(credential) {
    setError("")
    try {
      await loginWithGoogle(credential)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(
        err.response?.data?.detail || "Google sign-in failed. Please try again."
      )
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
