import { useEffect, useMemo, useState } from "react";
import api from "../api/client";

const TABS = [
  {
    value: "ALL",
    label: "All",
  },
  {
    value: "GRANT",
    label: "Grants",
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

function formatType(type) {
  if (type === "GRANT") {
    return "Grant";
  }

  if (type === "CALL_FOR_PAPER_NATIONAL") {
    return "National Call for Papers";
  }

  if (type === "CALL_FOR_PAPER_INTERNATIONAL") {
    return "International Call for Papers";
  }

  return type || "Opportunity";
}

function parseTextList(value) {
  if (!value) {
    return [];
  }

  try {
    if (Array.isArray(value)) {
      return value;
    }

    return value
      .replace(/[\[\]"]/g, "")
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean);
  } catch {
    return [];
  }
}

export default function Opportunities() {
  const [items, setItems] = useState([]);

  const [query, setQuery] = useState("");

  const [tab, setTab] = useState("ALL");

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);

      try {
        let endpoint = "/api/opportunities";

        if (tab === "GRANT") {
          endpoint = "/api/grants";
        }

        if (tab === "CALL_FOR_PAPER_NATIONAL") {
          endpoint = "/api/call-for-papers?scope=NATIONAL";
        }

        if (tab === "CALL_FOR_PAPER_INTERNATIONAL") {
          endpoint = "/api/call-for-papers?scope=INTERNATIONAL";
        }

        const response = await api.get(endpoint);

        setItems(response.data || []);
      } catch (error) {
        console.error("Unable to load opportunities", error);

        setItems([]);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [tab]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();

    return items.filter((item) => {
      const searchable = `

      ${item.title || ""}

      ${item.organization || ""}

      ${item.summary || ""}

      ${item.source_name || ""}

      ${item.discipline || ""}

      ${item.indexing_database || ""}

      `;

      return searchable.toLowerCase().includes(q);
    });
  }, [items, query]);

  const counts = useMemo(() => {
    const result = {
      GRANT: 0,

      CALL_FOR_PAPER_NATIONAL: 0,

      CALL_FOR_PAPER_INTERNATIONAL: 0,
    };

    items.forEach((item) => {
      if (result[item.opportunity_type] !== undefined) {
        result[item.opportunity_type]++;
      }
    });

    return result;
  }, [items]);

  return (
    <div>
      <h1 className="text-3xl font-black">Research Opportunities</h1>

      <p className="mt-2 max-w-3xl text-slate-600">
        Current grants and updated national and international calls for papers.
      </p>

      <div className="mt-6 flex flex-wrap gap-2">
        {TABS.map((tabItem) => (
          <button
            key={tabItem.value}
            onClick={() => setTab(tabItem.value)}
            className={`rounded-full px-4 py-2 text-sm font-semibold

              ${
                tab === tabItem.value
                  ? "bg-uc-800 text-white"
                  : "bg-white border border-slate-300 text-slate-700"
              }`}
          >
            {tabItem.label}

            {tabItem.value !== "ALL" && (
              <span className="ml-2">{counts[tabItem.value] || 0}</span>
            )}
          </button>
        ))}
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search opportunities..."
        className="mt-5 w-full max-w-2xl rounded-xl border border-slate-300 bg-white px-4 py-3"
      />

      {loading && (
        <p className="mt-6 text-slate-500">Loading opportunities...</p>
      )}

      {!loading && filtered.length === 0 && (
        <p className="mt-6 text-slate-500">No opportunities found.</p>
      )}

      <div className="mt-6 grid gap-5">
        {filtered.map((item) => (
          <article
            key={item.id}
            className="rounded-2xl border border-slate-200 bg-white p-6"
          >
            <div className="flex flex-wrap gap-2 text-xs font-bold uppercase">
              <span className="text-uc-700">
                {formatType(item.opportunity_type)}
              </span>

              {item.source_name && (
                <span className="text-slate-500">{item.source_name}</span>
              )}

              {item.status && (
                <span className="text-emerald-700">{item.status}</span>
              )}
            </div>

            <h2 className="mt-3 text-xl font-bold">{item.title}</h2>

            {item.organization && (
              <p className="mt-2 font-medium text-slate-700">
                {item.organization}
              </p>
            )}

            {item.summary && (
              <p className="mt-3 text-slate-600">{item.summary}</p>
            )}

            {item.deadline && (
              <p className="mt-3 text-sm text-slate-500">
                Deadline: {item.deadline}
              </p>
            )}

            {item.discipline && (
              <p className="mt-2 text-sm">Discipline: {item.discipline}</p>
            )}

            {item.indexing_database && (
              <p className="mt-2 text-sm">Indexing: {item.indexing_database}</p>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              {parseTextList(item.indexing_flags).map((flag) => (
                <span
                  key={flag}
                  className="rounded-full bg-purple-100 px-3 py-1 text-xs text-purple-800"
                >
                  {flag}
                </span>
              ))}
            </div>

            {item.source_url && (
              <a
                href={item.source_url}
                target="_blank"
                rel="noreferrer"
                className="mt-5 inline-block text-sm font-semibold text-uc-700"
              >
                Open official source →
              </a>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
