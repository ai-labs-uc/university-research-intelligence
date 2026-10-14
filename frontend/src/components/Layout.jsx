import { NavLink, Outlet, useNavigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import Logo from "./Logo"

const nav = [
  ["/", "Dashboard"],
  ["/opportunities", "Opportunities"],
  ["/research", "Research Registry"],
  ["/research/analytics", "Research Analytics"],
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
      <aside className="relative flex w-full flex-col bg-uc-950 p-4 text-white print:hidden lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:p-6">
        <div className="flex items-center gap-3">
          <Logo size={36} />
          <h1 className="text-base font-black leading-tight text-balance">Research Call for Paper Opportunity and Grants</h1>
        </div>
        <p className="mt-2 text-xs text-uc-200">University Research Office</p>
        <nav className="mt-5 flex gap-2 overflow-x-auto pb-1 lg:mt-8 lg:block lg:space-y-2 lg:overflow-visible lg:pb-0">
          {nav.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) =>               `shrink-0 rounded-xl px-4 py-3 text-sm lg:block ${isActive ? "bg-white text-uc-900" : "text-uc-100 hover:bg-white/10"}`
            }>{label}</NavLink>
          ))}
        </nav>
        <div className="mt-5 border-t border-white/10 pt-4 lg:mt-auto">
          {user && <div className="mb-3"><p className="truncate text-sm font-semibold">{user.name}</p><p className="truncate text-xs text-uc-200">{user.email}</p></div>}
          <button onClick={handleLogout} className="w-full rounded-xl px-4 py-2 text-left text-sm text-uc-100 hover:bg-white/10">Log out</button>
        </div>
      </aside>
      <main className="p-4 sm:p-6 lg:ml-64 lg:p-8 print:ml-0 print:p-0"><Outlet /></main>
    </div>
  )
}
