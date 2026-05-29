import { useEffect, useState } from "react";
import { fetchSkuAnalysis } from "../api/inventoryApi.js";
import RiskBadge from "../components/RiskBadge.jsx";

const fields = [
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
  ["建议补货数量", "recommended_replenishment_quantity"],
  ["建议动作", "recommended_action"],
  ["数据质量状态", "data_quality_status"],
];

function formatValue(value) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number" && !Number.isInteger(value)) return value.toFixed(2);
  return value;
}

function SkuDetail({ sellerSku, onBack }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
    loadDetail();
  }, [sellerSku]);

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>SKU Detail</h1>
          <p>{sellerSku}</p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>返回 Inventory</button>
      </div>

      {loading && <div className="state-line">Loading...</div>}
      {error && <div className="error-line">{error}</div>}
      {!loading && !error && !detail && <div className="empty-state">暂无数据</div>}

      {!loading && detail && (
        <div className="detail-layout">
          <div className="detail-grid">
            {fields.map(([label, key]) => (
              <div className="detail-item" key={key}>
                <span>{label}</span>
                {["recommended_action", "data_quality_status"].includes(key) ? (
                  <RiskBadge value={detail[key]} />
                ) : (
                  <strong>{formatValue(detail[key])}</strong>
                )}
              </div>
            ))}
            <div className="detail-item">
              <span>断货风险</span>
              <RiskBadge value={detail.stockout_risk_level} />
            </div>
            <div className="detail-item">
              <span>滞销风险</span>
              <RiskBadge value={detail.overstock_risk_level} />
            </div>
          </div>
          <section className="reason-panel">
            <h2>建议原因</h2>
            <p>{detail.action_reason || "暂无建议原因"}</p>
          </section>
        </div>
      )}
    </section>
  );
}

export default SkuDetail;
