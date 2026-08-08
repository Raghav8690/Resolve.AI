export default function ConfidenceBar({ confidence, size = 'md' }) {
  const pct = Math.round((confidence || 0) * 100);
  let color = '#43a047';
  if (pct < 60) color = '#e65100';
  else if (pct < 80) color = '#fb8c00';
  return (
    <div className={`conf ${size}`}>
      <div className="conf-label">Confidence <strong>{pct}%</strong></div>
      <div className="conf-track">
        <div className="conf-fill" style={{ width: `${pct}%`, background: color }}></div>
      </div>
    </div>
  );
}