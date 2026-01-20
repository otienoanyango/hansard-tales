# Docker Setup for Hansard Tales

This document explains how to run Hansard Tales locally using Docker for template development and preview.

## Prerequisites

- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

## Quick Start

### 1. Start the Development Server

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d
```

### 2. Access the Application

Open your browser and navigate to:
- **Local URL**: http://localhost:5000

You should see the Hansard Tales test page with the Kenyan flag-inspired color theme.

### 3. Stop the Server

```bash
# If running in foreground, press Ctrl+C

# If running in detached mode
docker-compose down
```

## Development Workflow

The Docker setup includes hot-reload for template development:

1. **Edit templates**: Changes to files in `templates/` are immediately reflected
2. **Edit static files**: Changes to `static/css/` and `static/js/` are immediately reflected
3. **Edit app.py**: Changes require container restart

### Restart Container

```bash
docker-compose restart
```

### View Logs

```bash
docker-compose logs -f
```

## Available Routes

- `/` - Home page (test page)
- `/mps/` - MPs listing (placeholder)
- `/parties/` - Parties page (placeholder)
- `/about/` - About page (placeholder)
- `/disclaimer/` - Disclaimer (placeholder)
- `/privacy/` - Privacy (placeholder)

## File Structure

```
.
├── app.py                 # Flask application
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Docker image definition
├── templates/            # Jinja2 templates (hot-reload)
│   ├── layouts/
│   │   └── base.html
│   └── pages/
│       └── test.html
└── static/              # Static assets (hot-reload)
    ├── css/
    │   └── main.css
    └── js/
        └── main.js
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, edit `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Change 5000 to any available port
```

Then access at http://localhost:8080

### Container Won't Start

```bash
# Remove old containers and rebuild
docker-compose down
docker-compose up --build
```

### View Container Logs

```bash
docker-compose logs web
```

## GitHub Pages Deployment

To generate a static site for GitHub Pages:

```bash
# Generate static files
python scripts/generate_static_site.py

# Output will be in ./dist/
```

The GitHub Actions workflow (`.github/workflows/deploy-pages.yml`) automatically:
1. Generates static HTML from templates
2. Deploys to GitHub Pages on push to main branch

### Enable GitHub Pages

1. Go to repository Settings → Pages
2. Source: GitHub Actions
3. Push to main branch to trigger deployment

## Production Deployment

For production, consider:
- Using Gunicorn instead of Flask dev server
- Adding nginx for static file serving
- Implementing proper routing and database connections
- Adding environment-specific configurations

Example production command:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
