import { useEffect, useState } from 'react';
import { BehaviorPage } from './components/BehaviorPage.jsx';
import { BenchmarkReport } from './components/BenchmarkReport.jsx';
import { CtaSection } from './components/CtaSection.jsx';
import { Hero } from './components/Hero.jsx';
import { LoopExplainer } from './components/LoopExplainer.jsx';
import { MetricsStrip } from './components/MetricsStrip.jsx';
import { useABLoop } from './hooks/useABLoop.js';

export default function App() {
  const [view, setView] = useState('home');
  const [lastResult, setLastResult] = useState(null);
  const ab = useABLoop();

  useEffect(() => {
    if (ab.phase === 'connected' && view !== 'behavior') {
      setView('behavior');
    }
  }, [ab.phase, view]);

  useEffect(() => {
    if (ab.phase === 'done' && ab.result) {
      setLastResult({ ...ab.result, winner: ab.winner });
    }
  }, [ab.phase, ab.result, ab.winner]);

  function openReport() {
    setView('report');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function returnHome() {
    setView('home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function startAI() {
    ab.runAnalysis();
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
            <a href="#cta">Waitlist</a>
          </nav>
          <div className="nav-actions">
            <a className="nav-icon" href="#metrics" aria-label="Open metrics panel">Metrics</a>
            <a className="button primary small" href="#hero">Run Demo</a>
          </div>
        </div>
      </header>
      <main>
        {view === 'home' ? (
          <>
            <Hero ab={ab} onComplete={setLastResult} onOpenReport={openReport} />
            <MetricsStrip />
            <LoopExplainer phase={ab.phase} />
            <CtaSection />
          </>
        ) : view === 'behavior' ? (
          <BehaviorPage ab={ab} onStart={startAI} onBack={returnHome} onOpenReport={openReport} />
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
            <a href="#hero">Platform</a>
            <a href="#metrics">Metrics</a>
            <a href="#how">Loop</a>
            <a href="#cta">Early Access</a>
          </div>
        </div>
      </footer>
    </>
  );
}
