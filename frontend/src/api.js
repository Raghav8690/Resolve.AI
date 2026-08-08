const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson(url, opts) {
  const res = await fetch(`${API_URL}${url}`, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const api = {
  getTickets: () => fetchJson('/api/tickets'),
  getTicket: (id) => fetchJson(`/api/tickets/${id}`),
  getBoard: () => fetchJson('/api/board'),
  streamNext: () => fetchJson('/api/stream/next'),
};