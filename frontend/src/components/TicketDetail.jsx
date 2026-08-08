import { useState } from 'react';
import ConfidenceBar from './ConfidenceBar';
import { api } from '../api';

const ACTIONS = ['redelivery', 'partial_refund', 'full_refund', 'coupon', 'refund_reissue', 'escalation', 'apology_no_action'];

export default function TicketDetail({ ticket, order, onReviewChange }) {
  const [action, setAction] = useState(ticket.action || 'redelivery');
  const [note, setNote] = useState(ticket.review_note || '');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  if (!ticket) return null;

  const pip = ticket.pipeline || {};
  const isSubmitted = ticket.review_status === 'submitted';
  const isApproved = ticket.review_status === 'approved';

  const submit = async () => {
    setSaving(true);
    setMsg(null);
    try {
      await api.submitReview(ticket.ticket_id, { action, note });
      setMsg({ ok: true, text: 'Solution submitted for review. Approve below to apply it.' });
      onReviewChange && onReviewChange();
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setSaving(false);
    }
  };

  const approve = async () => {
    setSaving(true);
    setMsg(null);
    try {
      await api.approveReview(ticket.ticket_id);
      setMsg({ ok: true, text: 'Approved — solution applied, ticket passed.' });
      onReviewChange && onReviewChange();
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setSaving(false);
    }
  };

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
          <p><strong>Review:</strong> {ticket.review_status || '—'}</p>
        </div>
        <ConfidenceBar confidence={ticket.confidence} size="md" />
        <div className="pipeline-metrics">
          <div><span>Confidence</span><strong>{Math.round(ticket.confidence * 100)}%</strong></div>
          <div><span>Agreement</span><strong>{pip.agreement}/3</strong></div>
          <div><span>Threshold</span><strong>≥{Math.round((pip.threshold || 0) * 100)}%</strong></div>
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
              <span className="precedent-sim">CSAT {p.csat}/5</span>
            </div>
            <div className="precedent-desc">{p.description}</div>
            <div className="precedent-action">Action: {p.resolution_action.replace(/_/g, ' ')}</div>
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

      {!isApproved && (
        <div className="detail-section review-form">
          <h3>{isSubmitted ? 'Override submitted solution' : ticket.lane === 'auto' ? 'Override auto-resolved solution' : 'Human solution'}</h3>
          <div className="review-fields">
            <label className="review-label">
              Action
              <select value={action} onChange={(e) => setAction(e.target.value)} disabled={isSubmitted || saving}>
                {ACTIONS.map((a) => <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>)}
              </select>
            </label>
            <label className="review-label">
              Review note / solution
              <textarea
                rows={3}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                disabled={isSubmitted || saving}
                placeholder="Explain the resolution, refund amount, follow-up, etc."
              />
            </label>
          </div>
          {isSubmitted ? (
            <button className="btn approve" onClick={approve} disabled={saving}>
              {saving ? 'Applying…' : '✓ Approve & Pass'}
            </button>
          ) : (
            <button className="btn submit" onClick={submit} disabled={saving}>
              {saving ? 'Submitting…' : 'Submit for Review'}
            </button>
          )}
          {msg && <div className={`review-msg ${msg.ok ? 'ok' : 'err'}`}>{msg.text}</div>}
          {isSubmitted && (
            <div className="review-note-box">Submitted note: {ticket.review_note || note}</div>
          )}
        </div>
      )}
    </div>
  );
}