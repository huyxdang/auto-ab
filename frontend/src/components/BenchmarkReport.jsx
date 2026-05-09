import { ArrowLeft, Check, ExternalLink } from 'lucide-react';
import { benchmarkReport } from '../data/benchmarkReport.js';

export function BenchmarkReport({ result, onBack }) {
  const report = benchmarkReport;
  const sourceUrl = result?.url || report.url;

  return (
    <section className="report-page">
      <div className="container report-shell">
        <div className="report-toolbar">
          <button className="button secondary" onClick={onBack} type="button">
            <ArrowLeft size={17} aria-hidden="true" />
            Command center
          </button>
          <span>auto-ab benchmark report</span>
        </div>

        <header className="report-hero">
          <div>
            <p className="status-badge">Experiment complete</p>
            <h1>Benchmark finished. Variant B is ready to ship.</h1>
            <p>{report.verdict}</p>
            <div className="report-target">
              <span>Target</span>
              <strong>{sourceUrl}</strong>
            </div>
          </div>
          <div className="leak-card">
            <p className="panel-kicker">Primary leak</p>
            <h2>{report.primaryLeak}</h2>
            <span>Confidence: {report.confidence}</span>
          </div>
        </header>

        <div className="score-grid">
          <ScoreCard label="Before score" value={report.scoreBefore} tone="muted" />
          <ScoreCard label="After score" value={report.scoreAfter} tone="primary" />
          <ScoreCard label="Projected lift" value={report.projectedLift} tone="primary" />
          <ScoreCard label="Confidence" value={report.confidence} tone="primary" />
        </div>

        <section className="report-section">
          <div className="report-section-heading">
            <p className="eyebrow">Benchmark metrics</p>
            <h2>Conversion path recovers once closed registration gets a fallback action.</h2>
          </div>
          <div className="kpi-grid">
            {report.kpis.map((kpi) => (
              <article className="kpi-card" key={kpi.label}>
                <span>{kpi.label}</span>
                <div>
                  <p><em>Before</em>{kpi.before}</p>
                  <p><em>After</em>{kpi.after}</p>
                </div>
                <strong>{kpi.delta}</strong>
              </article>
            ))}
          </div>
        </section>

        <section className="report-section split-report">
          <div>
            <div className="report-section-heading compact">
              <p className="eyebrow">Priority fixes</p>
              <h2>What auto-ab changed next.</h2>
            </div>
            <div className="issue-grid">
              {report.issues.map((issue) => (
                <article className="issue-card" key={issue.title}>
                  <div className="issue-topline">
                    <span className={`priority-pill ${issue.priority.toLowerCase()}`}>{issue.priority}</span>
                    <span>{issue.impact} impact</span>
                  </div>
                  <h3>{issue.title}</h3>
                  <p><strong>Weakness:</strong> {issue.weakness}</p>
                  <p><strong>Fix:</strong> {issue.fix}</p>
                </article>
              ))}
            </div>
          </div>

          <GeneratedSitePreview site={report.generatedSite} />
        </section>

        <section className="next-experiment">
          <div>
            <p className="eyebrow">Next experiment</p>
            <h2>{report.nextExperiment.test}</h2>
            <p>Primary KPI: {report.nextExperiment.primaryKpi}</p>
          </div>
          <div>
            <strong>{report.nextExperiment.recommendation}</strong>
            <button className="button primary" type="button">
              <ExternalLink size={17} aria-hidden="true" />
              Export variant brief
            </button>
          </div>
        </section>
      </div>
    </section>
  );
}

function ScoreCard({ label, value, tone }) {
  return (
    <article className={`score-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function GeneratedSitePreview({ site }) {
  return (
    <aside className="site-preview" aria-label="Generated improved site preview">
      <div className="browser-frame">
        <div className="browser-bar">
          <span>demo-site.variant.generated</span>
          <i /><i /><i />
        </div>
        <div className="preview-body">
          <span className="preview-status">{site.status}</span>
          <h2>{site.headline}</h2>
          <p>{site.subheadline}</p>
          <div className="preview-cta-row">
            <button className="button primary" type="button">{site.primaryCta}</button>
            <button className="button secondary" type="button">{site.secondaryCta}</button>
          </div>
          <div className="preview-proof">
            <div className="avatar-stack" aria-hidden="true">
              <span>A</span><span>B</span><span>C</span><span>D</span>
            </div>
            <p>{site.proof}</p>
          </div>
          <ul className="module-checklist">
            {site.modules.map((module) => (
              <li key={module}><Check size={15} aria-hidden="true" />{module}</li>
            ))}
          </ul>
        </div>
      </div>
    </aside>
  );
}
