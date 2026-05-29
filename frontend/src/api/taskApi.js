import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});

function compactParams(params) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== "" && value != null)
  );
}

export async function fetchTasks(filters = {}) {
  const response = await api.get("/api/tasks", {
    params: compactParams(filters),
  });
  return response.data;
}

export async function resolveTask(taskId) {
  const response = await api.post(`/api/tasks/${taskId}/resolve`, {
    operator_id: "demo_user",
    operator_note: "前端标记已处理",
  });
  return response.data;
}

export async function ignoreTask(taskId) {
  const response = await api.post(`/api/tasks/${taskId}/ignore`, {
    operator_id: "demo_user",
    operator_note: "前端标记忽略",
  });
  return response.data;
}
