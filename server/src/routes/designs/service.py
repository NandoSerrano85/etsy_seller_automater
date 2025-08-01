from server.src.entities.designs import DesignImages
from server.src.entities.canvas_config import CanvasConfig
from server.src.entities.size_config import SizeConfig
from server.src.message import (
    DesignNotFoundError,
    DesignCreateError,
    DesignGetAllError,
    DesignGetByIdError,
    DesignUpdateError,
    DesignDeleteError
)
from uuid import UUID
from sqlalchemy.orm import Session
from . import model
import logging
from typing import Optional


def _validate_canvas_config(db: Session, user_id: UUID, canvas_config_id: UUID) -> bool:
    """Validate that canvas config exists and belongs to the user"""
    canvas_config = db.query(CanvasConfig).filter(
        CanvasConfig.id == canvas_config_id,
        CanvasConfig.user_id == user_id,
        CanvasConfig.is_active == True
    ).first()
    return canvas_config is not None


def _validate_size_config(db: Session, user_id: UUID, size_config_id: UUID, canvas_config_id: Optional[UUID] = None) -> bool:
    """Validate that size config exists, belongs to the user, and is associated with the canvas config if provided"""
    query = db.query(SizeConfig).filter(
        SizeConfig.id == size_config_id,
        SizeConfig.user_id == user_id,
        SizeConfig.is_active == True
    )
    
    if canvas_config_id:
        query = query.filter(SizeConfig.canvas_id == canvas_config_id)
    
    size_config = query.first()
    return size_config is not None


def create_design(db: Session, user_id: UUID, design_data: model.DesignImageCreate) -> model.DesignImageResponse:
    try:
        # Validate canvas config if provided
        if design_data.canvas_config_id:
            if not _validate_canvas_config(db, user_id, design_data.canvas_config_id):
                logging.warning(f"Invalid canvas config ID: {design_data.canvas_config_id} for user: {user_id}")
                raise DesignCreateError()
        
        # Validate size config if provided
        if design_data.size_config_id:
            if not _validate_size_config(db, user_id, design_data.size_config_id, design_data.canvas_config_id):
                logging.warning(f"Invalid size config ID: {design_data.size_config_id} for user: {user_id}")
                raise DesignCreateError()
        
        design = DesignImages(
            user_id=user_id,
            filename=design_data.filename,
            file_path=design_data.file_path,
            description=design_data.description,
            canvas_config_id=design_data.canvas_config_id,
            size_config_id=design_data.size_config_id,
            is_active=design_data.is_active
        )
        
        db.add(design)
        db.commit()
        db.refresh(design)
        
        logging.info(f"Successfully created design with ID: {design.id} for user: {user_id}")
        return design
    except Exception as e:
        logging.error(f"Error creating design for user ID: {user_id}. Error: {e}")
        db.rollback()
        raise DesignCreateError()


def get_designs_by_user_id(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> model.DesignImageListResponse:
    try:
        designs = db.query(DesignImages).filter(
            DesignImages.user_id == user_id,
            DesignImages.is_active == True
        ).offset(skip).limit(limit).all()
        
        total = db.query(DesignImages).filter(
            DesignImages.user_id == user_id,
            DesignImages.is_active == True
        ).count()
        
        logging.info(f"Successfully retrieved {len(designs)} designs for user: {user_id}")
        # Convert SQLAlchemy objects to Pydantic models
        design_responses = [model.DesignImageResponse.model_validate(design) for design in designs]
        return model.DesignImageListResponse(designs=design_responses, total=total)
    except Exception as e:
        logging.error(f"Error getting designs for user ID: {user_id}. Error: {e}")
        raise DesignGetAllError()


def get_design_by_id(db: Session, design_id: UUID, user_id: UUID) -> model.DesignImageResponse:
    try:
        design = db.query(DesignImages).filter(
            DesignImages.id == design_id,
            DesignImages.user_id == user_id
        ).first()
        
        if not design:
            logging.warning(f"Design not found with ID: {design_id} for user: {user_id}")
            raise DesignNotFoundError(design_id)
        
        logging.info(f"Successfully retrieved design with ID: {design_id}")
        return design
    except Exception as e:
        if isinstance(e, DesignNotFoundError):
            raise e
        logging.error(f"Error getting design with ID: {design_id}. Error: {e}")
        raise DesignGetByIdError(design_id)


def update_design(db: Session, design_id: UUID, user_id: UUID, design_data: model.DesignImageUpdate) -> model.DesignImageResponse:
    try:
        design = db.query(DesignImages).filter(
            DesignImages.id == design_id,
            DesignImages.user_id == user_id
        ).first()
        
        if not design:
            logging.warning(f"Design not found with ID: {design_id} for user: {user_id}")
            raise DesignNotFoundError(design_id)
        
        # Validate canvas config if provided
        if design_data.canvas_config_id is not None:
            if not _validate_canvas_config(db, user_id, design_data.canvas_config_id):
                logging.warning(f"Invalid canvas config ID: {design_data.canvas_config_id} for user: {user_id}")
                raise DesignUpdateError(design_id)
        
        # Validate size config if provided
        if design_data.size_config_id is not None:
            canvas_config_id = design_data.canvas_config_id if design_data.canvas_config_id is not None else getattr(design, 'canvas_config_id', None)
            if not _validate_size_config(db, user_id, design_data.size_config_id, canvas_config_id):
                logging.warning(f"Invalid size config ID: {design_data.size_config_id} for user: {user_id}")
                raise DesignUpdateError(design_id)
        
        # Update only provided fields
        update_data = design_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(design, field, value)
        
        db.commit()
        db.refresh(design)
        
        logging.info(f"Successfully updated design with ID: {design_id}")
        return design
    except Exception as e:
        if isinstance(e, DesignNotFoundError):
            raise e
        logging.error(f"Error updating design with ID: {design_id}. Error: {e}")
        db.rollback()
        raise DesignUpdateError(design_id)


def delete_design(db: Session, design_id: UUID, user_id: UUID) -> None:
    try:
        design = db.query(DesignImages).filter(
            DesignImages.id == design_id,
            DesignImages.user_id == user_id
        ).first()
        
        if not design:
            logging.warning(f"Design not found with ID: {design_id} for user: {user_id}")
            raise DesignNotFoundError(design_id)
        
        # Soft delete by setting is_active to False
        setattr(design, 'is_active', False)
        db.commit()
        
        logging.info(f"Successfully deleted design with ID: {design_id}")
    except Exception as e:
        if isinstance(e, DesignNotFoundError):
            raise e
        logging.error(f"Error deleting design with ID: {design_id}. Error: {e}")
        db.rollback()
        raise DesignDeleteError(design_id)
