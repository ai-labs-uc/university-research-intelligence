import { useEffect, useMemo, useState } from "react";
import api from "../api/client";

const TABS = [
  ["ALL", "All"],

  ["CALL_FOR_PAPER_NATIONAL", "National Call for Papers"],

  ["CALL_FOR_PAPER_INTERNATIONAL", "International Call for Papers"],

  ["GRANT_PHILIPPINES", "Philippine Grants"],

  ["GRANT_INTERNATIONAL", "International Grants"],
];

export default function Opportunities() {
  const [items, setItems] = useState([]);

  const [query, setQuery] = useState("");

  const [tab, setTab] = useState("ALL");

  useEffect(() => {
    api.get("/api/opportunities").then((res) => {
      setItems(res.data || []);
    });
  }, []);

  function category(item) {
    return item.category || item.opportunity_type || "";
  }

  const counts = useMemo(() => {
    const result = {
      ALL: items.length,

      CALL_FOR_PAPER_NATIONAL: 0,

      CALL_FOR_PAPER_INTERNATIONAL: 0,

      GRANT_PHILIPPINES: 0,

      GRANT_INTERNATIONAL: 0,
    };

    items.forEach((item) => {
      const c = category(item);

      if (result[c] !== undefined) {
        result[c]++;
      }
    });

    return result;
  }, [items]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();

    return items

      .filter((item) => {
        if (tab === "ALL") return true;

        return category(item) === tab;
      })

      .filter((item) => {
        return `${item.title}
          ${item.organization}
          ${item.summary}
          ${category(item)}
          `
          .toLowerCase()
          .includes(q);
      });
  }, [items, tab, query]);

  return (
    <div>
      <h1 className="text-3xl font-black">Call for Papers &amp; Grants</h1>

      <p className="mt-2 text-slate-600">
        Research opportunities collected from official sources.
      </p>

      <div className="mt-6 flex flex-wrap gap-2">
        {TABS.map(([value, label]) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={
              tab === value
                ? "rounded-full bg-blue-700 px-4 py-2 text-sm font-semibold text-white"
                : "rounded-full border px-4 py-2 text-sm font-semibold"
            }
          >
            {label}

            <span className="ml-2">{counts[value]}</span>
          </button>
        ))}
      </div>

      <input
        className="mt-5 w-full rounded-xl border px-4 py-3"
        placeholder="Search calls and grants..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <div className="mt-6 grid gap-5">
        {filtered.map((item) => (
          <article key={item.id} className="rounded-2xl border bg-white p-6">
            <div className="flex flex-wrap gap-2 text-xs font-bold uppercase">
              <span className="text-blue-700">{category(item)}</span>

              <span className="text-slate-500">{item.organization}</span>

              {item.status && (
                <span className="text-green-700">{item.status}</span>
              )}
            </div>

            <h2 className="mt-3 text-xl font-bold">{item.title}</h2>

            <p className="mt-3 text-slate-600">
              {item.summary?.substring(0, 500)}
            </p>

            {item.indexing_database && (
              <p className="mt-3 text-sm text-purple-700">
                Indexing: {item.indexing_database}
              </p>
            )}

            {item.deadline && (
              <p className="mt-3 text-sm">Deadline: {item.deadline}</p>
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
