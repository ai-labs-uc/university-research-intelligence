import { useEffect, useState } from "react"
import api from "../api/client"

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [running, setRunning] = useState(false)

  async function load() {
    const response = await api.get("/api/dashboard")
    setData(response.data)
  }

  async function runPipeline() {
    setRunning(true)
    try {
      await api.post("/api/pipeline/run")
      await load()
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const cards = data
    ? [
        ["Total Opportunities", data.total_opportunities],
        ["Open Opportunities", data.open_opportunities],
        ["Call for Papers", data.call_for_paper_count],
        ["Grants", data.grant_count],
        ["Active Sources", data.active_sources],
      ]
    : []

  return (
    <div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-sm font-bold uppercase tracking-widest text-uc-700">
            University Research Office
          </p>
          <h1 className="mt-2 text-3xl font-black text-balance">
            Research Call for Paper Opportunity and Grants Dashboard
          </h1>
          <p className="mt-2 text-slate-600">
            Calls for papers and grant opportunities, gathered automatically.
          </p>
        </div>

        <button
          onClick={runPipeline}
          disabled={running}
          className="rounded-xl bg-uc-800 px-5 py-3 font-semibold text-white transition hover:bg-uc-900"
        >
          {running ? "Running..." : "Run Pipeline"}
        </button>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3 xl:grid-cols-5">
        {cards.map(([label, value]) => (
          <article
            key={label}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-4xl font-black">{value}</p>
          </article>
        ))}
      </div>

      <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-bold">
          Simplified Automation Flow
        </h2>
        <pre className="mt-4 overflow-auto rounded-xl bg-uc-950 p-5 text-sm text-uc-100">
{`Scheduled ETL run (cron)
 ↓
Python ETL / FastAPI
 ↓
Classify: call for paper or grant?
 ↓
MySQL
 ↓
React Dashboard`}
        </pre>
      </div>
    </div>
  )
}
