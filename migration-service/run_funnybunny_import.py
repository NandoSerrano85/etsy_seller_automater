#!/usr/bin/env python3
"""
Standalone script to import FunnyBunnyTransfers designs

Usage:
    python run_funnybunny_import.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
    QNAP_HOST - NAS host
    QNAP_USERNAME - NAS username
    QNAP_PASSWORD - NAS password
    FUNNYBUNNY_USER_EMAIL - (Optional) Email of user to import for
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add server to path
sys.path.insert(0, '/app/server')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'server'))


def main():
    """Run the FunnyBunnyTransfers import migration."""
    try:
        # Check for required environment variables
        required_vars = ['DATABASE_URL', 'QNAP_HOST', 'QNAP_USERNAME', 'QNAP_PASSWORD']
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            logger.error(f"Missing required environment variables: {', '.join(missing)}")
            sys.exit(1)

        # Create database connection
        from sqlalchemy import create_engine
        database_url = os.getenv('DATABASE_URL')
        engine = create_engine(database_url, pool_pre_ping=True)

        logger.info("Connecting to database...")
        connection = engine.connect()

        # Import and run the migration
        logger.info("Loading migration module...")
        from migrations.import_funnybunny_designs import upgrade

        logger.info("Running migration...")
        upgrade(connection)

        connection.close()
        logger.info("✅ Migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
