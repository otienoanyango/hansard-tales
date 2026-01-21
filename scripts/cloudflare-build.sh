#!/bin/bash
# Cloudflare Pages build script for Hansard Tales
# This script sets up the database and generates the static site

set -e  # Exit on any error

echo "=================================================="
echo "Hansard Tales - Cloudflare Pages Build"
echo "=================================================="

echo ""
echo "Step 1/6: Installing Python dependencies..."
pip install -e .

echo ""
echo "Step 2/6: Downloading spaCy language model..."
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

echo ""
echo "Step 3/6: Initializing database..."
hansard-init-db
hansard-init-parliament-data

echo ""
echo "Step 4/6: Importing MPs data..."
hansard-import-mps --file data/mps_13th_parliament.json --current

echo ""
echo "Step 5/6: Generating search index..."
hansard-generate-search-index

echo ""
echo "Step 6/6: Generating static site..."
hansard-generate-site

echo ""
echo "=================================================="
echo "Build complete! Site ready in output/ directory"
echo "=================================================="
