import ConfidenceBar from './ConfidenceBar';

export default function TicketCard({ ticket, isSelected, onClick }) {
  const lane = ticket.lane === 'auto' ? 'AUTO' : 'HUMAN';
  const reason = ticket.pipeline?.reason || '';
  const agree = ticket.pipeline?.agreement || 0;

  return (
    <div
      className={`ticket-card ${isSelected ? 'selected' : ''} ${ticket.lane === 'auto' ? 'auto-card' : 'human-card'}`}
      onClick={() => onClick(ticket.ticket_id, 'lane')}
    >
      <div className="ticket-header">
        <span className="ticket-id">{ticket.ticket_id}</span>
        <span className={`ticket-lane-badge ${ticket.lane === 'auto' ? 'auto-badge' : 'human-badge'}`}>
          {lane}
        </span>
      </div>
      <div className="ticket-description">{ticket.description}</div>
      <div className="ticket-meta">
        <span className="ticket-action">{ticket.action ? ticket.action.replace('_', ' ') : 'For review'}</span>
        <span className="ticket-agree">agree {agree}/3</span>
      </div>
      <div className="ticket-conf">
        <ConfidenceBar confidence={ticket.confidence} size="sm" />
        <span className="ticket-conf-label">{Math.round(ticket.confidence * 100)}%</span>
      </div>
      {lane === 'AUTO' && reason && <div className="ticket-reason">{reason}</div>}
      {lane === 'HUMAN' && reason && (
        <div className="ticket-reason">{reason.split('|')[0].replace(/_/g, ' ')}</div>
      )}
    </div>
  );
}