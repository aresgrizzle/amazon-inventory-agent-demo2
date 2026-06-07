import RiskBadge from "./RiskBadge.jsx";

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (Number.isNaN(number)) return value;
  return Number.isInteger(number) ? number : number.toFixed(digits);
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (Number.isNaN(number)) return "-";
  const percent = Math.abs(number) <= 1 ? number * 100 : number;
  return `${percent.toFixed(1)}%`;
}

function InventoryTable({ rows, onSelectSku }) {
  if (!rows.length) {
    return <div className="empty-state">暂无数据</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table inventory-table">
        <thead>
          <tr>
            <th>SKU</th>
            <th>ASIN</th>
            <th>可售库存</th>
            <th>总库存</th>
            <th>有效在途</th>
            <th>7日均销</th>
            <th>30日均销</th>
            <th>可售天数</th>
            <th>覆盖天数</th>
            <th>预计断货日</th>
            <th>断货风险</th>
            <th>滞销风险</th>
            <th>毛利率</th>
            <th>销量趋势</th>
            <th>决策置信度</th>
            <th>建议补货量</th>
            <th>建议动作</th>
            <th>数据质量</th>
            <th>判断原因</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.seller_sku} onClick={() => onSelectSku(row.seller_sku)}>
              <td className="sku-cell">{row.seller_sku}</td>
              <td>{row.asin}</td>
              <td>{row.fulfillable_quantity}</td>
              <td>{row.total_quantity}</td>
              <td>{row.effective_inbound_quantity}</td>
              <td>{formatNumber(row.avg_daily_sales_7d)}</td>
              <td>{formatNumber(row.avg_daily_sales_30d)}</td>
              <td>{formatNumber(row.available_days)}</td>
              <td>{formatNumber(row.total_cover_days)}</td>
              <td>{row.estimated_stockout_date || "-"}</td>
              <td><RiskBadge value={row.stockout_risk_level} /></td>
              <td><RiskBadge value={row.overstock_risk_level} /></td>
              <td>{formatPercent(row.gross_margin)}</td>
              <td><RiskBadge value={row.sales_trend || "unknown"} /></td>
              <td>{formatPercent(row.decision_confidence)}</td>
              <td>{row.recommended_replenishment_quantity}</td>
              <td><RiskBadge value={row.recommended_action} /></td>
              <td><RiskBadge value={row.data_quality_status} /></td>
              <td className="reason-cell">{row.action_reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default InventoryTable;
