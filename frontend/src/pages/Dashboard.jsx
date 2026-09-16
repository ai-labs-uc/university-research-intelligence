import { useEffect, useState } from "react";
import api from "../api/client";

export default function Dashboard() {
  const [data, setData] = useState({
    total_opportunities: 0,

    grants: 0,

    national_call_for_papers: 0,

    international_call_for_papers: 0,
  });

  useEffect(() => {
    api
      .get("/api/dashboard")
      .then((res) => {
        setData(res.data);
      })

      .catch((err) => {
        console.error("Dashboard error:", err);
      });
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-black">Research Intelligence Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-gray-500">Total Opportunities</p>

          <h2 className="text-3xl font-bold">{data.total_opportunities}</h2>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-gray-500">Research Grants</p>

          <h2 className="text-3xl font-bold">{data.grants}</h2>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-gray-500">National CFP</p>

          <h2 className="text-3xl font-bold">
            {data.national_call_for_papers}
          </h2>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-gray-500">International CFP</p>

          <h2 className="text-3xl font-bold">
            {data.international_call_for_papers}
          </h2>
        </div>
      </div>
    </div>
  );
}
