#!/bin/bash
"""
Setup script for phash-based duplicate detection system on Railway.

This script:
1. Sets up the environment
2. Runs the database migration and phash generation
3. Provides status updates

Usage:
    chmod +x scripts/setup_phash_system.sh
    ./scripts/setup_phash_system.sh
"""

set -e  # Exit on any error

echo "🚀 Setting up phash-based duplicate detection system..."
echo "==============================================="

# Check if we're in the right directory
if [ ! -f "scripts/generate_design_phashes.py" ]; then
    echo "❌ Error: Please run this script from the server root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected to find: scripts/generate_design_phashes.py"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable is not set"
    echo "   This is required to connect to the Railway database"
    exit 1
fi

echo "✅ Environment check passed"
echo "📦 Installing required dependencies..."

# Install required Python packages if not already installed
pip install --quiet pillow imagehash sqlalchemy psycopg2-binary

echo "✅ Dependencies installed"
echo "🗄️  Running database migration and phash generation..."

# Run the migration and phash generation script
python scripts/generate_design_phashes.py

# Check the result
if [ $? -eq 0 ]; then
    echo "✅ Phash system setup completed successfully!"
    echo ""
    echo "📊 System Status:"
    echo "   - Database migration: Applied"
    echo "   - Phash column: Added with index"
    echo "   - Existing designs: Processed for phashes"
    echo "   - Duplicate detection: Now using database-based phashes"
    echo ""
    echo "🎉 Your duplicate detection system is now optimized!"
    echo "   New uploads will automatically detect duplicates using fast database lookups."
else
    echo "❌ Phash system setup failed!"
    echo "   Please check the logs above for error details."
    exit 1
fi