"""
Organization service layer for business logic
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.src.entities.organization import Organization, OrganizationMember
from server.src.entities.user import User
from server.src.entities.org_features import OrgFeatures, Features
from server.src.entities.files import File
from server.src.entities.designs import DesignImages
from server.src.entities.mockup import Mockups
from server.src.entities.print_job import PrintJob
from server.src.entities.event import Event, EventTypes
from . import model

logger = logging.getLogger(__name__)

class OrganizationService:
    
    @staticmethod
    def create_organization(
        db: Session,
        org_data: model.OrganizationCreate,
        owner_user_id: Optional[UUID] = None
    ) -> Organization:
        """Create a new organization"""
        try:
            org = Organization(
                name=org_data.name,
                shop_name=org_data.shop_name,
                owner_user_id=owner_user_id
            )
            db.add(org)
            db.flush()  # Get the ID
            
            # Create default features
            features = OrgFeatures(
                org_id=org.id,
                features={
                    Features.MOCKUPS: True,
                    Features.DESIGNS: True,
                    Features.PRINT: True,
                    Features.ORDERS: True,
                    Features.ANALYTICS: True
                }
            )
            db.add(features)
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=org.id,
                user_id=owner_user_id,
                entity_type="Organization",
                entity_id=org.id,
                payload={"action": "organization_created", "name": org_data.name}
            )
            db.add(event)
            
            db.commit()
            db.refresh(org)
            
            logger.info(f"Created organization: {org.id} - {org.name}")
            return org
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating organization: {e}")
            raise

    @staticmethod
    def get_organization_by_id(db: Session, org_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        return db.query(Organization).filter(Organization.id == org_id).first()

    @staticmethod
    def get_organizations(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Organization], int]:
        """Get paginated list of organizations"""
        query = db.query(Organization)
        total = query.count()
        orgs = query.offset(skip).limit(limit).all()
        return orgs, total

    @staticmethod
    def update_organization(
        db: Session,
        org_id: UUID,
        org_data: model.OrganizationUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[Organization]:
        """Update organization"""
        try:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                return None
            
            # Update fields
            update_data = org_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(org, field, value)
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=org_id,
                user_id=user_id,
                entity_type="Organization",
                entity_id=org_id,
                payload={"action": "organization_updated", "changes": update_data}
            )
            db.add(event)
            
            db.commit()
            db.refresh(org)
            
            logger.info(f"Updated organization: {org_id}")
            return org
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating organization {org_id}: {e}")
            raise

    @staticmethod
    def delete_organization(db: Session, org_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete organization (cascade deletes all related data)"""
        try:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                return False
            
            # Log event before deletion
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_WARNING,
                org_id=org_id,
                user_id=user_id,
                entity_type="Organization",
                entity_id=org_id,
                payload={"action": "organization_deleted", "name": org.name}
            )
            db.add(event)
            db.flush()
            
            # Delete organization (cascades to all related entities)
            db.delete(org)
            db.commit()
            
            logger.warning(f"Deleted organization: {org_id} - {org.name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting organization {org_id}: {e}")
            raise

    @staticmethod
    def get_organization_features(db: Session, org_id: UUID) -> Optional[Dict[str, bool]]:
        """Get organization feature flags"""
        features = db.query(OrgFeatures).filter(OrgFeatures.org_id == org_id).first()
        return features.features if features else None

    @staticmethod
    def update_organization_features(
        db: Session,
        org_id: UUID,
        features_data: model.OrganizationFeatureUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[Dict[str, bool]]:
        """Update organization feature flags"""
        try:
            features = db.query(OrgFeatures).filter(OrgFeatures.org_id == org_id).first()
            if not features:
                # Create features if they don't exist
                features = OrgFeatures(org_id=org_id, features=features_data.features)
                db.add(features)
            else:
                # Update existing features
                if features.features is None:
                    features.features = {}
                features.features.update(features_data.features)
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=org_id,
                user_id=user_id,
                entity_type="OrgFeatures",
                entity_id=org_id,
                payload={"action": "features_updated", "changes": features_data.features}
            )
            db.add(event)
            
            db.commit()
            db.refresh(features)
            
            logger.info(f"Updated features for organization: {org_id}")
            return features.features
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating features for organization {org_id}: {e}")
            raise

    @staticmethod
    def get_organization_stats(db: Session, org_id: UUID) -> Dict[str, Any]:
        """Get organization statistics"""
        try:
            stats = {}
            
            # User count
            stats['user_count'] = db.query(func.count(User.id)).filter(User.org_id == org_id).scalar()
            
            # File count and size
            file_stats = db.query(
                func.count(File.id).label('count'),
                func.sum(File.file_size).label('total_size')
            ).filter(File.org_id == org_id).first()
            
            stats['file_count'] = file_stats.count or 0
            stats['total_file_size'] = file_stats.total_size or 0
            
            # Design count
            stats['design_count'] = db.query(func.count(DesignImages.id)).filter(
                DesignImages.org_id == org_id,
                DesignImages.is_active == True
            ).scalar()
            
            # Mockup count
            stats['mockup_count'] = db.query(func.count(Mockups.id)).filter(Mockups.org_id == org_id).scalar()
            
            # Print job stats
            print_job_stats = db.query(
                PrintJob.status,
                func.count(PrintJob.id).label('count')
            ).filter(PrintJob.org_id == org_id).group_by(PrintJob.status).all()
            
            stats['print_jobs'] = {status.value: count for status, count in print_job_stats}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats for organization {org_id}: {e}")
            return {}

    @staticmethod
    def check_user_access(db: Session, user_id: UUID, org_id: UUID) -> bool:
        """Check if user has access to organization"""
        user = db.query(User).filter(
            User.id == user_id,
            User.org_id == org_id,
            User.is_active == True
        ).first()
        return user is not None

    @staticmethod
    def get_organization_members(db: Session, org_id: UUID) -> List[Dict[str, Any]]:
        """Get all members of an organization"""
        try:
            # Get members from organization_members table
            members_query = db.query(OrganizationMember, User).join(
                User, OrganizationMember.user_id == User.id
            ).filter(OrganizationMember.organization_id == org_id).all()

            members_list = []
            for membership, user in members_query:
                members_list.append({
                    'user_id': str(user.id),
                    'user_name': user.name if hasattr(user, 'name') else user.email,
                    'email': user.email,
                    'role': membership.role,
                    'joined_at': membership.joined_at.isoformat() if membership.joined_at else None,
                    'is_active': user.is_active if hasattr(user, 'is_active') else True
                })

            # Also include users directly assigned to the org (legacy support)
            direct_users = db.query(User).filter(
                User.org_id == org_id,
                User.is_active == True
            ).all()

            for user in direct_users:
                # Avoid duplicates
                if not any(m['user_id'] == str(user.id) for m in members_list):
                    members_list.append({
                        'user_id': str(user.id),
                        'user_name': user.name if hasattr(user, 'name') else user.email,
                        'email': user.email,
                        'role': user.role if hasattr(user, 'role') else 'member',
                        'joined_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                        'is_active': user.is_active if hasattr(user, 'is_active') else True
                    })

            logger.info(f"Retrieved {len(members_list)} members for organization: {org_id}")
            return members_list

        except Exception as e:
            logger.error(f"Error getting members for organization {org_id}: {e}")
            return []