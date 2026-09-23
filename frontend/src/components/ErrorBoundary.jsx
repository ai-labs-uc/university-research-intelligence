import { Component } from "react"

/**
 * Catches render-time errors so a single bad field cannot blank the whole
 * app.
 *
 * Without this, any exception thrown during render unmounts the entire
 * React tree and leaves a white page with nothing to act on — which is
 * how "the dashboard crashes" looked from the outside. A boundary turns
 * that into a readable message plus a way out.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error("Unhandled render error:", error, info)
  }

  handleReload = () => {
    this.setState({ error: null })
    window.location.reload()
  }

  handleSignOut = () => {
    try {
      localStorage.removeItem("auth_token")
      localStorage.removeItem("auth_user")
    } catch {
      // storage can throw in private mode; signing out is best-effort
    }
    window.location.assign("/login")
  }

  render() {
    if (!this.state.error) {
      return this.props.children
    }

    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-xl font-black text-slate-900">
            Something went wrong
          </h1>
          <p className="mt-3 text-sm text-slate-600">
            This page hit an unexpected error. Reloading usually fixes it.
            If it keeps happening, sign out and back in.
          </p>

          <div className="mt-6 flex gap-3">
            <button
              onClick={this.handleReload}
              className="rounded-xl bg-uc-800 px-5 py-2.5 font-semibold text-white hover:bg-uc-900"
            >
              Reload
            </button>
            <button
              onClick={this.handleSignOut}
              className="rounded-xl border border-slate-300 px-5 py-2.5 font-semibold text-slate-700 hover:bg-slate-50"
            >
              Sign out
            </button>
          </div>

          {import.meta.env.DEV && (
            <pre className="mt-6 overflow-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-700">
              {String(this.state.error?.stack || this.state.error)}
            </pre>
          )}
        </div>
      </div>
    )
  }
}
