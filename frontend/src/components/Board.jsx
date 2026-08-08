import { useState, useEffect } from 'react';
import { api } from '../api';
import TicketCard from './TicketCard';
import TicketDetail from './TicketDetail';
import Loading from './Loading';

export default function Board() {
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [summary, setSummary] = useState({ auto_resolved: 0, human_review: 0, total: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [ticketsData, summaryData] = await Promise.all([
        api.getTickets(),
        api.getBoard()
      ]);
      setTickets(ticketsData);
      setSummary(summaryData);
    } catch (e) {
      console.error('Failed to load data', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleTicketClick(ticketId) {
    try {
      const detail = await api.getTicket(ticketId);
      setSelectedTicket(detail.ticket);
      setSelectedOrder(detail.order_context);
    } catch (e) {
      console.error('Failed to load ticket detail', e);
    }
  }

  const autoTickets = tickets.filter(t => t.lane === 'auto');
  const humanTickets = tickets.filter(t => t.lane === 'human');

  if (loading) return <Loading />;

  return (
    <div className="container">
      <header className="header">
        <h1>Resolve.AI</h1>
        <div className="summary">
          <div className="stat">
            <div className="stat-value">{summary.auto_resolved}</div>
            <div className="stat-label">Auto-Resolved</div>
          </div>
          <div className="stat">
            <div className="stat-value">{summary.human_review}</div>
            <div className="stat-label">Human Review</div>
          </div>
          <div className="stat">
            <div className="stat-value">{summary.total}</div>
            <div className="stat-label">Total</div>
          </div>
        </div>
      </header>

      <div className="board">
        <div className="lane auto-lane">
          <div className="lane-header">Auto-Resolved ({autoTickets.length})</div>
          <div className="ticket-list">
            {autoTickets.length === 0 ? <div className="empty">No auto-resolved tickets</div> : (
              autoTickets.map(t => (
                <TicketCard key={t.ticket_id} ticket={t} isSelected={selectedTicket?.ticket_id === t.ticket_id} onClick={handleTicketClick} />
              ))
            )}
          </div>
        </div>

        <div className="lane human-lane">
          <div className="lane-header">Human Review ({humanTickets.length})</div>
          <div className="ticket-list">
            {humanTickets.length === 0 ? <div className="empty">No human review tickets</div> : (
              humanTickets.map(t => (
                <TicketCard key={t.ticket_id} ticket={t} isSelected={selectedTicket?.ticket_id === t.ticket_id} onClick={handleTicketClick} />
              ))
            )}
          </div>
        </div>
      </div>

      <TicketDetail ticket={selectedTicket} order={selectedOrder} />
    </div>
  );
}
