#!/bin/bash
# Cloudflare Pages build script for Hansard Tales
# 
# NOTE: This script is NOT used in production.
# We deploy pre-built artifacts from GitHub Actions instead.
# 
# This file is kept for reference only.

set -e

echo "=================================================="
echo "Hansard Tales - Cloudflare Pages"
echo "=================================================="
echo ""
echo "⚠️  WARNING: This build script should not be running!"
echo ""
echo "Hansard Tales uses GitHub Actions for building."
echo "Cloudflare Pages should only deploy pre-built artifacts."
echo ""
echo "If you see this message, the deployment is misconfigured."
echo ""
echo "Please check:"
echo "1. Cloudflare Pages build command should be EMPTY"
echo "2. Deployment should use Wrangler CLI from GitHub Actions"
echo "3. See docs/CLOUDFLARE_DEPLOYMENT_SETUP.md for correct setup"
echo ""
echo "=================================================="

exit 1
