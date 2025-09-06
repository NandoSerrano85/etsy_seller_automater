#!/bin/bash

# Registry-based deployment script for QNAP Container Station
# This triggers the GitHub Actions workflow to build and push new images

set -e

PROJECT_NAME="printer-automater"
GITHUB_REPO="nandoserrano85/etsy_seller_automater"
REGISTRY="ghcr.io"

echo "🚀 Registry-Based Deployment Script"
echo "=================================="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes"
    read -p "Do you want to commit them first? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Please commit your changes and run this script again"
        exit 1
    fi
fi

echo ""
echo "🔨 Deployment Process:"
echo "1. Push code to GitHub"
echo "2. GitHub Actions builds Docker image"
echo "3. Image pushed to $REGISTRY/$GITHUB_REPO"
echo "4. QNAP Container Station auto-pulls new image"
echo ""

# Push to GitHub (this triggers the GitHub Actions workflow)
echo "📤 Pushing to GitHub..."
git push origin $CURRENT_BRANCH

# Wait a moment for GitHub to register the push
sleep 2

echo ""
echo "✅ Code pushed to GitHub!"
echo ""
echo "🔗 Monitor the deployment:"
echo "   GitHub Actions: https://github.com/$GITHUB_REPO/actions"
echo "   Container Registry: https://github.com/$GITHUB_REPO/pkgs/container/printer-automater-backend"
echo ""
echo "📋 Next steps:"
echo "   1. GitHub Actions will build and push the Docker image (~2-5 minutes)"
echo "   2. If Watchtower is configured, it will auto-update containers (~5 minutes)"
echo "   3. Or manually update on QNAP: docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🌍 Once deployed, check: http://printmadenas.myqnapcloud.com:8080/health"
echo ""
echo "🎉 Deployment initiated successfully!"