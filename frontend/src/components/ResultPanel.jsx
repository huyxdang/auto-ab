const phases = [
  { key: 'crawling', label: 'Scanning page...' },
  { key: 'diagnosing', label: 'Finding pain points...' },
  { key: 'generating', label: 'Generating variant...' },
  { key: 'benchmarking', label: 'Benchmarking lift...' },
];

export function ResultPanel({ phase, result, error, onOpenReport, onReset }) {
  if (phase === 'idle') {
    return (
      <div className="result-panel empty-state">
        <p className="panel-kicker">Ready</p>
        <h2>Paste a URL to get started.</h2>
        <p>We will simulate real visitor behavior, detect friction, and produce a stronger variant in one loop.</p>
      </div>
    );
  }

  if (phase !== 'done') {
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

  if (error) {
    return (
      <div className="result-panel">
        <p className="panel-kicker danger">Error</p>
        <h2>{error}</h2>
        <button className="button secondary" onClick={onReset} type="button">Try again</button>
      </div>
    );
  }

  return (
    <div className="result-panel result-final">
      <div className="result-header">
        <div>
          <p className="panel-kicker">Pain points found</p>
          <h2>{result.url}</h2>
        </div>
        <span className="uplift-chip">{result.uplift}</span>
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

      <div className="diff-grid">
        <VariantCard label="Before" model={result.baseline} tone="warning" />
        <VariantCard label="After" model={result.variant} tone="success" uplift={result.uplift} />
      </div>

      <div className="action-row">
        <button className="button primary" onClick={onOpenReport} type="button">View benchmark report</button>
        <button className="button secondary" onClick={onReset} type="button">Run loop again</button>
      </div>
    </div>
  );
}

function VariantCard({ label, model, tone, uplift }) {
  return (
    <article className={`variant-card ${tone}`}>
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

function isComplete(current, key) {
  return phases.findIndex((item) => item.key === key) < phases.findIndex((item) => item.key === current);
}
