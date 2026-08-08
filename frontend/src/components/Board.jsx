import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';
import TicketCard from './TicketCard';
import TicketDetail from './TicketDetail';
import Pipeline from './Pipeline';
import IncomingQueue from './IncomingQueue';
import LiveFeed, { PIPELINE_STEPS } from './LiveFeed';
import Loading from './Loading';

const STEP_DELAY = 900;

export default function Board() {
  const [tickets, setTickets] = useState([]);
  const [board, setBoard] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const [liveTrace, setLiveTrace] = useState(null);
  const [liveStep, setLiveStep] = useState(PIPELINE_STEPS[0]);
  const [liveTicket, setLiveTicket] = useState(null);
  const streamBusy = useRef(false);
  const timers = useRef([]);

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

  // 10s tick: pull ONE new ticket from the stream and animate it step-by-step
  const handleTick = useCallback(async () => {
    if (streamBusy.current) return;
    streamBusy.current = true;
    try {
      const next = await api.streamNext();
      if (next.done) return;
      setLiveTicket(next.ticket_id);
      setLiveTrace(next.trace);
      setLiveStep(PIPELINE_STEPS[0]);
      for (let i = 0; i < PIPELINE_STEPS.length; i++) {
        timers.current.push(setTimeout(() => setLiveStep(PIPELINE_STEPS[i]), i * STEP_DELAY));
      }
    } catch (e) {
      setError('Stream error: ' + e.message);
    } finally {
      streamBusy.current = false;
    }
  }, []);

  useEffect(() => {
    loadData().finally(() => setLoading(false));
    handleTick();
    const tick = setInterval(() => {
      loadData();
      handleTick();
    }, 10000);
    return () => {
      clearInterval(tick);
      timers.current.forEach(clearTimeout);
    };
  }, [loadData, handleTick]);

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
  const selectedId = selectedTicket?.ticket_id || (loading ? null : selectedTicket?.ticket_id);

  return (
    <div className="container">
      <header className="header">
        <div>
          <h1>Resolve.AI</h1>
          <div className="header-sub">Precedent-driven support resolution · Zepto</div>
        </div>
        <div className="header-right">
          <span className="live-indicator"><span className="live-dot"></span> STREAMING</span>
          <span className="last-updated">1 new ticket every 10s</span>
        </div>
      </header>

      {error && <div className="error-banner">⚠ {error}</div>}

      {!loading && board && (
        <section className="section">
          <h2 className="section-title">Decision Pipeline</h2>
          <Pipeline board={board} />
        </section>
      )}

      {liveTrace && (
        <section className="section">
          <div className="livefeed-wrap">
            <div className="livefeed-ticket">
              <span className="livefeed-badge">PROCESSING</span>
              <strong>{liveTicket}</strong>
              <span className="livefeed-tick">next in queue</span>
            </div>
            <LiveFeed trace={liveTrace} currentStep={liveStep} />
          </div>
        </section>
      )}

      {!loading && (
        <section className="section">
          <div className="section-head">
            <h2 className="section-title">Incoming Queue</h2>
            <div className="queue-summary">
              <span className="stat mini" style={{ color: '#2e7d32' }}>{board ? board.auto_resolved : 0} auto</span>
              <span className="stat mini" style={{ color: '#e65100' }}>{board ? board.human_review : 0} human</span>
              <span className="stat mini" style={{ color: '#666' }}>{board && board.pipeline_steps ? board.pipeline_steps.pending : 0} pending</span>
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
              {autoTickets.length === 0 ? <div className="empty">No auto-resolved tickets yet</div> : (
                autoTickets.map((t) => (
                  <TicketCard key={t.ticket_id} ticket={t} isSelected={t.ticket_id === selectedId} onClick={selectTicket} />
                ))
              )}
            </div>
          </div>

          <div className="lane human-lane">
            <div className="lane-header">Human Review ({humanTickets.length})</div>
            <div className="ticket-list">
              {humanTickets.length === 0 ? <div className="empty">No human review tickets yet</div> : (
                humanTickets.map((t) => (
                  <TicketCard key={t.ticket_id} ticket={t} isSelected={t.ticket_id === selectedId} onClick={selectTicket} />
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