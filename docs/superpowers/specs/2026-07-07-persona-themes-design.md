# Game-Inspired Themes — Design

## Summary
Add three game-inspired themes (Phantom Red, Golden TV, Deep Water) to the existing theme system, each with light and dark variants.

## Theme Definitions

### Phantom Red (Comic, Red)
- **Mood**: rebellious, punk-comic, high contrast
- **Dark**: near-black `#0d0d0d` bg, `#d92323` accent red, white text, `#1a0d0d` cards
- **Light**: comic-paper off-white `#f5f0eb` bg, `#d92323` accent, near-black text, `#eee8e3` cards
- **Positive**: `#22c55e` green, **Negative**: `#ef4444` red

### Golden TV (TV, Yellow)
- **Mood**: upbeat, bright, warm retro
- **Dark**: charcoal `#1a1a1a` bg, `#faa622` gold accent, `#ffe52c` yellow, warm white text
- **Light**: cream `#fef9e7` bg, `#daa520` gold accent, `#5c4400` brown text, `#fff8dc` cards
- **Positive**: `#22c55e` green, **Negative**: `#dc2626` red

### Deep Water (Water, Blue)
- **Mood**: melancholic, introspective, underwater
- **Dark**: deep navy `#001736` bg, `#00bbfa` cyan accent, `#79d7fd` light blue, white text
- **Light**: ice blue `#e8f4fd` bg, `#0088cc` blue accent, `#001833` navy text, `#f0f8ff` cards
- **Positive**: `#16a34a` green, **Negative**: `#dc2626` red

## Implementation

### Files to change
1. `desktop/src/themes.ts` — add 3 theme entries to `THEMES`, update `ThemeId` type, update `applyTheme` class list
2. `desktop/src/App.css` — add 6 CSS blocks (light + dark for `.theme-persona-5`, `.theme-persona-4`, `.theme-persona-3`)
3. `desktop/src/__tests__/App.test.tsx` — add test for Phantom Red theme switching + light mode toggle
4. `docs/usage.md` — update theme list

### CSS Variables per theme block
Each block sets: `--bg, --bg-card, --text, --text-secondary, --border, --nav-bg, --nav-active, --hover-light, --accent, --positive, --negative`

## Testing
- `npm test` — existing 7 tests must pass + new theme switching test
- `npm run build` — production build must succeed
