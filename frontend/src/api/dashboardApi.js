import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});

export async function fetchDashboardSummary() {
  const response = await api.get("/api/dashboard/summary");
  return response.data;
}

export async function runInventoryAgent() {
  const response = await api.post("/api/agent/run-inventory-analysis");
  return response.data;
}
