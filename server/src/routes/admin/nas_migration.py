from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import os

from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser

router = APIRouter(
    prefix='/api/admin',
    tags=['admin']
)

@router.post("/trigger-nas-migration")
async def trigger_nas_migration(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Manually trigger NAS design import migration"""

    # Only allow admin users to trigger this
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        logging.info(f"Manual NAS migration triggered by user {current_user.user_id}")

        # Import and run the migration
        from server.migrations.import_nas_designs import upgrade

        # Use the database connection from the session
        connection = db.connection()

        # Run the migration
        upgrade(connection)

        return {
            "success": True,
            "message": "NAS migration completed successfully"
        }

    except Exception as e:
        logging.error(f"Manual NAS migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/nas-migration-status")
async def check_nas_migration_status(db: Session = Depends(get_db)):
    """Check if NAS migration has run and how many designs were imported"""

    try:
        # Check how many designs are in the database from NAS paths
        result = db.execute("""
            SELECT COUNT(*) as count
            FROM design_images
            WHERE file_path LIKE '/share/Graphics/%'
            AND is_active = true
        """)
        nas_designs_count = result.fetchone()[0]

        # Check total designs
        result = db.execute("""
            SELECT COUNT(*) as count
            FROM design_images
            WHERE is_active = true
        """)
        total_designs_count = result.fetchone()[0]

        # Check NAS storage configuration
        nas_enabled = False
        nas_config_status = "Not configured"

        if all([os.getenv('QNAP_HOST'), os.getenv('QNAP_USERNAME'), os.getenv('QNAP_PASSWORD')]):
            nas_enabled = True
            nas_config_status = "Configured"

            # Try to check paramiko availability
            try:
                import paramiko
                nas_config_status = "Configured and paramiko available"
            except ImportError:
                nas_config_status = "Configured but paramiko not available"

        return {
            "nas_designs_imported": nas_designs_count,
            "total_designs": total_designs_count,
            "nas_enabled": nas_enabled,
            "nas_config_status": nas_config_status,
            "migration_needed": nas_enabled and nas_designs_count == 0
        }

    except Exception as e:
        logging.error(f"Error checking NAS migration status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")