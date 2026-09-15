import { useEffect, useMemo, useState } from "react"
import api from "../api/client"

const TABS = [
  ["ALL", "All"],
  ["CALL_FOR_PAPER", "Call for Papers"],
  ["GRANT", "Grants"],
]

export default function Opportunities() {
  const [items, setItems] = useState([])
  const [query, setQuery] = useState("")
  const [tab, setTab] = useState("ALL")

  useEffect(() => {
    api.get("/api/opportunities").then(r => setItems(r.data))
  }, [])

  const counts = useMemo(() => {
    const c = { CALL_FOR_PAPER: 0, GRANT: 0 }
    for (const item of items) {
      if (c[item.opportunity_type] !== undefined) c[item.opportunity_type]++
    }
    return c
  }, [items])

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    return items
      .filter(item => tab === "ALL" || item.opportunity_type === tab)
      .filter(item =>
        `${item.title} ${item.opportunity_type} ${item.source_name ?? ""}`
          .toLowerCase()
          .includes(q)
      )
  }, [items, query, tab])

  return (
    <div>
      <h1 className="text-3xl font-black">
        Call for Papers &amp; Grants
      </h1>
      <p className="mt-2 max-w-2xl text-slate-600">
        Every open call for papers and grant opportunity this system has
        picked up, in one list.
      </p>

      <div className="mt-6 flex flex-wrap gap-2">
        {TABS.map(([value, label]) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`rounded-full px-4 py-2 text-sm font-semibold ${
              tab === value
                ? "bg-uc-800 text-white"
                : "bg-white text-slate-700 border border-slate-300"
            }`}
          >
            {label}
            {value !== "ALL" && (
              <span
                className={
                  tab === value ? "ml-2 text-uc-100" : "ml-2 text-slate-400"
                }
              >
                {counts[value]}
              </span>
            )}
          </button>
        ))}
      </div>

      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search calls for papers and grants..."
        className="mt-4 w-full max-w-2xl rounded-xl border border-slate-300 bg-white px-4 py-3"
      />

      <div className="mt-6 grid gap-4">
        {filtered.length === 0 && (
          <p className="text-slate-500">
            No {tab === "ALL" ? "opportunities" : TABS.find(([v]) => v === tab)[1].toLowerCase()} match yet — try a different tab, clear the search, or run the pipeline.
          </p>
        )}

        {filtered.map(item => (
          <article
            key={item.id}
            className="rounded-2xl border border-slate-200 bg-white p-6"
          >
            <div className="flex flex-wrap gap-2 text-xs font-bold uppercase tracking-wider">
              <span className="text-uc-700">
                {item.opportunity_type === "CALL_FOR_PAPER"
                  ? "Call for Paper"
                  : "Grant"}
              </span>
              <span className="text-slate-500">
                {item.source_name}
              </span>
              <span className="text-emerald-700">
                {item.status}
              </span>
              {(item.indexing_flags || []).map(flag => (
                <span
                  key={flag}
                  className="rounded-full bg-purple-100 px-2 py-0.5 text-purple-800"
                  title="Indexing as stated on the source page — not independently verified"
                >
                  {flag.replaceAll("_", " ")}
                </span>
              ))}
            </div>

            <h2 className="mt-2 text-xl font-bold">
              {item.title}
            </h2>

            <p className="mt-3 text-slate-600">
              {item.summary}
            </p>

            <a
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-block text-sm font-semibold text-uc-700"
            >
              Open official source →
            </a>
          </article>
        ))}
      </div>
    </div>
  )
}
