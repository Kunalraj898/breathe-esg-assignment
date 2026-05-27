import { useEffect, useState, useCallback } from "react";
import { api } from "../api/emissions";
import RecordTable from "../components/RecordTable";

const ANALYST = "analyst@breathe.com"; // in a real app this comes from auth

export default function Records() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: "",
    scope: "",
    suspicious: "",
    source_type: "",
  });
  const [toast, setToast] = useState(null);

  const fetchRecords = useCallback(() => {
    setLoading(true);
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== "")
    );
    api.getRecords(params)
      .then((r) => setRecords(r.data.results ?? r.data))
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const handleReview = async (id, action) => {
    try {
      await api.reviewRecord(id, { action, reviewed_by: ANALYST });
      setToast({ type: "success", msg: `Record ${action}d successfully.` });
      fetchRecords();
    } catch (err) {
      setToast({ type: "error", msg: err.response?.data?.error ?? "Review failed." });
    }
    setTimeout(() => setToast(null), 3000);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Emission Records</h1>
          <p className="text-gray-500 mt-1">{records.length} records shown</p>
        </div>
      </div>

      {toast && (
        <div
          className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
            toast.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {toast.msg}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
        >
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>

        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={filters.scope}
          onChange={(e) => setFilters((f) => ({ ...f, scope: e.target.value }))}
        >
          <option value="">All Scopes</option>
          <option value="SCOPE1">Scope 1</option>
          <option value="SCOPE2">Scope 2</option>
          <option value="SCOPE3">Scope 3</option>
        </select>

        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={filters.source_type}
          onChange={(e) => setFilters((f) => ({ ...f, source_type: e.target.value }))}
        >
          <option value="">All Sources</option>
          <option value="SAP_FUEL">SAP Fuel</option>
          <option value="UTILITY">Utility</option>
          <option value="TRAVEL">Travel</option>
        </select>

        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={filters.suspicious}
          onChange={(e) => setFilters((f) => ({ ...f, suspicious: e.target.value }))}
        >
          <option value="">All Records</option>
          <option value="true">Suspicious Only</option>
          <option value="false">Clean Only</option>
        </select>

        <button
          onClick={() => setFilters({ status: "", scope: "", suspicious: "", source_type: "" })}
          className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 underline"
        >
          Clear filters
        </button>
      </div>

      <RecordTable records={records} onReview={handleReview} loading={loading} />
    </div>
  );
}
