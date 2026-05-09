import { useEffect, useState } from 'react';

const phases = [
  { key: 'connecting', label: 'Connecting analytics...' },
  { key: 'crawling', label: 'Scanning page...' },
  { key: 'diagnosing', label: 'Finding pain points...' },
  { key: 'generating', label: 'Drafting two variants...' },
  { key: 'testing', label: 'Running simulated A/B test...' },
];

export function ResultPanel({ phase, result, error, winner, onOpenReport, onReset }) {
  if (phase === 'idle') {
    return (
      <div className="result-panel empty-state">
        <p className="panel-kicker">Ready</p>
        <h2>Paste a URL to get started.</h2>
        <p>auto-ab connects to your analytics, simulates visitor behavior, drafts two variants, and runs the A/B test for you.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="result-panel">
        <p className="panel-kicker danger">Error</p>
        <h2>{error}</h2>
        <button className="button secondary" onClick={onReset} type="button">Try again</button>
      </div>
    );
  }

  const showProgress = ['connecting', 'crawling', 'diagnosing', 'generating'].includes(phase);
  if (showProgress) {
    return (
      <div className="result-panel">
        <p className="panel-kicker">Loop running</p>
        <div className="phase-list" aria-live="polite">
          {phases.map((item) => (
            <div className={`phase-row ${phase === item.key ? 'active' : ''} ${isComplete(phase, item.key) ? 'complete' : ''}`} key={item.key}>
              <span className="phase-dot" />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!result) return null;

  const variants = result.variants || [];
  const isTesting = phase === 'testing';
  const isDone = phase === 'done';

  return (
    <div className="result-panel result-final">
      <div className="result-header">
        <div>
          <p className="panel-kicker">{isDone ? 'Test complete' : 'Running A/B test'}</p>
          <h2>{result.url}</h2>
        </div>
        {isDone ? <span className="uplift-chip">Winner: Variant {winner}</span> : null}
      </div>

      <div className="pain-list">
        {result.painPoints.map((point) => (
          <article className="pain-item" key={`${point.section}-${point.type}`}>
            <div>
              <strong>{point.type}</strong>
              <span>{point.section}</span>
            </div>
            <p>{point.desc}</p>
            <span className={`severity ${point.severity}`}>{point.severity}</span>
          </article>
        ))}
      </div>

      <div className="diff-grid three">
        <VariantCard label="A · Baseline" model={result.baseline} tone="warning" />
        {variants.map((variant) => (
          <VariantCard
            key={variant.label}
            label={`${variant.label} · ${variant.hypothesis}`}
            model={variant}
            tone="success"
            uplift={isTesting ? <LiftBar target={variant.liftPct} /> : variant.uplift}
            isWinner={isDone && winner === variant.label}
          />
        ))}
      </div>

      {isDone ? (
        <div className="action-row">
          <button className="button primary" onClick={onOpenReport} type="button">View benchmark report</button>
          <button className="button secondary" onClick={onReset} type="button">Run loop again</button>
        </div>
      ) : null}
    </div>
  );
}

function VariantCard({ label, model, tone, uplift, isWinner }) {
  return (
    <article className={`variant-card ${tone}${isWinner ? ' is-winner' : ''}`}>
      <div className="variant-topline">
        <span>{label}</span>
        <strong>Score: {model.score}</strong>
      </div>
      <blockquote>{model.headline}</blockquote>
      <p>CVR: {model.cvr}</p>
      {uplift ? <span className="uplift-mini">{uplift}</span> : null}
      {model.changes ? (
        <ul>
          {model.changes.map((change) => <li key={change}>{change}</li>)}
        </ul>
      ) : null}
    </article>
  );
}

function LiftBar({ target }) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf;
    const start = performance.now();
    const duration = 1800;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      setValue(target * (1 - Math.pow(1 - t, 3)));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);
  return <span>+{value.toFixed(1)}%</span>;
}

function isComplete(current, key) {
  return phases.findIndex((item) => item.key === key) < phases.findIndex((item) => item.key === current);
}
