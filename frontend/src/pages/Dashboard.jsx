import { useEffect, useState } from "react";
import api from "../api/client";

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
  const [research, setResearch] = useState({ total_research: 0, by_status: {}, due_soon: 0, overdue: 0 });

  async function loadDashboard() {
    try {
      const response = await api.get("/api/dashboard");

      setData(response.data);
      const researchResponse = await api.get("/api/research/dashboard");
      setResearch(researchResponse.data);
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

  useEffect(() => {
    loadDashboard();
  }, []);

  const callForPapers =
    (data.national_call_for_papers || 0) +
    (data.international_call_for_papers || 0);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black">
            University Research Intelligence
          </h1>

          <p className="mt-2 text-slate-600">
            Monitor research grants and call for paper opportunities.
          </p>
        </div>

        <button
          onClick={runPipeline}
          disabled={running}
          className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white disabled:opacity-50"
        >
          {running ? "Running Pipeline..." : "Run Pipeline"}
        </button>
      </div>

      <div className="grid gap-5 md:grid-cols-5">
        <DashboardCard
          title="Total Opportunities"
          value={data.total_opportunities || 0}
        />

        <DashboardCard
          title="Open Opportunities"
          value={data.open_opportunities || 0}
        />

        <DashboardCard title="Call for Papers" value={callForPapers} />

        <DashboardCard title="Research Grants" value={data.grants || 0} />

        <DashboardCard
          title="Active Sources"
          value={data.active_sources || 0}
        />
      </div>

      <div className="rounded-2xl border bg-white p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="text-xl font-bold">Research Progress Monitoring</h2><p className="mt-1 text-sm text-slate-600">Institutional records visible to your role, grouped by current status.</p></div>
          <a href="/research" className="rounded-xl border px-4 py-2 text-sm font-semibold">Manage research</a>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <ProgressCard label="Research records" value={research.total_research} />
          <ProgressCard label="Ongoing" value={research.by_status?.ONGOING || 0} />
          <ProgressCard label="Completed" value={research.by_status?.COMPLETED || 0} />
          <ProgressCard label="Due within 30 days" value={research.due_soon} />
          <ProgressCard label="Past target date" value={research.overdue} danger />
        </div>
      </div>

      <div className="rounded-2xl border bg-white p-6">
        <h2 className="text-xl font-bold">Research Opportunity Pipeline</h2>

        <p className="mt-2 text-slate-600">
          The system collects, classifies, and organizes research opportunities
          from official sources.
        </p>
      </div>
    </div>
  );
}

function DashboardCard({ title, value }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <p className="text-sm font-semibold text-slate-500">{title}</p>

      <p className="mt-3 text-3xl font-black">{value}</p>
    </div>
  );
}

function ProgressCard({ label, value, danger = false }) {
  return <div className="rounded-xl border bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className={`mt-2 text-2xl font-black ${danger && value ? "text-red-700" : ""}`}>{value || 0}</p></div>
}
