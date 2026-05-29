import { useEffect, useState } from "react";
import { fetchTasks, ignoreTask, resolveTask } from "../api/taskApi.js";
import TaskCard from "../components/TaskCard.jsx";

const taskTypes = [
  "",
  "stockout_warning",
  "replenishment_suggestion",
  "overstock_warning",
  "unfulfillable_inventory_alert",
  "data_missing_alert",
];
const taskStatuses = ["", "pending", "resolved", "ignored"];
const priorities = ["", "P0", "P1", "P2", "P3"];

function TaskList({ reloadKey, onTaskUpdated }) {
  const [tasks, setTasks] = useState([]);
  const [filters, setFilters] = useState({
    task_type: "",
    task_status: "",
    priority: "",
    seller_sku: "",
  });
  const [loading, setLoading] = useState(true);
  const [busyTaskId, setBusyTaskId] = useState("");
  const [error, setError] = useState("");

  async function loadTasks(nextFilters = filters) {
    setLoading(true);
    setError("");
    try {
      setTasks(await fetchTasks(nextFilters));
    } catch (err) {
      setError(err.message || "任务数据加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, [reloadKey]);

  function updateFilter(name, value) {
    const nextFilters = { ...filters, [name]: value };
    setFilters(nextFilters);
    loadTasks(nextFilters);
  }

  async function updateTask(taskId, action) {
    setBusyTaskId(taskId);
    setError("");
    try {
      if (action === "resolve") {
        await resolveTask(taskId);
      } else {
        await ignoreTask(taskId);
      }
      await loadTasks();
      onTaskUpdated();
    } catch (err) {
      setError(err.message || "任务状态更新失败");
    } finally {
      setBusyTaskId("");
    }
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>Tasks</h1>
          <p>库存 Agent 生成的运营待办</p>
        </div>
        <div className="record-count">{tasks.length} tasks</div>
      </div>

      <div className="filter-bar">
        <input
          value={filters.seller_sku}
          onChange={(event) => updateFilter("seller_sku", event.target.value)}
          placeholder="搜索 SKU"
        />
        <select value={filters.task_type} onChange={(event) => updateFilter("task_type", event.target.value)}>
          {taskTypes.map((option) => (
            <option key={option} value={option}>{option || "任务类型"}</option>
          ))}
        </select>
        <select value={filters.task_status} onChange={(event) => updateFilter("task_status", event.target.value)}>
          {taskStatuses.map((option) => (
            <option key={option} value={option}>{option || "任务状态"}</option>
          ))}
        </select>
        <select value={filters.priority} onChange={(event) => updateFilter("priority", event.target.value)}>
          {priorities.map((option) => (
            <option key={option} value={option}>{option || "优先级"}</option>
          ))}
        </select>
      </div>

      {loading && <div className="state-line">Loading...</div>}
      {error && <div className="error-line">{error}</div>}
      {!loading && !error && tasks.length === 0 && <div className="empty-state">暂无数据</div>}
      {!loading && !error && tasks.length > 0 && (
        <div className="task-list">
          {tasks.map((task) => (
            <TaskCard
              key={task.task_id}
              task={task}
              busy={busyTaskId === task.task_id}
              onResolve={(taskId) => updateTask(taskId, "resolve")}
              onIgnore={(taskId) => updateTask(taskId, "ignore")}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default TaskList;
