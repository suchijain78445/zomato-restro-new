---
name: Lumina Noir
colors:
  surface: '#10131a'
  surface-dim: '#10131a'
  surface-bright: '#363940'
  surface-container-lowest: '#0b0e14'
  surface-container-low: '#191c22'
  surface-container: '#1d2026'
  surface-container-high: '#272a31'
  surface-container-highest: '#32353c'
  on-surface: '#e1e2eb'
  on-surface-variant: '#e4bebc'
  inverse-surface: '#e1e2eb'
  inverse-on-surface: '#2e3037'
  outline: '#ab8987'
  outline-variant: '#5b403f'
  surface-tint: '#ffb3b1'
  primary: '#ffb3b1'
  on-primary: '#680011'
  primary-container: '#ff535a'
  on-primary-container: '#5b000e'
  inverse-primary: '#bb162c'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#10131a'
  on-background: '#e1e2eb'
  surface-variant: '#32353c'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  ai-chat:
    fontFamily: Plus Jakarta Sans
    fontSize: 17px
    fontWeight: '500'
    lineHeight: '1.5'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  xxl: 64px
  container-max: 1280px
  gutter: 20px
---

## Brand & Style
The design system is centered around a high-end, futuristic AI concierge experience. The personality is sophisticated, predictive, and ultra-modern. It utilizes a **Glassmorphism** style layered over a deep, obsidian-like canvas. 

The aesthetic leverages high-contrast vibrant accents against a dark slate background to evoke a sense of late-night luxury and culinary precision. The emotional response is one of effortless intelligence—where the UI feels like a premium translucent layer floating over a rich, textured world of gastronomy.

## Colors
This design system uses a curated dark palette to emphasize depth and "glow" effects. 
- **Primary (Zomato Red):** Reserved for core actions and brand identity.
- **Secondary (Violet Glow):** Used exclusively for AI-driven features, suggestions, and concierge interactions.
- **Tertiary (Amber/Gold):** Utilized for premium status, ratings, and special highlights.
- **Success (Emerald):** Dedicated to positive outcomes, order confirmations, and health ratings.

The background is a deep charcoal slate (#0B0E14) that allows the glassmorphic surfaces and light-leaks to appear vibrant without overwhelming the user.

## Typography
Plus Jakarta Sans provides a friendly yet modern geometric feel that balances the technical glassmorphism. Headlines use tighter letter-spacing and heavier weights to command attention. Body text is set with generous line-height to ensure legibility against dark backgrounds. For AI-generated text, use the `ai-chat` token which features a medium weight for enhanced clarity during interaction.

## Layout & Spacing
This design system utilizes a **fluid grid** model for mobile and a **12-column fixed grid** for desktop (max-width 1280px). Spacing follows a 4px base unit, focusing on "breathing room" to maintain the premium feel. 

- **Mobile:** 4-column grid, 16px margins.
- **Tablet:** 8-column grid, 24px margins.
- **Desktop:** 12-column grid, 40px margins.

Use `xl` and `xxl` spacing for separating major content sections to allow the background glows and glass blurs to remain visible and distinct.

## Elevation & Depth
Depth is not communicated through traditional shadows, but through **Tonal Layering** and **Backdrop Blurs**.
- **Level 0 (Base):** Deep Charcoal (#0B0E14).
- **Level 1 (Cards/Surfaces):** Semi-transparent white (3% opacity) with a 16px backdrop blur and a subtle 1px border (8% white).
- **Level 2 (Floating/Modals):** Same as Level 1 but with a 32px backdrop blur and an external "glow" using a low-opacity Primary or Secondary color (e.g., 10% Crimson glow).
- **AI Highlight:** Elements associated with the Concierge should feature a 1px "gradient stroke" (Crimson to Violet) to distinguish them from static UI.

## Shapes
The design uses **Rounded** geometry (base 0.5rem). 
- **Buttons and Inputs:** 0.5rem (8px) for a structured, professional look.
- **Cards and Containers:** 1rem (16px) to emphasize the soft, organic nature of the glassmorphic panes.
- **AI Avatars/Icons:** Full pill-shape (3rem+) to signify the "fluid" and "dynamic" nature of the concierge.

## Components
- **Buttons:**
  - *Primary:* Solid Crimson (#E23744) with white text.
  - *AI Action:* Gradient (Crimson to Violet) with a subtle outer glow on hover.
  - *Secondary:* Glass surface with white 1px border.
- **Glass Cards:** Must feature `backdrop-filter: blur(16px)` and a subtle top-down linear gradient border to simulate light hitting the edge.
- **Input Fields:** Darker than the background (#06080A) with a Crimson focus ring and 16px padding.
- **AI Chat Bubbles:** Violet-tinted glass for AI responses; standard glass for user input.
- **Rating Chips:** Use Amber/Gold text with a semi-transparent gold background (10% opacity) for high-end restaurants.
- **Concierge Pulse:** An animated, soft-glowing violet ring used to indicate the AI is "thinking" or processing a request.