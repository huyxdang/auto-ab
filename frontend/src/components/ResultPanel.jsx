import { useEffect, useState } from 'react';

const phases = [
  { key: 'connecting', label: 'Connecting analytics...' },
  { key: 'crawling', label: 'Crawling DOM...' },
  { key: 'diagnosing', label: 'Clustering drop-off signals...' },
  { key: 'generating', label: 'Generating control/variant diff...' },
  { key: 'testing', label: 'Streaming simulated conversions...' },
];

export function ResultPanel({ phase, result, error, winner, onOpenReport, onReset }) {
  if (phase === 'idle') {
    return null;
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
        <p className="panel-kicker">AI loop running</p>
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
  const allVariants = variants.length ? variants : result.variant ? [{ ...result.variant, label: 'B' }] : [];
  const [activeVariantIndex, setActiveVariantIndex] = useState(0);
  const primaryVariant = allVariants[activeVariantIndex] || allVariants[0] || result.variant;
  const secondaryVariant = allVariants[(activeVariantIndex + 1) % allVariants.length];
  const isTesting = phase === 'testing';
  const isDone = phase === 'done';

  function cycleVariant() {
    if (allVariants.length <= 1) return;
    setActiveVariantIndex((index) => (index + 1) % allVariants.length);
  }

  return (
    <div className="result-panel result-final">
      <div className="result-header">
        <div>
          <p className="panel-kicker">{isDone ? 'Test complete' : 'Running A/B test'}</p>
          <h2>{result.url}</h2>
        </div>
        {isDone ? <span className="uplift-chip">Winner: Variant {winner}</span> : null}
      </div>

      <div className="result-section-title">
        <p className="panel-kicker">Friction diagnosis</p>
        <h3>Behavior signals converted into concrete website problems.</h3>
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

      <div className="result-section-title compact">
        <p className="panel-kicker">Generated website</p>
        <h3>Original page vs AI-improved page.</h3>
      </div>

      <WebsiteComparison
        baseline={result.baseline}
        cycleVariant={cycleVariant}
        isWinner={isDone && winner === primaryVariant?.label}
        isTesting={isTesting}
        uplift={primaryVariant ? (isTesting ? <LiftBar target={primaryVariant.liftPct} /> : primaryVariant.uplift) : null}
        variant={primaryVariant}
        variantCount={allVariants.length}
      />

      {secondaryVariant && secondaryVariant !== primaryVariant ? (
        <article className={`runner-up-card${isDone && winner === secondaryVariant.label ? ' is-winner' : ''}`}>
          <div>
            <p className="panel-kicker">Alternate route</p>
            <strong>Variant {secondaryVariant.label}: {secondaryVariant.hypothesis}</strong>
            <span>{secondaryVariant.headline}</span>
          </div>
          <span className="uplift-mini">{isTesting ? <LiftBar target={secondaryVariant.liftPct} /> : secondaryVariant.uplift}</span>
        </article>
      ) : null}

      {isDone ? (
        <div className="action-row">
          <button className="button primary" onClick={() => document.querySelector('[data-generated-site]')?.scrollIntoView({ behavior: 'smooth', block: 'center' })} type="button">View generated website</button>
          <button className="button secondary" onClick={cycleVariant} type="button">Run loop again</button>
          <button className="button secondary" onClick={onOpenReport} type="button">Open benchmark report</button>
        </div>
      ) : null}
    </div>
  );
}

function WebsiteComparison({ baseline, variant, uplift, isTesting, isWinner, cycleVariant, variantCount }) {
  const [viewMode, setViewMode] = useState('compare');
  const controlSite = baseline?.site || DEFAULT_CONTROL_SITE;
  const variantSite = variant?.site || buildVariantSite(variant);
  const changes = variantSite.changes || variant?.changes || [];
  const showOriginal = viewMode === 'compare' || viewMode === 'original';
  const showGenerated = viewMode === 'compare' || viewMode === 'generated';

  return (
    <div className="website-result">
      <div className="website-view-toggle" aria-label="Website comparison view">
        <button className={viewMode === 'compare' ? 'active' : ''} onClick={() => setViewMode('compare')} type="button">Side by side</button>
        <button className={viewMode === 'original' ? 'active' : ''} onClick={() => setViewMode('original')} type="button">View original</button>
        <button className={viewMode === 'generated' ? 'active' : ''} onClick={() => setViewMode('generated')} type="button">View generated</button>
        <button disabled={variantCount <= 1} onClick={cycleVariant} type="button">Cycle variants</button>
        <a href={variantSite.fullPagePath || '/auto-ab/generated/variant-b.html'} target="_blank" rel="noreferrer">Open full page</a>
      </div>

      <div className={`website-compare ${viewMode !== 'compare' ? 'single' : ''}`}>
        {showOriginal ? <WebsitePreview label="Original website2" site={controlSite} tone="control" /> : null}
        {showGenerated ? <WebsitePreview isWinner={isWinner} label={`Generated Variant ${variant?.label || 'B'}`} site={variantSite} tone="variant" uplift={uplift} /> : null}
      </div>

      <div className="generated-changes">
        <div>
          <p className="panel-kicker">Generated page improvements</p>
          <h3>{isTesting ? 'Testing generated treatment against the control.' : 'What changed in the generated page.'}</h3>
        </div>
        <ul>
          {changes.map((change) => <li key={change}>{change}</li>)}
        </ul>
      </div>

      <div className="next-loop-rail">
        <span>01 Kept: outcome-led hero</span>
        <span>02 Testing next: proof placement</span>
        <span>03 Candidate: sticky mobile CTA</span>
      </div>
    </div>
  );
}

function WebsitePreview({ label, site, tone, uplift, isWinner }) {
  return (
    <article className={`website-preview actual-site-preview ${tone}${isWinner ? ' is-winner' : ''}`} data-generated-site={tone === 'variant' ? 'true' : undefined}>
      <div className="site-browser-bar">
        <span>{label}</span>
        {uplift ? <strong>{uplift} predicted lift</strong> : null}
      </div>
      <div className="site-preview-page">
        <div className="site-preview-topbar">
          <span><i />{site.brand}</span>
          <nav><em>Agenda</em><em>Judges</em><em>{site.navCta}</em></nav>
        </div>
        <div className="site-preview-hero">
          <div className="site-preview-main">
            <span className="site-eyebrow">{site.eyebrow}</span>
            <span className="preview-status">{site.status}</span>
            <h2>{site.headline}</h2>
            <p>{site.subheadline}</p>
            <div className="site-preview-trust">
              {site.trust.map((item) => <span key={item}>{item}</span>)}
            </div>
            <div className="site-preview-facts">
              {site.facts.map((item) => <span className={item.tone || ''} key={item.label}><b>{item.value}</b>{item.label}</span>)}
            </div>
            <div className="site-preview-cta">
              <button className="button primary" type="button">{site.primaryCta}</button>
              <button className="button secondary" type="button">{site.secondaryCta}</button>
            </div>
          </div>
          <aside className="site-poster-card">
            <strong>{site.sideTitle}</strong>
            <p>{site.sideCopy}</p>
            <span>{site.posterTag}</span>
          </aside>
        </div>
        <div className="site-preview-proof">
          {site.proof.map((item) => <span key={item}>{item}</span>)}
        </div>
        <div className="site-preview-modules">
          {site.modules.map((item) => <span key={item}>{item}</span>)}
        </div>
        {site.experiments?.length ? (
          <div className="site-preview-experiments">
            {site.experiments.map((item) => <span key={item}>{item}</span>)}
          </div>
        ) : null}
        {site.stickyCta ? <div className="site-sticky-preview">{site.stickyCta}</div> : null}
      </div>
    </article>
  );
}

function buildVariantSite(variant) {
  return {
    ...DEFAULT_VARIANT_SITE,
    headline: variant?.headline || DEFAULT_VARIANT_SITE.headline,
    changes: variant?.changes || DEFAULT_VARIANT_SITE.changes,
  };
}

function VariantCard({ label, model, tone, uplift, isWinner, hypothesis }) {
  return (
    <article className={`variant-card ${tone}${isWinner ? ' is-winner' : ''}`}>
      <div className="variant-topline">
        <span>{label}</span>
        <strong>Score: {model.score}</strong>
      </div>
      {hypothesis ? <p className="variant-hypothesis">{hypothesis}</p> : null}
      <blockquote>{model.headline}</blockquote>
      <p>CVR: {model.cvr}</p>
      {uplift ? <span className="uplift-mini">{uplift} predicted uplift</span> : null}
      {model.changes ? (
        <ul>
          {model.changes.map((change) => <li key={change}>{change}</li>)}
        </ul>
      ) : null}
    </article>
  );
}

const DEFAULT_CONTROL_SITE = {
  brand: 'Codex Community Vietnam',
  navCta: 'Join waitlist',
  eyebrow: 'AI Hackathon - Weekend Build with Codex and CAR',
  status: 'Closed · waitlist open',
  headline: 'Build and ship an AI agent in 1 day.',
  subheadline: 'A hands-on Ho Chi Minh City build session for engineers, founders, and operators learning practical agentic engineering with OpenAI Codex and Codex Auto Runner.',
  primaryCta: 'Join waitlist',
  secondaryCta: 'View Luma Event',
  sideTitle: 'Codex Auto Runner',
  sideCopy: 'Official Luma event poster dominates the hero while conversion actions compete below the fold.',
  posterTag: 'Event Poster',
  trust: ['175 builders going', 'Sold out fast', '3 build tracks'],
  facts: [
    { value: 'May 09', label: 'Event date' },
    { value: 'HCMC', label: 'Local build session' },
    { value: 'Closed', label: 'Registration status', tone: 'closed' },
  ],
  proof: ['1 day from concept to demo', '175 builders registered', '3 tracks'],
  modules: ['Agenda below fold', 'Judges lower down', 'Footer repeats waitlist'],
  experiments: [],
  fullPagePath: '/auto-ab/website2/index.html',
};

const DEFAULT_VARIANT_SITE = {
  brand: 'Codex Community Vietnam',
  navCta: 'Join next cohort',
  eyebrow: 'Next Codex sprint · HCMC waitlist now open',
  status: 'Next cohort waitlist is live · first invites release soon',
  headline: 'Get the Codex launch kit before the next build sprint opens',
  subheadline: 'Sold-out traffic now lands on a high-intent offer: setup guide, CAR templates, judge criteria, and team matching before registration reopens.',
  primaryCta: 'Claim next-cohort invite',
  secondaryCta: 'Preview shipped agents',
  sideTitle: 'Cohort Launch Kit',
  sideCopy: 'The poster becomes proof. The generated page sells a live next action instead of replaying a closed event.',
  posterTag: 'Generated Variant',
  trust: ['175 builders registered', 'Sold out fast', '3 build tracks', 'Judges from Scale, Depth, Impact'],
  facts: [
    { value: 'Next', label: 'Cohort waitlist' },
    { value: 'HCMC', label: 'Local build session' },
    { value: 'Open', label: 'Early invite status' },
  ],
  proof: ['Setup guide unlocked', 'CAR templates included', 'Team matching before launch'],
  modules: ['Invite ladder replaces dead-end status', 'Proof rail promoted above agenda', 'Luma/GitHub moved to resource drawer'],
  experiments: ['Next test: launch kit vs cohort headline', 'Mobile sticky invite bar', 'Judge proof carousel'],
  stickyCta: 'Sticky mobile bar: Claim invite + get setup guide',
  fullPagePath: '/auto-ab/generated/variant-b.html',
  changes: ['Closed status converted into a live next-cohort invite ladder', 'Hero offer changed from attending a closed event to claiming a launch kit', 'Poster demoted into proof so the form owns the visual hierarchy', 'Luma and GitHub links moved into a resource drawer after email capture', 'Next loop will test sticky mobile invite bar and judge-proof carousel'],
};

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
