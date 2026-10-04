import { useEffect, useMemo, useState } from "react";
import api, { errorMessage } from "../api/client";

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

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  // This request previously had no .catch(). Any failure — an expired
  // token, or the backend waking from sleep — became an unhandled
  // promise rejection and the page just sat there empty with no
  // explanation. A 401 is left to the axios interceptor, which signs the
  // user out and lets ProtectedRoute send them to /login.
  useEffect(() => {
    let cancelled = false;

    api
      .get("/api/opportunities")
      .then((res) => {
        if (cancelled) return;
        setItems(Array.isArray(res.data) ? res.data : []);
      })
      .catch((err) => {
        if (cancelled || err?.response?.status === 401) return;
        setError(errorMessage(err, "Couldn't load opportunities."));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
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
        return `${item.title} ${item.organization} ${item.summary} ${category(item)}`
          .toLowerCase()
          .includes(q);
      });
  }, [items, tab, query]);

  // Printing captures whatever is currently filtered/searched rather than
  // always every opportunity, so the hard copy matches what the person
  // was actually looking at (e.g. just "Philippine Grants").
  const activeTabLabel = TABS.find(([value]) => value === tab)?.[1] ?? "All";

  const printedAt = new Date().toLocaleString("en-PH", {
    dateStyle: "long",
    timeStyle: "short",
  });

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black">Call for Papers &amp; Grants</h1>

          <p className="mt-2 text-slate-600">
            Research opportunities collected from official sources.
          </p>
        </div>

        {/* Prints exactly what's currently filtered/searched below --
            hidden on the printed page itself via print:hidden. */}
        <button
          type="button"
          onClick={() => window.print()}
          className="print:hidden flex h-fit items-center gap-2 rounded-xl border border-uc-700 px-4 py-2 text-sm font-semibold text-uc-700 hover:bg-uc-50"
          title="Print a hard copy of the opportunities currently shown below"
        >
          Print
        </button>
      </div>

      {/* Only rendered on paper -- gives the hard copy a header saying
          what it is, which filter produced it, and when it was printed,
          none of which is obvious once it's out of the browser. */}
      <div className="hidden print:block print:mb-6">
        <p className="text-base font-bold">Call for Papers &amp; Grants</p>

        <p className="text-sm font-semibold text-slate-700">
          {activeTabLabel} &middot; {filtered.length} opportunit{filtered.length === 1 ? "y" : "ies"}
        </p>

        <p className="text-xs text-slate-500">Printed {printedAt}</p>
      </div>

      <div className="mt-6 flex flex-wrap gap-2 print:hidden">
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
        className="mt-5 w-full rounded-xl border px-4 py-3 print:hidden"
        placeholder="Search calls and grants..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {loading && (
        <p className="mt-6 text-slate-500 print:hidden">Loading opportunities…</p>
      )}

      {error && !loading && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 print:hidden">
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-3 rounded-lg border border-red-300 px-4 py-2 text-sm font-semibold text-red-700"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <p className="mt-6 text-slate-500">
          No opportunities match this filter yet.
        </p>
      )}

      <div className="mt-6 grid gap-5 print:mt-0 print:gap-4">
        {filtered.map((item) => (
          <article
            key={item.id}
            className="rounded-2xl border bg-white p-6 print:break-inside-avoid print:rounded-none print:border-slate-300 print:p-4"
          >
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
              className="mt-4 inline-block font-semibold text-blue-700 print:hidden"
            >
              Open official source →
            </a>

            {/* A clickable link does nothing on paper, so the printed
                copy shows the actual URL as text instead. */}
            {item.source_url && (
              <p className="mt-4 hidden text-sm break-all text-slate-600 print:block">
                Source: {item.source_url}
              </p>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
