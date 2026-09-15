import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import GoogleButton from "../auth/GoogleButton"
import Logo from "../components/Logo"

export default function Register() {
  const { register, loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError("")
    setSubmitting(true)
    try {
      await register(name, email, password)
      navigate("/", { replace: true })
    } catch (err) {
      setError(
        err.response?.data?.detail || "Couldn't register. Please try again."
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function handleGoogleCredential(credential) {
    setError("")
    try {
      await loginWithGoogle(credential)
      navigate("/", { replace: true })
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
        <h1 className="mt-2 text-2xl font-black">Create an account</h1>

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
            required
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Full name"
            className="w-full rounded-xl border border-slate-300 px-4 py-3"
          />
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
            minLength={8}
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Password (min. 8 characters)"
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
            {submitting ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-uc-700">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
