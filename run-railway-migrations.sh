#!/bin/bash
# Script to trigger Railway migrations
# This script provides multiple ways to run migrations in Railway

echo "🚀 Railway Migration Runner"
echo "=========================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed"
    echo "   Install it with: npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI is installed"
echo ""

# Option 1: Redeploy migration service
echo "📦 Option 1: Redeploy migration service"
echo "   This will restart the migration service and run all migrations"
echo ""
echo "   Command: railway redeploy --service migration-service --environment production"
echo ""

# Option 2: Manual run via Railway run
echo "🔧 Option 2: Run migrations manually"
echo "   This runs migrations directly in the Railway environment"
echo ""
echo "   Command: railway run --service migration-service python run-migrations.py"
echo ""

# Option 3: Dashboard instructions
echo "🌐 Option 3: Use Railway Dashboard"
echo "   1. Go to https://railway.app/dashboard"
echo "   2. Select your PrintPilot project"
echo "   3. Find the 'migration-service'"
echo "   4. Click the three dots menu (...)"
echo "   5. Click 'Redeploy'"
echo ""

# Ask user which option they want
echo "Which option would you like to use?"
echo "1) Redeploy migration service (recommended)"
echo "2) Run migrations manually"
echo "3) Show dashboard link"
echo ""

read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "🔄 Redeploying migration service..."
        railway redeploy --service migration-service --environment production
        ;;
    2)
        echo ""
        echo "🔄 Running migrations manually..."
        railway run --service migration-service --environment production python run-migrations.py
        ;;
    3)
        echo ""
        echo "Opening Railway dashboard..."
        open "https://railway.app/dashboard"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"
