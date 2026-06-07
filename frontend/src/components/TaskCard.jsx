import RiskBadge from "./RiskBadge.jsx";

function formatCurrency(value) {
  const number = Number(value || 0);
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatEmpty(value) {
  return value === null || value === undefined || value === "" ? "-" : value;
}

function taskTitle(task) {
  const sku = task.seller_sku || "该 SKU";
  const quantity = task.action_parameters?.recommended_quantity || "";
  const titles = {
    stockout_warning: `${sku} 存在断货风险`,
    replenishment_suggestion: `${sku} 建议补货${quantity ? ` ${quantity} 件` : ""}`,
    overstock_warning: `${sku} 存在高库存/滞销风险`,
    unfulfillable_inventory_alert: `${sku} 存在不可售库存异常`,
    data_missing_alert: `${sku} 需要补全运营数据`,
  };
  return titles[task.task_type] || task.task_title || "运营待办";
}

function TaskCard({ task, onResolve, onIgnore, busy, readOnly = false }) {
  const isDone = task.task_status === "resolved" || task.task_status === "ignored";

  return (
    <article className={`task-card ${readOnly ? "read-only" : ""}`}>
      <div className="task-card-main">
        <div className="task-title-row">
          <h3>{taskTitle(task)}</h3>
          <div className="badge-row">
            <RiskBadge value={task.priority} />
            <RiskBadge value={task.task_status} />
          </div>
        </div>
        <div className="task-meta">
          <span>{task.seller_sku}</span>
          <span><RiskBadge value={task.task_type} /></span>
          <span><RiskBadge value={task.suggested_action} /></span>
          <span>{task.approval_required ? "需要审批" : "无需审批"}</span>
        </div>

        <div className="task-impact-grid">
          <div>
            <span>问题类型</span>
            <RiskBadge value={task.problem_type || "unknown"} />
          </div>
          <div>
            <span>影响等级</span>
            <RiskBadge value={task.impact_level || "unknown"} />
          </div>
          <div>
            <span>预估影响金额</span>
            <strong>{formatCurrency(task.estimated_impact_value)}</strong>
          </div>
          <div>
            <span>审批级别</span>
            <RiskBadge value={task.approval_level || "none"} />
          </div>
        </div>

        <p>{task.task_description || "暂无任务说明。"}</p>
        <div className="task-foot">
          <span>风险等级：<RiskBadge value={task.risk_level} /></span>
          <span>{new Date(task.created_at).toLocaleString()}</span>
        </div>
      </div>
      {!readOnly && (
        <div className="task-actions">
          <button type="button" disabled={busy || isDone} onClick={() => onResolve(task.task_id)}>
            标记已处理
          </button>
          <button type="button" disabled={busy || isDone} onClick={() => onIgnore(task.task_id)}>
            暂不处理
          </button>
        </div>
      )}
    </article>
  );
}

export default TaskCard;
