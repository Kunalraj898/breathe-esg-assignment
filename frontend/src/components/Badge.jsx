const styles = {
  PENDING: "bg-yellow-100 text-yellow-800",
  APPROVED: "bg-green-100 text-green-800",
  REJECTED: "bg-red-100 text-red-800",
  SCOPE1: "bg-orange-100 text-orange-800",
  SCOPE2: "bg-blue-100 text-blue-800",
  SCOPE3: "bg-purple-100 text-purple-800",
  SAP_FUEL: "bg-orange-100 text-orange-700",
  UTILITY: "bg-blue-100 text-blue-700",
  TRAVEL: "bg-purple-100 text-purple-700",
};

export default function Badge({ value }) {
  const label = value?.replace("_", " ") ?? "";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        styles[value] ?? "bg-gray-100 text-gray-700"
      }`}
    >
      {label}
    </span>
  );
}
