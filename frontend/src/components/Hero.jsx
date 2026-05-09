import { Link2, Radar } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useABLoop } from '../hooks/useABLoop.js';
import { ResultPanel } from './ResultPanel.jsx';

export function Hero({ onComplete, onOpenReport }) {
  const [url, setUrl] = useState('');
  const [touched, setTouched] = useState(false);
  const { phase, result, error, runLoop, reset } = useABLoop();
  const isRunning = phase !== 'idle' && phase !== 'done';
  const isValid = isValidUrl(url);
  const showError = touched && url.length > 0 && !isValid;

  useEffect(() => {
    if (phase === 'done' && result) onComplete?.(result);
  }, [onComplete, phase, result]);

  function handleSubmit(event) {
    event.preventDefault();
    setTouched(true);
    if (!isValid || isRunning) return;
    runLoop(url.trim());
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
            Input your landing page URL. auto-ab analyzes behavior signals, finds conversion friction, and generates the next website variant.
          </p>
        </div>

        <div className="app-panel" aria-label="URL analysis panel">
          <form className="url-form" onSubmit={handleSubmit} noValidate>
            <label className="sr-only" htmlFor="url-input">
              Website URL
            </label>
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
                aria-invalid={showError}
                aria-describedby={showError ? 'url-error' : undefined}
              />
            </div>
            <button className="button primary" disabled={!isValid || isRunning} type="submit">
              <Radar size={18} aria-hidden="true" />
              {isRunning ? 'Scanning' : 'Initialize scan'}
            </button>
          </form>
          {showError ? <p className="inline-error" id="url-error">Looks like that's not a URL - try https://...</p> : null}
          <SystemLog phase={phase} />
          <ResultPanel error={error} phase={phase} result={result} onOpenReport={onOpenReport} onReset={handleReset} />
        </div>
      </div>
    </section>
  );
}

function SystemLog({ phase }) {
  const lines = {
    idle: ['Awaiting target URL input...', 'Crawler initialized and ready.', 'DOM parsing modules loaded.'],
    crawling: ['Target received.', 'Scanning page structure...', 'Collecting simulated session signals...'],
    diagnosing: ['Clustering friction events.', 'Weak CTA hierarchy detected.', 'Trust gap probability elevated.'],
    generating: ['Prompt guardrails loaded.', 'Generating variant copy...', 'Re-ranking candidate treatments.'],
    benchmarking: ['Running AI judge benchmark.', 'Comparing baseline score to variant score.', 'Preparing experiment package.'],
    done: ['Variant generated.', 'Benchmark complete.', 'Experiment ready to deploy.'],
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
