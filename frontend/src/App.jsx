import { useState } from 'react';
import { BenchmarkReport } from './components/BenchmarkReport.jsx';
import { CtaSection } from './components/CtaSection.jsx';
import { Hero } from './components/Hero.jsx';
import { LoopExplainer } from './components/LoopExplainer.jsx';
import { MetricsStrip } from './components/MetricsStrip.jsx';

export default function App() {
  const [view, setView] = useState('home');
  const [lastResult, setLastResult] = useState(null);

  function openReport() {
    setView('report');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function returnHome() {
    setView('home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <>
      <header className="top-nav">
        <div className="nav-inner">
          <button className="brand-lockup" onClick={returnHome} type="button">auto-ab</button>
          <nav aria-label="Primary navigation">
            <a className="active" href="#hero">Platform</a>
            <a href="#metrics">Signals</a>
            <a href="#how">Loop</a>
            <a href="#cta">API</a>
          </nav>
          <div className="nav-actions">
            <a className="nav-icon" href="#metrics" aria-label="Open monitoring panel">MON</a>
            <a className="button primary small" href="#hero">Deploy Experiment</a>
          </div>
        </div>
      </header>
      <main>
        {view === 'home' ? (
          <>
            <Hero onComplete={setLastResult} onOpenReport={openReport} />
            <MetricsStrip />
            <LoopExplainer />
            <CtaSection />
          </>
        ) : (
          <BenchmarkReport result={lastResult} onBack={returnHome} />
        )}
      </main>
      <footer className="footer">
        <div className="container footer-grid">
          <div>
            <strong>auto-ab</strong>
            <p>Autonomous website optimization powered by real behavior signals.</p>
          </div>
          <div className="footer-links">
            <a href="#hero">Documentation</a>
            <a href="#how">API Reference</a>
            <a href="#metrics">Status</a>
            <a href="#cta">Privacy Policy</a>
          </div>
        </div>
      </footer>
    </>
  );
}
