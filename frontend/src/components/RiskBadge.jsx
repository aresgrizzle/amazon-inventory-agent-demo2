const labels = {
  critical: "critical",
  high: "high",
  medium: "medium",
  low: "low",
  unknown: "unknown",
  complete: "complete",
  missing_sales: "missing_sales",
  missing_config: "missing_config",
  missing_inventory: "missing_inventory",
  invalid_sales: "invalid_sales",
  invalid_config: "invalid_config",
  replenish_now: "replenish_now",
  prepare_replenishment: "prepare_replenishment",
  clearance_or_reduce_replenishment: "clearance_or_reduce",
  complete_missing_data: "complete_missing_data",
  keep_monitoring: "keep_monitoring",
  P0: "P0",
  P1: "P1",
  P2: "P2",
  P3: "P3",
  pending: "pending",
  resolved: "resolved",
  ignored: "ignored",
};

function RiskBadge({ value }) {
  const normalized = value || "unknown";
  return <span className={`risk-badge ${normalized}`}>{labels[normalized] || normalized}</span>;
}

export default RiskBadge;
