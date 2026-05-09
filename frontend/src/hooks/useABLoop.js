import { useState } from 'react';
import { mockResults } from '../data/mockResults.js';

const WEBSITE2_CONTEXT = {
  sourceFile: 'website2/index.html',
  goal: 'Convert sold-out event visitors into next cohort waitlist signups.',
  elements: [
    {
      selector: '.hero-copy h1',
      copy: 'Build and ship an AI agent in 1 day.',
      signal: '82% viewport attention',
      diagnosis: 'Strong promise, but can be sharpened around next-session outcome.',
    },
    {
      selector: '.facts .status-closed',
      copy: 'Registration Closed',
      signal: '38% exits after noticing',
      diagnosis: 'Closed status creates dead-end anxiety before fallback CTA is clear.',
    },
    {
      selector: '#waitlist',
      copy: 'Enter email for next event waitlist',
      signal: '14 rage-click clusters',
      diagnosis: 'Waitlist fallback is useful but visually feels secondary to the closed event.',
    },
    {
      selector: '[data-cta="luma"]',
      copy: 'View Luma Event',
      signal: '23% intent leakage',
      diagnosis: 'Secondary event link pulls users away from conversion.',
    },
    {
      selector: '#judges',
      copy: 'Track judges',
      signal: 'High trust, low reach',
      diagnosis: 'Credibility is strong but appears too late for hesitant visitors.',
    },
  ],
};

export function useABLoop() {
  const [phase, setPhase] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [winner, setWinner] = useState(null);
  const [target, setTarget] = useState({ url: '', source: 'simulated' });
  const [pendingFetch, setPendingFetch] = useState(null);

  async function runConnect(url, source = 'simulated') {
    setError(null);
    setResult(null);
    setWinner(null);
    setTarget({ url, source });

    const fetchPromise = getAnalysis(url, source).catch(() => ({ ...mockResults, url, analyticsSource: source }));
    setPendingFetch(() => fetchPromise);

    setPhase('connecting');
    await delay(1400);
    setPhase('connected');
  }

  async function runAnalysis() {
    if (!pendingFetch) return;

    setPhase('crawling');
    await delay(800);
    setPhase('diagnosing');
    await delay(1100);
    setPhase('generating');
    await delay(1400);

    const data = await pendingFetch;
    const dual = expandToTwoVariants(data);
    setResult({ ...dual, url: target.url, analyticsSource: target.source });

    setPhase('testing');
    await delay(2200);
    setWinner(pickWinner(dual));
    setPhase('done');
  }

  function reset() {
    setPhase('idle');
    setResult(null);
    setError(null);
    setWinner(null);
    setPendingFetch(null);
  }

  return { phase, result, error, winner, target, runConnect, runAnalysis, reset };
}

async function getAnalysis(url, source) {
  const response = await fetch('/api/analyze-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, analytics_source: source, page_context: WEBSITE2_CONTEXT }),
  });
  if (!response.ok) throw new Error('API error');
  return response.json();
}

function expandToTwoVariants(data) {
  if (Array.isArray(data.variants) && data.variants.length >= 2) return data;

  const recs = data.variant?.changes || [];
  const liftPct = parseFloat((data.uplift || '+0%').replace(/[^0-9.\-]/g, '')) || 0;

  const variantB = {
    ...data.variant,
    label: 'B',
    hypothesis: recs[0] || 'Rewrite the hero around a specific outcome.',
    changes: recs.slice(0, 2),
    uplift: `+${liftPct.toFixed(0)}%`,
    liftPct,
  };

  const altLift = Math.max(0, liftPct - 6 - Math.random() * 4);
  const variantC = {
    ...data.variant,
    label: 'C',
    hypothesis: recs[2] || recs[1] || 'Reorder pricing and proof to build trust earlier.',
    changes: recs.slice(2, 4).length ? recs.slice(2, 4) : recs.slice(1, 3),
    headline: rephrase(data.variant?.headline),
    uplift: `+${altLift.toFixed(0)}%`,
    liftPct: altLift,
  };

  return { ...data, variants: [variantB, variantC] };
}

function pickWinner(data) {
  const [b, c] = data.variants;
  return b.liftPct >= c.liftPct ? 'B' : 'C';
}

function rephrase(headline) {
  if (!headline) return 'Stop guessing. Ship the next test in one click.';
  return headline.replace(/\.$/, '') + ' — without writing a line of code.';
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
