import RiskBadge from "./RiskBadge.jsx";

function InsightCard({ insight, onClick }) {
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
      <p>{insight.summary || "暂无问题概述"}</p>
      <div className="insight-metrics">
        <span>{insight.affected_sku_count || 0} SKUs</span>
        <span>{insight.task_count || 0} tasks</span>
      </div>
      <div className="insight-action">
        <span>Recommended action</span>
        <RiskBadge value={insight.recommended_action} />
      </div>
    </article>
  );
}

export default InsightCard;
