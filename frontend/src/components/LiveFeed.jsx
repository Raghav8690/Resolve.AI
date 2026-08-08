import { useState } from 'react';
import ConfidenceBar from './ConfidenceBar';

export const PIPELINE_STEPS = ['step1_vectorize', 'step2_cosine', 'step3_top3', 'step4_confidence', 'step5_guardrail', 'step6_route'];

const STEP_TITLES = {
  step1_vector: '1 · TF-IDF Vectorize',
  step2_cosine: '2 · Cosine vs Resolved DB',
  step3_top3: '3 · Top-3 Retrieval',
  step4_confidence: '4 · Confidence Score',
  step5_guardrail: '5 · Order Guardrails',
  step6_route: '6 · Route Decision',
};

export default function LiveFeed({ trace, currentStep }) {
  const idx = PIPELINE_STEPS.indexOf(currentStep);

  return (
    <div className="livefeed">
      <div className="livefeed-steps">
        {PIPELINE_STEPS.map((key, i) => {
          const data = (trace || {})[key] || {};
          const isCurrent = i === idx;
          const isDone = idx > i && !isCurrent;
          return (
            <div key={key} className={`lf-step ${isCurrent ? 'current' : ''} ${isDone ? 'done' : ''} ${idx < i ? 'future' : ''}`}>
              <div className="lf-step-head">
                <span className={`lf-dot ${isDone ? 'ok' : isCurrent ? 'spin' : ''}`}>{isDone ? '✓' : ''}</span>
                <span className="lf-title">{STEP_TITLES[key]}</span>
              </div>
              {isCurrent && <StepContent stepKey={key} data={data} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StepContent({ stepKey, data }) {
  if (stepKey === 'step1_vector') {
    const tokens = Object.entries(data.tokens || {});
    return (
      <div className="lf-body">
        <div className="lf-ish-meta">
          <div className="lf-stat"><span>tokens</span><strong>{data.num_tokens}</strong></div>
          <div className="lf-stat"><span>vector dim</span><strong>{data.vector_dim}</strong></div>
        </div>
        <div className="lf-token-cloud">
          {tokens.map(([tok, w]) => (
            <span key={tok} className="lf-token" style={{ fontSize: `${Math.min(12 + w * 12, 22)}px` }}>{tok}</span>
          ))}
          {tokens.length === 0 && <span className="lf-note">query had no matching vocabulary</span>}
        </div>
      </div>
    );
  }
  if (stepKey === 'step2_cosine') {
    const topK = data.top_k || [];
    return (
      <div className="lf-body">
        <div className="lf-ish-meta">
          <div className="lf-stat"><span>pool</span><strong>{data.pool_size}</strong></div>
          <div className="lf-stat"><span>top sim</span><strong>{(data.top_similarity * 100).toFixed(0)}%</strong></div>
        </div>
        <div className="lf-ranks">
          {topK.slice(0, 3).map((p, i) => (
            <div key={i} className="lf-rank">
              <span className="lf-rank-id">{p.ticket_id}</span>
              <div className="lf-rank-bar"><div className="lf-rank-fill" style={{ width: `${Math.round(p.similarity * 100)}%` }} /></div>
              <span className="lf-rank-score">{(p.similarity * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  if (stepKey === 'step3_top3') {
    const topk = data.precedents || [];
    return (
      <div className="lf-body">
        <div className="lf-precedents">
          {topk.map((p, i) => (
            <div key={i} className="lf-prec">
              <div className="lf-prec-line"><span className="lf-prec-id">{p.ticket_id}</span><span className="lf-prec-sim">{(p.similarity * 100).toFixed(0)}%</span></div>
              <div className="lf-prec-desc">{p.description}</div>
              <div className="lf-prec-meta">{p.resolution_action.replace('_', ' ')} · CSAT {p.csat}/5</div>
            </div>
          ))}
        </div>
        <div className="lf-stat center"><span>agreement</span><strong>{data.agree_count}/3</strong></div>
      </div>
    );
  }
  if (stepKey === 'step4_confidence') {
    return (
      <div className="lf-body">
        <ConfidenceBar confidence={data.confidence} size="md" />
        <div className="lf-ish-meta">
          <div className="lf-stat"><span>similarity</span><strong>{(data.top_similarity * 100).toFixed(0)}%</strong></div>
          <div className="lf-stat"><span>agreement</span><strong>{data.agreement}/3</strong></div>
          <div className="lf-stat"><span>formula</span><strong className="sm">{data.formula}</strong></div>
        </div>
      </div>
    );
  }
  if (stepKey === 'step5_guardrail') {
    const flags = data.flags || [];
    return (
      <div className="lf-body">
        <div className="lf-ish-meta">
          <div className="lf-stat"><span>order</span><strong>{data.order_status}</strong></div>
          <div className="lf-stat"><span>value</span><strong>₹{data.order_value}</strong></div>
        </div>
        <div className="flags">
          {flags.length === 0 ? <span className="flag pass">PASS — order constraints satisfied</span> : flags.map((f, i) => <span key={i} className="flag">{f.replace(/_/g, ' ')}</span>)}
        </div>
      </div>
    );
  }
  if (stepKey === 'step6_route') {
    const auto = data.lane === 'auto';
    return (
      <div className="lf-body">
        <div className={`lf-route ${auto ? 'auto' : 'human'}`}>
          <strong>{auto ? '⟶ AUTO-RESOLVE' : '⟶ HUMAN REVIEW'}</strong>
          {data.action && <span className="lf-action">{data.action.replace('_', ' ')}</span>}
        </div>
        <div className="lf-reason">{(data.reason || '').split('|')[0].replace(/_/g, ' ')}</div>
      </div>
    );
  }
  return null;
}