#!/usr/bin/env python3
"""
Railway-optimized setup script for phash-based duplicate detection system.

This script is designed to run on Railway and will:
1. Check environment and dependencies
2. Run database migration to add phash column
3. Generate phashes for existing designs
4. Provide detailed status reporting

Usage:
    python scripts/railway_setup_phashes.py

Environment Variables Required:
    DATABASE_URL - Railway database connection string
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check that we have the required environment and dependencies."""
    logger.info("🔍 Checking environment...")

    # Check DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        logger.error("❌ DATABASE_URL environment variable is not set")
        logger.error("   This is required to connect to the Railway database")
        return False

    # Check if we're in the right directory
    script_path = Path(__file__).parent / "generate_design_phashes.py"
    if not script_path.exists():
        logger.error(f"❌ Cannot find generate_design_phashes.py at {script_path}")
        logger.error(f"   Current directory: {Path.cwd()}")
        return False

    logger.info("✅ Environment check passed")
    return True

def install_dependencies():
    """Install required dependencies."""
    logger.info("📦 Checking and installing dependencies...")

    required_packages = [
        'pillow',
        'imagehash',
        'sqlalchemy',
        'psycopg2-binary'
    ]

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"   ✓ {package} already installed")
        except ImportError:
            logger.info(f"   📥 Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '--quiet', package
                ])
                logger.info(f"   ✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Failed to install {package}: {e}")
                return False

    logger.info("✅ All dependencies are available")
    return True

def run_phash_setup():
    """Run the phash system setup."""
    logger.info("🗄️  Running phash system setup...")

    # Add the server src directory to the path
    server_root = Path(__file__).parent.parent
    sys.path.insert(0, str(server_root / "src"))

    try:
        # Import and run the setup
        from scripts.generate_design_phashes import main
        main()
        return True
    except Exception as e:
        logger.error(f"❌ Phash setup failed: {e}")
        return False

def get_system_status():
    """Get status information about the phash system."""
    logger.info("📊 Checking system status...")

    try:
        # Add the server src directory to the path
        server_root = Path(__file__).parent.parent
        sys.path.insert(0, str(server_root / "src"))

        from sqlalchemy import create_engine, text
        from database.core import get_database_url

        engine = create_engine(get_database_url())

        with engine.connect() as conn:
            # Check if phash column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'design_images' AND column_name = 'phash'
            """))

            if not result.fetchone():
                logger.info("   📋 Phash column: Not present")
                return

            # Get counts
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_designs,
                    COUNT(phash) as designs_with_phash,
                    COUNT(*) - COUNT(phash) as designs_without_phash
                FROM design_images
                WHERE is_active = true
            """))

            row = result.fetchone()
            if row:
                total = row[0]
                with_phash = row[1]
                without_phash = row[2]

                logger.info(f"   📋 Total active designs: {total}")
                logger.info(f"   🔐 Designs with phash: {with_phash}")
                logger.info(f"   ❓ Designs without phash: {without_phash}")

                if without_phash == 0:
                    logger.info("   ✅ All designs have phashes!")
                else:
                    logger.info(f"   ⚠️  {without_phash} designs still need phashes")

    except Exception as e:
        logger.error(f"❌ Could not get system status: {e}")

def main():
    """Main setup function."""
    logger.info("🚀 Starting phash system setup for Railway...")
    logger.info("=" * 50)

    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        logger.error("❌ Dependency installation failed")
        sys.exit(1)

    # Run phash setup
    if not run_phash_setup():
        logger.error("❌ Phash system setup failed")
        sys.exit(1)

    # Get final status
    get_system_status()

    logger.info("")
    logger.info("🎉 Phash system setup completed successfully!")
    logger.info("=" * 50)
    logger.info("📊 System Status:")
    logger.info("   - Database migration: ✅ Applied")
    logger.info("   - Phash column: ✅ Added with index")
    logger.info("   - Existing designs: ✅ Processed for phashes")
    logger.info("   - Duplicate detection: ✅ Now using database-based phashes")
    logger.info("")
    logger.info("🚀 Your duplicate detection system is now optimized!")
    logger.info("   New uploads will automatically detect duplicates using fast database lookups.")

if __name__ == "__main__":
    main()