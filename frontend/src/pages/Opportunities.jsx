import { useEffect, useMemo, useState } from "react";
import api from "../api/client";

const TABS = [
  {
    value: "ALL",
    label: "All Opportunities",
  },
  {
    value: "GRANT_PHILIPPINES",
    label: "Philippine Grants",
  },
  {
    value: "GRANT_INTERNATIONAL",
    label: "International Grants",
  },
  {
    value: "CALL_FOR_PAPER_NATIONAL",
    label: "National Call for Papers",
  },
  {
    value: "CALL_FOR_PAPER_INTERNATIONAL",
    label: "International Call for Papers",
  },
];

export default function Opportunities() {
  const [items, setItems] = useState([]);

  const [tab, setTab] = useState("ALL");

  const [query, setQuery] = useState("");

  useEffect(() => {
    async function loadOpportunities() {
      try {
        const response = await api.get("/api/opportunities");

        setItems(response.data || []);
      } catch (error) {
        console.error("Failed loading opportunities:", error);
      }
    }

    loadOpportunities();
  }, []);

  const counts = useMemo(() => {
    const result = {};

    TABS.forEach((tab) => {
      result[tab.value] = 0;
    });

    items.forEach((item) => {
      const category = item.category || item.opportunity_type || "";

      if (result[category] !== undefined) {
        result[category]++;
      }
    });

    result.ALL = items.length;

    return result;
  }, [items]);

  const filtered = useMemo(() => {
    const search = query.toLowerCase();

    return items.filter((item) => {
      const category = item.category || item.opportunity_type || "";

      const matchTab = tab === "ALL" || category === tab;

      const searchableText = `

        ${item.title || ""}

        ${item.organization || ""}

        ${item.summary || ""}

        ${category}

      `.toLowerCase();

      const matchSearch = searchableText.includes(search);

      return matchTab && matchSearch;
    });
  }, [items, tab, query]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black">Research Opportunities</h1>

        <p className="mt-2 text-slate-600">
          Research grants, funding opportunities, and academic call-for-paper
          opportunities.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {TABS.map((item) => (
          <button
            key={item.value}
            onClick={() => setTab(item.value)}
            className={
              tab === item.value
                ? "rounded-full bg-blue-700 px-4 py-2 text-sm font-semibold text-white"
                : "rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
            }
          >
            {item.label}

            <span className="ml-2">{counts[item.value] || 0}</span>
          </button>
        ))}
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search opportunities..."
        className="w-full rounded-xl border border-slate-300 px-4 py-3"
      />

      <div className="grid gap-5">
        {filtered.length === 0 && (
          <div className="rounded-xl border bg-white p-6 text-slate-500">
            No opportunities found.
          </div>
        )}

        {filtered.map((item) => (
          <article
            key={item.id}
            className="rounded-2xl border bg-white p-6 shadow-sm"
          >
            <div className="flex flex-wrap gap-2 text-xs font-bold uppercase">
              <span className="rounded-full bg-blue-100 px-3 py-1 text-blue-700">
                {item.category || item.opportunity_type}
              </span>

              {item.organization && (
                <span className="rounded-full bg-slate-100 px-3 py-1">
                  {item.organization}
                </span>
              )}

              {item.indexing_database && (
                <span className="rounded-full bg-purple-100 px-3 py-1 text-purple-700">
                  {item.indexing_database}
                </span>
              )}
            </div>

            <h2 className="mt-4 text-xl font-bold">{item.title}</h2>

            <p className="mt-3 text-slate-600">
              {item.summary
                ? item.summary.substring(0, 500)
                : "No description available."}
            </p>

            {item.deadline && (
              <p className="mt-3 text-sm font-semibold">
                Deadline: {item.deadline}
              </p>
            )}

            <a
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-block font-semibold text-blue-700"
            >
              Open official source →
            </a>
          </article>
        ))}
      </div>
    </div>
  );
}
