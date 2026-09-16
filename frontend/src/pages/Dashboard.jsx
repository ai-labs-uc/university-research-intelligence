import { useEffect, useState } from "react";
import api from "../api/client";

export default function Dashboard() {
  const [data, setData] = useState(null);

  const [running, setRunning] = useState(false);

  async function load() {
    const res = await api.get("/api/dashboard");

    setData(res.data);
  }

  async function runPipeline() {
    setRunning(true);

    try {
      await api.post("/api/pipeline/run");

      await load();
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (!data) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black">
            University Research Intelligence
          </h1>

          <p className="mt-2 text-slate-600">
            Research grants and academic opportunities monitoring dashboard.
          </p>
        </div>

        <button
          onClick={runPipeline}
          disabled={running}
          className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white disabled:opacity-50"
        >
          {running ? "Running..." : "Run Pipeline"}
        </button>
      </div>

      <div className="grid gap-5 md:grid-cols-5">
        <Card
          title="Total Opportunities"
          value={data.total_opportunities ?? data.total ?? 0}
        />

        <Card title="Open Opportunities" value={data.open_opportunities ?? 0} />

        <Card title="Call for Papers" value={data.call_for_papers ?? 0} />

        <Card title="Grants" value={data.grants ?? 0} />

        <Card title="Active Sources" value={data.active_sources ?? 0} />
      </div>

      <div className="rounded-2xl border bg-white p-6">
        <h2 className="text-xl font-bold">Research Opportunity Pipeline</h2>

        <p className="mt-2 text-slate-600">
          The system collects, classifies, and organizes research calls,
          conferences, and funding opportunities.
        </p>
      </div>
    </div>
  );
}

function Card({ title, value }) {
  return (
    <div className="rounded-2xl border bg-white p-5">
      <p className="text-sm text-slate-500">{title}</p>

      <p className="mt-3 text-3xl font-black">{value}</p>
    </div>
  );
}
