Then your positioning should be:

Demo: simulated users to prove the optimization loop.
Real app: real user behavior data powers the loop.

So you are not building a fake A/B testing tool. You are building:

An autonomous website optimization system that learns from real user behavior and generates better website variants.

Better Product Hypothesis

Use this:

Website owners collect user behavior data through analytics, heatmaps, and session recordings, but they struggle to translate that data into concrete design improvements. We believe an AI system can automatically analyze real user behavior, identify conversion bottlenecks, generate improved website variants, and continuously run an optimization loop. For the hackathon demo, we simulate user behavior to demonstrate the full workflow before real traffic is available.

This is much more credible.

Real Product Loop
Real user visits website
        ↓
Collect behavior data
        ↓
Generate heatmap / drop-off / friction analysis
        ↓
AI identifies conversion problems
        ↓
AI generates new website variant
        ↓
Run A/B test
        ↓
Measure real conversion lift
        ↓
Keep improving
Demo Loop
Input target customer + website goal
        ↓
Simulate user behavior
        ↓
Generate synthetic heatmap
        ↓
Detect likely friction points
        ↓
Generate improved website
        ↓
Show before/after

The demo is basically a sandbox version of the real system.

Why Your Product Over Alternatives?

Current tools:

Hotjar / Microsoft Clarity show what users do.
Optimizely / VWO help run A/B tests.
Google Analytics gives traffic and conversion data.
Webflow / Framer / Wix AI help generate websites.

But your product connects all of them into one loop:

It does not just show analytics.
It turns behavior data into new website versions automatically.

That is the key.

Sharp Positioning

Say this:

Existing tools tell you what happened. Our product decides what to change next.

That is the money line.

Target Customer

Best target:

Small businesses, indie founders, agencies, and e-commerce brands

They have enough traffic to collect data, but not enough expertise or time to manually analyze it.

Their pain:

“I can see people are leaving my website, but I don’t know why or what to change.”

Their gain:

“My website improves itself using real visitor behavior.”

Current Demo Priorities

The local frontend should present the demo as a sandbox version of the real product loop, not as a fake A/B testing toy.

Demo narrative:

1. Paste a URL and choose an analytics source.
2. Show simulated visitor behavior: sessions, heatmap, recordings, bounce/friction tags.
3. Hand those behavior signals to AI.
4. Show friction diagnosis before recommendations.
5. Show Control vs Variant diff with predicted uplift.
6. Show the optimization loop progressing from ingest to diagnose to generate to test.

Important UX rules:

Do not scroll users back to the page top during the demo flow.
Do not reset scan state when START AI is clicked.
Do not show zero metrics on first load.
Avoid premature production claims like API access unless framed as early access.
Use clear labels: RUN DEMO, METRICS, WAITLIST, EARLY ACCESS.

Hero Product Moment

The strongest product moment is not the heatmap alone. It is the handoff from behavior data to AI-generated website improvements.

The result panel should always make this sequence obvious:

Behavior signals → friction diagnosis → Control vs Variant diff → predicted conversion lift.

Latest Demo Direction

The demo should analyze the actual local target site at:

website2/index.html

Do not represent behavior analysis as a generic fake heatmap or recreated mini HTML screenshot. The behavior panel should feel like auto-ab parsed the real page structure and mapped user behavior to actual DOM/page elements.

Behavior Evidence Direction

Use element-based behavior analysis instead of fake heatmap-first storytelling.

Important website2 elements:

- .hero-copy h1
  Copy: "Build and ship an AI agent in 1 day."
  Signal: high viewport attention.
  Meaning: strong promise, but can be sharpened around next-session outcome.

- .facts .status-closed
  Copy: "Registration Closed"
  Signal: exits after noticing closed state.
  Meaning: closed status creates dead-end anxiety before fallback CTA is clear.

- #waitlist
  Copy: "Enter email for next event waitlist"
  Signal: rage-click or hesitation clusters.
  Meaning: waitlist fallback is useful but visually feels secondary to the closed event.

- [data-cta="luma"]
  Copy: "View Luma Event"
  Signal: intent leakage.
  Meaning: secondary event link pulls users away from conversion.

- #judges
  Copy: "Track judges"
  Signal: high trust, low reach.
  Meaning: credibility is strong but appears too late for hesitant visitors.

Session Recording Direction

Session recordings should simulate mouse navigation, not just list tags.

Each recording should drive a mouse path replay with steps such as:

- read hero promise
- noticed Registration Closed
- hovered waitlist form
- clicked Join Waitlist
- escaped to Luma
- scrolled to agenda
- checked judges
- submitted waitlist

Generated Website Direction

The AI result should not rely on the benchmark report as the primary product moment.

The main result panel should show:

1. Behavior signals
2. Friction diagnosis
3. Original website vs generated improved website
4. Predicted lift
5. Generated page improvements
6. Next optimization loop

The generated website comparison should use the actual website2 structure, not a generic preview.

Original Website Preview

Must reflect website2:

- Brand: Codex Community Vietnam
- Nav: Agenda, Judges, Join Waitlist
- Eyebrow: AI Hackathon - Weekend Build with Codex and CAR
- Headline: Build and ship an AI agent in 1 day.
- Subhead: A hands-on Ho Chi Minh City build session for engineers, founders, and operators learning practical agentic engineering with OpenAI Codex and Codex Auto Runner.
- Trust chips: 175 builders going, Sold out fast, 3 build tracks
- Facts: May 09, HCMC, Registration Closed
- Waitlist form
- Secondary CTAs: View Luma Event, CAR Repository
- Poster card
- Lower sections: event metrics, agenda, judges, conversion quote, footer

Generated Website Brainstorm

Primary generated variant should focus on fallback conversion for sold-out traffic.

Recommended generated version:

Status:
This session is full - next cohort waitlist open

Headline:
Join the next Codex sprint and ship your first AI agent in one day

Subhead:
Get early access to the next hands-on build day, Codex setup guide, CAR workflow templates, and team matching before registration opens.

Primary CTA:
Join next cohort waitlist

Secondary CTA:
See what builders ship

Trust proof above CTA:
175 builders registered - Sold out fast - 3 build tracks - Judges from Scale, Depth, Impact

Generated Improvements

Show page-level improvements, not generic variant text:

- Closed status reframed into a next-cohort availability banner
- Waitlist CTA moved above secondary Luma and GitHub links
- Judge and builder proof promoted before agenda
- Hero copy rewritten around shipping the first working agent
- Sticky mobile waitlist CTA queued for the next optimization loop

Comparison Controls

The result panel should support:

- Side by side
- View original
- View generated

The default should be side-by-side on desktop and stacked on mobile.

Important Product Rule

Heatmap should not be built from fake HTML screenshots anymore.

Use element-based analysis for behavior evidence.
Use old-vs-new website preview only in the generated result section.

OpenAI Integration Direction

Use the local .env OpenAI API key only from server-side code. Never expose the key to browser code, logs, or frontend bundles.

The generation endpoint should accept behavior signals, friction diagnosis, and website2 page context, then return structured JSON for generated website variants. The frontend should fall back to mockResults when the endpoint fails or the key is unavailable.
