# Hansard Tales - Templates

This directory contains Jinja2 templates for generating the static site.

## Directory Structure

```
templates/
├── layouts/          # Base layouts and page structures
│   └── base.html    # Main base template with header, footer, navigation
├── components/      # Reusable UI components
│   └── (future components)
└── pages/           # Page-specific templates
    └── (future pages)
```

## Template Hierarchy

All page templates should extend `layouts/base.html`:

```jinja2
{% extends "layouts/base.html" %}

{% block title %}Page Title - Hansard Tales{% endblock %}

{% block content %}
    <!-- Page content here -->
{% endblock %}
```

## Available Blocks

The base template provides the following blocks for customization:

- `title` - Page title (appears in browser tab)
- `meta_description` - Meta description for SEO
- `extra_css` - Additional CSS files or inline styles
- `content` - Main page content
- `extra_js` - Additional JavaScript files or inline scripts

## Template Variables

### Global Variables (available in all templates)

- `current_year` - Current year for copyright notice
- `last_updated` - Last update timestamp
- `active_page` - Current page identifier for navigation highlighting

### URL Functions

Use `url_for()` to generate URLs:

```jinja2
<a href="{{ url_for('index') }}">Home</a>
<a href="{{ url_for('mp_profile', mp_id=123) }}">MP Profile</a>
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
```

## Mobile-First Design

All templates follow a mobile-first responsive design approach:

- Base styles target mobile devices (320px+)
- Tablet styles at 768px breakpoint
- Desktop styles at 1024px breakpoint
- Maximum content width: 1200px

## Accessibility

Templates follow basic WCAG 2.1 guidelines:

- Semantic HTML5 elements
- Proper heading hierarchy
- Alt text for images
- ARIA labels for interactive elements
- Keyboard navigation support
- Sufficient color contrast

## CSS Framework

We use a custom CSS framework with:

- CSS variables for theming
- Mobile-first responsive design
- Utility classes for common patterns
- Print-friendly styles

See `static/css/main.css` for the complete stylesheet.
