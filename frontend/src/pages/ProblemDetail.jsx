import RiskBadge from "../components/RiskBadge.jsx";
import TaskCard from "../components/TaskCard.jsx";

function EmptyList({ children }) {
  return <div className="empty-state compact">{children}</div>;
}

function ProblemDetail({ insight, onBack }) {
  if (!insight) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h1>Problem Detail</h1>
            <p>未选择风险问题</p>
          </div>
          <button className="secondary-button" type="button" onClick={onBack}>返回 Tasks</button>
        </div>
        <EmptyList>暂无数据</EmptyList>
      </section>
    );
  }

  const relatedTasks = insight.related_tasks || [];

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>{insight.title}</h1>
          <p>Agent 风险问题详情</p>
        </div>
        <button className="secondary-button" type="button" onClick={onBack}>返回 Tasks</button>
      </div>

      <div className="problem-summary-grid">
        <div className="detail-item">
          <span>风险等级</span>
          <RiskBadge value={insight.risk_level} />
        </div>
        <div className="detail-item">
          <span>优先级</span>
          <RiskBadge value={insight.priority} />
        </div>
        <div className="detail-item">
          <span>涉及 SKU</span>
          <strong>{insight.affected_sku_count || 0}</strong>
        </div>
        <div className="detail-item">
          <span>关联任务</span>
          <strong>{insight.task_count || 0}</strong>
        </div>
      </div>

      <section className="problem-panel">
        <h2>问题概述</h2>
        <p>{insight.summary || "暂无问题概述"}</p>
      </section>

      <section className="problem-panel">
        <h2>涉及 SKU 列表</h2>
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
          <div><span>Recommended action</span><RiskBadge value={insight.recommended_action} /></div>
          <div><span>Risk level</span><RiskBadge value={insight.risk_level} /></div>
          <div><span>Priority</span><RiskBadge value={insight.priority} /></div>
          <div><span>Task IDs</span><strong>{insight.related_task_ids?.length || 0}</strong></div>
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
        <h2>AI 解决方案</h2>
        {insight.solution?.length ? (
          <ul className="problem-list">
            {insight.solution.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : (
          <EmptyList>暂无解决方案</EmptyList>
        )}
      </section>

      <section className="problem-panel">
        <h2>关联任务列表</h2>
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
          <EmptyList>暂无关联任务</EmptyList>
        )}
      </section>
    </section>
  );
}

export default ProblemDetail;
