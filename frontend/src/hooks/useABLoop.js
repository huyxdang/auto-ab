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
    hypothesis: 'Trust-first route: sell judge credibility before asking for the email.',
    changes: ['Promote judges and tracks beside the hero form', 'Replace poster dominance with judge proof carousel', 'Move agenda below conversion proof'],
    headline: 'Meet the judges, get the kit, then claim your next sprint invite',
    site: {
      ...data.variant?.site,
      headline: 'Meet the judges, get the kit, then claim your next sprint invite',
      status: 'Judge-backed next cohort waitlist',
      primaryCta: 'Get judge-backed invite',
      secondaryCta: 'Review judging tracks',
      sideTitle: 'Judge Proof Rail',
      sideCopy: 'Credibility moves from lower page sections into the first decision moment.',
      modules: ['Judges promoted above agenda', 'Track criteria added to hero', 'Poster becomes supporting proof'],
      experiments: ['Next test: judge-first vs kit-first', 'Track selector before email', 'Proof carousel timing'],
      stickyCta: 'Sticky mobile bar: Get invite + judging criteria',
    },
    uplift: `+${altLift.toFixed(0)}%`,
    liftPct: altLift,
  };

  const variantD = {
    ...data.variant,
    label: 'D',
    hypothesis: 'Mobile-first route: keep the next cohort CTA visible during scroll.',
    changes: ['Add sticky mobile invite bar', 'Condense hero facts into one availability strip', 'Move resources behind email capture'],
    headline: 'Save your next Codex sprint seat while you browse the agenda',
    site: {
      ...data.variant?.site,
      headline: 'Save your next Codex sprint seat while you browse the agenda',
      status: 'Mobile sticky invite test',
      primaryCta: 'Save next sprint seat',
      secondaryCta: 'Browse agenda first',
      sideTitle: 'Sticky Conversion Layer',
      sideCopy: 'The CTA follows high-intent visitors as they inspect agenda, judges, and resources.',
      modules: ['Sticky CTA follows scroll', 'Availability strip replaces closed card', 'Resources unlock after email'],
      experiments: ['Next test: sticky vs static CTA', 'Agenda-first mobile path', 'Email unlock resources'],
      stickyCta: 'Sticky mobile bar: Save seat + unlock CAR templates',
    },
    uplift: `+${Math.max(0, liftPct - 4).toFixed(0)}%`,
    liftPct: Math.max(0, liftPct - 4),
  };

  return { ...data, variants: [variantB, variantC, variantD] };
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
