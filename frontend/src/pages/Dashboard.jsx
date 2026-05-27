import { useEffect, useState } from "react";
import { api } from "../api/emissions";
import StatCard from "../components/StatCard";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getDashboard()
      .then((res) => setStats(res.data))
      .catch(() => setError("Failed to load dashboard data."));
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">ESG Emissions Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of all ingested emission records</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          {error}
        </div>
      )}

      {!stats && !error && (
        <div className="text-gray-400 text-center py-12">Loading...</div>
      )}

      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <StatCard label="Total Records" value={stats.total} color="gray" />
            <StatCard label="Pending" value={stats.pending} color="yellow" />
            <StatCard label="Approved" value={stats.approved} color="green" />
            <StatCard label="Rejected" value={stats.rejected} color="red" />
            <StatCard label="Suspicious" value={stats.suspicious} color="yellow" sub="Need review" />
            <StatCard
              label="Total CO₂e"
              value={stats.total_co2e_kg ? `${Number(stats.total_co2e_kg).toLocaleString()} kg` : "—"}
              color="blue"
              sub="kg CO₂ equivalent"
            />
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Scope Breakdown</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-xs text-orange-600 font-medium uppercase">Scope 1</p>
                <p className="text-sm text-orange-700 mt-1">Direct combustion (fuel)</p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-600 font-medium uppercase">Scope 2</p>
                <p className="text-sm text-blue-700 mt-1">Purchased electricity</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-xs text-purple-600 font-medium uppercase">Scope 3</p>
                <p className="text-sm text-purple-700 mt-1">Business travel</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
