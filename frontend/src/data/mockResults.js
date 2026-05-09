export const mockResults = {
  url: 'https://example.com',
  painPoints: [
    {
      section: 'Hero',
      type: 'Copy mismatch',
      severity: 'high',
      desc: 'Users expect pricing info; hero leads with a feature list.',
    },
    {
      section: 'CTA',
      type: 'Weak hierarchy',
      severity: 'high',
      desc: 'Primary button competes with three secondary links at the same visual weight.',
    },
    {
      section: 'Social proof',
      type: 'Trust gap',
      severity: 'medium',
      desc: 'Testimonials are below the fold; user objections occur earlier.',
    },
  ],
  baseline: {
    headline: 'Welcome to the AI platform for modern teams.',
    score: 71,
    cvr: '3.8%',
  },
  variant: {
    headline: 'Cut drop-off 30% before you ship a single line of code.',
    score: 86,
    cvr: '4.6%',
    changes: ['Headline rewritten for outcome clarity', 'CTA moved above fold', 'Trust section promoted'],
  },
  uplift: '+21%',
};
