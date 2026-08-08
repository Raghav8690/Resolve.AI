import ConfidenceBar from './ConfidenceBar';

export default function TicketDetail({ ticket, order }) {
  if (!ticket) return null;

  const pip = ticket.pipeline || {};

  return (
    <div className="detail-panel">
      <div className="detail-section">
        <h3>Ticket Details</h3>
        <div className="detail-grid">
          <p><strong>ID:</strong> {ticket.ticket_id}</p>
          <p><strong>Order:</strong> {ticket.order_id}</p>
          <p><strong>Description:</strong> {ticket.description}</p>
          <p>
            <strong>Lane:</strong>{' '}
            <span className={`ticket-lane-badge ${ticket.lane === 'auto' ? 'auto-badge' : 'human-badge'}`}>
              {ticket.lane.toUpperCase()}
            </span>
          </p>
          <p><strong>Action:</strong> <span className="ticket-action">{ticket.action ? ticket.action.replace('_', ' ') : 'Pending human review'}</span></p>
          <p><strong>Status:</strong> {ticket.status}</p>
        </div>
        <ConfidenceBar confidence={ticket.confidence} size="md" />
        <div className="pipeline-metrics">
          <div><span>Avg match</span><strong>{Math.round((pip.avg_distinct_similarity || 0) * 100)}%</strong></div>
          <div><span>Closest precedent</span><strong>{Math.round((pip.top_similarity || 0) * 100)}%</strong></div>
          <div><span>Agreement</span><strong>{pip.agreement}/3</strong></div>
          <div><span>Threshold</span><strong>≥{pip.threshold}</strong></div>
          <div><span>Precedents</span><strong>{pip.matched}</strong></div>
        </div>
      </div>

      {order && (
        <div className="detail-section">
          <h3>Order Context</h3>
          <div className="detail-grid">
            <p><strong>Status:</strong> {order.delivery_status}</p>
            <p><strong>Value:</strong> ₹{order.value_inr}</p>
            <p><strong>Items:</strong> {order.items}</p>
            <p><strong>Delivery:</strong> {order.delivery_time_min} min</p>
          </div>
        </div>
      )}

      {ticket.guardrail_flags && ticket.guardrail_flags.length > 0 && (
        <div className="detail-section">
          <h3>Guardrail Flags</h3>
          <div className="flags">
            {ticket.guardrail_flags.map((flag, i) => (
              <span key={i} className="flag">{flag.replace(/_/g, ' ')}</span>
            ))}
          </div>
        </div>
      )}

      <div className="detail-section">
        <h3>Top Precedents (why)</h3>
        {ticket.precedents.map((p, i) => (
          <div key={i} className="precedent-item">
            <div className="precedent-header">
              <span className="precedent-id">{p.ticket_id}</span>
              <span className="precedent-sim">Sim: {(p.similarity * 100).toFixed(0)}%</span>
            </div>
            <div className="precedent-desc">{p.description}</div>
            <div className="precedent-action">Action: {p.resolution_action.replace(/_/g, ' ')} | CSAT: {p.csat}/5</div>
          </div>
        ))}
      </div>

      <div className="detail-section">
        <h3>Reasoning</h3>
        <div className="explanation-box">{ticket.explanation}</div>
      </div>

      {ticket.reply && (
        <div className="detail-section">
          <h3>Drafted Customer Reply</h3>
          <div className="reply-box">{ticket.reply}</div>
        </div>
      )}
    </div>
  );
}