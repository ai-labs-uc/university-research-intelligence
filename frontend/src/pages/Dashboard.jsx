import { useEffect, useState } from "react";
import api from "../api/client"; function ScheduleNotice({ dueSoon, overdue }) {
  const [showAll, setShowAll] = useState({ due: false, overdue: false });
  const date = value => new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  const plural = (number, word) => String(number) + " " + word + (number === 1 ? "" : "s");
  const items = type => [...(type === "due" ? dueSoon : overdue)].sort((a, b) => type === "due" ? a.days - b.days : a.days - b.days);
  const card = (record, type) => {
    const late = Math.abs(record.days);
    const timing = type === "due" ? plural(record.days, "day") + " remaining" : "About " + plural(Math.max(1, Math.ceil(late / 30)), "month") + " (" + plural(late, "day") + ") overdue";
    return <article key={record.id} className="rounded-lg border border-slate-200 bg-white p-3"><div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between"><div><h4 className="font-bold text-slate-900">{record.title}</h4><p className="mt-1 text-xs text-slate-600">{record.college_or_unit || "UC research record"} · Progress: {record.progress_percent || 0}%</p></div><span className={"w-fit rounded-full px-2 py-1 text-xs font-bold " + (type === "due" ? "bg-amber-100 text-amber-900" : "bg-rose-100 text-rose-900")}>{timing}</span></div><div className="mt-3 grid gap-2 text-xs text-slate-700 sm:grid-cols-3"><p><strong>Proposal target:</strong> {date(record.target)}</p><p><strong>Approved duration:</strong> {record.approved_duration_months ? plural(record.approved_duration_months, "month") : "Not recorded"}</p><p><strong>Action:</strong> {type === "due" ? "Check milestones and outputs." : "Update, extend, or complete."}</p></div></article>;
  };
  const group = type => {
    const list = items(type); if (!list.length) return null;
    const due = type === "due"; const visible = showAll[type] ? list : list.slice(0, 5);
    const title = due ? "Due within 30 days" : "Past proposal target";
    const help = due ? "Approaching the approved proposal target date." : "Passed the approved proposal target date; review the record now.";
    return <section className={"rounded-xl border p-4 " + (due ? "border-amber-200 bg-amber-50" : "border-rose-200 bg-rose-50")}><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex items-center gap-2"><h3 className="font-bold">{title}</h3><span className="rounded-full bg-white px-2 py-1 text-xs font-black">{list.length}</span></div><p className="mt-1 text-sm text-slate-700">{help}</p></div><span className="rounded-full bg-white px-2 py-1 text-xs font-semibold">{list.length === 1 ? "1 research record" : String(list.length) + " research records"}</span></div><div className="mt-4 space-y-3">{visible.map(record => card(record, type))}</div>{list.length > 5 && <button onClick={() => setShowAll(current => ({ ...current, [type]: !current[type] }))} className="mt-4 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold">{showAll[type] ? "Show fewer records" : "Show all " + list.length + " records"}</button>}</section>;
  };
  if (!dueSoon.length && !overdue.length) return null;
  return <section className="col-span-1 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5 md:col-span-2 lg:col-span-5"><div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-sm font-semibold text-uc-700">Proposal schedule alerts</p><h2 className="mt-1 text-xl font-black">Records requiring timely monitoring</h2><p className="mt-1 max-w-3xl text-sm text-slate-600">Alerts are calculated from the approved proposal start date and duration. An alert is a reminder to verify status; it does not automatically mean the research failed.</p></div><a href="/research" className="w-full rounded-lg border bg-white px-4 py-2 text-center text-sm font-semibold sm:w-auto">Open Research Registry</a></div><div className="mt-5 grid gap-4 lg:grid-cols-2">{group("due")}{group("overdue")}</div><p className="mt-4 text-xs text-slate-600"><strong>Follow-through:</strong> record a progress update for due research. For past-target research, document an approved extension, update the completion status, or state the reason for the revised schedule.</p></section>;
}

export default function Dashboard() {
  const [data, setData] = useState({
    total_opportunities: 0,
    grants: 0,
    national_call_for_papers: 0,
    international_call_for_papers: 0,
    open_opportunities: 0,
    active_sources: 0,
  });
  const [running, setRunning] = useState(false);
  const [research, setResearch] = useState({ total_research: 0, by_status: {}, due_soon: 0, overdue: 0 }); const [schedule, setSchedule] = useState({ dueSoon: [], overdue: [] });

  async function loadDashboard() {
    try {
      const response = await api.get("/api/dashboard");
      setData(response.data);
      const researchResponse = await api.get("/api/research/dashboard");
      setResearch(researchResponse.data); const recordsResponse = await api.get("/api/research"); const today = new Date(); today.setHours(0, 0, 0, 0); const active = recordsResponse.data.filter(record => !["COMPLETED", "ARCHIVED"].includes(record.status) && record.target_completion_date).map(record => { const target = new Date(`${String(record.target_completion_date).slice(0, 10)}T00:00:00`); return { ...record, target, days: Math.round((target - today) / 86400000) }; }); setSchedule({ dueSoon: active.filter(record => record.days >= 0 && record.days <= 30), overdue: active.filter(record => record.days < 0) });
    } catch (error) {
      console.error("Dashboard loading failed:", error);
    }
  }

  async function runPipeline() {
    try {
      setRunning(true);
      await api.post("/api/pipeline/run");
      await loadDashboard();
    } catch (error) {
      console.error("Pipeline failed:", error);
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => { loadDashboard(); }, []);

  const callForPapers = (data.national_call_for_papers || 0) + (data.international_call_for_papers || 0);

  return (
    <div className="space-y-6 sm:space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black sm:text-3xl">University Research Intelligence</h1>
          <p className="mt-2 text-slate-600">Monitor research grants and call for paper opportunities.</p>
        </div>
        <button onClick={runPipeline} disabled={running} className="w-full rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white disabled:opacity-50 sm:w-auto">
          {running ? "Running Pipeline..." : "Run Pipeline"}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <DashboardCard title="Total Opportunities" value={data.total_opportunities || 0} />
        <DashboardCard title="Open Opportunities" value={data.open_opportunities || 0} />
        <DashboardCard title="Call for Papers" value={callForPapers} />
        <DashboardCard title="Research Grants" value={data.grants || 0} />
        <DashboardCard title="Active Sources" value={data.active_sources || 0} />
      </div>

      <div className="rounded-2xl border bg-white p-4 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold">Research Progress Monitoring</h2>
            <p className="mt-1 text-sm text-slate-600">Progress and target dates are based on the approved proposal schedule.</p>
          </div>
          <a href="/research" className="w-full rounded-xl border px-4 py-2 text-center text-sm font-semibold sm:w-auto">Manage research</a>
        </div>
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <ProgressCard label="Research records" value={research.total_research} />
          <ProgressCard label="Ongoing" value={research.by_status?.ONGOING || 0} />
          <ProgressCard label="Completed" value={research.by_status?.COMPLETED || 0} />
          <ProgressCard label="Due in 30 days (proposal schedule)" value={research.due_soon} /><ScheduleNotice dueSoon={schedule.dueSoon} overdue={schedule.overdue} />
          <ProgressCard label="Past proposal target date" value={research.overdue} danger />
        </div>
      </div>

      <div className="rounded-2xl border bg-white p-4 sm:p-6">
        <h2 className="text-xl font-bold">Research Opportunity Pipeline</h2>
        <p className="mt-2 text-slate-600">The system collects, classifies, and organizes research opportunities from official sources.</p>
      </div>
    </div>
  );
}

function DashboardCard({ title, value }) {
  return <div className="rounded-2xl border bg-white p-4 shadow-sm sm:p-5"><p className="text-sm font-semibold text-slate-500">{title}</p><p className="mt-3 text-3xl font-black">{value}</p></div>;
}

function ProgressCard({ label, value, danger = false }) {
  return <div className="rounded-xl border bg-slate-50 p-4"><p className="text-xs font-semibold uppercase leading-5 tracking-wide text-slate-500">{label}</p><p className={`mt-2 text-2xl font-black ${danger && value ? "text-red-700" : ""}`}>{value || 0}</p></div>;
}
