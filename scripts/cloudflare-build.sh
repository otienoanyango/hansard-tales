#!/bin/bash
# Cloudflare Pages build script for Hansard Tales
# This script generates the static site from pre-existing database

set -e  # Exit on any error

echo "=================================================="
echo "Hansard Tales - Cloudflare Pages Build"
echo "=================================================="

echo ""
echo "Step 1/4: Installing Python dependencies..."
pip install -e .

echo ""
echo "Step 2/4: Downloading spaCy language model..."
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

echo ""
echo "Step 3/4: Generating search index..."
hansard-generate-search-index

echo ""
echo "Step 4/4: Generating static site..."
hansard-generate-site

echo ""
echo "=================================================="
echo "Build complete! Site ready in output/ directory"
echo "=================================================="
