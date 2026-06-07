import { useEffect, useState } from "react";
import { getSkuAiAnalysis } from "../api/aiApi.js";
import { fetchSkuAnalysis } from "../api/inventoryApi.js";
import RiskBadge from "../components/RiskBadge.jsx";

const baseFields = [
  ["SKU", "seller_sku"],
  ["ASIN", "asin"],
  ["可售库存", "fulfillable_quantity"],
  ["总库存", "total_quantity"],
  ["有效在途库存", "effective_inbound_quantity"],
  ["近 7 日日均销量", "avg_daily_sales_7d"],
  ["近 30 日日均销量", "avg_daily_sales_30d"],
  ["可售天数", "available_days"],
  ["总库存覆盖天数", "total_cover_days"],
  ["预计断货日期", "estimated_stockout_date"],
  ["建议补货量", "recommended_replenishment_quantity"],
  ["建议动作", "recommended_action"],
  ["数据质量", "data_quality_status"],
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
  if (value === null || value === undefined || value === "") return "暂无";
  const number = Number(value);
  if (Number.isNaN(number)) return "暂无";
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
        <h2>AI 单品解读</h2>
        {data?.generated_at && <span>{new Date(data.generated_at).toLocaleString()}</span>}
      </div>
      {loading && <div className="state-line">正在生成 AI 单品解读...</div>}
      {!loading && error && <div className="error-line">{error}</div>}
      {!loading && !error && data?.configured === false && (
        <div className="state-line">AI 单品解读暂未配置。</div>
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
        setError(err.message || "SKU 详情加载失败");
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
        setAiError(err.message || "AI 单品解读加载失败");
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
          <h1>SKU 详情</h1>
          <p>{sellerSku}</p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>返回库存诊断</button>
      </div>

      {loading && <div className="state-line">正在加载 SKU 详情...</div>}
      {error && <div className="error-line">{error}</div>}
      {!loading && !error && !detail && <div className="empty-state">暂无数据</div>}

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
            <DetailItem label="断货风险">
              <RiskBadge value={detail.stockout_risk_level} />
            </DetailItem>
            <DetailItem label="滞销风险">
              <RiskBadge value={detail.overstock_risk_level} />
            </DetailItem>
          </div>

          <div className="intelligence-grid">
            <IntelligenceSection title="利润表现">
              <div className="mini-metric-grid">
                <DetailItem label="当前售价"><strong>{formatCurrency(detail.current_price)}</strong></DetailItem>
                <DetailItem label="综合到仓成本"><strong>{formatCurrency(detail.landed_cost)}</strong></DetailItem>
                <DetailItem label="毛利率"><strong>{formatPercent(detail.gross_margin)}</strong></DetailItem>
              </div>
            </IntelligenceSection>

            <IntelligenceSection title="补货策略">
              <div className="mini-metric-grid">
                <DetailItem label="总补货周期"><strong>{formatEmpty(detail.total_replenishment_lead_time_days)} 天</strong></DetailItem>
                <DetailItem label="目标覆盖天数"><strong>{formatEmpty(detail.target_cover_days)} 天</strong></DetailItem>
                <DetailItem label="安全库存天数"><strong>{formatEmpty(detail.safety_stock_days)} 天</strong></DetailItem>
                <DetailItem label="最小起订量"><strong>{formatEmpty(detail.moq)}</strong></DetailItem>
              </div>
            </IntelligenceSection>

            <IntelligenceSection title="决策依据">
              <div className="mini-metric-grid">
                <DetailItem label="断货风险分"><strong>{formatScore(detail.stockout_risk_score)}</strong></DetailItem>
                <DetailItem label="滞销风险分"><strong>{formatScore(detail.overstock_risk_score)}</strong></DetailItem>
                <DetailItem label="预估断货损失"><strong>{formatCurrency(detail.estimated_lost_revenue)}</strong></DetailItem>
                <DetailItem label="决策置信度"><strong>{formatPercent(detail.decision_confidence)}</strong></DetailItem>
              </div>
              <div className="decision-explanation">
                <span>系统判断说明</span>
                <p>{detail.decision_explanation || detail.action_reason || "暂无决策说明。"}</p>
              </div>
            </IntelligenceSection>
          </div>

          <section className="reason-panel">
            <h2>建议原因</h2>
            <p>{detail.action_reason || "暂无建议原因。"}</p>
          </section>

          <SkuAiPanel data={aiAnalysis} loading={aiLoading} error={aiError} />
        </div>
      )}
    </section>
  );
}

export default SkuDetail;
