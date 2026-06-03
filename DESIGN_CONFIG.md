# ISS-NMR Project Page — Design Configuration

## Color System (Nature Journal Style)

### CSS Variables (defined in `doc/static/css/index.css` `:root`)

```
/* Brand accent colors */
--nature-red:         #CC3300   /* Nature signature red — badges, section underlines, awards */
--nature-red-light:   #F5C5B5   /* Border for red elements */
--nature-red-bg:      #FFF5F2   /* Background for red badge */
--nature-teal:        #1A6FA8   /* Links, interactive — confident blue */
--nature-teal-dark:   #0D4F7C   /* Deep navy — hover / button dark state */

/* Button two-state palette */
--btn-light-bg:       #D6EEFF   /* Default: light blue bg */
--btn-light-border:   #7FB8DE   /* Default: medium blue border */
--btn-light-text:     #0D4F7C   /* Default: dark navy text */
--btn-dark-bg:        #0D4F7C   /* Hover: dark navy bg, white text */

/* Text hierarchy */
--text-primary:       #1F1F1F   /* Main body text */
--text-bold:          #111111   /* <strong> */
--text-italic:        #444444   /* <em> */
--text-secondary:     #555555   /* Captions, institution names */
--text-light:         #888888   /* Footnotes, timestamps */
--text-link:          #1A6FA8   /* Inline links */
--text-link-hover:    #0D4F7C

/* Backgrounds */
--background-primary:   #FAFAF8   /* Page base — warm off-white */
--background-secondary: #F3F1EC   /* Alternating sections (Abstract, Poster) */
--background-accent:    #E9E7E1   /* Pre/code, hover states */
--background-card:      #FFFFFF   /* Carousel cards, dropdowns */
--background-footer:    #2E2E2E   /* Dark footer */

/* Borders */
--border-color:       #DDDBD6   /* Standard warm border */
--border-strong:      #BBBBBB   /* Stronger dividers */

/* Aliases (used in generic components) */
--primary-color:  #2A6041
--primary-hover:  #1D4730
--accent-color:   #CC3300
```

### Hardcoded colors (not in variables)

| Selector | Property | Value | Reason |
|----------|----------|-------|--------|
| `footer a` | color | `#7DC5A8` | Light green readable on dark footer |
| `footer a:hover` | color | `#AADDC0` | Lighter on hover |
| `footer .content` | color | `#AAAAAA` | Muted text on dark bg |
| `code` | color | `#333333` | Monospace, slightly warm dark |
| `.copy-bibtex-btn.copied` | background | `#3D7A34` | Success green (Nature-ish) |

### Typography

| Element | Font | Weight | Color |
|---------|------|--------|-------|
| `.publication-title` (h1) | Times New Roman | 800 | `--text-primary` |
| `.title.is-3` (sections) | Times New Roman | 700 | `--text-primary` |
| Body | Inter | 400 | `--text-primary` |
| `<strong>` | inherit | 700 | `--text-bold` (#111111) |
| `<em>` | inherit, italic | inherit | `--text-italic` (#444444) |
| Author links | Inter | 600 | `--nature-teal` (#2A6041 deep forest green) |
| Institution text | Inter | 500 | `--text-secondary` |

### Key Element Styles

**Buttons (Paper / arXiv / Code)**

- Background: `#2A6041` (deep forest green), Hover: `#1D4730`
- Font size: `1.25rem` (20px), Weight: 600
- Border-radius: `8px`

**ICML Badge (`.venue-badge`)**

- Background: `#FFF5F2`, Border: `#F5C5B5`
- Text: `#CC3300`, Font size: `1.375rem` (22px), Weight: 600
- Border-radius: `2rem` (pill shape)
- Margin: `1.5rem` top, `0.75rem` bottom (balances column padding below)

**Section title underline (`.title.is-3::after`)**

- Width: `48px`, Height: `2px`, Color: `#CC3300`

**BibTeX pre block**

- Background: `--background-accent`, Left border: `3px solid #2A6041`

**Footer**

- Background: `#2E2E2E`, Top border: `3px solid #CC3300`

**Dropdown header**

- Background: `--background-secondary`, Bottom border: `2px solid #CC3300`

### Layout

| Property | Value |
|----------|-------|
| Container max-width | `1150px` |
| Hero-body padding | `4rem 1rem` |
| Border-radius (default) | `8px` |
| Border-radius (large) | `12px` |

### Font Sizes (key elements)

| Element | Size |
|---------|------|
| Title `.is-1` (Bulma) | `3rem` = 48px |
| Authors `.is-size-5` (Bulma) | `1.25rem` = 20px |
| Institution `.is-size-6` (Bulma) | `1rem` = 16px |
| ICML Badge | `1.375rem` = 22px |
| Buttons | `1.25rem` = 20px |
| Abstract body | `1.1rem` = ~18px |

---

*Style files: `doc/static/css/index.css` (custom), `doc/static/css/bulma.min.css` (framework)*
