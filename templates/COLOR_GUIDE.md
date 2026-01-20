# Hansard Tales Color Guide

## Design Philosophy
Kenyan flag-inspired colors with a warm, professional aesthetic. Colors are subtle to avoid overwhelming the page while maintaining national identity. Uses system fonts for optimal performance and native look.

## Typography

### Font Stack
Helvetica Neue as primary font with system font fallback:
```css
font-family: "Helvetica Neue", -apple-system, BlinkMacSystemFont, 
             "Segoe UI", Roboto, Arial, "Noto Sans", sans-serif, 
             "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", 
             "Noto Color Emoji";
```

**Benefits:**
- Clean, professional Helvetica Neue on macOS/iOS
- Graceful fallback to system fonts on other platforms
- No font downloads (uses pre-installed fonts)
- Excellent readability across all devices
- Supports emoji across platforms

**Platform Fonts:**
- macOS/iOS: Helvetica Neue (primary)
- Windows: Segoe UI (fallback)
- Android: Roboto (fallback)
- Linux: System default sans-serif (fallback)

## Color Palette

### Base Colors
- **Warm White** (`#FAF9F6`): Main background color
  - Tailwind class: `bg-warm-white`
  - Usage: Page background, creating a soft, warm feel

- **White** (`#FFFFFF`): Content backgrounds
  - Tailwind class: `bg-white`
  - Usage: Cards, sections, header, footer

- **Black** (`#000000`): Borders and definition
  - Tailwind class: `border-black`
  - Usage: All borders (2px solid) for clear visual separation

### Kenya Green (Primary Accent)
Subtle green shades inspired by the Kenyan flag:
- `kenya-green-50` to `kenya-green-900`
- Primary shade: `kenya-green-600` (#1f7f54)
- Light backgrounds: `kenya-green-100` (#dcf2e4)
- Text: `kenya-green-700` to `kenya-green-800`

**Usage:**
- Active navigation states
- Primary buttons
- Section underlines
- Hover states for links

### Kenya Red (Secondary Accent)
Subtle red shades inspired by the Kenyan flag:
- `kenya-red-50` to `kenya-red-900`
- Primary shade: `kenya-red-600` (#dc2626)
- Light backgrounds: `kenya-red-100` (#fee2e2)
- Borders: `kenya-red-400` (#f87171)

**Usage:**
- Section heading underlines
- Secondary buttons
- Alert/important states
- Accent borders

### Gray Scale
Standard Tailwind grays for text and subtle elements:
- `text-gray-900`: Primary text
- `text-gray-700`: Secondary text
- `text-gray-600`: Muted text
- `text-gray-500`: Placeholder text

## Component Patterns

### Navigation
- Active page: `bg-kenya-green-100 text-kenya-green-800 font-semibold border border-black`
- Inactive: `text-gray-700 hover:bg-gray-100 hover:text-kenya-green-700`

### Buttons
- Primary: `bg-kenya-green-600 text-white border-2 border-black hover:bg-kenya-green-700`
- Secondary: `bg-kenya-red-600 text-white border-2 border-black hover:bg-kenya-red-700`
- Outline: `bg-white text-gray-900 border-2 border-black hover:bg-gray-100`

### Cards/Sections
- Background: `bg-white`
- Border: `border-2 border-black`
- Shadow: `shadow-sm`
- Rounded: `rounded-lg`

### Headings
- Main heading underline: `border-b-4 border-kenya-green-500`
- Section heading underline: `border-b-2 border-kenya-red-400`

## Accessibility
- All text meets WCAG AA contrast requirements
- Focus states: 2px solid kenya-green outline with 2px offset
- Semantic HTML with proper ARIA labels
- Mobile-first responsive design

## Tailwind Configuration
Custom colors and fonts are configured in the base template's inline Tailwind config:
```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'warm-white': '#FAF9F6',
                'kenya-green': { /* 50-900 shades */ },
                'kenya-red': { /* 50-900 shades */ }
            },
            fontFamily: {
                sans: ['"Helvetica Neue"', '-apple-system', /* system fonts */]
            }
        }
    }
}
```

## Performance
- **Zero font downloads**: System fonts load instantly
- **Tailwind via CDN**: No build step required
- **Minimal custom CSS**: Only essential overrides
- **Optimized for static generation**: Fast GitHub Pages deployment
