import { useEffect, useState } from "react";
import { fetchInventoryAnalysis } from "../api/inventoryApi.js";
import InventoryTable from "../components/InventoryTable.jsx";

const riskOptions = ["", "critical", "high", "medium", "low", "unknown"];
const dataQualityOptions = [
  "",
  "complete",
  "missing_sales",
  "missing_config",
  "missing_inventory",
  "invalid_sales",
  "invalid_config",
];

function InventoryList({ reloadKey, onSelectSku }) {
  const [rows, setRows] = useState([]);
  const [filters, setFilters] = useState({
    stockout_risk_level: "",
    overstock_risk_level: "",
    data_quality_status: "",
    seller_sku: "",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadRows(nextFilters = filters) {
    setLoading(true);
    setError("");
    try {
      setRows(await fetchInventoryAnalysis(nextFilters));
    } catch (err) {
      setError(err.message || "库存分析数据加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRows();
  }, [reloadKey]);

  function updateFilter(name, value) {
    const nextFilters = { ...filters, [name]: value };
    setFilters(nextFilters);
    loadRows(nextFilters);
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>Inventory</h1>
          <p>SKU 级库存风险分析结果</p>
        </div>
        <div className="record-count">{rows.length} rows</div>
      </div>

      <div className="filter-bar">
        <input
          value={filters.seller_sku}
          onChange={(event) => updateFilter("seller_sku", event.target.value)}
          placeholder="搜索 SKU"
        />
        <select
          value={filters.stockout_risk_level}
          onChange={(event) => updateFilter("stockout_risk_level", event.target.value)}
        >
          {riskOptions.map((option) => (
            <option key={option} value={option}>{option || "断货风险"}</option>
          ))}
        </select>
        <select
          value={filters.overstock_risk_level}
          onChange={(event) => updateFilter("overstock_risk_level", event.target.value)}
        >
          {riskOptions.map((option) => (
            <option key={option} value={option}>{option || "滞销风险"}</option>
          ))}
        </select>
        <select
          value={filters.data_quality_status}
          onChange={(event) => updateFilter("data_quality_status", event.target.value)}
        >
          {dataQualityOptions.map((option) => (
            <option key={option} value={option}>{option || "数据质量"}</option>
          ))}
        </select>
      </div>

      {loading && <div className="state-line">Loading...</div>}
      {error && <div className="error-line">{error}</div>}
      {!loading && !error && <InventoryTable rows={rows} onSelectSku={onSelectSku} />}
    </section>
  );
}

export default InventoryList;
