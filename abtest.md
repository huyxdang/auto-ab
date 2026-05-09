You decide **B** by forming a clear hypothesis from the user behavior data.

Not:

> “Let’s make the website prettier.”

But:

> “Users are dropping because X, so we change Y, and expect Z to improve.”

## Formula

```text
Observation → Diagnosis → Change → Expected result
```

Example:

```text
Observation:
Users scroll to pricing but do not click “Buy”.

Diagnosis:
They are interested, but not convinced the price is worth it.

Change for B:
Move testimonials and benefits above pricing.

Expected result:
More CTA clicks after pricing.
```

That is how B is decided.

---

## Example 1: Weak headline

Data:

```text
High attention on hero
Low CTA click rate
Fast drop-off after first section
```

Hypothesis:

> Users notice the page, but they do not understand the value fast enough.

Version B:

```text
Change headline from:
“AI Website Optimization Platform”

To:
“Find out why visitors leave — then generate a better landing page automatically”
```

---

## Example 2: CTA problem

Data:

```text
Users hover over CTA
Few users click
```

Hypothesis:

> CTA is too vague or too high-commitment.

Version B:

```text
Change CTA from:
“Get Started”

To:
“Get Free Website Diagnosis”
```

---

## Example 3: Pricing drop-off

Data:

```text
Many users exit at pricing
Low scroll after pricing
```

Hypothesis:

> Users see the price before they understand enough value.

Version B:

```text
Move social proof above pricing
Add “What you get” bullets
Add FAQ under pricing
```

---

## Example 4: Users ignore important section

Data:

```text
Low heatmap attention on feature section
Low scroll depth
```

Hypothesis:

> The page is too long or the section is not visually scannable.

Version B:

```text
Shorten feature copy
Use 3 benefit cards
Move strongest benefit higher
```

---

# For your product, B should be generated like this

```text
1. Read analytics data
2. Identify biggest conversion bottleneck
3. Pick one main hypothesis
4. Generate a variant that tests only that hypothesis
5. Predict which metric should improve
```

The important part: **B should usually test one major idea, not 10 changes at once.**

Bad B:

```text
New headline
New colors
New layout
New pricing
New CTA
New testimonials
New images
```

Why bad? If B wins, you do not know which change caused it.

Good B:

```text
Only improve hero messaging and CTA.
```

Now you know what you tested.

---

## In your AI system

Your backend should output something like:

```json
{
  "hypothesis": "Users are interested but do not understand the value quickly enough.",
  "evidence": [
    "High hero attention",
    "Low CTA click rate",
    "Fast drop-off after first section"
  ],
  "variant_b_changes": [
    {
      "section": "hero",
      "change": "Rewrite headline to focus on user outcome"
    },
    {
      "section": "hero_cta",
      "change": "Change CTA from 'Get Started' to 'Get Free Website Diagnosis'"
    }
  ],
  "expected_metric_lift": {
    "cta_click_rate": "+20%",
    "bounce_rate": "-12%"
  }
}
```

## Simple answer

**B is not random. B is the AI’s best proposed fix for the biggest detected conversion problem.**
