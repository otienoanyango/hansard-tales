# Hansard Tales - Quick Start Guide

## View Templates Locally

### Option 1: Docker (Recommended)

**Prerequisites**: Docker Desktop installed

```bash
# Start the development server
docker-compose up

# Open in browser
open http://localhost:5000
```

The server includes hot-reload - edit templates or CSS and refresh to see changes instantly.

**Stop the server**: Press `Ctrl+C` or run `docker-compose down`

### Option 2: Python Flask (No Docker)

**Prerequisites**: Python 3.11+

```bash
# Install Flask
pip install flask

# Run the development server
python app.py

# Open in browser
open http://localhost:5000
```

### Option 3: Static Site (GitHub Pages Preview)

```bash
# Generate static HTML files
python scripts/generate_static_site.py

# Open the generated files
open dist/index.html
```

## Available Pages

- **Home**: http://localhost:5000/ (test page with color demonstrations)
- **MPs**: http://localhost:5000/mps/ (placeholder)
- **Parties**: http://localhost:5000/parties/ (placeholder)
- **About**: http://localhost:5000/about/ (placeholder)

## Template Development

### File Structure

```
templates/
├── layouts/
│   └── base.html          # Base template with navigation
├── pages/
│   └── test.html          # Test page (currently used for all routes)
└── components/            # Reusable components (empty for now)

static/
├── css/
│   └── main.css          # Minimal custom CSS
└── js/
    └── main.js           # Mobile navigation JavaScript
```

### Color Theme

The site uses Kenyan flag-inspired colors:
- **Base**: Warm white (#FAF9F6)
- **Primary**: Kenya green (subtle shades)
- **Secondary**: Kenya red (subtle shades)
- **Borders**: Black (2px solid)

See `templates/COLOR_GUIDE.md` for complete color palette.

### Tailwind CSS

The templates use Tailwind CSS via CDN. Custom colors are configured inline in `base.html`:

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'warm-white': '#FAF9F6',
                'kenya-green': { /* shades 50-900 */ },
                'kenya-red': { /* shades 50-900 */ }
            }
        }
    }
}
```

## GitHub Pages Deployment

### Automatic Deployment

Push to `main` branch triggers automatic deployment via GitHub Actions:

```bash
git push origin main
```

Your site will be available at: `https://[username].github.io/hansard-tales/`

### Manual Deployment

```bash
# Generate static site
python scripts/generate_static_site.py

# Deploy dist/ folder to GitHub Pages
# (Configure in repository Settings → Pages → Source: GitHub Actions)
```

### Enable GitHub Pages

1. Go to repository **Settings** → **Pages**
2. Source: **GitHub Actions**
3. Push to main branch to trigger deployment

## Next Steps

1. **Create actual page templates**: Replace test.html with real pages
2. **Add components**: Create reusable components in `templates/components/`
3. **Connect to database**: Integrate with SQLite database for MP data
4. **Add search functionality**: Implement search and filtering
5. **Deploy to production**: Use Cloudflare Pages or similar

## Troubleshooting

### Port 5000 already in use

Edit `docker-compose.yml` or `app.py` to use a different port:

```yaml
# docker-compose.yml
ports:
  - "8080:5000"
```

### Templates not updating

- **Docker**: Changes should be instant (hot-reload enabled)
- **Flask**: Restart the server with `Ctrl+C` and `python app.py`
- **Static**: Re-run `python scripts/generate_static_site.py`

### Docker issues

```bash
# Rebuild from scratch
docker-compose down
docker-compose up --build

# View logs
docker-compose logs -f
```

## Documentation

- **Docker Setup**: See `DOCKER_SETUP.md`
- **Color Guide**: See `templates/COLOR_GUIDE.md`
- **Development**: See `docs/DEVELOPMENT.md`
- **Architecture**: See `docs/ARCHITECTURE.md`

## Support

For issues or questions, check the documentation or create an issue in the repository.
