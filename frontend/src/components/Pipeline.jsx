export default function Pipeline({ board }) {
  const steps = [
    { key: 'incoming', label: 'Incoming Queue', desc: 'new tickets pulled', color: '#607d8b' },
    { key: 'matched', label: 'TF-IDF Match', desc: 'top-3 precedents', color: '#5c6bc0' },
    { key: 'guardrail_checked', label: 'Order Guardrails', desc: 'refund cap / status', color: '#ffa726' },
    { key: 'llm_reply', label: 'LLM Reply Top', desc: 'drafted reply', color: '#26a69a' },
  ];

  const ps = (board && board.pipeline_steps) || {};
  const counts = {};
  steps.forEach((s) => {
    counts[s.key] = ps[s.key] !== undefined ? ps[s.key] : 0;
  });

  return (
    <div className="pipeline-row">
      {steps.map((s, i) => (
        <div key={s.key} className={`pipeline-step ${i < steps.length - 1 ? 'has-arrow' : ''}`}>
          <div className="pipeline-count" style={{ color: s.color }}>{counts[s.key]}</div>
          <div className="pipeline-label">{s.label}</div>
          <div className="pipeline-desc">{s.desc}</div>
        </div>
      ))}
    </div>
  );
}