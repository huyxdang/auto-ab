import { useState } from 'react';
import { mockResults } from '../data/mockResults.js';

export function useABLoop() {
  const [phase, setPhase] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function runLoop(url) {
    setError(null);
    setResult(null);

    const fetchPromise = getAnalysis(url).catch(() => ({ ...mockResults, url }));

    setPhase('crawling');
    await delay(800);
    setPhase('diagnosing');
    await delay(1000);
    setPhase('generating');
    await delay(1200);
    setPhase('benchmarking');

    const data = await fetchPromise;
    await delay(400);
    setResult({ ...data, url });
    setPhase('done');
  }

  function reset() {
    setPhase('idle');
    setResult(null);
    setError(null);
  }

  return { phase, result, error, runLoop, reset };
}

async function getAnalysis(url) {
  const response = await fetch('/api/analyze-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!response.ok) throw new Error('API error');
  return response.json();
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
