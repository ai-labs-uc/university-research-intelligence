import { useEffect, useState } from "react";
import api from "../api/client";

const TABS = [
  {
    key: "ALL",
    label: "All",
  },
  {
    key: "GRANT",
    label: "Grants",
  },
  {
    key: "CALL_FOR_PAPER_NATIONAL",
    label: "National Call for Papers",
  },
  {
    key: "CALL_FOR_PAPER_INTERNATIONAL",
    label: "International Call for Papers",
  },
];

export default function Opportunities() {
  const [items, setItems] = useState([]);

  const [tab, setTab] = useState("ALL");

  useEffect(() => {
    api
      .get("/api/opportunities")
      .then((res) => {
        setItems(res.data || []);
      })
      .catch((err) => {
        console.error(err);
      });
  }, []);

  const filtered = items.filter((item) => {
    if (tab === "ALL") return true;

    if (tab === "GRANT") {
      return item.category?.startsWith("GRANT");
    }

    return item.category === tab;
  });

  return (
    <div>
      <h1 className="text-3xl font-bold">Research Opportunities</h1>

      <div className="flex gap-3 mt-5">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={
              tab === t.key
                ? "bg-blue-600 text-white px-4 py-2 rounded"
                : "border px-4 py-2 rounded"
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-6 space-y-4">
        {filtered.map((item) => (
          <div key={item.id} className="border rounded-xl p-5">
            <h2 className="font-bold text-xl">{item.title}</h2>

            <p>{item.organization}</p>

            <p className="text-sm text-gray-500">{item.category}</p>

            <p className="mt-3">{item.summary?.substring(0, 300)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
