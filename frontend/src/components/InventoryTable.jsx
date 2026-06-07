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
    return <div className="empty-state">No data</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table inventory-table">
        <thead>
          <tr>
            <th>SKU</th>
            <th>ASIN</th>
            <th>Available</th>
            <th>Total</th>
            <th>Inbound</th>
            <th>7D Sales</th>
            <th>30D Sales</th>
            <th>Available Days</th>
            <th>Cover Days</th>
            <th>Stockout Date</th>
            <th>Stockout Risk</th>
            <th>Overstock Risk</th>
            <th>Gross Margin</th>
            <th>Sales Trend</th>
            <th>Decision Confidence</th>
            <th>Replenish Qty</th>
            <th>Action</th>
            <th>Data Quality</th>
            <th>Reason</th>
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
