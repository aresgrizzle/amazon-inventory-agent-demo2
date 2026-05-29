import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});

function compactParams(params) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== "" && value != null)
  );
}

export async function fetchInventoryAnalysis(filters = {}) {
  const response = await api.get("/api/inventory/analysis", {
    params: compactParams(filters),
  });
  return response.data;
}

export async function fetchSkuAnalysis(sellerSku) {
  const response = await api.get(`/api/inventory/analysis/${encodeURIComponent(sellerSku)}`);
  return response.data;
}
