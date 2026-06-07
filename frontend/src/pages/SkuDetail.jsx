import { useEffect, useState } from "react";
import { getSkuAiAnalysis } from "../api/aiApi.js";
import { fetchSkuAnalysis } from "../api/inventoryApi.js";
import RiskBadge from "../components/RiskBadge.jsx";

const baseFields = [
  ["SKU", "seller_sku"],
  ["ASIN", "asin"],
  ["Available Inventory", "fulfillable_quantity"],
  ["Total Inventory", "total_quantity"],
  ["Effective Inbound", "effective_inbound_quantity"],
  ["7D Avg Sales", "avg_daily_sales_7d"],
  ["30D Avg Sales", "avg_daily_sales_30d"],
  ["Available Days", "available_days"],
  ["Total Cover Days", "total_cover_days"],
  ["Estimated Stockout Date", "estimated_stockout_date"],
  ["Recommended Qty", "recommended_replenishment_quantity"],
  ["Recommended Action", "recommended_action"],
  ["Data Quality", "data_quality_status"],
];

function formatEmpty(value) {
  return value === null || value === undefined || value === "" ? "-" : value;
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number" && !Number.isInteger(value)) return value.toFixed(2);
  return value;
}

function formatCurrency(value) {
  if (value === null || value === undefined || value === "") return "$0.00";
  const number = Number(value);
  if (Number.isNaN(number)) return "$0.00";
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  const number = Number(value);
  if (Number.isNaN(number)) return "N/A";
  const percent = Math.abs(number) <= 1 ? number * 100 : number;
  return `${percent.toFixed(1)}%`;
}

function formatScore(value) {
  if (value === null || value === undefined || value === "") return "0.0";
  const number = Number(value);
  if (Number.isNaN(number)) return "0.0";
  return number.toFixed(1);
}

function DetailItem({ label, children }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      {children}
    </div>
  );
}

function IntelligenceSection({ title, children }) {
  return (
    <section className="intelligence-card">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function SkuAiPanel({ data, loading, error }) {
  return (
    <section className="ai-panel">
      <div className="ai-panel-header">
        <h2>AI Analysis</h2>
        {data?.generated_at && <span>{new Date(data.generated_at).toLocaleString()}</span>}
      </div>
      {loading && <div className="state-line">Loading AI analysis...</div>}
      {!loading && error && <div className="error-line">{error}</div>}
      {!loading && !error && data?.configured === false && (
        <div className="state-line">AI analysis is not configured.</div>
      )}
      {!loading && !error && data?.error && <div className="error-line">{data.error}</div>}
      {!loading && !error && data?.analysis && <p className="ai-content">{data.analysis}</p>}
    </section>
  );
}

function SkuDetail({ sellerSku, onBack }) {
  const [detail, setDetail] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(true);
  const [error, setError] = useState("");
  const [aiError, setAiError] = useState("");

  useEffect(() => {
    async function loadDetail() {
      setLoading(true);
      setError("");
      try {
        setDetail(await fetchSkuAnalysis(sellerSku));
      } catch (err) {
        setError(err.message || "SKU detail failed to load");
      } finally {
        setLoading(false);
      }
    }

    async function loadAiAnalysis() {
      setAiLoading(true);
      setAiError("");
      try {
        setAiAnalysis(await getSkuAiAnalysis(sellerSku));
      } catch (err) {
        setAiError(err.message || "AI analysis failed to load");
      } finally {
        setAiLoading(false);
      }
    }

    loadDetail();
    loadAiAnalysis();
  }, [sellerSku]);

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>SKU Detail</h1>
          <p>{sellerSku}</p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>Back to Inventory</button>
      </div>

      {loading && <div className="state-line">Loading...</div>}
      {error && <div className="error-line">{error}</div>}
      {!loading && !error && !detail && <div className="empty-state">No data</div>}

      {!loading && detail && (
        <div className="detail-layout">
          <div className="detail-grid">
            {baseFields.map(([label, key]) => (
              <DetailItem label={label} key={key}>
                {["recommended_action", "data_quality_status"].includes(key) ? (
                  <RiskBadge value={detail[key]} />
                ) : (
                  <strong>{formatValue(detail[key])}</strong>
                )}
              </DetailItem>
            ))}
            <DetailItem label="Stockout Risk">
              <RiskBadge value={detail.stockout_risk_level} />
            </DetailItem>
            <DetailItem label="Overstock Risk">
              <RiskBadge value={detail.overstock_risk_level} />
            </DetailItem>
          </div>

          <div className="intelligence-grid">
            <IntelligenceSection title="Profitability">
              <div className="mini-metric-grid">
                <DetailItem label="Current Price"><strong>{formatCurrency(detail.current_price)}</strong></DetailItem>
                <DetailItem label="Landed Cost"><strong>{formatCurrency(detail.landed_cost)}</strong></DetailItem>
                <DetailItem label="Gross Margin"><strong>{formatPercent(detail.gross_margin)}</strong></DetailItem>
              </div>
            </IntelligenceSection>

            <IntelligenceSection title="Replenishment Policy">
              <div className="mini-metric-grid">
                <DetailItem label="Lead Time"><strong>{formatEmpty(detail.total_replenishment_lead_time_days)} days</strong></DetailItem>
                <DetailItem label="Target Cover"><strong>{formatEmpty(detail.target_cover_days)} days</strong></DetailItem>
                <DetailItem label="Safety Stock"><strong>{formatEmpty(detail.safety_stock_days)} days</strong></DetailItem>
                <DetailItem label="MOQ"><strong>{formatEmpty(detail.moq)}</strong></DetailItem>
              </div>
            </IntelligenceSection>

            <IntelligenceSection title="Decision Intelligence">
              <div className="mini-metric-grid">
                <DetailItem label="Stockout Score"><strong>{formatScore(detail.stockout_risk_score)}</strong></DetailItem>
                <DetailItem label="Overstock Score"><strong>{formatScore(detail.overstock_risk_score)}</strong></DetailItem>
                <DetailItem label="Lost Revenue"><strong>{formatCurrency(detail.estimated_lost_revenue)}</strong></DetailItem>
                <DetailItem label="Confidence"><strong>{formatPercent(detail.decision_confidence)}</strong></DetailItem>
              </div>
              <div className="decision-explanation">
                <span>Decision Explanation</span>
                <p>{detail.decision_explanation || detail.action_reason || "No decision explanation available."}</p>
              </div>
            </IntelligenceSection>
          </div>

          <section className="reason-panel">
            <h2>Recommendation Reason</h2>
            <p>{detail.action_reason || "No recommendation reason available."}</p>
          </section>

          <SkuAiPanel data={aiAnalysis} loading={aiLoading} error={aiError} />
        </div>
      )}
    </section>
  );
}

export default SkuDetail;
