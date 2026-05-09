---
name: A/B Pilot Identity
colors:
  surface: '#0d1515'
  surface-dim: '#0d1515'
  surface-bright: '#333b3b'
  surface-container-lowest: '#080f10'
  surface-container-low: '#151d1d'
  surface-container: '#192121'
  surface-container-high: '#242b2c'
  surface-container-highest: '#2e3636'
  on-surface: '#dce4e4'
  on-surface-variant: '#bec8c9'
  inverse-surface: '#dce4e4'
  inverse-on-surface: '#2a3232'
  outline: '#889394'
  outline-variant: '#3e494a'
  surface-tint: '#83d3db'
  primary: '#83d3db'
  on-primary: '#00363b'
  primary-container: '#63b4bc'
  on-primary-container: '#004449'
  inverse-primary: '#006970'
  secondary: '#c3c7c5'
  on-secondary: '#2c3130'
  secondary-container: '#454a49'
  on-secondary-container: '#b5b9b7'
  tertiary: '#ffb689'
  on-tertiary: '#512300'
  tertiary-container: '#e09768'
  on-tertiary-container: '#612f08'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9ff0f8'
  primary-fixed-dim: '#83d3db'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f55'
  secondary-fixed: '#dfe3e1'
  secondary-fixed-dim: '#c3c7c5'
  on-secondary-fixed: '#181d1c'
  on-secondary-fixed-variant: '#434846'
  tertiary-fixed: '#ffdbc8'
  tertiary-fixed-dim: '#ffb689'
  on-tertiary-fixed: '#311300'
  on-tertiary-fixed-variant: '#6e3912'
  background: '#0d1515'
  on-background: '#dce4e4'
  surface-variant: '#2e3636'
typography:
  display-lg:
    fontFamily: Clash Display
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Clash Display
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Clash Display
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Satoshi
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Satoshi
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Satoshi
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Satoshi
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  section-gap: 48px
  layout-max-width: 1440px
---
## Brand & Style

The design system is engineered for high-stakes decision-making and technical precision. It targets data scientists, growth engineers, and product architects who value clarity over decoration. The aesthetic leans into **Technical Minimalism**, characterized by high-density information display, surgical accuracy in alignment, and a "dashboard-first" mentality.

The emotional response should be one of "controlled power"—the user should feel they are operating a sophisticated piece of machinery. Visuals avoid soft, organic shapes in favor of sharp geometry and structured data visualizations. There are no decorative gradients or "friendly" rounded corners; every element serves a functional purpose in the A/B testing workflow.

## Colors

The palette is strictly constrained to reinforce the technical nature of the product.

- **Background (#0e1212):** A deep, teal-tinted black that provides more depth than pure neutral black, reducing eye strain during long analytical sessions.
- **Surface (#141918):** Used for cards and elevated containers to create a subtle shift in depth without relying on aggressive borders.
- **Primary Accent (#63b4bc):** A cold, crystalline teal used sparingly for CTA buttons, active states, and focal data points.
- **Typography & UI:** High-contrast white (#FFFFFF) for headers, muted slate (#8c9494) for secondary metadata, and very low-opacity teal borders for structural separation.

## Typography

This design system utilizes a tiered typographic approach to ensure data density remains legible.

- **Headings:** Clash Display provides a "sharp" and modern architectural feel. Use it for page titles and significant section headers.
- **Body:** Satoshi is the workhorse, chosen for its exceptional legibility and neutral character in technical contexts.
- **Data & Code:** For statistical outputs, confidence intervals, and ID strings, use a monospaced font (JetBrains Mono) to ensure character alignment in tables.
- **Scaling:** On mobile devices, `display-lg` scales down to 32px, and `headline-lg` scales to 24px to maintain layout integrity.

## Layout & Spacing

The layout is built on a **12-column fixed-width grid** for desktop, centered on the viewport. This ensures that large-scale data visualizations do not become overly distorted on ultrawide monitors.

- **Rhythm:** An 8px base unit drives all spacing. Component heights are strictly regulated (32px, 40px, 48px).
- **Density:** The system prioritizes "Information Density." Negative space is used strategically to group related metrics, but never at the expense of requiring excessive scrolling.
- **Breakpoints:**
  - Mobile (0-767px): Single column, 16px margins.
  - Tablet (768-1023px): 6 columns, 24px margins.
  - Desktop (1024px+): 12 columns, 32px margins, 1440px max-width.

## Elevation & Depth

Depth in this design system is achieved through **Tonal Layering** and **Luminescent Borders** rather than traditional drop shadows.

- **Base Layer:** Background (#0e1212) for the canvas.
- **Mid Layer:** Surface (#141918) for main content cards. These cards use a 1px solid border of #ffffff (10% opacity) to define edges.
- **Interactive Layer:** Elements like active dropdowns or hovered buttons use a subtle "Teal Glow"—a drop shadow with 0px offset, 12px blur, and #63b4bc at 20% opacity.
- **Glass Effects:** Used exclusively for floating modals or sticky navigation headers. Background-blur (12px) is combined with a semi-transparent version of the Surface color.

## Shapes

The shape language balances modern software aesthetics with technical rigor.

- **Containers:** All cards, dashboard panels, and modal containers use a **16px radius**. This softens the "industrial" feel just enough to make the interface feel premium.
- **Controls:** Interactive elements like chips, status indicators, and primary action buttons use a **999px (Pill)** radius. This creates a distinct visual hierarchy between "content" (square-ish) and "actions" (round).
- **Inputs:** Text fields and data inputs use a smaller **8px radius** to maximize internal space for text.

## Components

- **Buttons:**

  - *Primary:* Solid Teal (#63b4bc) with black text. Pill-shaped.
  - *Secondary:* Ghost style with a 1px #63b4bc border.
  - *States:* On hover, add a subtle teal outer glow.
- **Data Cards:**

  - Background: #141918.
  - Border: 1px #ffffff (10% opacity).
  - Header: Satoshi Bold 12px All-caps.
- **Input Fields:**

  - Darker than the surface (#0e1212) to create an "inset" feel.
  - Focused state: 1px Teal border with a 4px teal outer glow.
- **Status Pills:**

  - Use monochromatic variants of the functional colors (e.g., a dark green background with a bright green dot for "Active" tests).
- **Technical List Items:**

  - Use 1px bottom borders for list separation. Use monospaced fonts for numerical columns to ensure vertical alignment of decimal points.
- **Charts:**

  - Line charts should use 2px stroke weights. Grid lines must be very faint (#ffffff at 5% opacity). No fills under the lines unless representing "Confidence Intervals."
