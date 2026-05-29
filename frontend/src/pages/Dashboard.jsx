import { useEffect, useState } from "react";
import { fetchDashboardSummary, runInventoryAgent } from "../api/dashboardApi.js";
import MetricCard from "../components/MetricCard.jsx";

function Dashboard({ reloadKey, onAgentRun }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadSummary() {
    setLoading(true);
    setError("");
    try {
      setSummary(await fetchDashboardSummary());
    } catch (err) {
      setError(err.message || "Dashboard 数据加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSummary();
  }, [reloadKey]);

  async function handleRunAgent() {
    setRunning(true);
    setError("");
    setMessage("");
    try {
      const result = await runInventoryAgent();
      setMessage(`${result.message}: analyzed ${result.analyzed_skus}, tasks ${result.generated_tasks}`);
      await loadSummary();
      onAgentRun();
    } catch (err) {
      setError(err.message || "库存 Agent 运行失败");
    } finally {
      setRunning(false);
    }
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>库存风险、数据质量和待办任务总览</p>
        </div>
        <button className="primary-button" type="button" onClick={handleRunAgent} disabled={running}>
          {running ? "运行中..." : "重新运行库存 Agent"}
        </button>
      </div>

      {loading && <div className="state-line">Loading...</div>}
      {error && <div className="error-line">{error}</div>}
      {message && <div className="success-line">{message}</div>}

      {!loading && summary && (
        <div className="metrics-grid">
          <MetricCard label="总 SKU 数" value={summary.total_skus} />
          <MetricCard label="Critical 断货风险" value={summary.critical_stockout_count} tone="danger" />
          <MetricCard label="High 断货风险" value={summary.high_stockout_count} tone="warning" />
          <MetricCard label="高滞销风险" value={summary.overstock_high_count} tone="warning" />
          <MetricCard label="数据缺失" value={summary.data_missing_count} tone="info" />
          <MetricCard label="待处理任务" value={summary.pending_task_count} tone="info" />
          <MetricCard label="总任务数" value={summary.total_tasks} />
        </div>
      )}
    </section>
  );
}

export default Dashboard;
