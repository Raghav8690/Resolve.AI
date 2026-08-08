import ConfidenceBar from './ConfidenceBar';

const STATUS_COLOR = {
  'auto-resolved': '#2e7d32',
  'human-review': '#e65100',
};

export default function IncomingQueue({ tickets, onSelect, selectedId, processing }) {
  const sorted = [...tickets].sort((a, b) => (a.ticket_id < b.ticket_id ? -1 : 1));

  return (
    <div className="queue-panel">
      <div className="queue-header">
        <h3>Incoming Ticket Queue</h3>
        <div className="queue-badge">{sorted.length} new tickets</div>
      </div>
      <div className="queue-list">
        {sorted.map((t) => {
          const isSelected = t.ticket_id === selectedId;
          const isProcessing = processing && isSelected;
          const showStatus = t.status === 'auto-resolved' ? 'AUTO' : 'HUMAN';
          return (
            <div
              key={t.ticket_id}
              className={`queue-item ${isSelected ? 'selected' : ''} ${isProcessing ? 'processing' : ''}`}
              onClick={() => onSelect(t.ticket_id)}
            >
              <div className="queue-item-top">
                <span className="queue-ticket-id">{t.ticket_id}</span>
                <span className="queue-status" style={{ background: STATUS_COLOR[t.status] || '#666' }}>
                  {showStatus}
                </span>
              </div>
              <div className="queue-desc">{t.description}</div>
              <div className="queue-meta">
                <span>{t.order_id}</span>
                <span className="queue-action">{(t.action || 'pending review').replace('_', ' ')}</span>
              </div>
              <div className="queue-sim">
                <ConfidenceBar confidence={t.confidence} size="sm" />
                <span className="queue-agree">match {(t.pipeline?.avg_distinct_similarity || 0) * 100 >= 100 ? 100 : Math.round((t.pipeline?.avg_distinct_similarity || 0) * 100)}% · agree {t.pipeline?.agreement}/3</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}