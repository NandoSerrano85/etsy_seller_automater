from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

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