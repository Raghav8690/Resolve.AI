const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson(url) {
  const res = await fetch(`${API_URL}${url}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const api = {
  getTickets: () => fetchJson('/api/tickets'),
  getTicket: (id) => fetchJson(`/api/tickets/${id}`),
  getBoard: () => fetchJson('/api/board'),
  processAll: () => fetchJson('/api/process', { method: 'POST' }),
};
