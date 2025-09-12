"""
Printer service layer for printer management
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from server.src.entities.printer import Printer, PrinterType
from server.src.entities.event import Event, EventTypes
from server.src.entities.template import EtsyProductTemplate
from . import model

logger = logging.getLogger(__name__)

class PrinterService:
    
    @staticmethod
    def create_printer(
        db: Session,
        user_id: UUID,
        org_id: UUID,
        printer_data: model.PrinterCreate
    ) -> Printer:
        """Create a new printer for user"""
        try:
            # If setting as default, unset other defaults
            if printer_data.is_default:
                db.query(Printer).filter(
                    Printer.user_id == user_id,
                    Printer.org_id == org_id
                ).update({Printer.is_default: False})
            
            printer = Printer(
                user_id=user_id,
                org_id=org_id,
                name=printer_data.name,
                printer_type=printer_data.printer_type.value,
                manufacturer=printer_data.manufacturer,
                model=printer_data.model,
                description=printer_data.description,
                max_width_inches=printer_data.max_width_inches,
                max_height_inches=printer_data.max_height_inches,
                dpi=printer_data.dpi,
                supported_template_ids=printer_data.supported_template_ids,
                is_default=printer_data.is_default
            )
            db.add(printer)
            db.flush()
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=org_id,
                user_id=user_id,
                entity_type="Printer",
                entity_id=printer.id,
                payload={
                    "action": "printer_created",
                    "name": printer_data.name,
                    "printer_type": printer_data.printer_type.value,
                    "dpi": printer_data.dpi,
                    "max_dimensions": f"{printer_data.max_width_inches}x{printer_data.max_height_inches}"
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(printer)
            
            logger.info(f"Created printer: {printer.id} - {printer.name}")
            return printer
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating printer: {e}")
            raise

    @staticmethod
    def get_printer_by_id(db: Session, printer_id: UUID) -> Optional[Printer]:
        """Get printer by ID"""
        return db.query(Printer).filter(Printer.id == printer_id).first()

    @staticmethod
    def get_user_printers(
        db: Session,
        user_id: UUID,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> tuple[List[Printer], int]:
        """Get user's printers"""
        query = db.query(Printer).filter(
            Printer.user_id == user_id,
            Printer.org_id == org_id
        )
        
        if active_only:
            query = query.filter(Printer.is_active == True)
        
        # Order by default first, then by name
        query = query.order_by(Printer.is_default.desc(), Printer.name)
        
        total = query.count()
        printers = query.offset(skip).limit(limit).all()
        return printers, total

    @staticmethod
    def update_printer(
        db: Session,
        printer_id: UUID,
        printer_data: model.PrinterUpdate,
        user_id: UUID
    ) -> Optional[Printer]:
        """Update printer"""
        try:
            printer = db.query(Printer).filter(Printer.id == printer_id).first()
            if not printer:
                return None
            
            # If setting as default, unset other defaults for same user
            if printer_data.is_default:
                db.query(Printer).filter(
                    Printer.user_id == printer.user_id,
                    Printer.org_id == printer.org_id,
                    Printer.id != printer_id
                ).update({Printer.is_default: False})
            
            # Update fields
            update_data = printer_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(printer, field, value)
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=printer.org_id,
                user_id=user_id,
                entity_type="Printer",
                entity_id=printer_id,
                payload={"action": "printer_updated", "changes": update_data}
            )
            db.add(event)
            
            db.commit()
            db.refresh(printer)
            
            logger.info(f"Updated printer: {printer_id}")
            return printer
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating printer {printer_id}: {e}")
            raise

    @staticmethod
    def delete_printer(
        db: Session,
        printer_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete printer"""
        try:
            printer = db.query(Printer).filter(Printer.id == printer_id).first()
            if not printer:
                return False
            
            # Log event before deletion
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_WARNING,
                org_id=printer.org_id,
                user_id=user_id,
                entity_type="Printer",
                entity_id=printer_id,
                payload={
                    "action": "printer_deleted",
                    "name": printer.name,
                    "printer_type": printer.printer_type
                }
            )
            db.add(event)
            db.flush()
            
            # Delete printer
            db.delete(printer)
            db.commit()
            
            logger.warning(f"Deleted printer: {printer_id} - {printer.name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting printer {printer_id}: {e}")
            raise

    @staticmethod
    def check_printer_capability(
        db: Session,
        printer_id: UUID,
        width_inches: float,
        height_inches: float,
        template_id: Optional[UUID] = None
    ) -> model.PrinterCapabilityResponse:
        """Check if printer can handle given dimensions and template"""
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        if not printer:
            raise ValueError("Printer not found")
        
        width_fits = width_inches <= printer.max_width_inches
        height_fits = height_inches <= printer.max_height_inches
        can_print = width_fits and height_fits
        
        template_supported = None
        if template_id:
            template_supported = printer.supports_template(template_id)
            can_print = can_print and template_supported
        
        # Generate reason if can't print
        reason = None
        if not can_print:
            reasons = []
            if not width_fits:
                reasons.append(f"Width {width_inches}\" exceeds max {printer.max_width_inches}\"")
            if not height_fits:
                reasons.append(f"Height {height_inches}\" exceeds max {printer.max_height_inches}\"")
            if template_supported is False:
                reasons.append(f"Template {template_id} not supported")
            reason = "; ".join(reasons)
        
        return model.PrinterCapabilityResponse(
            can_print=can_print,
            printer_id=printer.id,
            printer_name=printer.name,
            width_fits=width_fits,
            height_fits=height_fits,
            template_supported=template_supported,
            reason=reason
        )

    @staticmethod
    def find_compatible_printers(
        db: Session,
        user_id: UUID,
        org_id: UUID,
        width_inches: float,
        height_inches: float,
        template_id: Optional[UUID] = None
    ) -> List[Printer]:
        """Find printers that can handle given dimensions and template"""
        query = db.query(Printer).filter(
            Printer.user_id == user_id,
            Printer.org_id == org_id,
            Printer.is_active == True,
            Printer.max_width_inches >= width_inches,
            Printer.max_height_inches >= height_inches
        )
        
        printers = query.order_by(Printer.is_default.desc(), Printer.dpi.desc()).all()
        
        # Filter by template support if specified
        if template_id:
            compatible_printers = []
            for printer in printers:
                if printer.supports_template(template_id):
                    compatible_printers.append(printer)
            return compatible_printers
        
        return printers

    @staticmethod
    def get_default_printer(db: Session, user_id: UUID, org_id: UUID) -> Optional[Printer]:
        """Get user's default printer"""
        return db.query(Printer).filter(
            Printer.user_id == user_id,
            Printer.org_id == org_id,
            Printer.is_default == True,
            Printer.is_active == True
        ).first()

    @staticmethod
    def set_default_printer(
        db: Session,
        printer_id: UUID,
        user_id: UUID
    ) -> Optional[Printer]:
        """Set printer as default for user"""
        try:
            printer = db.query(Printer).filter(
                Printer.id == printer_id,
                Printer.user_id == user_id
            ).first()
            
            if not printer:
                return None
            
            # Unset all other defaults for this user
            db.query(Printer).filter(
                Printer.user_id == user_id,
                Printer.org_id == printer.org_id
            ).update({Printer.is_default: False})
            
            # Set this printer as default
            printer.is_default = True
            
            # Log event
            event = Event.create_event(
                event_type=EventTypes.SYSTEM_INFO,
                org_id=printer.org_id,
                user_id=user_id,
                entity_type="Printer",
                entity_id=printer_id,
                payload={
                    "action": "default_printer_changed",
                    "printer_name": printer.name
                }
            )
            db.add(event)
            
            db.commit()
            db.refresh(printer)
            
            logger.info(f"Set default printer: {printer_id} for user {user_id}")
            return printer
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting default printer {printer_id}: {e}")
            raise

    @staticmethod
    def get_printer_stats(db: Session, user_id: UUID, org_id: UUID) -> model.PrinterStatsResponse:
        """Get printer statistics for user"""
        try:
            # Total and active printers
            total_printers = db.query(func.count(Printer.id)).filter(
                Printer.user_id == user_id,
                Printer.org_id == org_id
            ).scalar() or 0
            
            active_printers = db.query(func.count(Printer.id)).filter(
                Printer.user_id == user_id,
                Printer.org_id == org_id,
                Printer.is_active == True
            ).scalar() or 0
            
            # Printers by type
            type_stats = db.query(
                Printer.printer_type,
                func.count(Printer.id).label('count')
            ).filter(
                Printer.user_id == user_id,
                Printer.org_id == org_id,
                Printer.is_active == True
            ).group_by(Printer.printer_type).all()
            
            # Default printer
            default_printer = db.query(Printer).filter(
                Printer.user_id == user_id,
                Printer.org_id == org_id,
                Printer.is_default == True,
                Printer.is_active == True
            ).first()
            
            # Average DPI
            avg_dpi = db.query(func.avg(Printer.dpi)).filter(
                Printer.user_id == user_id,
                Printer.org_id == org_id,
                Printer.is_active == True
            ).scalar()
            
            return model.PrinterStatsResponse(
                total_printers=total_printers,
                active_printers=active_printers,
                by_type={printer_type: count for printer_type, count in type_stats},
                default_printer_id=default_printer.id if default_printer else None,
                average_dpi=float(avg_dpi) if avg_dpi else None
            )
            
        except Exception as e:
            logger.error(f"Error getting printer stats for user {user_id}: {e}")
            return model.PrinterStatsResponse(
                total_printers=0,
                active_printers=0,
                by_type={},
                default_printer_id=None,
                average_dpi=None
            )

    @staticmethod
    def get_suggestions() -> model.PrinterSuggestionsResponse:
        """Get printer configuration suggestions"""
        return model.PrinterSuggestionsResponse(
            dpi_suggestions=Printer.get_dpi_suggestions(),
            printer_types=Printer.get_printer_types(),
            common_sizes=[
                {"name": "Letter", "width": 8.5, "height": 11, "description": "Standard letter size"},
                {"name": "A4", "width": 8.27, "height": 11.69, "description": "International A4"},
                {"name": "Tabloid", "width": 11, "height": 17, "description": "Large format"},
                {"name": "A3", "width": 11.69, "height": 16.54, "description": "International A3"},
                {"name": "Large Format 24\"", "width": 24, "height": 36, "description": "Professional large format"},
                {"name": "Large Format 36\"", "width": 36, "height": 48, "description": "Wide format printing"},
            ]
        )