import { useState } from "react"

/**
 * Renders the university's real logo — frontend/public/uc-logo.png, the
 * official UC seal (see docs/BRANDING.md for its source and how to swap
 * it for a different file). It's a tall seal shape, not a square icon,
 * so it renders with object-contain inside a fixed-size box rather than
 * being cropped.
 *
 * If that file is ever missing or fails to load, this falls back to a
 * plain, obviously-generic monogram badge in the brand green rather than
 * drawing a stand-in seal/crest — recreating a specific institution's
 * actual insignia from memory would be inaccurate, so a genuine fallback
 * is a safer failure mode than a fabricated one.
 */
export default function Logo({ size = 40, className = "" }) {
  const [failed, setFailed] = useState(false)

  if (!failed) {
    return (
      <img
        src="/uc-logo.png"
        alt="University of the Cordilleras"
        width={size}
        height={size}
        onError={() => setFailed(true)}
        className={`object-contain ${className}`}
      />
    )
  }

  return (
    <div
      title="University of the Cordilleras (logo image failed to load)"
      style={{ width: size, height: size }}
      className={`flex items-center justify-center rounded-full bg-uc-700 font-black text-white ${className}`}
    >
      <span style={{ fontSize: size * 0.4 }}>UC</span>
    </div>
  )
}
