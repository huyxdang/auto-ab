import { Link2, Radar } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ResultPanel } from './ResultPanel.jsx';

const DEFAULT_TARGET_URL = 'https://quotations-crm-pieces-vii.trycloudflare.com/';

const ANALYTICS_SOURCES = [
  { value: 'simulated', label: 'Simulated visitors' },
  { value: 'posthog', label: 'PostHog' },
  { value: 'ga4', label: 'Google Analytics 4' },
  { value: 'hotjar', label: 'Hotjar' },
];

export function Hero({ ab, onComplete, onOpenReport }) {
  const [url, setUrl] = useState(DEFAULT_TARGET_URL);
  const [source, setSource] = useState('simulated');
  const [touched, setTouched] = useState(false);
  const { phase, result, error, winner, runConnect, reset } = ab;
  const isRunning = phase !== 'idle' && phase !== 'done';
  const isValid = isValidUrl(url);
  const showError = touched && url.length > 0 && !isValid;

  useEffect(() => {
    if (phase === 'done' && result) onComplete?.({ ...result, winner });
  }, [onComplete, phase, result, winner]);

  function handleSubmit(event) {
    event.preventDefault();
    setTouched(true);
    if (!isValid || isRunning) return;
    runConnect(url.trim(), source);
  }

  function handleReset() {
    reset();
    setTouched(false);
  }

  return (
    <section className="hero section" id="hero">
      <div className="container hero-shell">
        <div className="hero-copy reveal-on-load">
          <p className="status-badge">System ready</p>
          <h1>Analyze. Inject. Optimize.</h1>
          <p className="hero-subtitle">
            Paste a URL and choose an analytics source. This sandbox simulates visitor behavior to show how auto-ab turns real signals into better website variants.
          </p>
        </div>

        <div className="app-panel" aria-label="URL analysis panel">
          <form className="url-form" onSubmit={handleSubmit} noValidate>
            <label className="sr-only" htmlFor="url-input">Website URL</label>
            <div className="url-input-wrap">
              <Link2 size={18} aria-hidden="true" />
              <input
                id="url-input"
                value={url}
                onBlur={() => setTouched(true)}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://yoursite.com"
                type="url"
                inputMode="url"
                title={url}
                aria-invalid={showError}
                aria-describedby={showError ? 'url-error' : undefined}
              />
            </div>
            <select
              className="source-select"
              value={source}
              onChange={(event) => setSource(event.target.value)}
              disabled={isRunning}
              aria-label="Analytics source"
            >
              {ANALYTICS_SOURCES.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <button className="button primary" disabled={!isValid || isRunning} type="submit">
              <Radar size={18} aria-hidden="true" />
              {isRunning ? 'Running' : 'Initialize scan'}
            </button>
          </form>
          {showError ? <p className="inline-error" id="url-error">Looks like that's not a URL — try https://...</p> : null}
          <SystemLog phase={phase} source={source} />
          <ResultPanel error={error} phase={phase} result={result} winner={winner} onOpenReport={onOpenReport} onReset={handleReset} />
        </div>
      </div>
    </section>
  );
}

function SystemLog({ phase, source }) {
  const sourceLabel = ANALYTICS_SOURCES.find((s) => s.value === source)?.label || 'analytics';
  const lines = {
    idle: ['Awaiting target URL input...', 'Crawler initialized and ready.', 'DOM parsing modules loaded.'],
    connecting: [`Connecting to ${sourceLabel}...`, 'Authenticating session token.', 'Loaded 1,247 sessions · 3,891 events from last 7 days.'],
    crawling: ['Target received.', 'Scanning page structure...', 'Collecting visitor signals from analytics source.'],
    diagnosing: ['Clustering friction events.', 'Weak CTA hierarchy detected.', 'Trust gap probability elevated.'],
    generating: ['Prompt guardrails loaded.', 'Drafting Variant B (hero rewrite).', 'Drafting Variant C (proof reorder).'],
    testing: ['Splitting traffic 50/50 across variants.', 'Streaming synthetic conversions...', 'Confidence interval narrowing.'],
    done: ['Test concluded.', 'Winner selected.', 'Experiment ready to deploy.'],
  };

  return (
    <div className="system-log" aria-live="polite">
      <div className="terminal-bar">
        <span>scanner_daemon.sh</span>
        <div><i /><i /><i className="active" /></div>
      </div>
      <div className="terminal-body">
        {(lines[phase] || lines.idle).map((line) => (
          <p key={line}><span>&gt;</span>{line}</p>
        ))}
        <p><span>&gt;</span><b>_</b></p>
      </div>
    </div>
  );
}

function isValidUrl(value) {
  try {
    const parsed = new URL(value.trim());
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}
