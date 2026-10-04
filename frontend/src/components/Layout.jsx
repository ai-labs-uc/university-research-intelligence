import { NavLink, Outlet, useNavigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import Logo from "./Logo"

const nav = [
  ["/", "Dashboard"],
  ["/opportunities", "Opportunities"],
  ["/sources", "Sources"],
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate("/login", { replace: true })
  }

  return (
    <div className="min-h-screen">
      {/* print:hidden -- the sidebar nav is pure chrome, not something
          anyone wants on a printed hard copy of a grant/CFP list. */}
      <aside className="fixed inset-y-0 left-0 flex w-64 flex-col bg-uc-950 p-6 text-white print:hidden">
        <div className="flex items-center gap-3">
          <Logo size={36} />
          <h1 className="text-base font-black leading-tight text-balance">
            Research Call for Paper Opportunity and Grants
          </h1>
        </div>

        <p className="mt-2 text-xs text-uc-200">
          University Research Office
        </p>

        <nav className="mt-8 space-y-2">
          {nav.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `block rounded-xl px-4 py-3 text-sm ${
                  isActive
                    ? "bg-white text-uc-900"
                    : "text-uc-100 hover:bg-white/10"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto border-t border-white/10 pt-4">
          {user && (
            <div className="mb-3">
              <p className="truncate text-sm font-semibold">{user.name}</p>
              <p className="truncate text-xs text-uc-200">{user.email}</p>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="w-full rounded-xl px-4 py-2 text-left text-sm text-uc-100 hover:bg-white/10"
          >
            Log out
          </button>
        </div>
      </aside>

      {/* print:ml-0/p-0 -- without the sidebar, the content shouldn't
          keep reserving a 16rem left margin on the printed page. */}
      <main className="ml-64 p-8 print:ml-0 print:p-0">
        <Outlet />
      </main>
    </div>
  )
}
