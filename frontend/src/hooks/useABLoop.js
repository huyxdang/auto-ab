import { useState } from 'react';
import { mockResults } from '../data/mockResults.js';

const BACKEND_URL = import.meta.env.VITE_API_URL || null;

export function useABLoop() {
  const [phase, setPhase] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function runLoop(url) {
    setError(null);
    setResult(null);

    try {
      setPhase('crawling');
      await delay(800);

      setPhase('diagnosing');
      await delay(1000);

      setPhase('generating');
      await delay(1200);

      setPhase('benchmarking');
      const data = await getAnalysis(url);

      await delay(700);
      setResult({ ...data, url });
      setPhase('done');
    } catch {
      await delay(700);
      setResult({ ...mockResults, url });
      setPhase('done');
    }
  }

  function reset() {
    setPhase('idle');
    setResult(null);
    setError(null);
  }

  return { phase, result, error, runLoop, reset };
}

async function getAnalysis(url) {
  if (!BACKEND_URL) return mockResults;

  const response = await fetch(`${BACKEND_URL}/analyze`, {
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
