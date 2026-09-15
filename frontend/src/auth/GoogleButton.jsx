import { useEffect, useRef, useState } from "react"

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

let scriptPromise = null

function loadGoogleScript() {
  if (scriptPromise) return scriptPromise

  scriptPromise = new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve()
      return
    }
    const script = document.createElement("script")
    script.src = "https://accounts.google.com/gsi/client"
    script.async = true
    script.defer = true
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })

  return scriptPromise
}

// Renders Google's own "Sign in with Google" button (Google Identity
// Services) and hands the resulting ID token to onCredential. Silently
// renders nothing if no Client ID is configured — see docs/AUTH.md —
// so the rest of the login page still works with email/password alone.
export default function GoogleButton({ onCredential }) {
  const divRef = useRef(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (!CLIENT_ID) return

    let cancelled = false

    loadGoogleScript()
      .then(() => {
        if (cancelled || !divRef.current) return
        window.google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: response => onCredential(response.credential),
        })
        window.google.accounts.id.renderButton(divRef.current, {
          theme: "outline",
          size: "large",
          width: 320,
        })
      })
      .catch(() => setFailed(true))

    return () => {
      cancelled = true
    }
  }, [onCredential])

  if (!CLIENT_ID) {
    return (
      <p className="text-xs text-slate-400">
        Google sign-in isn't configured on this deployment yet.
      </p>
    )
  }

  if (failed) {
    return (
      <p className="text-xs text-amber-600">
        Couldn't load Google Sign-In — check your connection and reload.
      </p>
    )
  }

  return <div ref={divRef} />
}
