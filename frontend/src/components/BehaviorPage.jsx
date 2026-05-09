import { Activity, ArrowLeft, Clock, MousePointerClick, Play, Sparkles, Users } from 'lucide-react';

const HEATMAP_DOTS = [
  { left: '32%', top: '14%', size: 180, intensity: 0.92, label: 'Hero CTA' },
  { left: '68%', top: '18%', size: 140, intensity: 0.76, label: 'Secondary link' },
  { left: '24%', top: '42%', size: 130, intensity: 0.62 },
  { left: '74%', top: '46%', size: 100, intensity: 0.45 },
  { left: '50%', top: '64%', size: 220, intensity: 0.88, label: 'Pricing block' },
  { left: '20%', top: '78%', size: 90, intensity: 0.34 },
  { left: '78%', top: '82%', size: 110, intensity: 0.41 },
];

const RECORDINGS = [
  { id: '#sess_8a2f', user: 'Visitor · United States', duration: '02:14', dropoff: 'Bounced after pricing', severity: 'high', scroll: 62 },
  { id: '#sess_b91c', user: 'Visitor · Germany', duration: '01:38', dropoff: 'Rage-clicked CTA', severity: 'high', scroll: 41 },
  { id: '#sess_4d77', user: 'Visitor · India', duration: '00:52', dropoff: 'Left at hero', severity: 'medium', scroll: 18 },
  { id: '#sess_2e10', user: 'Visitor · United Kingdom', duration: '03:47', dropoff: 'Converted', severity: 'low', scroll: 100 },
  { id: '#sess_f3a5', user: 'Visitor · Canada', duration: '01:11', dropoff: 'Hesitated at testimonials', severity: 'medium', scroll: 55 },
];

const SOURCE_LABELS = {
  simulated: 'Simulated visitors',
  posthog: 'PostHog',
  ga4: 'Google Analytics 4',
  hotjar: 'Hotjar',
};

export function BehaviorPage({ target, onStart, onBack }) {
  const sourceLabel = SOURCE_LABELS[target?.source] || 'analytics';
  return (
    <section className="behavior-page">
      <div className="container">
        <button className="behavior-back" onClick={onBack} type="button">
          <ArrowLeft size={16} aria-hidden="true" /> Back
        </button>

        <header className="behavior-header">
          <p className="panel-kicker">Connected · {sourceLabel}</p>
          <h1>Last 7 days of visitor behavior</h1>
          <p className="behavior-sub">
            <code>{target?.url}</code> · 1,247 sessions · 3,891 events
          </p>
        </header>

        <div className="behavior-stats">
          <Stat icon={<Users size={16} />} label="Sessions" value="1,247" />
          <Stat icon={<MousePointerClick size={16} />} label="Click events" value="3,891" />
          <Stat icon={<Clock size={16} />} label="Avg. time on page" value="01:42" />
          <Stat icon={<Activity size={16} />} label="Bounce rate" value="58%" trend="up" />
        </div>

        <div className="behavior-grid">
          <article className="behavior-card">
            <header>
              <h2>Click heatmap</h2>
              <span className="panel-kicker">Aggregated · 1,247 sessions</span>
            </header>
            <div className="heatmap-frame">
              <div className="heatmap-page">
                <div className="hp-block hp-hero" />
                <div className="hp-block hp-row" />
                <div className="hp-block hp-row narrow" />
                <div className="hp-block hp-grid">
                  <span /><span /><span />
                </div>
                <div className="hp-block hp-row" />
                {HEATMAP_DOTS.map((dot, i) => (
                  <span
                    key={i}
                    className="heat-dot"
                    style={{
                      left: dot.left,
                      top: dot.top,
                      width: dot.size,
                      height: dot.size,
                      opacity: dot.intensity,
                    }}
                    title={dot.label}
                  />
                ))}
              </div>
            </div>
            <p className="behavior-note">Heaviest attention sits on the hero CTA and pricing block. Secondary links steal clicks from the primary action.</p>
          </article>

          <article className="behavior-card">
            <header>
              <h2>Session recordings</h2>
              <span className="panel-kicker">5 of 1,247 · most informative</span>
            </header>
            <ul className="recording-list">
              {RECORDINGS.map((rec) => (
                <li key={rec.id} className="recording-row">
                  <button className="rec-play" type="button" aria-label={`Play ${rec.id}`}>
                    <Play size={14} fill="currentColor" />
                  </button>
                  <div className="rec-meta">
                    <strong>{rec.id}</strong>
                    <span>{rec.user}</span>
                  </div>
                  <div className="rec-scrubber">
                    <div className="scrub-bar"><div style={{ width: `${rec.scroll}%` }} /></div>
                    <span>{rec.duration}</span>
                  </div>
                  <span className={`severity ${rec.severity}`}>{rec.dropoff}</span>
                </li>
              ))}
            </ul>
          </article>
        </div>

        <div className="behavior-cta">
          <div>
            <p className="panel-kicker">Ready</p>
            <h2>Hand this to the AI.</h2>
            <p>auto-ab will diagnose friction, draft two variants, and run a simulated A/B test against the data above.</p>
          </div>
          <button className="button primary large" onClick={onStart} type="button">
            <Sparkles size={18} aria-hidden="true" /> Start AI
          </button>
        </div>
      </div>
    </section>
  );
}

function Stat({ icon, label, value, trend }) {
  return (
    <div className="behavior-stat">
      <span className="stat-icon">{icon}</span>
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}{trend === 'up' ? <em>↑</em> : null}</strong>
    </div>
  );
}
