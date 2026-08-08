export default function TicketDetail({ ticket, order }) {
  if (!ticket) return null;

  return (
    <div className="detail-panel">
      <div className="detail-section">
        <h3>Ticket Details</h3>
        <p><strong>ID:</strong> {ticket.ticket_id}</p>
        <p><strong>Order:</strong> {ticket.order_id}</p>
        <p><strong>Description:</strong> {ticket.description}</p>
        <p><strong>Lane:</strong> <span className={`ticket-lane-badge ${ticket.lane === 'auto' ? 'auto-badge' : 'human-badge'}`}>{ticket.lane.toUpperCase()}</span></p>
        <p><strong>Action:</strong> <span className="ticket-action">{ticket.action || 'Pending human review'}</span></p>
        <p><strong>Confidence:</strong> {(ticket.confidence * 100).toFixed(1)}%</p>
      </div>

      {ticket.guardrail_flags.length > 0 && (
        <div className="detail-section">
          <h3>Guardrail Flags</h3>
          <div className="flags">
            {ticket.guardrail_flags.map((flag, i) => (
              <span key={i} className="flag">{flag}</span>
            ))}
          </div>
        </div>
      )}

      <div className="detail-section">
        <h3>Top Precedents</h3>
        {ticket.precedents.map((p, i) => (
          <div key={i} className="precedent-item">
            <div className="precedent-header">
              <span className="precedent-id">{p.ticket_id}</span>
              <span className="precedent-sim">Sim: {(p.similarity * 100).toFixed(1)}%</span>
            </div>
            <div className="precedent-desc">{p.description}</div>
            <div className="precedent-action">Action: {p.resolution_action} | CSAT: {p.csat}/5</div>
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
