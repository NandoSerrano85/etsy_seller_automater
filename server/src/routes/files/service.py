"""
File service layer for NAS-based file management
"""

import logging
import hashlib
import os
from typing import List, Optional, Dict, Any, BinaryIO
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from server.src.entities.files import File, FileType, FileStatus
from server.src.entities.event import Event, EventTypes
from server.src.entities.organization import Organization
from server.src.utils.nas_storage import NASStorage
from . import model

logger = logging.getLogger(__name__)

class FileService:
    
    @staticmethod
    def calculate_sha256(file_content: bytes) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def get_nas_path(org_id: UUID, shop_name: str, file_type: str, filename: str) -> str:
        """Generate NAS path for file"""
        # Format: /share/Graphics/{shop_name}/{file_type}/{filename}
        return f"/share/Graphics/{shop_name}/{file_type}/{filename}"
    
    @staticmethod
    def upload_file(
        db: Session,
        org_id: UUID,
        file_data: model.FileUploadRequest,
        file_content: bytes,
        user_id: Optional[UUID] = None
    ) -> File:
        """Upload file to NAS and create database record"""
        try:
            # Get organization to get shop_name
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                raise ValueError("Organization not found")
            
            # Calculate file properties
            file_size = len(file_content)
            sha256_hash = FileService.calculate_sha256(file_content)
            
            # Check for duplicate file
            existing_file = db.query(File).filter(
                File.org_id == org_id,
                File.sha256 == sha256_hash,
                File.status != FileStatus.ARCHIVED
            ).first()
            
            if existing_file:
                logger.info(f"Duplicate file found: {existing_file.id}")
                return existing_file
            
            # Generate NAS path
            nas_path = FileService.get_nas_path(
                org_id=org_id,
                shop_name=org.shop_name,
                file_type=file_data.file_type.value,
                filename=file_data.filename
            )
            
            # Create file record
            file_record = File(
                org_id=org_id,
                file_type=FileType(file_data.file_type.value),
                status=FileStatus.UPLOADING,
                nas_path=nas_path,
                filename=file_data.filename,
                original_filename=file_data.filename,
                mime_type=file_data.mime_type,
                file_size=file_size,
                sha256=sha256_hash,
                metadata=file_data.metadata,
                created_by=user_id
            )
            db.add(file_record)
            db.flush()
            
            try:
                # Upload to NAS
                nas_storage = NASStorage()
                nas_storage.save_file_content(nas_path, file_content)
                
                # Update status to ready
                file_record.status = FileStatus.READY
                
                # Log success event
                event = Event.create_event(
                    event_type=EventTypes.SYSTEM_INFO,
                    org_id=org_id,
                    user_id=user_id,
                    entity_type="File",
                    entity_id=file_record.id,
                    payload={
                        "action": "file_uploaded",
                        "filename": file_data.filename,
                        "file_type": file_data.file_type.value,
                        "file_size": file_size
                    }
                )
                db.add(event)
                
            except Exception as nas_error:
                # Update status to failed
                file_record.status = FileStatus.FAILED
                
                # Log error event
                event = Event.create_event(
                    event_type=EventTypes.SYSTEM_ERROR,
                    org_id=org_id,
                    user_id=user_id,
                    entity_type="File",
                    entity_id=file_record.id,
                    payload={
                        "action": "file_upload_failed",
                        "filename": file_data.filename,
                        "error": str(nas_error)
                    }
                )
                db.add(event)
                logger.error(f"NAS upload failed for file {file_record.id}: {nas_error}")
            
            db.commit()
            db.refresh(file_record)
            
            logger.info(f"File upload completed: {file_record.id} - {file_record.filename}")
            return file_record
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error uploading file: {e}")
            raise

    @staticmethod
    def get_file_by_id(db: Session, file_id: UUID) -> Optional[File]:
        """Get file by ID"""
        return db.query(File).filter(File.id == file_id).first()

    @staticmethod
    def search_files(
        db: Session,
        org_id: UUID,
        search_params: model.FileSearchRequest,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[File], int]:
        """Search files with filters"""
        query = db.query(File).filter(File.org_id == org_id)
        
        # Apply filters
        if search_params.file_type:
            query = query.filter(File.file_type == FileType(search_params.file_type.value))
        
        if search_params.status:
            query = query.filter(File.status == FileStatus(search_params.status.value))
        
        if search_params.filename_contains:
            query = query.filter(
                or_(
                    File.filename.ilike(f"%{search_params.filename_contains}%"),
                    File.original_filename.ilike(f"%{search_params.filename_contains}%")
                )
            )
        
        if search_params.sha256:
            query = query.filter(File.sha256 == search_params.sha256)
        
        if search_params.created_after:
            query = query.filter(File.created_at >= search_params.created_after)
        
        if search_params.created_before:
            query = query.filter(File.created_at <= search_params.created_before)
        
        # Order by creation date descending
        query = query.order_by(File.created_at.desc())
        
        total = query.count()
        files = query.offset(skip).limit(limit).all()
        return files, total

    @staticmethod
    def update_file(
        db: Session,
        file_id: UUID,
        file_data: model.FileUpdateRequest,
        user_id: Optional[UUID] = None
    ) -> Optional[File]:
        """Update file metadata"""
        try:
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return None
            
            # Update fields
            update_data = file_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "status" and value:
                    setattr(file_record, field, FileStatus(value))
                else:
                    setattr(file_record, field, value)
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=file_record.org_id,
                user_id=user_id,
                entity_type="File",
                entity_id=file_id,
                payload={"action": "file_updated", "changes": update_data}
            )
            db.add(event)
            
            db.commit()
            db.refresh(file_record)
            
            logger.info(f"Updated file: {file_id}")
            return file_record
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating file {file_id}: {e}")
            raise

    @staticmethod
    def delete_file(
        db: Session,
        file_id: UUID,
        user_id: Optional[UUID] = None,
        soft_delete: bool = True
    ) -> bool:
        """Delete file (soft delete by default)"""
        try:
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return False
            
            if soft_delete:
                # Archive the file
                file_record.status = FileStatus.ARCHIVED
                
                # Log event
                event = Event.create_event(
                    event_type=EventTypes.SYSTEM_WARNING,
                    org_id=file_record.org_id,
                    user_id=user_id,
                    entity_type="File",
                    entity_id=file_id,
                    payload={
                        "action": "file_archived",
                        "filename": file_record.filename
                    }
                )
                db.add(event)
                
                db.commit()
                db.refresh(file_record)
                
                logger.info(f"Archived file: {file_id}")
            else:
                # Hard delete - remove from NAS and database
                try:
                    nas_storage = NASStorage()
                    nas_storage.delete_file(file_record.nas_path)
                except Exception as nas_error:
                    logger.warning(f"Failed to delete file from NAS: {nas_error}")
                
                # Log event before deletion
                event = Event.create_event(
                    event_type=EventTypes.SYSTEM_WARNING,
                    org_id=file_record.org_id,
                    user_id=user_id,
                    entity_type="File",
                    entity_id=file_id,
                    payload={
                        "action": "file_deleted_permanently",
                        "filename": file_record.filename,
                        "nas_path": file_record.nas_path
                    }
                )
                db.add(event)
                db.flush()
                
                # Delete from database
                db.delete(file_record)
                db.commit()
                
                logger.warning(f"Permanently deleted file: {file_id}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting file {file_id}: {e}")
            raise

    @staticmethod
    def get_file_content(db: Session, file_id: UUID) -> Optional[bytes]:
        """Get file content from NAS"""
        try:
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record or file_record.status != FileStatus.READY:
                return None
            
            nas_storage = NASStorage()
            return nas_storage.get_file_content(file_record.nas_path)
            
        except Exception as e:
            logger.error(f"Error getting file content for {file_id}: {e}")
            return None

    @staticmethod
    def get_storage_stats(db: Session, org_id: UUID) -> Dict[str, Any]:
        """Get file storage statistics for organization"""
        try:
            # File count by type
            type_stats = db.query(
                File.file_type,
                func.count(File.id).label('count'),
                func.sum(File.file_size).label('total_size')
            ).filter(
                File.org_id == org_id,
                File.status != FileStatus.ARCHIVED
            ).group_by(File.file_type).all()
            
            # Overall stats
            overall_stats = db.query(
                func.count(File.id).label('total_files'),
                func.sum(File.file_size).label('total_size')
            ).filter(
                File.org_id == org_id,
                File.status != FileStatus.ARCHIVED
            ).first()
            
            return {
                "total_files": overall_stats.total_files or 0,
                "total_size": overall_stats.total_size or 0,
                "by_type": {
                    file_type.value: {
                        "count": count,
                        "total_size": total_size or 0
                    }
                    for file_type, count, total_size in type_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats for org {org_id}: {e}")
            return {}