export default function TicketCard({ ticket, isSelected, onClick }) {
  return (
    <div 
      className={`ticket-card ${isSelected ? 'selected' : ''} ${ticket.lane === 'auto' ? 'auto-card' : 'human-card'}`}
      onClick={() => onClick(ticket.ticket_id)}
    >
      <div className="ticket-header">
        <span className="ticket-id">{ticket.ticket_id}</span>
        <span className={`ticket-lane-badge ${ticket.lane === 'auto' ? 'auto-badge' : 'human-badge'}`}>
          {ticket.lane === 'auto' ? 'AUTO' : 'HUMAN'}
        </span>
      </div>
      <div className="ticket-description">{ticket.description}</div>
      <div className="ticket-meta">
        {ticket.action && <span className="ticket-action">Action: {ticket.action}</span>}
        <span className="ticket-confidence">Confidence: {(ticket.confidence * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
