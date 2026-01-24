#!/bin/bash

# Multi-Tenant Storefront Deployment Script
# This script helps deploy your storefront to Vercel

set -e

echo "🚀 CraftFlow Multi-Tenant Storefront Deployment"
echo "================================================"
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
    echo "✅ Vercel CLI installed"
else
    echo "✅ Vercel CLI found"
fi

echo ""
echo "📋 Pre-deployment Checklist:"
echo ""

# Check for required files
if [ -f "vercel.json" ]; then
    echo "✅ vercel.json exists"
else
    echo "❌ vercel.json not found"
    exit 1
fi

if [ -f "package.json" ]; then
    echo "✅ package.json exists"
else
    echo "❌ package.json not found"
    exit 1
fi

if [ -f "next.config.js" ]; then
    echo "✅ next.config.js exists"
else
    echo "❌ next.config.js not found"
    exit 1
fi

echo ""
echo "🔧 Environment Variables Needed:"
echo ""
echo "1. NEXT_PUBLIC_API_URL (your backend URL)"
echo "2. NEXT_PUBLIC_STRIPE_PUBLIC_KEY (your Stripe key)"
echo ""

read -p "Have you set these in Vercel dashboard? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please set environment variables in Vercel dashboard first:"
    echo "1. Go to your project settings"
    echo "2. Navigate to Environment Variables"
    echo "3. Add the required variables"
    echo ""
    exit 1
fi

echo ""
echo "🎯 Deployment Options:"
echo ""
echo "1) Deploy to production (yoursite.vercel.app)"
echo "2) Deploy preview/staging"
echo "3) Cancel"
echo ""

read -p "Choose an option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Deploying to production..."
        vercel --prod
        echo ""
        echo "✅ Production deployment complete!"
        echo ""
        echo "📝 Next Steps:"
        echo "1. Visit your Vercel dashboard to see the deployment"
        echo "2. Test your store: https://yourdomain.vercel.app/store/test-shop"
        echo "3. Add your custom domain in Vercel settings"
        ;;
    2)
        echo ""
        echo "🚀 Deploying preview..."
        vercel
        echo ""
        echo "✅ Preview deployment complete!"
        echo "Visit the URL above to test your changes"
        ;;
    3)
        echo "Deployment cancelled"
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo "🎉 Deployment process finished!"
echo ""
echo "📚 For more info, see DEPLOYMENT.md"
echo ""
