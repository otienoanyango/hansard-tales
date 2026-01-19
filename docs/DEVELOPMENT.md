# Development Guide

This guide covers the local development workflow for Hansard Tales.

## Prerequisites

- **Python 3.11 or higher** (3.12 recommended)
- **Git** for version control
- **pip** for package management
- **Internet connection** for downloading dependencies and Hansard PDFs

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/hansard-tales.git
cd hansard-tales
```

### 2. Create Virtual Environment

We strongly recommend using a virtual environment to isolate project dependencies.

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt indicating the virtual environment is active.

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download spaCy Language Model

The project uses spaCy for Named Entity Recognition. Download the English language model:

```bash
python -m spacy download en_core_web_sm
```

### 5. Initialize Database

```bash
python scripts/init_db.py
```

This creates the SQLite database with the required schema.

## Development Workflow

### Activating the Virtual Environment

Always activate the virtual environment before working on the project:

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### Deactivating the Virtual Environment

When you're done working:

```bash
deactivate
```

## Running the Application

### Full Processing Pipeline

Run the complete pipeline (scraping, processing, site generation):

```bash
python scripts/main.py
```

### Individual Components

Run specific parts of the pipeline:

```bash
# Scrape new Hansard PDFs
python scripts/scraper.py

# Process PDFs and extract statements
python scripts/processor.py

# Generate static site
python scripts/generate_site.py

# Generate search index
python scripts/generate_search_index.py
```

### Local Development Server

Serve the generated static site locally:

```bash
cd output
python -m http.server 8000
```

Visit http://localhost:8000 in your browser.

## Testing

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=scripts --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Specific Test File

```bash
pytest tests/test_scraper.py -v
```

### Run Tests Matching Pattern

```bash
pytest -k "test_mp_identification" -v
```

## Code Quality

### Format Code with Black

```bash
black scripts/ tests/
```

### Lint Code with Flake8

```bash
flake8 scripts/ tests/
```

### Type Check with mypy

```bash
mypy scripts/
```

## Project Structure

```
hansard-tales/
├── data/                    # Data storage
│   ├── pdfs/               # Downloaded Hansard PDFs (gitignored)
│   └── hansard.db          # SQLite database
├── scripts/                # Python processing scripts
│   ├── init_db.py         # Database initialization
│   ├── scraper.py         # Hansard PDF scraper
│   ├── processor.py       # PDF text extraction & parsing
│   ├── generate_site.py   # Static site generator
│   └── main.py            # Main processing pipeline
├── templates/              # Jinja2 HTML templates
├── output/                 # Generated static site (gitignored)
├── tests/                  # Test files
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── pytest.ini             # Pytest configuration
```

## Common Tasks

### Add a New Dependency

1. Add the package to `requirements.txt`
2. Install it: `pip install -r requirements.txt`
3. Commit the updated `requirements.txt`

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Freeze Current Dependencies

```bash
pip freeze > requirements-frozen.txt
```

### Clear Database and Start Fresh

```bash
rm data/hansard.db
python scripts/init_db.py
```

### Clear Downloaded PDFs

```bash
rm data/pdfs/*.pdf
```

### Regenerate Static Site

```bash
python scripts/generate_site.py
```

## Troubleshooting

### Virtual Environment Not Activating

**Issue**: `source venv/bin/activate` doesn't work

**Solution**: 
- Ensure you created the venv: `python3 -m venv venv`
- Try absolute path: `source /full/path/to/venv/bin/activate`

### spaCy Model Not Found

**Issue**: `Can't find model 'en_core_web_sm'`

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

### Import Errors

**Issue**: `ModuleNotFoundError: No module named 'pdfplumber'`

**Solution**:
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Database Locked Error

**Issue**: `sqlite3.OperationalError: database is locked`

**Solution**:
- Close any other processes accessing the database
- Restart the script

### PDF Download Failures

**Issue**: Scraper fails to download PDFs

**Solution**:
- Check internet connection
- Verify parliament.go.ke is accessible
- Check rate limiting (add delays between requests)

## Git Workflow

### Feature Branch Development

1. Create feature branch:
   ```bash
   git checkout -b feat/feature-name
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: description of changes"
   ```

3. Push to remote:
   ```bash
   git push origin feat/feature-name
   ```

4. Create pull request for review

### Commit Message Format

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## Performance Tips

### Speed Up PDF Processing

- Process PDFs in batches
- Use multiprocessing for parallel processing (future enhancement)
- Cache extracted text to avoid reprocessing

### Optimize Database Queries

- Use indexes (already created in schema)
- Use views for complex queries
- Batch inserts with transactions

### Reduce Site Generation Time

- Only regenerate changed pages
- Use template caching
- Minimize database queries

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Open an issue on GitHub
- **Code Examples**: See `scripts/` for implementation examples

## Next Steps

After setup, you can:

1. Run the scraper to download sample PDFs
2. Process PDFs to extract MP statements
3. Generate the static site
4. View the site locally

See the main [README.md](../README.md) for more information.
