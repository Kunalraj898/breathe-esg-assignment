import { useEffect, useRef, useState } from "react";
import { api } from "../api/emissions";

const SOURCE_TYPES = [
  { value: "SAP_FUEL", label: "SAP Fuel / Procurement" },
  { value: "UTILITY", label: "Utility Electricity" },
  { value: "TRAVEL", label: "Corporate Travel" },
];

export default function Upload() {
  const [companies, setCompanies] = useState([]);
  const [dataSources, setDataSources] = useState([]);
  const [form, setForm] = useState({
    company: "",
    data_source: "",
    uploaded_by: "",
    file: null,
  });
  const [newCompany, setNewCompany] = useState("");
  const [newSource, setNewSource] = useState({ name: "", source_type: "SAP_FUEL" });
  const [status, setStatus] = useState(null); // null | "loading" | "success" | "error"
  const [message, setMessage] = useState("");
  const fileRef = useRef();

  useEffect(() => {
    api.getCompanies().then((r) => setCompanies(r.data.results ?? r.data));
  }, []);

  useEffect(() => {
    if (form.company) {
      api.getDataSources(form.company).then((r) =>
        setDataSources(r.data.results ?? r.data)
      );
    }
  }, [form.company]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.file || !form.company || !form.data_source || !form.uploaded_by) {
      setMessage("All fields are required.");
      setStatus("error");
      return;
    }
    const fd = new FormData();
    fd.append("company", form.company);
    fd.append("data_source", form.data_source);
    fd.append("uploaded_by", form.uploaded_by);
    fd.append("file", form.file);

    setStatus("loading");
    setMessage("");
    try {
      const res = await api.uploadFile(fd);
      setStatus("success");
      setMessage(
        `Upload complete! ${res.data.row_count} rows ingested from "${res.data.original_filename}".`
      );
      setForm({ company: form.company, data_source: "", uploaded_by: "", file: null });
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setStatus("error");
      setMessage(err.response?.data?.error ?? "Upload failed. Check your CSV format.");
    }
  };

  const handleAddCompany = async () => {
    if (!newCompany.trim()) return;
    const slug = newCompany.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
    try {
      const res = await api.createCompany({ name: newCompany, slug });
      setCompanies((prev) => [...prev, res.data]);
      setForm((f) => ({ ...f, company: String(res.data.id) }));
      setNewCompany("");
    } catch {
      setMessage("Failed to create company.");
      setStatus("error");
    }
  };

  const handleAddSource = async () => {
    if (!newSource.name.trim() || !form.company) return;
    try {
      const res = await api.createDataSource({ ...newSource, company: form.company });
      setDataSources((prev) => [...prev, res.data]);
      setForm((f) => ({ ...f, data_source: String(res.data.id) }));
      setNewSource({ name: "", source_type: "SAP_FUEL" });
    } catch {
      setMessage("Failed to create data source.");
      setStatus("error");
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Upload Emissions Data</h1>
        <p className="text-gray-500 mt-1">
          Upload SAP fuel, utility electricity, or corporate travel CSVs.
        </p>
      </div>

      {status === "success" && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg p-4 mb-6">
          {message}
        </div>
      )}
      {status === "error" && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-xl border border-gray-200 p-6">

        {/* Company */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
          <div className="flex gap-2">
            <select
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              value={form.company}
              onChange={(e) => setForm((f) => ({ ...f, company: e.target.value, data_source: "" }))}
            >
              <option value="">Select company…</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2 mt-2">
            <input
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Or add new company…"
              value={newCompany}
              onChange={(e) => setNewCompany(e.target.value)}
            />
            <button
              type="button"
              onClick={handleAddCompany}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition"
            >
              Add
            </button>
          </div>
        </div>

        {/* Data Source */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Data Source</label>
          <select
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            value={form.data_source}
            onChange={(e) => setForm((f) => ({ ...f, data_source: e.target.value }))}
            disabled={!form.company}
          >
            <option value="">Select data source…</option>
            {dataSources.map((ds) => (
              <option key={ds.id} value={ds.id}>{ds.name}</option>
            ))}
          </select>
          {form.company && (
            <div className="flex gap-2 mt-2">
              <input
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
                placeholder="New source name…"
                value={newSource.name}
                onChange={(e) => setNewSource((s) => ({ ...s, name: e.target.value }))}
              />
              <select
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
                value={newSource.source_type}
                onChange={(e) => setNewSource((s) => ({ ...s, source_type: e.target.value }))}
              >
                {SOURCE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={handleAddSource}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition"
              >
                Add
              </button>
            </div>
          )}
        </div>

        {/* Uploaded by */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Your Name / Email</label>
          <input
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="analyst@company.com"
            value={form.uploaded_by}
            onChange={(e) => setForm((f) => ({ ...f, uploaded_by: e.target.value }))}
          />
        </div>

        {/* File */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">CSV File</label>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-green-50 file:text-green-700 file:font-medium hover:file:bg-green-100"
            onChange={(e) => setForm((f) => ({ ...f, file: e.target.files[0] }))}
          />
        </div>

        <button
          type="submit"
          disabled={status === "loading"}
          className="w-full py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition disabled:opacity-50"
        >
          {status === "loading" ? "Uploading & Ingesting…" : "Upload & Ingest"}
        </button>
      </form>
    </div>
  );
}
