import { useState } from 'react';

export function CtaSection() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const canSubmit = email.includes('@') && email.includes('.');

  function handleSubmit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitted(true);
  }

  return (
    <section className="section cta-section" id="cta">
      <div className="container cta-card">
        <div>
          <p className="eyebrow">Early access</p>
          <h2>Your next winning variant is one paste away.</h2>
          <p>Plug the loop into your site, connect real behavior data, and let the product decide what to improve next.</p>
        </div>
        <form className="cta-form" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="email-input">Email address</label>
          <input
            id="email-input"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="founder@company.com"
            type="email"
          />
          <button className="button primary" disabled={!canSubmit} type="submit">Request early access</button>
          {submitted ? <p className="success-message">Request captured. We will follow up with access details.</p> : null}
        </form>
        <p className="stack-line">React · LLM judge · Supabase · REST API</p>
      </div>
    </section>
  );
}
