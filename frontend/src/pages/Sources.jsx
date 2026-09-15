import { useEffect, useState } from "react"
import api from "../api/client"

export default function Sources() {
  const [items, setItems] = useState([])

  useEffect(() => {
    api.get("/api/sources").then(r => setItems(r.data))
  }, [])

  return (
    <div>
      <h1 className="text-3xl font-black">Opportunity Sources</h1>

      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left">Code</th>
              <th className="px-4 py-3 text-left">Source</th>
              <th className="px-4 py-3 text-left">Trust</th>
              <th className="px-4 py-3 text-left">Enabled</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-semibold">{item.code}</td>
                <td className="px-4 py-3">{item.name}</td>
                <td className="px-4 py-3">{item.trust_level}</td>
                <td className="px-4 py-3">{item.enabled ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
