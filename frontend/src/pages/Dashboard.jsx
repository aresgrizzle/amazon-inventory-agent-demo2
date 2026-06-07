import { useEffect, useState } from "react";
import { getDashboardAiSummary } from "../api/aiApi.js";
import { fetchDashboardSummary, runInventoryAgent } from "../api/dashboardApi.js";
import MetricCard from "../components/MetricCard.jsx";

function formatCurrency(value) {
  const number = Number(value || 0);
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  const number = Number(value);
  if (Number.isNaN(number)) return "N/A";
  return `${number.toFixed(1)}%`;
}

function AiPanel({ data, loading, error }) {
  return (
    <section className="ai-panel">
      <div className="ai-panel-header">
        <h2>AI Summary</h2>
        {data?.generated_at && <span>{new Date(data.generated_at).toLocaleString()}</span>}
      </div>
      {loading && <div className="state-line">Loading AI summary...</div>}
      {!loading && error && <div className="error-line">{error}</div>}
      {!loading && !error && data?.configured === false && (
        <div className="state-line">AI summary is not configured.</div>
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
      setError(err.message || "Dashboard data failed to load");
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
      setAiError(err.message || "AI summary failed to load");
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
      setMessage(`${result.message}: analyzed ${result.analyzed_skus}, tasks ${result.generated_tasks}`);
      await loadSummary();
      await loadAiSummary();
      onAgentRun();
    } catch (err) {
      setError(err.message || "Inventory Agent failed to run");
    } finally {
      setRunning(false);
    }
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Inventory risk, decision quality, and operations workload overview</p>
        </div>
        <button className="primary-button" type="button" onClick={handleRunAgent} disabled={running}>
          {running ? "Running..." : "Run Inventory Agent"}
        </button>
      </div>

      {loading && <div className="state-line">Loading...</div>}
      {error && <div className="error-line">{error}</div>}
      {message && <div className="success-line">{message}</div>}

      {!loading && summary && (
        <div className="metrics-grid expanded">
          <MetricCard label="Total SKUs" value={summary.total_skus} />
          <MetricCard label="Critical Stockout" value={summary.critical_stockout_count} tone="danger" />
          <MetricCard label="High Stockout" value={summary.high_stockout_count} tone="warning" />
          <MetricCard label="High Overstock" value={summary.overstock_high_count} tone="warning" />
          <MetricCard label="Data Missing" value={summary.data_missing_count} tone="info" />
          <MetricCard label="Pending Tasks" value={summary.pending_task_count} tone="info" />
          <MetricCard label="Total Tasks" value={summary.total_tasks} />
          <MetricCard
            label="Estimated Lost Revenue"
            value={formatCurrency(summary.estimated_lost_revenue_total)}
            tone="danger"
          />
          <MetricCard label="High Impact Tasks" value={summary.high_impact_task_count ?? 0} tone="warning" />
          <MetricCard
            label="Avg Decision Confidence"
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
