import { useEffect, useRef, useState } from 'react';

const metrics = [
  { value: 24.8, suffix: '%', label: 'Average uplift', meta: 'Control vs Variant', decimals: 1 },
  { value: 3, prefix: '< ', suffix: 's', label: 'Analysis speed', meta: 'Time to first insight', decimals: 0 },
  { value: 10000, suffix: '+', label: 'Variants tested', meta: 'LLM-evaluated', decimals: 0 },
  { value: 99, suffix: '%', label: 'Statistical rigor', meta: 'Bayesian confidence', decimals: 0 },
];

export function MetricsStrip() {
  const sectionRef = useRef(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setActive(true);
          observer.disconnect();
        }
      },
      { threshold: 0.35 },
    );

    if (sectionRef.current) observer.observe(sectionRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="section metrics-section" id="metrics" ref={sectionRef}>
      <div className="container">
        <div className="center-heading">
          <p className="eyebrow">System capabilities</p>
        </div>
        <div className="metrics-grid">
          {metrics.map((metric) => (
            <MetricCard active={active} key={metric.label} metric={metric} />
          ))}
        </div>
      </div>
    </section>
  );
}

function MetricCard({ active, metric }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!active) return undefined;

    const duration = 1100;
    const startedAt = performance.now();
    let frame = 0;

    function tick(now) {
      const progress = Math.min((now - startedAt) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(metric.value * eased);
      if (progress < 1) frame = requestAnimationFrame(tick);
    }

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [active, metric.value]);

  const formatted = metric.decimals ? count.toFixed(metric.decimals) : Math.round(count).toLocaleString();

  return (
    <article className="metric-card">
      <div className="metric-topline">
        <span>{metric.meta}</span>
      </div>
      <strong>{metric.prefix || ''}{formatted}{metric.suffix}</strong>
      <h3>{metric.label}</h3>
      <div className="mini-bars" aria-hidden="true">
        <i /><i /><i /><i /><i /><i />
      </div>
    </article>
  );
}
