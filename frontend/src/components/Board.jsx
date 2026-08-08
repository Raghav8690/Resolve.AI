import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';
import TicketCard from './TicketCard';
import TicketDetail from './TicketDetail';
import Pipeline from './Pipeline';
import IncomingQueue from './IncomingQueue';
import ConfidenceBar from './ConfidenceBar';
import Loading from './Loading';

export default function Board() {
  const [tickets, setTickets] = useState([]);
  const [board, setBoard] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [ticketsData, boardData] = await Promise.all([api.getTickets(), api.getBoard()]);
      setTickets(ticketsData);
      setBoard(boardData);
      setError(null);
    } catch (e) {
      setError(`Failed to reach backend at ${import.meta.env.VITE_API_URL}`);
    }
  }, []);

  useEffect(() => {
    loadData().finally(() => setLoading(false));
    const timer = setInterval(loadData, 10000);
    return () => clearInterval(timer);
  }, [loadData]);

  const selectTicket = useCallback(async (id) => {
    setProcessing(true);
    try {
      const detail = await api.getTicket(id);
      setSelectedTicket(detail.ticket);
      setSelectedOrder(detail.order_context);
    } catch (e) {
      console.error('Failed to load detail', e);
    } finally {
      setTimeout(() => setProcessing(false), 400);
    }
  }, []);

  const autoTickets = tickets.filter((t) => t.lane === 'auto');
  const humanTickets = tickets.filter((t) => t.lane === 'human');
  const selectedId = selectedTicket?.ticket_id || loading ? null : selectedTicket?.ticket_id;

  const boardConf = board?.auto_resolved !== undefined;

  return (
    <div className="container">
      <header className="header">
        <div>
          <h1>Resolve.AI</h1>
          <div className="header-sub">Precedent-driven support resolution · Zepto</div>
        </div>
        <div className="header-right">
          <span className="live-indicator"><span className="live-dot"></span> LIVE</span>
          <span className="last-updated">auto-refreshes every 10s</span>
        </div>
      </header>

      {error && <div className="error-banner">⚠ {error}</div>}

      {!loading && board && (
        <section className="section">
          <h2 className="section-title">Decision Pipeline</h2>
          <Pipeline board={board} />
        </section>
      )}

      {!loading && (
        <section className="section">
          <div className="section-head">
            <h2 className="section-title">Incoming Queue</h2>
            <div className="queue-summary">
              <span className="stat mini" style={{ color: '#2e7d32' }}>{board ? board.auto_resolved : 0} auto</span>
              <span className="stat mini" style={{ color: '#e65100' }}>{board ? board.human_review : 0} human</span>
            </div>
          </div>
          <IncomingQueue tickets={tickets} onSelect={selectTicket} selectedId={selectedId} processing={processing} />
        </section>
      )}

      <section className="section">
        <h2 className="section-title">Two-Lane Board</h2>
        <div className="board">
          <div className="lane auto-lane">
            <div className="lane-header">Auto-Resolved ({autoTickets.length})</div>
            <div className="ticket-list">
              {autoTickets.length === 0 ? <div className="empty">No auto-resolved tickets</div> : (
                autoTickets.map((t) => (
                  <TicketCard
                    key={t.ticket_id}
                    ticket={t}
                    isSelected={t.ticket_id === selectedId}
                    onClick={selectTicket}
                  />
                ))
              )}
            </div>
          </div>

          <div className="lane human-lane">
            <div className="lane-header">Human Review ({humanTickets.length})</div>
            <div className="ticket-list">
              {humanTickets.length === 0 ? <div className="empty">No human review tickets</div> : (
                humanTickets.map((t) => (
                  <TicketCard
                    key={t.ticket_id}
                    ticket={t}
                    isSelected={t.ticket_id === selectedId}
                    onClick={selectTicket}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </section>

      <TicketDetail ticket={selectedTicket} order={selectedOrder} />
    </div>
  );
}