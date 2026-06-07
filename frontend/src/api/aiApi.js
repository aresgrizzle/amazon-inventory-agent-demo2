import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});

export async function getDashboardAiSummary() {
  const response = await api.get("/api/ai/dashboard-summary");
  return response.data;
}

export async function getSkuAiAnalysis(sellerSku) {
  const response = await api.get(`/api/ai/sku-analysis/${encodeURIComponent(sellerSku)}`);
  return response.data;
}

export async function getTaskAiPriority() {
  const response = await api.get("/api/ai/task-priority");
  return response.data;
}

export async function getTaskInsights() {
  const response = await api.get("/api/ai/task-insights");
  return response.data;
}
