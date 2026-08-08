const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson(url, opts) {
  const res = await fetch(`${API_URL}${url}`, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function qs(params) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p.set(k, v);
  });
  const s = p.toString();
  return s ? `?${s}` : '';
}

export const api = {
  getTickets: (params = {}) => fetchJson(`/api/tickets${qs(params)}`),
  getTicket: (id) => fetchJson(`/api/tickets/${id}`),
  getBoard: () => fetchJson('/api/board'),
  streamNext: () => fetchJson('/api/stream/next'),
  getReviewQueue: (params = {}) => fetchJson(`/api/review/queue${qs(params)}`),
  getReviewTags: () => fetchJson('/api/review/tags'),
  submitReview: (id, body) => fetchJson(`/api/review/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
  approveReview: (id) => fetchJson(`/api/review/${id}/approve`, { method: 'POST' }),
};