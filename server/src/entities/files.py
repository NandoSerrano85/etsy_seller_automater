"""
File Entity for NAS-based storage
Tracks file metadata in database while files are stored on QNAP NAS
"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from ..database.core import Base

# File type enum
file_type_enum = ENUM(
    'original', 'design', 'mockup', 'print_file', 
    'watermark', 'template', 'export', 'other',
    name='file_type_enum',
    create_type=False
)

file_status_enum = ENUM(
    'uploading', 'ready', 'processing', 'failed', 'archived',
    name='file_status_enum', 
    create_type=False
)

class File(Base):
    __tablename__ = 'files'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    
    # File type and status
    file_type = Column(file_type_enum, nullable=False)
    status = Column(file_status_enum, default='ready')
    
    # NAS storage information
    nas_path = Column(String, nullable=False)  # Full path on NAS
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    
    # File metadata
    mime_type = Column(String)
    file_size = Column(BigInteger)
    width = Column(Integer)
    height = Column(Integer)
    sha256 = Column(String)  # For deduplication
    
    # Additional metadata as JSON
    metadata = Column(JSONB, default={})
    
    # Audit fields
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", back_populates="files")
    created_by_user = relationship("User", back_populates="files")
    
    def __repr__(self):
        return f"<File(id={self.id}, filename={self.filename}, type={self.file_type})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'org_id': str(self.org_id),
            'file_type': self.file_type,
            'status': self.status,
            'nas_path': self.nas_path,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'sha256': self.sha256,
            'metadata': self.metadata,
            'created_by': str(self.created_by) if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }