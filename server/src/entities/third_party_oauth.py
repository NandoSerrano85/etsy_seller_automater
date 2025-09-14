from sqlalchemy import Column, DateTime, func, ForeignKey, Text 
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class ThirdPartyOAuthToken(Base):
    __tablename__ = 'third_party_oauth_tokens'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(seconds=3600))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship('User', back_populates='third_party_tokens')
    # __table_args__ = (UniqueConstraint('user_id', 'access_token', name='_user_token_uc'),)