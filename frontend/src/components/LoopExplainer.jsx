import { useEffect, useRef, useState } from 'react';

const steps = [
  {
    number: '01',
    title: 'Ingest & Map',
    description: 'Parse your DOM and map visible modules, copy blocks, CTAs, and trust surfaces instantly.',
  },
  {
    number: '02',
    title: 'Diagnose Friction',
    description: 'Cluster likely drop-off points by weak hierarchy, trust gap, copy mismatch, and overload.',
  },
  {
    number: '03',
    title: 'Generate Variants',
    description: 'LLMs draft high-converting copy and layout changes from behavioral signals and guardrails.',
  },
  {
    number: '04',
    title: 'Converge & Deploy',
    description: 'Benchmark the new treatment, route the winner, and restart the optimization loop.',
  },
];

export function LoopExplainer({ phase }) {
  const sectionRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const activeIndex = getActiveIndex(phase);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.25 },
    );

    if (sectionRef.current) observer.observe(sectionRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section className={`section loop-section ${visible ? 'is-visible' : ''}`} id="how" ref={sectionRef}>
      <div className="container">
        <div className="center-heading wide">
          <h2>The Optimization Loop</h2>
          <p>Continuous, automated refinement of your funnel.</p>
        </div>
        <div className="timeline">
          {steps.map((step, index) => (
            <article className={`timeline-card ${activeIndex === index ? 'is-active' : ''}`} key={step.title} style={{ '--delay': `${index * 120}ms` }}>
              <span className="step-number">{step.number}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function getActiveIndex(phase) {
  if (['connected', 'crawling'].includes(phase)) return 0;
  if (phase === 'diagnosing') return 1;
  if (phase === 'generating') return 2;
  if (['testing', 'done'].includes(phase)) return 3;
  return -1;
}
