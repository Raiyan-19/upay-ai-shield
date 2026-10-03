Upay Light Design System

Overview

The Upay Light Design System is an airy, high-clarity fintech visual framework
inspired by Upay’s core brand elements: the signature Upay Yellow and Cobalt
Blue dual-figure emblem.

This system eliminates heavy dark surfaces in favor of a clean, light-first
canvas composed of crisp whites, soft cool-gray tints, and vibrant brand
accents. It prioritizes legibility, financial transparency, lightweight
interaction patterns, and natural touch affordances across mobile apps and web
platforms.

1. Color Palette (Light System)

Primary Brand
├── Upay Yellow:     #FFCD00  (Primary CTA, highlights, active badges)
├── Upay Yellow Light:#FFF3B3 (Subtle yellow container tint, active surface)
├── Upay Blue:       #005BAC  (Primary brand headers, key actions, icons)
├── Upay Blue Tint:  #E8F2FC  (Soft blue pill background, icon backdrops)
└── Upay Blue Dark:  #003E75  (Deep brand text, accessible high-contrast links)

Surfaces & Backgrounds
├── Base Canvas:     #FAFBFC  (Main page backdrop, clean and glare-free)
├── Surface Pure:    #FFFFFF  (Cards, modals, bottom sheets, form fields)
├── Surface Muted:   #F1F5F9  (Divider strips, inactive states, chips)
└── Banner Yellow:   #FFD200  (Wavy locator & campaign highlight panels)

Typography & Neutrals
├── Text Primary:    #0F172A  (Headers, Bengali wordmark, high-emphasis text)
├── Text Secondary:  #475569  (Body copy, transactional explanations)
├── Text Tertiary:   #94A3B8  (Placeholders, timestamps, subtle borders)
└── Border Subtle:   #E2E8F0  (Card outlines, table borders, dividers)

System & Endorsement
├── UCB Red:         #E30613  (UCB endorsement badge, error states)
├── Success Green:   #10B981  (Completed transactions, balance positive)
└── Warning Amber:   #F59E0B  (Pending confirmations, advisory alerts)

2. Typography

Optimized for dual-script readability in both English and Bengali (উপায়).

  - English Font: Inter, -apple-system, Segoe UI, sans-serif
  - Bengali Font: Hind Siliguri, Noto Sans Bengali, sans-serif
  - Weight Distribution: Light (300), Regular (400), Medium (500), Semi-Bold
    (600), Bold (700)

Type Scale

| Role                   | Font Size | Line Height | Weight                  | Color Target               |
| :--------------------- | :-------- | :---------- | :---------------------- | :------------------------- |
| **Display Header**     | `36px`    | `44px`      | Bold (`700`)            | Upay Blue (`#005BAC`)      |
| **Section Title (H1)** | `28px`    | `36px`      | Bold (`700`)            | Upay Blue (`#005BAC`)      |
| **Locator Title**      | `26px`    | `34px`      | Bold (`700`)            | Text Primary (`#0F172A`)   |
| **Card Header (H2)**   | `20px`    | `28px`      | Semi-Bold (`600`)       | Upay Blue Dark (`#003E75`) |
| **Footer Column (H3)** | `16px`    | `24px`      | Bold (`700`), Uppercase | Upay Blue (`#005BAC`)      |
| **Service Label**      | `15px`    | `20px`      | Semi-Bold (`600`)       | Text Primary (`#0F172A`)   |
| **Body Regular**       | `14px`    | `22px`      | Regular (`400`)         | Text Secondary (`#475569`) |
| **Caption / Helper**   | `12px`    | `16px`      | Medium (`500`)          | Text Tertiary (`#94A3B8`)  |

3. Spacing & Layout

Built on a strict 8px baseline grid for balanced rhythm and consistent UI
density:

[4px]  xxs : Micro gap, icon-to-badge offset
[8px]  xs  : Inline tag padding, field icon spacing
[16px] sm  : Card internal padding, button inline padding (compact)
[24px] md  : Service grid gaps, button horizontal padding (standard)
[32px] lg  : Card-to-card margin, stack section gap
[48px] xl  : Component cluster spacing, modal margins
[64px] 2xl : Major section padding (Desktop/Web)

4. Border Radius

  - sm (6px): Tags, transaction chips, micro status pills.
  - md (12px): App store badges, input form containers.
  - lg (20px): Service action cards, floating promotional banners.
  - pill (9999px): Interactive buttons (View More), search inputs, circular
    avatar icons.

5. Light Elevation & Shadows

Diffused, ambient shadows with zero harsh black tones to maintain an airy feel:

  - shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)
      - Usage: Unfocused inputs, resting cards.
  - shadow-card: 0 4px 20px rgba(0, 91, 172, 0.06)
      - Usage: Service tiles, dropdown menus, transaction summaries.
  - shadow-hover: 0 10px 25px rgba(0, 91, 172, 0.10)
      - Usage: Card hover states, interactive buttons on mouse-over.
  - shadow-pill: 0 4px 14px rgba(255, 205, 0, 0.35)
      - Usage: Yellow CTA focus/active states.

6. Components

6.1 Brand Header & Logo Mark

      ( Yellow )   ( Blue )
          ●           ●
          ╰─╮       ╭─╯
            ╰───────╯
              উপায়
       [একটি UCB প্রতিষ্ঠান]

  - Mark Structure: Two mirrored, curved figures leaning toward each other with
    round circular heads to create a smiling "U" gesture.
      - Left Figure: Upay Yellow (#FFCD00).
      - Right Figure: Upay Blue (#005BAC).
  - Logotype: Custom bold Bengali script উপায় in #0F172A (Text Primary).
  - Endorsement Lockup: একটি UCB প্রতিষ্ঠান placed underneath with the distinct
    red oval UCB badge (#E30613).

6.2 Buttons & Action Triggers

Primary Button (View More / Main CTA)

  - Shape: Full pill (border-radius: 9999px).
  - Background: Solid Upay Yellow (#FFCD00).
  - Text: 15px Semi-Bold, #0F172A (Dark Charcoal).
  - Height: 48px (min-width 160px).
  - Shadow: shadow-pill.
  - States:
      - Hover: Background #FFD633, translateY(-1px).
      - Active: Background #E5B800, scale(0.98).

Secondary Button

  - Shape: Full pill (border-radius: 9999px).
  - Background: White (#FFFFFF).
  - Border: 1.5px solid Upay Blue (#005BAC).
  - Text: 15px Semi-Bold, Upay Blue (#005BAC).
  - States:
      - Hover: Background Upay Blue Tint (#E8F2FC).

6.3 Service Grid Cards

  - Container: White (#FFFFFF), border-radius: 20px, border 1px solid #E2E8F0,
    padding 24px 16px.
  - Shadow: shadow-card.
  - Iconography Format:
      - Dual-tone line-art with flat color fills.
      - Blue (#005BAC) and Yellow (#FFCD00) as dominant tones; soft pastel
        accents for utility items.
  - Services Supported:
      - Cash In: Smartphone pulling cash into rear wallet.
      - Cash Out: Smartphone extracting currency outward.
      - Send Money: Taka bank note (৳) with dynamic directional flight arrows.
      - Make Payment: Linear QR Code framed alongside a phone scanner viewport.
      - Add Money: Layered cardholder with a circular plus badge (+).
      - Pay Bill: Smartphone screen containing utility icons (electric pole,
        burner flame, water tap, satellite dish).
  - Label: Centered below icon, 15px Semi-Bold #0F172A, top margin 12px.

6.4 Transition Banner ("Where to Find Us")

  - Top Divider: Organic, asymmetrical wave divider SVG transitioning seamlessly
    from White (#FFFFFF) to Upay Yellow (#FFD200).
  - Background: Solid Upay Yellow (#FFD200).
  - Content Styling:
      - Heading: 26px Bold, Text Primary (#0F172A).
      - Paragraph: 15px Regular, Text Primary (#0F172A) with high line-height
        (24px).
  - Locator Illustration: Stylized light-yellow map vector with concentric
    dual-ring blue location pins (#005BAC).

6.5 Light Footer Architecture

Replaces all dark slate containers with a clean, low-contrast, light surface
layout:

  - Background: Soft Gray Canvas (#F8FAFC).
  - Top Border: 1px solid #E2E8F0.
  - Column Headings: Upay Blue (#005BAC), 14px Bold, Uppercase, letter-spacing
    0.5px.
  - Link Items: #475569 Regular 14px, transition to Upay Blue (#005BAC) on
    hover.
  - Contact Line Items:
      - Circular icon containers: #FFFFFF fill with 1px solid #E2E8F0 and
        #005BAC line glyphs.
      - Values (e.g., 16268, branch addresses) in #0F172A.
  - Social Media Icons: 36px circular white pills with subtle gray borders and
    Upay Blue brand icons.
  - App Download Badges: Light mode store buttons (clean black pill containers
    on light gray ground).
  - Legal & Copyright: Bottom divider strip (#E2E8F0) with subtext in #94A3B8.

7. Do's and Don'ts

1.  Do use Upay Yellow (#FFCD00) on white or light-gray backgrounds exclusively
    with dark charcoal text (#0F172A) for strict contrast compliance.
2.  Do keep cards and panels crisp white (#FFFFFF) over the soft base canvas
    (#FAFBFC) to preserve spatial depth without needing heavy borders.
3.  Do utilize the organic curved wave pattern when introducing full-bleed
    yellow campaign blocks.
4.  Don't use black, dark gray, or slate backdrops for navigation, footers, or
    modals.
5.  Don't swap the logo colors (the left person must always be Yellow, the right
    person must always be Blue).
6.  Don't apply harsh black drop shadows to buttons or cards; use subtle tinted
    shadows (rgba(0, 91, 172, 0.06) or rgba(255, 205, 0, 0.35)).
7.  Do use full pill radii (9999px) on all primary CTA buttons for
    touch-friendly affordance.
