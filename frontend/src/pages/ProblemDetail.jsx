import RiskBadge from "../components/RiskBadge.jsx";
import TaskCard from "../components/TaskCard.jsx";

function EmptyList({ children }) {
  return <div className="empty-state compact">{children}</div>;
}

function formatCurrency(value) {
  const number = Number(value || 0);
  return `$${number.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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
            <h1>问题详情</h1>
            <p>未选择风险问题卡片</p>
          </div>
          <button className="secondary-button" type="button" onClick={onBack}>返回运营待办</button>
        </div>
        <EmptyList>暂无数据</EmptyList>
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
          <p>库存 Agent 识别出的运营问题详情</p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>返回运营待办</button>
      </div>

      <div className="problem-summary-grid expanded">
        <div className="detail-item">
          <span>风险等级</span>
          <RiskBadge value={insight.risk_level} />
        </div>
        <div className="detail-item">
          <span>优先级</span>
          <RiskBadge value={insight.priority} />
        </div>
        <div className="detail-item">
          <span>影响等级</span>
          <RiskBadge value={impactLevel} />
        </div>
        <div className="detail-item">
          <span>预估影响金额</span>
          <strong>{formatCurrency(estimatedImpactValue)}</strong>
        </div>
        <div className="detail-item">
          <span>审批级别</span>
          <RiskBadge value={approval} />
        </div>
        <div className="detail-item">
          <span>涉及 SKU</span>
          <strong>{insight.affected_sku_count || 0}</strong>
        </div>
        <div className="detail-item">
          <span>关联待办</span>
          <strong>{insight.task_count || 0}</strong>
        </div>
      </div>

      <section className="problem-panel">
        <h2>问题概述</h2>
        <p>{insight.summary || "暂无问题概述。"}</p>
      </section>

      <section className="problem-panel">
        <h2>关联 SKU</h2>
        {insight.related_skus?.length ? (
          <div className="sku-chip-list">
            {insight.related_skus.map((sku) => <span key={sku}>{sku}</span>)}
          </div>
        ) : (
          <EmptyList>暂无关联 SKU</EmptyList>
        )}
      </section>

      <section className="problem-panel">
        <h2>关键数据</h2>
        <div className="key-data-grid">
          <div><span>建议动作</span><RiskBadge value={insight.recommended_action} /></div>
          <div><span>风险等级</span><RiskBadge value={insight.risk_level} /></div>
          <div><span>优先级</span><RiskBadge value={insight.priority} /></div>
          <div><span>影响等级</span><RiskBadge value={impactLevel} /></div>
          <div><span>预估影响金额</span><strong>{formatCurrency(estimatedImpactValue)}</strong></div>
          <div><span>审批级别</span><RiskBadge value={approval} /></div>
          <div><span>关联任务数</span><strong>{insight.related_task_ids?.length || 0}</strong></div>
        </div>
      </section>

      <section className="problem-panel">
        <h2>风险点</h2>
        {insight.risk_points?.length ? (
          <ul className="problem-list">
            {insight.risk_points.map((point) => <li key={point}>{point}</li>)}
          </ul>
        ) : (
          <EmptyList>暂无风险点</EmptyList>
        )}
      </section>

      <section className="problem-panel">
        <h2>AI 处理建议</h2>
        {insight.solution?.length ? (
          <ul className="problem-list">
            {insight.solution.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : (
          <EmptyList>暂无处理建议</EmptyList>
        )}
      </section>

      <section className="problem-panel">
        <h2>关联运营待办</h2>
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
          <EmptyList>暂无关联待办</EmptyList>
        )}
      </section>
    </section>
  );
}

export default ProblemDetail;
