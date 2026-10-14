import { useEffect, useMemo, useState } from "react"
import api, { errorMessage } from "../api/client"

const emptyForm = {
  title: "", abstract: "", college_or_unit: "", researcher_type: "FACULTY",
  researchers: "", keywords: "", status: "DRAFT", visibility: "INSTITUTIONAL",
  target_completion_date: "", funding_source: "", progress_percent: 0,
}

const splitList = value => value.split(",").map(item => item.trim()).filter(Boolean)

export default function Researches() {
  const [records, setRecords] = useState([])
  const [query, setQuery] = useState("")
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState("")
  const [saving, setSaving] = useState(false)
  const [recommendations, setRecommendations] = useState([])

  async function load() {
    try {
      const response = await api.get("/api/research", { params: query ? { q: query } : {} })
      setRecords(response.data)
    } catch (error) {
      setMessage(errorMessage(error, "Could not load research records."))
    }
  }

  useEffect(() => { load() }, [])

  const heading = editing ? "Edit research record" : "Add research record"
  const visibleRecords = useMemo(() => records, [records])

  function beginEdit(record) {
    setEditing(record)
    setRecommendations([])
    setFile(null)
    setForm({
      title: record.title || "", abstract: record.abstract || "", college_or_unit: record.college_or_unit || "",
      researcher_type: record.researcher_type || "FACULTY", researchers: (record.researchers || []).join(", "),
      keywords: (record.keywords || []).join(", "), status: record.status || "DRAFT",
      visibility: record.visibility || "INSTITUTIONAL", target_completion_date: record.target_completion_date ? String(record.target_completion_date).slice(0, 10) : "",
      funding_source: record.funding_source || "", progress_percent: record.progress_percent || 0,
    })
  }

  function reset() {
    setEditing(null); setForm(emptyForm); setFile(null); setRecommendations([]); setMessage("")
  }

  async function submit(event) {
    event.preventDefault()
    setSaving(true); setMessage("")
    const payload = {
      ...form,
      researchers: splitList(form.researchers), keywords: splitList(form.keywords),
      progress_percent: Number(form.progress_percent || 0),
      target_completion_date: form.target_completion_date || null,
      funding_source: form.funding_source || null,
    }
    try {
      const response = editing
        ? await api.put(`/api/research/${editing.id}`, payload)
        : await api.post("/api/research", payload)
      if (file) {
        const upload = new FormData(); upload.append("file", file)
        await api.post(`/api/research/${response.data.id}/attachments`, upload)
      }
      setMessage("Research record saved.")
      await load(); reset()
    } catch (error) {
      setMessage(errorMessage(error, "Could not save the research record."))
    } finally { setSaving(false) }
  }

  async function remove(record) {
    if (!window.confirm(`Remove “${record.title}”? This hides the record from normal views.`)) return
    try { await api.delete(`/api/research/${record.id}`); await load(); if (editing?.id === record.id) reset() }
    catch (error) { setMessage(errorMessage(error, "Could not remove the research record.")) }
  }

  async function showRecommendations(record) {
    try {
      const response = await api.get(`/api/research/${record.id}/recommendations`)
      setEditing(record); setRecommendations(response.data)
      setMessage(response.data.length ? "Opportunity matches use the research record’s visible keywords and abstract." : "No current opportunity matches were found yet.")
    } catch (error) { setMessage(errorMessage(error, "Could not load opportunity matches.")) }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><h1 className="text-3xl font-black">Research Registry</h1><p className="mt-2 text-slate-600">Add, update, search, and monitor ongoing or completed UC research.</p></div>
        <button onClick={reset} className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white">New research record</button>
      </div>

      {message && <p className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{message}</p>}

      <div className="grid gap-6 xl:grid-cols-[1.3fr_.9fr]">
        <section className="rounded-2xl border bg-white p-5 shadow-sm">
          <div className="flex gap-2"><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search title, abstract, keyword, or college" className="w-full rounded-lg border px-3 py-2" /><button onClick={load} className="rounded-lg border px-4 font-semibold">Search</button></div>
          <div className="mt-5 space-y-3">
            {visibleRecords.map(record => <article key={record.id} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-bold">{record.title}</h2><p className="mt-1 text-sm text-slate-600">{record.college_or_unit} · {record.researcher_type?.replaceAll("_", " ")}</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold">{record.status?.replaceAll("_", " ")}</span></div>
              <p className="mt-2 text-sm text-slate-700">{record.abstract}</p>
              <p className="mt-2 text-xs text-slate-500">Progress: {record.progress_percent || 0}% · Keywords: {(record.keywords || []).join(", ") || "Not set"}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-sm"><button onClick={() => beginEdit(record)} className="rounded-lg border px-3 py-1.5">Edit</button><button onClick={() => showRecommendations(record)} className="rounded-lg border px-3 py-1.5">Find matching calls</button><button onClick={() => remove(record)} className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700">Delete</button></div>
            </article>)}
            {!visibleRecords.length && <p className="py-8 text-center text-slate-500">No research records found.</p>}
          </div>
        </section>

        <aside className="rounded-2xl border bg-white p-5 shadow-sm">
          <h2 className="text-xl font-bold">{heading}</h2>
          <form onSubmit={submit} className="mt-4 space-y-3">
            <Field label="Research title" value={form.title} onChange={value => setForm({ ...form, title: value })} required />
            <label className="block text-sm font-semibold">Abstract<textarea value={form.abstract} onChange={e => setForm({ ...form, abstract: e.target.value })} required minLength="20" rows="4" className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label>
            <Field label="College or unit" value={form.college_or_unit} onChange={value => setForm({ ...form, college_or_unit: value })} required />
            <div className="grid gap-3 sm:grid-cols-2"><Select label="Researcher type" value={form.researcher_type} onChange={value => setForm({ ...form, researcher_type: value })} options={["FACULTY", "NON_TEACHING_STAFF", "STUDENT", "OTHER"]} /><Select label="Status" value={form.status} onChange={value => setForm({ ...form, status: value })} options={["DRAFT", "PENDING_REVIEW", "ONGOING", "COMPLETED", "ARCHIVED"]} /></div>
            <Field label="Researchers (comma-separated)" value={form.researchers} onChange={value => setForm({ ...form, researchers: value })} />
            <Field label="Keywords (comma-separated)" value={form.keywords} onChange={value => setForm({ ...form, keywords: value })} />
            <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-semibold">Target completion<input type="date" value={form.target_completion_date} onChange={e => setForm({ ...form, target_completion_date: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label><label className="text-sm font-semibold">Progress %<input type="number" min="0" max="100" value={form.progress_percent} onChange={e => setForm({ ...form, progress_percent: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label></div>
            <Field label="Funding source" value={form.funding_source} onChange={value => setForm({ ...form, funding_source: value })} />
            <label className="block text-sm font-semibold">Research document (PDF, DOC, or DOCX; up to 10 MB)<input type="file" accept=".pdf,.doc,.docx" onChange={e => setFile(e.target.files?.[0] || null)} className="mt-1 block w-full text-sm font-normal" /></label>
            <div className="flex gap-2"><button disabled={saving} className="rounded-lg bg-blue-700 px-4 py-2 font-semibold text-white disabled:opacity-50">{saving ? "Saving..." : "Save record"}</button>{editing && <button type="button" onClick={reset} className="rounded-lg border px-4 py-2">Cancel</button>}</div>
          </form>
          {recommendations.length > 0 && <div className="mt-6 border-t pt-4"><h3 className="font-bold">Recommended calls</h3>{recommendations.map(item => <a key={item.id} href={item.source_url} target="_blank" rel="noreferrer" className="mt-3 block rounded-lg border p-3 text-sm hover:bg-slate-50"><strong>{item.title}</strong><span className="mt-1 block text-slate-600">{item.organization} · {item.reasons.join(" ")}</span></a>)}</div>}
        </aside>
      </div>
    </div>
  )
}

function Field({ label, value, onChange, required = false }) { return <label className="block text-sm font-semibold">{label}<input value={value} onChange={e => onChange(e.target.value)} required={required} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label> }
function Select({ label, value, onChange, options }) { return <label className="block text-sm font-semibold">{label}<select value={value} onChange={e => onChange(e.target.value)} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal">{options.map(option => <option key={option}>{option.replaceAll("_", " ")}</option>)}</select></label> }
