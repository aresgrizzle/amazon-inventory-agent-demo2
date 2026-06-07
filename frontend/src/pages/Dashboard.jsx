import { useEffect, useState } from "react";
import { getDashboardAiSummary } from "../api/aiApi.js";
import { fetchDashboardSummary, runInventoryAgent } from "../api/dashboardApi.js";
import MetricCard from "../components/MetricCard.jsx";

function formatCurrency(value) {
  const number = Number(value || 0);
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "暂无";
  const number = Number(value);
  if (Number.isNaN(number)) return "暂无";
  return `${number.toFixed(1)}%`;
}

function AiPanel({ data, loading, error }) {
  return (
    <section className="ai-panel">
      <div className="ai-panel-header">
        <h2>AI 运营复盘</h2>
        {data?.generated_at && <span>{new Date(data.generated_at).toLocaleString()}</span>}
      </div>
      {loading && <div className="state-line">正在生成 AI 运营复盘...</div>}
      {!loading && error && <div className="error-line">{error}</div>}
      {!loading && !error && data?.configured === false && (
        <div className="state-line">AI 运营复盘暂未配置。</div>
      )}
      {!loading && !error && data?.error && <div className="error-line">{data.error}</div>}
      {!loading && !error && data?.summary && <p className="ai-content">{data.summary}</p>}
    </section>
  );
}

function Dashboard({ reloadKey, onAgentRun }) {
  const [summary, setSummary] = useState(null);
  const [aiSummary, setAiSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [aiError, setAiError] = useState("");
  const [message, setMessage] = useState("");

  async function loadSummary() {
    setLoading(true);
    setError("");
    try {
      setSummary(await fetchDashboardSummary());
    } catch (err) {
      setError(err.message || "经营看板数据加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadAiSummary() {
    setAiLoading(true);
    setAiError("");
    try {
      setAiSummary(await getDashboardAiSummary());
    } catch (err) {
      setAiError(err.message || "AI 运营复盘加载失败");
    } finally {
      setAiLoading(false);
    }
  }

  useEffect(() => {
    loadSummary();
    loadAiSummary();
  }, [reloadKey]);

  async function handleRunAgent() {
    setRunning(true);
    setError("");
    setMessage("");
    try {
      const result = await runInventoryAgent();
      setMessage(`库存 Agent 已完成分析：${result.analyzed_skus} 个 SKU，生成 ${result.generated_tasks} 个待办`);
      await loadSummary();
      await loadAiSummary();
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
          <h1>经营看板</h1>
          <p>库存风险、补货决策质量和运营待办总览</p>
        </div>
        <button className="primary-button" type="button" onClick={handleRunAgent} disabled={running}>
          {running ? "分析中..." : "重新运行库存 Agent"}
        </button>
      </div>

      {loading && <div className="state-line">正在加载经营看板...</div>}
      {error && <div className="error-line">{error}</div>}
      {message && <div className="success-line">{message}</div>}

      {!loading && summary && (
        <div className="metrics-grid expanded">
          <MetricCard label="总 SKU 数" value={summary.total_skus} />
          <MetricCard label="严重断货风险" value={summary.critical_stockout_count} tone="danger" />
          <MetricCard label="高断货风险" value={summary.high_stockout_count} tone="warning" />
          <MetricCard label="高库存/滞销风险" value={summary.overstock_high_count} tone="warning" />
          <MetricCard label="数据待补全" value={summary.data_missing_count} tone="info" />
          <MetricCard label="待处理任务" value={summary.pending_task_count} tone="info" />
          <MetricCard label="任务总数" value={summary.total_tasks} />
          <MetricCard
            label="预估断货损失"
            value={formatCurrency(summary.estimated_lost_revenue_total)}
            tone="danger"
          />
          <MetricCard label="高影响任务" value={summary.high_impact_task_count ?? 0} tone="warning" />
          <MetricCard
            label="平均决策置信度"
            value={formatPercent(summary.avg_decision_confidence)}
            tone="info"
          />
        </div>
      )}

      <AiPanel data={aiSummary} loading={aiLoading} error={aiError} />
    </section>
  );
}

export default Dashboard;
