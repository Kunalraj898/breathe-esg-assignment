import Badge from "./Badge";

export default function RecordTable({ records, onReview, loading }) {
  if (loading) {
    return (
      <div className="text-center py-12 text-gray-400">Loading records...</div>
    );
  }

  if (!records.length) {
    return (
      <div className="text-center py-12 text-gray-400">No records found.</div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            {[
              "Date", "Source", "Description", "Qty", "Unit",
              "CO₂e (kg)", "Scope", "Status", "Suspicious", "Actions",
            ].map((h) => (
              <th
                key={h}
                className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {records.map((r) => (
            <tr
              key={r.id}
              className={r.is_suspicious ? "bg-yellow-50" : ""}
            >
              <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                {r.activity_date ?? "—"}
              </td>
              <td className="px-4 py-3">
                <Badge value={r.source_type} />
              </td>
              <td className="px-4 py-3 max-w-xs truncate text-gray-700">
                {r.description || "—"}
              </td>
              <td className="px-4 py-3 text-right font-mono text-gray-700">
                {r.quantity != null ? Number(r.quantity).toLocaleString() : "—"}
              </td>
              <td className="px-4 py-3 text-gray-500">{r.unit || "—"}</td>
              <td className="px-4 py-3 text-right font-mono font-medium text-gray-800">
                {r.co2e_kg != null ? Number(r.co2e_kg).toFixed(2) : "—"}
              </td>
              <td className="px-4 py-3">
                <Badge value={r.scope} />
              </td>
              <td className="px-4 py-3">
                <Badge value={r.status} />
              </td>
              <td className="px-4 py-3">
                {r.is_suspicious ? (
                  <span
                    className="text-yellow-600 font-medium cursor-help"
                    title={r.suspicious_reason}
                  >
                    ⚠ Flag
                  </span>
                ) : (
                  <span className="text-gray-300">—</span>
                )}
              </td>
              <td className="px-4 py-3">
                {r.is_locked ? (
                  <span className="text-xs text-gray-400">Locked</span>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => onReview(r.id, "approve")}
                      className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => onReview(r.id, "reject")}
                      className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
