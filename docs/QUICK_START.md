# Quick Start Guide

Get Hansard Tales running locally in 5 minutes.

## Prerequisites

- Python 3.11+ installed
- Git installed
- Terminal/Command Prompt access

## Setup Steps

### 1. Clone and Navigate

```bash
git clone https://github.com/yourusername/hansard-tales.git
cd hansard-tales
```

### 2. Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Run Processing Pipeline

```bash
python scripts/main.py
```

### 6. View the Site

```bash
cd output
python -m http.server 8000
```

Open http://localhost:8000 in your browser.

## What's Next?

- Read [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development workflow
- Check [README.md](../README.md) for project overview
- Explore the `scripts/` directory to understand the processing pipeline

## Troubleshooting

**Virtual environment not activating?**
- Ensure Python 3.11+ is installed: `python3 --version`
- Try creating venv again: `python3 -m venv venv`

**Module not found errors?**
- Activate virtual environment first
- Reinstall: `pip install -r requirements.txt`

**spaCy model missing?**
- Run: `python -m spacy download en_core_web_sm`

## Need Help?

Open an issue on GitHub or check the full documentation in `docs/`.
