import { useEffect, useState } from "react";
import api from "../api/client"; function ScheduleNotice({ dueSoon, overdue }) { if (!dueSoon.length && !overdue.length) return null; const date = value => new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }); return <div className="col-span-1 grid gap-3 md:col-span-2 md:grid-cols-2 lg:col-span-5"><div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950"><strong>Due within 30 days means:</strong> an ongoing research is approaching its approved proposal target date. {dueSoon.map(record => <p key={record.id} className="mt-2"><strong>Due soon — </strong>{record.title}: target {date(record.target)}; {record.days} day{record.days === 1 ? "" : "s"} remaining.</p>)}</div><div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-950"><strong>Past proposal target means:</strong> an ongoing research has passed its approved proposal target date and needs an update, extension, or completion status. {overdue.map(record => <p key={record.id} className="mt-2"><strong>Past target — </strong>{record.title}: target {date(record.target)}; about {Math.max(1, Math.ceil(Math.abs(record.days) / 30))} month{Math.max(1, Math.ceil(Math.abs(record.days) / 30)) === 1 ? "" : "s"} ({Math.abs(record.days)} days) overdue.</p>)}</div></div> }

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
