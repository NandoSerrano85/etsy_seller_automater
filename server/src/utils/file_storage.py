"""
File Storage Adapter for QNAP NAS
Provides a unified interface for file storage operations with Railway + QNAP architecture
"""

import os
import logging
import hashlib
from typing import Optional, Tuple, BinaryIO
from pathlib import Path
from datetime import datetime
from io import BytesIO

from .nas_storage import nas_storage
from ..database.core import get_db
from ..entities.files import File
from sqlalchemy.orm import Session

class FileStorageAdapter:
    """
    Unified file storage adapter for Railway + QNAP NAS architecture
    
    Handles:
    - File uploads to NAS
    - Database metadata tracking
    - Deduplication via SHA256
    - Path management
    - Error handling
    """
    
    def __init__(self):
        self.nas = nas_storage
        self.base_path = "/share/Graphics"
    
    def _calculate_sha256(self, content: bytes) -> str:
        """Calculate SHA256 hash for deduplication"""
        return hashlib.sha256(content).hexdigest()
    
    def _generate_nas_path(self, shop_name: str, file_type: str, filename: str) -> str:
        """
        Generate standardized NAS path based on file type
        
        Structure:
        /share/Graphics/{shop_name}/
        ├── Designs/{template_name}/
        ├── Digital/{template_name}/
        ├── Mockups/BaseMockups/{template_name}/
        ├── Mockups/BaseMockups/Watermarks/
        ├── Printfiles/
        └── Templates/
        """
        
        type_paths = {
            'design': 'Designs',
            'design_digital': 'Digital', 
            'mockup': 'Mockups/BaseMockups',
            'watermark': 'Mockups/BaseMockups/Watermarks',
            'print_file': 'Printfiles',
            'template': 'Templates',
            'export': 'Exports',
            'original': 'Originals'
        }
        
        folder = type_paths.get(file_type, 'Other')
        return f"{folder}/{filename}"
    
    def upload_file(
        self, 
        file_content: bytes, 
        filename: str, 
        shop_name: str, 
        org_id: str,
        file_type: str = 'other',
        template_name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Upload file to NAS and create database record
        
        Returns:
            Tuple[success: bool, file_id: str, file_info: dict]
        """
        
        if not self.nas.enabled:
            logging.error("NAS storage is not enabled")
            return False, None, None
        
        try:
            # Calculate file hash for deduplication
            file_hash = self._calculate_sha256(file_content)
            file_size = len(file_content)
            
            # Check for existing file by hash (deduplication)
            db = next(get_db())
            existing_file = db.query(File).filter(
                File.org_id == org_id,
                File.sha256 == file_hash
            ).first()
            
            if existing_file:
                logging.info(f"File already exists (deduplicated): {existing_file.id}")
                file_info = {
                    'id': str(existing_file.id),
                    'nas_path': existing_file.nas_path,
                    'filename': existing_file.filename,
                    'file_size': existing_file.file_size,
                    'deduplicated': True
                }
                return True, str(existing_file.id), file_info
            
            # Generate NAS path
            if template_name and file_type in ['design', 'mockup']:
                if file_type == 'design' and metadata and metadata.get('is_digital'):
                    nas_relative_path = f"Digital/{template_name}/{filename}"
                else:
                    nas_relative_path = f"{self._generate_nas_path(shop_name, file_type, filename).replace('Designs/', f'Designs/{template_name}/').replace('Mockups/BaseMockups/', f'Mockups/BaseMockups/{template_name}/')}"
            else:
                nas_relative_path = self._generate_nas_path(shop_name, file_type, filename)
            
            # Upload to NAS
            success = self.nas.upload_file_content(
                file_content=file_content,
                shop_name=shop_name,
                relative_path=nas_relative_path
            )
            
            if not success:
                logging.error(f"Failed to upload file to NAS: {nas_relative_path}")
                return False, None, None
            
            # Create database record
            nas_full_path = f"{self.base_path}/{shop_name}/{nas_relative_path}"
            
            file_record = File(
                org_id=org_id,
                file_type=file_type,
                nas_path=nas_full_path,
                filename=filename,
                original_filename=filename,
                file_size=file_size,
                sha256=file_hash,
                status='ready',
                metadata=metadata or {},
                created_by=user_id
            )
            
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            file_info = {
                'id': str(file_record.id),
                'nas_path': nas_full_path,
                'filename': filename,
                'file_size': file_size,
                'deduplicated': False
            }
            
            logging.info(f"Successfully uploaded file: {file_record.id} -> {nas_full_path}")
            return True, str(file_record.id), file_info
            
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            return False, None, None
    
    def upload_from_fastapi_file(
        self,
        upload_file,
        shop_name: str,
        org_id: str,
        file_type: str = 'other',
        template_name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Upload from FastAPI UploadFile object
        """
        try:
            # Read file content
            file_content = upload_file.read()
            filename = upload_file.filename or f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Reset file pointer for potential reuse
            upload_file.seek(0)
            
            # Get file metadata
            if not metadata:
                metadata = {}
            metadata.update({
                'content_type': upload_file.content_type,
                'original_filename': upload_file.filename
            })
            
            return self.upload_file(
                file_content=file_content,
                filename=filename,
                shop_name=shop_name,
                org_id=org_id,
                file_type=file_type,
                template_name=template_name,
                user_id=user_id,
                metadata=metadata
            )
            
        except Exception as e:
            logging.error(f"Error uploading FastAPI file: {e}")
            return False, None, None
    
    def get_file_info(self, file_id: str, org_id: str) -> Optional[dict]:
        """Get file information from database"""
        try:
            db = next(get_db())
            file_record = db.query(File).filter(
                File.id == file_id,
                File.org_id == org_id
            ).first()
            
            if not file_record:
                return None
            
            return {
                'id': str(file_record.id),
                'filename': file_record.filename,
                'nas_path': file_record.nas_path,
                'file_type': file_record.file_type,
                'file_size': file_record.file_size,
                'sha256': file_record.sha256,
                'status': file_record.status,
                'metadata': file_record.metadata,
                'created_at': file_record.created_at
            }
            
        except Exception as e:
            logging.error(f"Error getting file info: {e}")
            return None
    
    def delete_file(self, file_id: str, org_id: str) -> bool:
        """Delete file from NAS and database"""
        try:
            db = next(get_db())
            file_record = db.query(File).filter(
                File.id == file_id,
                File.org_id == org_id
            ).first()
            
            if not file_record:
                logging.warning(f"File not found for deletion: {file_id}")
                return False
            
            # Extract shop name from nas_path for deletion
            # Path format: /share/Graphics/{shop_name}/...
            path_parts = file_record.nas_path.replace('/share/Graphics/', '').split('/')
            if len(path_parts) < 2:
                logging.error(f"Invalid NAS path format: {file_record.nas_path}")
                return False
            
            shop_name = path_parts[0]
            relative_path = '/'.join(path_parts[1:])
            
            # Delete from NAS
            nas_success = self.nas.delete_file(shop_name, relative_path)
            
            # Delete from database regardless of NAS success
            db.delete(file_record)
            db.commit()
            
            if nas_success:
                logging.info(f"Successfully deleted file: {file_id}")
            else:
                logging.warning(f"File deleted from database but not from NAS: {file_id}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error deleting file: {e}")
            return False
    
    def list_files(
        self, 
        org_id: str, 
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[list, int]:
        """List files with optional filtering"""
        try:
            db = next(get_db())
            query = db.query(File).filter(File.org_id == org_id)
            
            if file_type:
                query = query.filter(File.file_type == file_type)
            
            total = query.count()
            files = query.offset(offset).limit(limit).all()
            
            file_list = []
            for file_record in files:
                file_list.append({
                    'id': str(file_record.id),
                    'filename': file_record.filename,
                    'file_type': file_record.file_type,
                    'file_size': file_record.file_size,
                    'status': file_record.status,
                    'created_at': file_record.created_at
                })
            
            return file_list, total
            
        except Exception as e:
            logging.error(f"Error listing files: {e}")
            return [], 0

# Global instance
file_storage = FileStorageAdapter()