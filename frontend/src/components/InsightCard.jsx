import RiskBadge from "./RiskBadge.jsx";

function formatCurrency(value) {
  const number = Number(value || 0);
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function topTaskValue(insight, field) {
  const tasks = insight.related_tasks || [];
  return tasks.find((task) => task?.[field])?.[field] || insight[field];
}

function InsightCard({ insight, onClick }) {
  const impactLevel = topTaskValue(insight, "impact_level") || "unknown";
  const estimatedImpactValue = topTaskValue(insight, "estimated_impact_value") || 0;
  const approvalLevel = topTaskValue(insight, "approval_level") || "none";

  function handleKeyDown(event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick();
    }
  }

  return (
    <article className="insight-card" onClick={onClick} onKeyDown={handleKeyDown} role="button" tabIndex={0}>
      <div className="insight-card-top">
        <h3>{insight.title}</h3>
        <div className="badge-row">
          <RiskBadge value={insight.risk_level} />
          <RiskBadge value={insight.priority} />
        </div>
      </div>
      <p>{insight.summary || "No problem summary available."}</p>
      <div className="insight-metrics">
        <span>{insight.affected_sku_count || 0} SKUs</span>
        <span>{insight.task_count || 0} tasks</span>
      </div>
      <div className="insight-impact-row">
        <div>
          <span>Impact</span>
          <RiskBadge value={impactLevel} />
        </div>
        <div>
          <span>Est. Value</span>
          <strong>{formatCurrency(estimatedImpactValue)}</strong>
        </div>
        <div>
          <span>Approval</span>
          <strong>{approvalLevel}</strong>
        </div>
      </div>
      <div className="insight-action">
        <span>Recommended action</span>
        <RiskBadge value={insight.recommended_action} />
      </div>
    </article>
  );
}

export default InsightCard;
