import RiskBadge from "./RiskBadge.jsx";

function TaskCard({ task, onResolve, onIgnore, busy }) {
  const isDone = task.task_status === "resolved" || task.task_status === "ignored";

  return (
    <article className="task-card">
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
          <span>{task.approval_required ? "需要审批" : "无需审批"}</span>
        </div>
        <p>{task.task_description || "暂无任务描述"}</p>
        <div className="task-foot">
          <span>Risk: <RiskBadge value={task.risk_level} /></span>
          <span>{new Date(task.created_at).toLocaleString()}</span>
        </div>
      </div>
      <div className="task-actions">
        <button type="button" disabled={busy || isDone} onClick={() => onResolve(task.task_id)}>
          标记已解决
        </button>
        <button type="button" disabled={busy || isDone} onClick={() => onIgnore(task.task_id)}>
          忽略任务
        </button>
      </div>
    </article>
  );
}

export default TaskCard;
