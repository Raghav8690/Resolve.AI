import { useState, useEffect, useMemo } from 'react';
import ConfidenceBar from './ConfidenceBar';
import TicketDetail from './TicketDetail';
import { api } from '../api';

const STATUS_COLOR = {
  'auto-resolved': '#2e7d32',
  'human-review': '#e65100',
  'review-submitted': '#ff8f00',
  'resolved': '#2e7d32',
};

export default function IncomingQueue({ tickets, onSelect, selectedId, selectedTicket, selectedOrder, processing, onReviewChange }) {
  const [query, setQuery] = useState('');
  const [minConf, setMinConf] = useState(0);
  const [maxConf, setMaxConf] = useState(100);
  const [lane, setLane] = useState('all');
  const [activeTags, setActiveTags] = useState([]);
  const [allTags, setAllTags] = useState([]);

  useEffect(() => {
    api.getReviewTags().then((r) => setAllTags(r.tags)).catch(() => {});
  }, []);

  const toggleTag = (tag) => {
    setActiveTags((prev) => (prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]));
  };

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return [...tickets]
      .filter((t) => Math.round(t.confidence * 100) >= minConf && Math.round(t.confidence * 100) <= maxConf)
      .filter((t) => lane === 'all' || t.lane === lane)
      .filter((t) => activeTags.length === 0 || (t.tags || []).some((tg) => activeTags.includes(tg)))
      .filter((t) => !q || `${t.ticket_id} ${t.description} ${(t.tags || []).join(' ')}`.toLowerCase().includes(q))
      .sort((a, b) => (a.ticket_id < b.ticket_id ? -1 : 1));
  }, [tickets, query, minConf, maxConf, lane, activeTags]);

  return (
    <div className="queue-panel">
      <div className="queue-header">
        <h3>Incoming Ticket Queue</h3>
        <div className="queue-badge">{filtered.length} / {tickets.length} tickets</div>
      </div>

      <div className="filter-bar">
        <input
          className="filter-input"
          placeholder="Search ticket id, description, tag…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="filter-row filter-range-row">
          <span className="filter-range-label">Confidence between</span>
          <input
            type="number"
            className="filter-number"
            min="0"
            max="100"
            value={minConf}
            onChange={(e) => setMinConf(Math.max(0, Math.min(100, Number(e.target.value) || 0)))}
            placeholder="min %"
          />
          <span className="filter-range-sep">and</span>
          <input
            type="number"
            className="filter-number-input"
            min="0"
            max="100"
            value={maxConf}
            onChange={(e) => setMaxConf(Math.max(0, Math.min(100, Number(e.target.value) || 100)))}
            placeholder="max %"
          />
          <span className="filter-range-unit">%</span>
          <select className="filter-select" value={lane} onChange={(e) => setLane(e.target.value)}>
            <option value="all">All lanes</option>
            <option value="auto">Auto-resolved</option>
            <option value="human">Human review</option>
            <option value="review">In review (override)</option>
          </select>
        </div>
        <div className="filter-tags">
          {allTags.map((tag) => (
            <button
              key={tag}
              className={`tag-chip ${activeTags.includes(tag) ? 'active' : ''}`}
              onClick={() => toggleTag(tag)}
            >
              {tag.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="queue-list">
        {filtered.length === 0 && <div className="empty">No tickets match the filters</div>}
        {filtered.map((t) => {
          const isSelected = t.ticket_id === selectedId;
          const isProcessing = processing && isSelected;
          const showStatus = t.status === 'auto-resolved' ? 'AUTO' : t.status === 'resolved' ? 'RESOLVED' : 'HUMAN';
          return (
            <div key={t.ticket_id}>
              <div
                className={`queue-item ${isSelected ? 'selected' : ''} ${isProcessing ? 'processing' : ''}`}
                onClick={() => onSelect(t.ticket_id, 'queue')}
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
                  <span className="queue-agree">{Math.round(t.confidence * 100)}% · agree {t.pipeline?.agreement ?? 0}/3</span>
                </div>
                {(t.tags || []).length > 0 && (
                  <div className="queue-tags">
                    {(t.tags || []).map((tg) => (
                      <span key={tg} className="mini-tag">{tg.replace(/_/g, ' ')}</span>
                    ))}
                  </div>
                )}
                {t.review_status === 'submitted' && (
                  <div className="queue-review-note">Review note: {t.review_note}</div>
                )}
              </div>
              {isSelected && selectedTicket && (
                <div className="card-detail">
                  <TicketDetail ticket={selectedTicket} order={selectedOrder} onReviewChange={() => onReviewChange && onReviewChange(selectedTicket.ticket_id, 'queue')} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}