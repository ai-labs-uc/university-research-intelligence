import { useEffect, useMemo, useState } from "react"
import api, { errorMessage } from "../api/client"

const emptyForm = {
  title: "", abstract: "", college_or_unit: "", researcher_type: "FACULTY",
  researchers: "", keywords: "", status: "DRAFT", visibility: "INSTITUTIONAL",
  start_date: "", approved_duration_months: "", target_completion_date: "", funding_source: "", progress_percent: 0,
}

const splitList = value => value.split(",").map(item => item.trim()).filter(Boolean); const proposalTargetDate = (startDate, months) => { if (!startDate || !months || Number(months) < 1) return ""; const [year, month, day] = startDate.split("-").map(Number); const finalMonth = new Date(Date.UTC(year, month - 1 + Number(months) + 1, 0)); return [finalMonth.getUTCFullYear(), String(finalMonth.getUTCMonth() + 1).padStart(2, "0"), String(Math.min(day, finalMonth.getUTCDate())).padStart(2, "0")].join("-") }

export default function Researches() {
  const [records, setRecords] = useState([])
  const [query, setQuery] = useState("")
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState("")
  const [saving, setSaving] = useState(false)
  const [recommendations, setRecommendations] = useState([])
  const [selected, setSelected] = useState(null)
  
  

  async function load() {
    try {
      const response = await api.get("/api/research", { params: query ? { q: query } : {} })
      setRecords(response.data)
    } catch (error) {
      setMessage(errorMessage(error, "Could not load research records."))
    }
  }  useEffect(() => { load() }, [])

  useEffect(() => {
    if (!selected) return
    const frame = requestAnimationFrame(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "smooth" }))
    return () => cancelAnimationFrame(frame)
  }, [selected])

  useEffect(() => {
    if (!recommendations.length) return
    const frame = requestAnimationFrame(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "smooth" }))
    return () => cancelAnimationFrame(frame)
  }, [recommendations])

  const heading = editing ? "Edit research record" : "Add research record"
  const visibleRecords = useMemo(() => records, [records])

  function beginEdit(record) {
    setEditing(record)
    setSelected(record)
    setRecommendations([])
    setFile(null)
    setForm({
      title: record.title || "", abstract: record.abstract || "", college_or_unit: record.college_or_unit || "",
      researcher_type: record.researcher_type || "FACULTY", researchers: (record.researchers || []).join(", "),
      keywords: (record.keywords || []).join(", "), status: record.status || "DRAFT",
      visibility: record.visibility || "INSTITUTIONAL", start_date: record.start_date ? String(record.start_date).slice(0, 10) : "", approved_duration_months: record.approved_duration_months || "", target_completion_date: record.target_completion_date ? String(record.target_completion_date).slice(0, 10) : "",
      funding_source: record.funding_source || "", progress_percent: record.progress_percent || 0,
    })
  }

  function reset() {
    setEditing(null); setSelected(null); setForm(emptyForm); setFile(null); setRecommendations([]); setMessage("")
  }

  async function submit(event) {
    event.preventDefault()
    setSaving(true); setMessage("")
    const payload = {
      ...form,
      researchers: splitList(form.researchers), keywords: splitList(form.keywords),
      progress_percent: Number(form.progress_percent || 0), start_date: form.start_date || null, approved_duration_months: form.approved_duration_months ? Number(form.approved_duration_months) : undefined,
      target_completion_date: proposalTargetDate(form.start_date, form.approved_duration_months) || form.target_completion_date || null,
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
      setSelected(record); setRecommendations(response.data)
      setMessage(response.data.length ? "Matches are advisory and use the research record’s keywords and abstract." : "No current opportunity matches were found yet.")
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
              <div className="mt-3 flex flex-wrap gap-2 text-sm"><button onClick={() => { setSelected(record); setRecommendations([]) }} className="rounded-lg border px-3 py-1.5">View record</button><button onClick={() => beginEdit(record)} className="rounded-lg border px-3 py-1.5">Edit</button><button onClick={() => showRecommendations(record)} className="rounded-lg border border-uc-700 px-3 py-1.5 text-uc-800">Find matching calls</button><button onClick={() => remove(record)} className="rounded-lg border border-red-200 px-3 py-1.5 text-red-700">Delete</button></div>
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
            <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-semibold">Proposal start date<input type="date" required value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label><label className="text-sm font-semibold">Approved duration (months)<input type="number" required min="1" max="120" value={form.approved_duration_months} onChange={e => setForm({ ...form, approved_duration_months: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label></div><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-semibold">Calculated proposal target completion<input type="date" readOnly value={proposalTargetDate(form.start_date, form.approved_duration_months) || form.target_completion_date} className="mt-1 w-full rounded-lg border bg-slate-50 px-3 py-2 font-normal text-slate-600" /></label><label className="text-sm font-semibold">Progress %<input type="number" min="0" max="100" value={form.progress_percent} onChange={e => setForm({ ...form, progress_percent: e.target.value })} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label></div>
            <Field label="Funding source" value={form.funding_source} onChange={value => setForm({ ...form, funding_source: value })} />
            <label className="block text-sm font-semibold">Research document (PDF, DOC, or DOCX; up to 10 MB)<input type="file" accept=".pdf,.doc,.docx" onChange={e => setFile(e.target.files?.[0] || null)} className="mt-1 block w-full text-sm font-normal" /></label>
            <div className="flex gap-2"><button disabled={saving} className="rounded-lg bg-blue-700 px-4 py-2 font-semibold text-white disabled:opacity-50">{saving ? "Saving..." : "Save record"}</button>{editing && <button type="button" onClick={reset} className="rounded-lg border px-4 py-2">Cancel</button>}</div>
          </form>
        </aside>
      </div>

      {selected && <section className="rounded-2xl border bg-white p-6 shadow-sm print:rounded-none print:border-slate-300 print:shadow-none">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm font-semibold text-uc-700">Research record</p><h2 className="mt-1 text-2xl font-black">{selected.title}</h2><p className="mt-2 text-sm text-slate-600">{selected.college_or_unit} · {selected.researcher_type?.replaceAll("_", " ")}</p></div><div className="flex gap-2 print:hidden"><button onClick={() => window.print()} className="rounded-lg border px-4 py-2 text-sm font-semibold">Print record</button><button onClick={() => { setSelected(null); setRecommendations([]) }} className="rounded-lg border px-4 py-2 text-sm">Close</button></div></div>
        <div className="mt-5 grid gap-4 md:grid-cols-3"><Detail label="Status" value={selected.status?.replaceAll("_", " ")} /><Detail label="Progress" value={`${selected.progress_percent || 0}%`} /><Detail label="Target completion" value={selected.target_completion_date ? String(selected.target_completion_date).slice(0, 10) : "Not set"} /></div>
        <div className="mt-5"><h3 className="font-bold">Abstract</h3><p className="mt-2 leading-6 text-slate-700">{selected.abstract}</p></div>
        <div className="mt-5 grid gap-5 md:grid-cols-2"><div><h3 className="font-bold">Researchers</h3><p className="mt-2 text-sm text-slate-700">{(selected.researchers || []).join(", ") || "Not recorded"}</p></div><div><h3 className="font-bold">Keywords</h3><p className="mt-2 text-sm text-slate-700">{(selected.keywords || []).join(", ") || "Not recorded"}</p></div></div>
        {recommendations.length > 0 && <div className="mt-6 border-t pt-5"><h3 className="text-lg font-bold">Recommended calls and grants</h3><p className="mt-1 text-sm text-slate-600">Possible opportunities based on the record’s title, abstract, and keywords. Verify eligibility and deadlines with the official source.</p><div className="mt-4 grid gap-3 lg:grid-cols-2">{recommendations.map(item => <a key={item.id} href={item.source_url} target="_blank" rel="noreferrer" className="rounded-xl border p-4 text-sm hover:bg-slate-50"><div className="flex flex-wrap gap-2"><span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-bold text-blue-800">{item.opportunity_type === "GRANT" ? "Grant" : "Call for papers"}</span><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold">{item.scope === "INTERNATIONAL" ? "International" : "National"}</span></div><strong className="mt-3 block">{item.title}</strong><span className="mt-1 block text-slate-600">{item.organization}</span><span className="mt-2 block text-slate-500">{item.reasons.join(" · ")}</span></a>)}</div></div>}
      </section>}
    </div>
  )
}

function Field({ label, value, onChange, required = false }) { return <label className="block text-sm font-semibold">{label}<input value={value} onChange={e => onChange(e.target.value)} required={required} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal" /></label> }
function Select({ label, value, onChange, options }) { return <label className="block text-sm font-semibold">{label}<select value={value} onChange={e => onChange(e.target.value)} className="mt-1 w-full rounded-lg border px-3 py-2 font-normal">{options.map(option => <option key={option}>{option.replaceAll("_", " ")}</option>)}</select></label> }
function Detail({ label, value }) { return <div className="rounded-xl bg-slate-50 p-4 print:border print:bg-white"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 font-bold">{value || "Not set"}</p></div> }
