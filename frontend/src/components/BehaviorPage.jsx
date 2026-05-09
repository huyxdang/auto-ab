import { Activity, ArrowLeft, Clock, MousePointerClick, Play, Sparkles, Users } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import website2Html from '../../../website2/index.html?raw';
import { ResultPanel } from './ResultPanel.jsx';

const ELEMENT_SIGNALS = [
  {
    id: 'hero',
    selector: '.hero-copy h1',
    copy: 'Build and ship an AI agent in 1 day.',
    signal: '82% viewport attention',
    severity: 'low',
    diagnosis: 'Strong promise. Keep it, but make the next-session outcome clearer.',
  },
  {
    id: 'status',
    selector: '.facts .status-closed',
    copy: 'Registration Closed',
    signal: '38% exits after noticing',
    severity: 'high',
    diagnosis: 'Closed status creates dead-end anxiety before the fallback CTA is clear.',
  },
  {
    id: 'waitlist',
    selector: '#waitlist',
    copy: 'Enter email for next event waitlist',
    signal: '14 rage-click clusters',
    severity: 'high',
    diagnosis: 'Waitlist fallback is useful but visually feels secondary to the closed event.',
  },
  {
    id: 'luma',
    selector: '[data-cta="luma"]',
    copy: 'View Luma Event',
    signal: '23% intent leakage',
    severity: 'medium',
    diagnosis: 'Secondary event link pulls users away from the conversion path.',
  },
  {
    id: 'judges',
    selector: '#judges',
    copy: 'Track judges',
    signal: 'High trust, low reach',
    severity: 'medium',
    diagnosis: 'Credibility is strong but appears too late for hesitant visitors.',
  },
];

const RECORDINGS = [
  {
    id: '#sess_8a2f',
    user: 'Visitor · United States',
    duration: '02:14',
    dropoff: 'Bounced after status',
    severity: 'high',
    scroll: 62,
    hotspot: 'status',
    path: [
      { id: 'hero', label: 'Read hero promise', x: 22, y: 23 },
      { id: 'status', label: 'Noticed Registration Closed', x: 34, y: 49 },
      { id: 'waitlist', label: 'Hovered waitlist form', x: 29, y: 67 },
      { id: 'exit', label: 'Exited without email', x: 72, y: 82 },
    ],
  },
  {
    id: '#sess_b91c',
    user: 'Visitor · Germany',
    duration: '01:38',
    dropoff: 'Rage-clicked waitlist',
    severity: 'high',
    scroll: 41,
    hotspot: 'waitlist',
    path: [
      { id: 'hero', label: 'Skimmed headline', x: 21, y: 25 },
      { id: 'waitlist', label: 'Focused email field', x: 28, y: 66 },
      { id: 'waitlist', label: 'Clicked Join Waitlist twice', x: 43, y: 66 },
      { id: 'luma', label: 'Escaped to Luma link', x: 21, y: 76 },
    ],
  },
  {
    id: '#sess_4d77',
    user: 'Visitor · India',
    duration: '00:52',
    dropoff: 'Left at hero',
    severity: 'medium',
    scroll: 18,
    hotspot: 'hero',
    path: [
      { id: 'hero', label: 'Read headline', x: 24, y: 25 },
      { id: 'poster', label: 'Glanced at poster', x: 74, y: 34 },
      { id: 'hero', label: 'Returned to hero copy', x: 30, y: 38 },
    ],
  },
  {
    id: '#sess_2e10',
    user: 'Visitor · United Kingdom',
    duration: '03:47',
    dropoff: 'Converted to waitlist',
    severity: 'low',
    scroll: 100,
    hotspot: 'waitlist',
    path: [
      { id: 'hero', label: 'Read promise', x: 24, y: 24 },
      { id: 'proof', label: 'Checked proof chips', x: 28, y: 41 },
      { id: 'waitlist', label: 'Entered email', x: 29, y: 66 },
      { id: 'waitlist', label: 'Submitted waitlist', x: 43, y: 66 },
    ],
  },
  {
    id: '#sess_f3a5',
    user: 'Visitor · Canada',
    duration: '01:11',
    dropoff: 'Scrolled to judges',
    severity: 'medium',
    scroll: 78,
    hotspot: 'judges',
    path: [
      { id: 'hero', label: 'Read event claim', x: 22, y: 25 },
      { id: 'agenda', label: 'Scrolled agenda', x: 48, y: 74 },
      { id: 'judges', label: 'Checked judges', x: 68, y: 84 },
      { id: 'waitlist', label: 'Returned to waitlist', x: 31, y: 66 },
    ],
  },
];

const SOURCE_LABELS = {
  simulated: 'Simulated visitors',
  posthog: 'PostHog',
  ga4: 'Google Analytics 4',
  hotjar: 'Hotjar',
};

export function BehaviorPage({ ab, onStart, onBack, onOpenReport }) {
  const { phase, result, error, winner, reset, target } = ab;
  const resultRef = useRef(null);
  const behavior = result?.behavior;
  const elementSignals = behavior?.elementSignals?.length ? behavior.elementSignals : ELEMENT_SIGNALS;
  const recordings = behavior?.recordings?.length ? behavior.recordings : RECORDINGS;
  const [activeRecordingId, setActiveRecordingId] = useState(recordings[1]?.id || recordings[0]?.id);
  const [replayMode, setReplayMode] = useState('combined');
  const sourceLabel = SOURCE_LABELS[target?.source] || 'analytics';
  const activeRecording = recordings.find((rec) => rec.id === activeRecordingId) || recordings[0];
  const aiRunning = ['crawling', 'diagnosing', 'generating', 'testing'].includes(phase);
  const aiStarted = ['crawling', 'diagnosing', 'generating', 'testing', 'done'].includes(phase);
  const sessionCount = formatNumber(behavior?.sessions || 1247);
  const eventCount = formatNumber(behavior?.events || 3891);

  useEffect(() => {
    if (recordings.some((rec) => rec.id === activeRecordingId)) return;
    setActiveRecordingId(recordings[1]?.id || recordings[0]?.id);
  }, [activeRecordingId, recordings]);

  useEffect(() => {
    if (!aiStarted || !resultRef.current) return;
    resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [aiStarted, phase]);

  function handleStart() {
    if (aiRunning) return;
    onStart();
  }

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
            <code>{target?.url}</code> · {sessionCount} sessions · {eventCount} events
          </p>
        </header>

        <div className="behavior-stats">
          <Stat icon={<Users size={16} />} label="Sessions" value={sessionCount} />
          <Stat icon={<MousePointerClick size={16} />} label="Click events" value={eventCount} />
          <Stat icon={<Clock size={16} />} label="Avg. time on page" value={behavior?.averageTimeOnPage || '01:42'} />
          <Stat icon={<Activity size={16} />} label="Bounce rate" value={behavior?.bounceRate || '58%'} trend="up" />
        </div>

        <article className="behavior-card behavior-site-card">
          <header>
            <h2>Actual website replay + heatmap</h2>
            <div className="replay-controls" aria-label="Replay display mode">
              <button className={replayMode === 'combined' ? 'active' : ''} onClick={() => setReplayMode('combined')} type="button">Combined</button>
              <button className={replayMode === 'heatmap' ? 'active' : ''} onClick={() => setReplayMode('heatmap')} type="button">Heatmap</button>
              <button className={replayMode === 'path' ? 'active' : ''} onClick={() => setReplayMode('path')} type="button">Mouse path</button>
            </div>
          </header>
          <div className="active-session-summary">
            <span>{activeRecording?.id}</span>
            <strong>{activeRecording?.dropoff}</strong>
            <p>{sessionInsight(activeRecording)}</p>
          </div>
          <MousePathReplay mode={replayMode} recording={activeRecording} />
          <p className="behavior-note">Click a session recording to replay its mouse path over the actual page. Heat zones show where attention clusters before the AI diagnosis.</p>
        </article>

        <div className="behavior-grid">
          <article className="behavior-card">
            <header>
              <h2>Element behavior map</h2>
              <span className="panel-kicker">DOM signals · website2/index.html</span>
            </header>
            <ElementMap activeElement={activeRecording?.hotspot} signals={elementSignals} />
            <p className="behavior-note">auto-ab parsed the actual page elements, then mapped session behavior to conversion friction. The strongest issue is not low attention; it is closed-registration anxiety before the waitlist fallback feels primary.</p>
          </article>

          <article className="behavior-card">
            <header>
              <h2>Session recordings</h2>
              <span className="panel-kicker">{recordings.length} of {sessionCount} · most informative</span>
            </header>
            <ul className="recording-list">
              {recordings.map((rec) => (
                <li key={rec.id} className={`recording-row ${activeRecordingId === rec.id ? 'is-active' : ''}`}>
                  <button className="rec-play" onClick={() => setActiveRecordingId(rec.id)} type="button" aria-label={`Replay ${rec.id} mouse path`}>
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
                  <button className={`severity ${rec.severity}`} onClick={() => setActiveRecordingId(rec.id)} type="button">{rec.dropoff}</button>
                </li>
              ))}
            </ul>
          </article>
        </div>

        <div className="behavior-cta">
          <div>
            <p className="panel-kicker">Ready</p>
            <h2>Hand this to the AI.</h2>
            <p>auto-ab will diagnose friction, draft variants, and show the next test it would run from these behavior signals.</p>
          </div>
          <button className="button primary large" disabled={aiRunning} onClick={handleStart} type="button">
            <Sparkles size={18} aria-hidden="true" /> {aiRunning ? 'AI running' : 'Start AI'}
          </button>
        </div>

        {aiStarted ? (
          <div className="behavior-ai-result" ref={resultRef}>
            <ResultPanel
              error={error}
              phase={phase}
              result={result}
              winner={winner}
              onOpenReport={onOpenReport}
              onReset={reset}
            />
          </div>
        ) : null}
      </div>
    </section>
  );
}

function ElementMap({ activeElement, signals }) {
  return (
    <div className="element-map">
      {signals.map((item) => (
        <article className={`element-row ${activeElement === item.id ? 'is-active' : ''}`} key={item.selector}>
          <div className="element-selector">
            <strong>{item.selector}</strong>
            <span>{item.copy}</span>
          </div>
          <div className="element-signal">
            <span className={`severity ${item.severity}`}>{item.severity}</span>
            <b>{item.signal}</b>
          </div>
          <p>{item.diagnosis}</p>
        </article>
      ))}
    </div>
  );
}

function MousePathReplay({ recording, mode = 'combined' }) {
  if (!recording) return null;
  const showHeatmap = mode === 'combined' || mode === 'heatmap';
  const showPath = mode === 'combined' || mode === 'path';

  return (
    <div className="mouse-replay">
      <div className="mouse-stage" aria-label={`Mouse path for ${recording.id}`}>
        <iframe className="mouse-site-frame" srcDoc={website2Html} title="website2 replay target" />
        <div className="mouse-stage-overlay" />
        {showHeatmap ? (
          <div className="site-heat-layer" aria-hidden="true">
            {recording.path.map((step, index) => (
              <span
                className={`site-heat-dot heat-${step.id}`}
                key={`${recording.id}-heat-${index}`}
                style={{ left: `${step.x}%`, top: `${step.y}%`, '--heat-size': `${150 - index * 18}px` }}
              />
            ))}
          </div>
        ) : null}
        {showPath ? recording.path.map((step, index) => (
          <span
            className="path-node"
            key={`${recording.id}-${index}`}
            style={{ left: `${step.x}%`, top: `${step.y}%`, '--delay': `${index * 120}ms` }}
            title={step.label}
          >
            {index + 1}
          </span>
        )) : null}
      </div>
      <div className="path-steps">
        {recording.path.map((step, index) => (
          <span key={`${recording.id}-${step.label}`}><b>{index + 1}</b>{step.label}</span>
        ))}
      </div>
    </div>
  );
}

function sessionInsight(recording) {
  if (!recording) return 'Select a recording to inspect the behavior path.';
  if (recording.hotspot === 'waitlist') return 'AI sees intent at the waitlist, but the fallback offer needs stronger framing and less CTA competition.';
  if (recording.hotspot === 'status') return 'AI sees the closed status acting like a stop sign before users understand the next-cohort option.';
  if (recording.hotspot === 'judges') return 'AI sees credibility interest, but that proof appears too late for hesitant visitors.';
  return 'AI maps attention back to the hero promise and checks whether the next action is specific enough.';
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-US').format(Number(value) || 0);
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
