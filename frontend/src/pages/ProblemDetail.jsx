import RiskBadge from "../components/RiskBadge.jsx";
import TaskCard from "../components/TaskCard.jsx";

function EmptyList({ children }) {
  return <div className="empty-state compact">{children}</div>;
}

function formatCurrency(value) {
  const number = Number(value || 0);
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  const number = Number(value);
  if (Number.isNaN(number)) return "N/A";
  const percent = Math.abs(number) <= 1 ? number * 100 : number;
  return `${percent.toFixed(1)}%`;
}

function highestImpactLevel(tasks) {
  const order = { high: 3, medium: 2, low: 1, none: 0, unknown: 0 };
  return tasks.reduce((best, task) => {
    const current = task.impact_level || "unknown";
    return (order[current] || 0) > (order[best] || 0) ? current : best;
  }, "unknown");
}

function approvalLevel(tasks) {
  const order = { owner: 4, manager: 3, operator: 2, none: 1 };
  return tasks.reduce((best, task) => {
    const current = task.approval_level || "none";
    return (order[current] || 0) > (order[best] || 0) ? current : best;
  }, "none");
}

function ProblemDetail({ insight, onBack }) {
  if (!insight) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h1>Problem Detail</h1>
            <p>No risk insight selected</p>
          </div>
          <button className="secondary-button" type="button" onClick={onBack}>Back to Tasks</button>
        </div>
        <EmptyList>No data</EmptyList>
      </section>
    );
  }

  const relatedTasks = insight.related_tasks || [];
  const estimatedImpactValue = relatedTasks.reduce(
    (total, task) => total + Number(task.estimated_impact_value || 0),
    0
  );
  const impactLevel = highestImpactLevel(relatedTasks);
  const approval = approvalLevel(relatedTasks);

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>{insight.title}</h1>
          <p>Agent risk problem detail</p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>Back to Tasks</button>
      </div>

      <div className="problem-summary-grid expanded">
        <div className="detail-item">
          <span>Risk Level</span>
          <RiskBadge value={insight.risk_level} />
        </div>
        <div className="detail-item">
          <span>Priority</span>
          <RiskBadge value={insight.priority} />
        </div>
        <div className="detail-item">
          <span>Impact Level</span>
          <RiskBadge value={impactLevel} />
        </div>
        <div className="detail-item">
          <span>Estimated Impact</span>
          <strong>{formatCurrency(estimatedImpactValue)}</strong>
        </div>
        <div className="detail-item">
          <span>Approval Level</span>
          <strong>{approval}</strong>
        </div>
        <div className="detail-item">
          <span>Affected SKUs</span>
          <strong>{insight.affected_sku_count || 0}</strong>
        </div>
        <div className="detail-item">
          <span>Related Tasks</span>
          <strong>{insight.task_count || 0}</strong>
        </div>
      </div>

      <section className="problem-panel">
        <h2>Problem Summary</h2>
        <p>{insight.summary || "No problem summary available."}</p>
      </section>

      <section className="problem-panel">
        <h2>Related SKUs</h2>
        {insight.related_skus?.length ? (
          <div className="sku-chip-list">
            {insight.related_skus.map((sku) => <span key={sku}>{sku}</span>)}
          </div>
        ) : (
          <EmptyList>No related SKUs</EmptyList>
        )}
      </section>

      <section className="problem-panel">
        <h2>Key Data</h2>
        <div className="key-data-grid">
          <div><span>Recommended action</span><RiskBadge value={insight.recommended_action} /></div>
          <div><span>Risk level</span><RiskBadge value={insight.risk_level} /></div>
          <div><span>Priority</span><RiskBadge value={insight.priority} /></div>
          <div><span>Impact level</span><RiskBadge value={impactLevel} /></div>
          <div><span>Estimated impact</span><strong>{formatCurrency(estimatedImpactValue)}</strong></div>
          <div><span>Approval level</span><strong>{approval}</strong></div>
          <div><span>Task IDs</span><strong>{insight.related_task_ids?.length || 0}</strong></div>
          <div><span>Avg confidence</span><strong>{formatPercent(null)}</strong></div>
        </div>
      </section>

      <section className="problem-panel">
        <h2>Risk Points</h2>
        {insight.risk_points?.length ? (
          <ul className="problem-list">
            {insight.risk_points.map((point) => <li key={point}>{point}</li>)}
          </ul>
        ) : (
          <EmptyList>No risk points</EmptyList>
        )}
      </section>

      <section className="problem-panel">
        <h2>AI Solution</h2>
        {insight.solution?.length ? (
          <ul className="problem-list">
            {insight.solution.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : (
          <EmptyList>No solution available</EmptyList>
        )}
      </section>

      <section className="problem-panel">
        <h2>Related Tasks</h2>
        {relatedTasks.length ? (
          <div className="task-list">
            {relatedTasks.map((task) => (
              <TaskCard
                key={task.task_id}
                task={task}
                busy={false}
                readOnly
              />
            ))}
          </div>
        ) : (
          <EmptyList>No related tasks</EmptyList>
        )}
      </section>
    </section>
  );
}

export default ProblemDetail;
