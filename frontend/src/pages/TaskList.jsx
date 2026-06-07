import { useEffect, useState } from "react";
import { getTaskInsights } from "../api/aiApi.js";
import { fetchTasks, ignoreTask, resolveTask } from "../api/taskApi.js";
import InsightCard from "../components/InsightCard.jsx";
import TaskCard from "../components/TaskCard.jsx";

const taskTypes = [
  "",
  "stockout_warning",
  "replenishment_suggestion",
  "overstock_warning",
  "unfulfillable_inventory_alert",
  "data_missing_alert",
];
const taskTypeLabels = {
  stockout_warning: "断货预警",
  replenishment_suggestion: "补货建议",
  overstock_warning: "滞销/高库存",
  unfulfillable_inventory_alert: "不可售异常",
  data_missing_alert: "数据缺失",
};
const taskStatuses = ["", "pending", "resolved", "ignored"];
const taskStatusLabels = {
  pending: "待处理",
  resolved: "已解决",
  ignored: "已忽略",
};
const priorities = ["", "P0", "P1", "P2", "P3"];

function RiskInsightCenter({ data, loading, error, tasks, onSelectInsight }) {
  const insights = data?.insights || [];

  function enrichInsight(insight) {
    const taskIds = new Set(insight.related_task_ids || []);
    const skus = new Set(insight.related_skus || []);
    const relatedTasks = tasks.filter(
      (task) => taskIds.has(task.task_id) || skus.has(task.seller_sku)
    );
    return { ...insight, related_tasks: relatedTasks };
  }

  return (
    <section className="risk-center">
      <div className="section-header">
        <div>
          <h2>风险洞察中心</h2>
          <p>AI 将未完成待办归纳成可追踪、可处理的运营问题卡片</p>
        </div>
        {data?.generated_at && <span>{new Date(data.generated_at).toLocaleString()}</span>}
      </div>

      {loading && <div className="state-line">正在生成风险洞察...</div>}
      {!loading && error && <div className="error-line">{error}</div>}
      {!loading && !error && data?.configured === false && (
        <div className="state-line">AI 风险洞察暂未配置。</div>
      )}
      {!loading && !error && data?.error && <div className="error-line">{data.error}</div>}
      {!loading && !error && data?.configured !== false && insights.length === 0 && !data?.error && (
        <div className="empty-state">暂无风险问题卡片</div>
      )}
      {!loading && !error && insights.length > 0 && (
        <div className="insight-grid">
          {insights.map((insight) => {
            const enrichedInsight = enrichInsight(insight);
            return (
              <InsightCard
                key={insight.id}
                insight={enrichedInsight}
                onClick={() => onSelectInsight(enrichedInsight)}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}

function TaskList({ reloadKey, onTaskUpdated, onSelectInsight }) {
  const [tasks, setTasks] = useState([]);
  const [allTasks, setAllTasks] = useState([]);
  const [filters, setFilters] = useState({
    task_type: "",
    task_status: "",
    priority: "",
    seller_sku: "",
  });
  const [insightData, setInsightData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [insightLoading, setInsightLoading] = useState(true);
  const [busyTaskId, setBusyTaskId] = useState("");
  const [error, setError] = useState("");
  const [insightError, setInsightError] = useState("");

  async function loadTasks(nextFilters = filters) {
    setLoading(true);
    setError("");
    try {
      const nextTasks = await fetchTasks(nextFilters);
      setTasks(nextTasks);
      if (Object.values(nextFilters).every((value) => value === "")) {
        setAllTasks(nextTasks);
      }
    } catch (err) {
      setError(err.message || "运营待办加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadAllTasks() {
    setAllTasks(await fetchTasks({}));
  }

  async function loadInsights() {
    setInsightLoading(true);
    setInsightError("");
    try {
      setInsightData(await getTaskInsights());
    } catch (err) {
      setInsightError(err.message || "风险洞察加载失败");
    } finally {
      setInsightLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
    loadAllTasks();
    loadInsights();
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
      await loadAllTasks();
      await loadInsights();
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
          <h1>运营待办</h1>
          <p>库存 Agent 生成的补货、断货、滞销和数据补全任务</p>
        </div>
        <div className="record-count">{tasks.length} 条</div>
      </div>

      <RiskInsightCenter
        data={insightData}
        loading={insightLoading}
        error={insightError}
        tasks={allTasks.length ? allTasks : tasks}
        onSelectInsight={onSelectInsight}
      />

      <div className="section-header task-section-header">
        <div>
          <h2>任务明细</h2>
          <p>按任务类型、处理状态、优先级和 SKU 筛选原始待办</p>
        </div>
      </div>

      <div className="filter-bar">
        <input
          value={filters.seller_sku}
          onChange={(event) => updateFilter("seller_sku", event.target.value)}
          placeholder="搜索 SKU"
        />
        <select value={filters.task_type} onChange={(event) => updateFilter("task_type", event.target.value)}>
          {taskTypes.map((option) => (
            <option key={option} value={option}>{option ? taskTypeLabels[option] : "任务类型"}</option>
          ))}
        </select>
        <select value={filters.task_status} onChange={(event) => updateFilter("task_status", event.target.value)}>
          {taskStatuses.map((option) => (
            <option key={option} value={option}>{option ? taskStatusLabels[option] : "处理状态"}</option>
          ))}
        </select>
        <select value={filters.priority} onChange={(event) => updateFilter("priority", event.target.value)}>
          {priorities.map((option) => (
            <option key={option} value={option}>{option || "优先级"}</option>
          ))}
        </select>
      </div>

      {loading && <div className="state-line">正在加载运营待办...</div>}
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
