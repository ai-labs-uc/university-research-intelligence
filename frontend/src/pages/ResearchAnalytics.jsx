import { useEffect, useMemo, useState } from "react"
import api, { errorMessage } from "../api/client"

const statusLabels = {
  DRAFT: "Draft",
  PENDING_REVIEW: "Pending review",
  ONGOING: "Ongoing",
  COMPLETED: "Completed",
  ARCHIVED: "Archived",
}

const typeLabels = {
  FACULTY: "Faculty",
  NON_TEACHING_STAFF: "Non-teaching staff",
  STUDENT: "Student",
  OTHER: "Other",
}

const statusColors = ["#64748b", "#d97706", "#2563eb", "#15803d", "#94a3b8"]

export default function ResearchAnalytics() {
  const [analytics, setAnalytics] = useState(null)
  const [message, setMessage] = useState("")

  useEffect(() => {
    api.get("/api/research/analytics")
      .then(response => setAnalytics(response.data))
      .catch(error => setMessage(errorMessage(error, "Could not load research analytics.")))
  }, [])

  const total = analytics?.total_research || 0
  const statusRows = useMemo(() => Object.entries(analytics?.by_status || {}).map(([key, value]) => ({ label: statusLabels[key] || key, value })), [analytics])
  const visibleStatusRows = useMemo(() => statusRows.filter(row => row.value > 0), [statusRows])
  const typeRows = useMemo(() => Object.entries(analytics?.by_researcher_type || {}).filter(([, value]) => value > 0).map(([key, value]) => ({ label: typeLabels[key] || key, value })), [analytics])

  return (
    <div className="space-y-6 print:space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-4 print:block">
        <div>
          <p className="text-sm font-semibold text-uc-700">University of the Cordilleras · Research Services Office</p>
          <h1 className="mt-1 text-3xl font-black">Research Registry Analytics</h1>
          <p className="mt-2 text-slate-600">Institutional view of ongoing and completed research records.</p>
        </div>
        <button onClick={() => window.print()} className="print:hidden rounded-xl bg-uc-800 px-5 py-3 font-semibold text-white">Print report</button>
      </header>

      {message && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 print:hidden">{message}</p>}
      {!analytics && !message && <p className="rounded-xl border bg-white p-6 text-slate-600">Loading analytics…</p>}

      {analytics && <>
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Registered research" value={total} />
          <Metric label="Ongoing research" value={analytics.by_status?.ONGOING || 0} />
          <Metric label="Completed research" value={analytics.by_status?.COMPLETED || 0} />
          <Metric label="Completion rate" value={(analytics.completed_rate || 0) + "%"} />
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <Panel title="Research status" subtitle="Current distribution of registered research">
            <StatusPieChart rows={visibleStatusRows} total={total} />
          </Panel>
          <Panel title="Researcher group" subtitle="Registered projects by primary researcher group">
            <BarList rows={typeRows} total={total} colors={["#0f766e", "#7c3aed", "#db2777", "#475569"]} />
          </Panel>
          <Panel title="Research by college or unit" subtitle="Top units by visible registry records">
            <BarList rows={analytics.by_college_or_unit || []} total={total} colors={["#0f766e"]} />
          </Panel>
          <Panel title="Research registration trend" subtitle="Records grouped by research start year">
            <BarList rows={analytics.by_start_year || []} total={total} colors={["#2563eb"]} />
          </Panel>
        </section>

        <section className="rounded-2xl border bg-white p-6 print:rounded-none print:border-slate-300 print:p-4">
          <h2 className="text-xl font-bold">Progress monitoring note</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-4 print:border print:bg-white"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Average ongoing progress</p><p className="mt-2 text-3xl font-black">{analytics.ongoing_average_progress || 0}%</p></div>
            <div className="rounded-xl bg-slate-50 p-4 print:border print:bg-white"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Report generated</p><p className="mt-2 font-bold">{formatDate(analytics.generated_at)}</p><p className="mt-1 text-sm text-slate-600">Restricted records are only included when your role is authorized to view them.</p></div>
          </div>
        </section>
      </>}
    </div>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-2xl border bg-white p-5 shadow-sm print:rounded-none print:shadow-none"><p className="text-sm font-semibold text-slate-500">{label}</p><p className="mt-3 text-3xl font-black">{value}</p></div>
}

function Panel({ title, subtitle, children }) {
  return <section className="rounded-2xl border bg-white p-6 print:rounded-none print:border-slate-300 print:p-4"><h2 className="text-xl font-bold">{title}</h2><p className="mt-1 text-sm text-slate-600">{subtitle}</p><div className="mt-5">{children}</div></section>
}

function StatusPieChart({ rows, total }) {
  if (!rows.length || !total) return <p className="py-8 text-center text-sm text-slate-500">No research records to display.</p>
  let progress = 0
  const segments = rows.map((row, index) => {
    const start = progress
    progress += (row.value / total) * 100
    return statusColors[index % statusColors.length] + " " + start + "% " + progress + "%"
  })
  const gradient = "conic-gradient(" + segments.join(", ") + ")"

  return <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-start">
    <div className="relative h-48 w-48 shrink-0 rounded-full" role="img" aria-label="Research status pie chart" style={{ background: gradient, WebkitPrintColorAdjust: "exact", printColorAdjust: "exact" }}>
      <div className="absolute inset-8 flex flex-col items-center justify-center rounded-full bg-white text-center print:border">
        <span className="text-3xl font-black">{total}</span>
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Records</span>
      </div>
    </div>
    <ul className="w-full space-y-2">{rows.map((row, index) => <li key={row.label} className="flex items-center justify-between gap-3 text-sm"><span className="flex items-center gap-2 font-medium"><span className="h-3 w-3 rounded-full" style={{ backgroundColor: statusColors[index % statusColors.length], WebkitPrintColorAdjust: "exact", printColorAdjust: "exact" }} />{row.label}</span><span className="font-bold">{row.value} ({Math.round((row.value / total) * 100)}%)</span></li>)}</ul>
  </div>
}

function BarList({ rows, total, colors }) {
  if (!rows.length) return <p className="py-8 text-center text-sm text-slate-500">No research records to display.</p>
  return <div className="space-y-4">{rows.map((row, index) => <div key={row.label}><div className="flex items-center justify-between gap-4 text-sm"><span className="font-medium">{row.label}</span><span className="font-bold">{row.value}</span></div><div className="mt-1.5 h-3 overflow-hidden rounded-full bg-slate-100 print:border"><div className="h-full rounded-full" style={{ width: (total ? Math.max((row.value / total) * 100, row.value ? 3 : 0) : 0) + "%", backgroundColor: colors[index % colors.length], WebkitPrintColorAdjust: "exact", printColorAdjust: "exact" }} /></div></div>)}</div>
}

function formatDate(value) {
  if (!value) return "Not available"
  return new Intl.DateTimeFormat("en-PH", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value))
}
