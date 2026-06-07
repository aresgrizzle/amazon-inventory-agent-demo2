import RiskBadge from "./RiskBadge.jsx";

function formatCurrency(value) {
  const number = Number(value || 0);
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatEmpty(value) {
  return value === null || value === undefined || value === "" ? "-" : value;
}

function TaskCard({ task, onResolve, onIgnore, busy, readOnly = false }) {
  const isDone = task.task_status === "resolved" || task.task_status === "ignored";

  return (
    <article className={`task-card ${readOnly ? "read-only" : ""}`}>
      <div className="task-card-main">
        <div className="task-title-row">
          <h3>{task.task_title}</h3>
          <div className="badge-row">
            <RiskBadge value={task.priority} />
            <RiskBadge value={task.task_status} />
          </div>
        </div>
        <div className="task-meta">
          <span>{task.seller_sku}</span>
          <span>{task.task_type}</span>
          <span>{task.suggested_action}</span>
          <span>{task.approval_required ? "Approval required" : "No approval"}</span>
        </div>

        <div className="task-impact-grid">
          <div>
            <span>Problem</span>
            <strong>{formatEmpty(task.problem_type)}</strong>
          </div>
          <div>
            <span>Impact</span>
            <RiskBadge value={task.impact_level || "unknown"} />
          </div>
          <div>
            <span>Est. Value</span>
            <strong>{formatCurrency(task.estimated_impact_value)}</strong>
          </div>
          <div>
            <span>Approval</span>
            <strong>{formatEmpty(task.approval_level)}</strong>
          </div>
        </div>

        <p>{task.task_description || "No task description available."}</p>
        <div className="task-foot">
          <span>Risk: <RiskBadge value={task.risk_level} /></span>
          <span>{new Date(task.created_at).toLocaleString()}</span>
        </div>
      </div>
      {!readOnly && (
        <div className="task-actions">
          <button type="button" disabled={busy || isDone} onClick={() => onResolve(task.task_id)}>
            Mark resolved
          </button>
          <button type="button" disabled={busy || isDone} onClick={() => onIgnore(task.task_id)}>
            Ignore task
          </button>
        </div>
      )}
    </article>
  );
}

export default TaskCard;
