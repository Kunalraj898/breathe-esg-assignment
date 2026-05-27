import { Link, useLocation } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/upload", label: "Upload Data" },
  { to: "/records", label: "Records" },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-green-600 font-bold text-xl">Breathe</span>
        <span className="text-gray-400 font-light text-xl">ESG</span>
      </div>
      <div className="flex gap-6">
        {links.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            className={`text-sm font-medium transition-colors ${
              pathname === to
                ? "text-green-600 border-b-2 border-green-600 pb-1"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
