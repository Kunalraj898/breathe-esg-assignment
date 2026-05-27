import client from "./client";

export const api = {
  // Companies
  getCompanies: () => client.get("/companies/"),
  createCompany: (data) => client.post("/companies/", data),

  // Data Sources
  getDataSources: (companyId) =>
    client.get("/data-sources/", { params: { company: companyId } }),
  createDataSource: (data) => client.post("/data-sources/", data),

  // Uploads
  uploadFile: (formData) =>
    client.post("/uploads/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  getUploads: (companyId) =>
    client.get("/uploads/", { params: { company: companyId } }),

  // Records
  getRecords: (params = {}) => client.get("/records/", { params }),
  reviewRecord: (id, data) => client.post(`/records/${id}/review/`, data),
  getDashboard: (companyId) =>
    client.get("/records/dashboard/", { params: { company: companyId } }),

  // Audit logs
  getAuditLogs: (params = {}) => client.get("/audit-logs/", { params }),
};
