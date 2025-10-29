"""
Medication service layer for CRUD operations and business logic.

Implements comprehensive medication management including CRUD operations,
deactivation, search, and validation with proper error handling.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func, or_, and_
from fastapi import HTTPException, status

from app.models.medication import MedicationMaster
from app.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    MedicationSearchParams,
    MedicationListResponse,
    MedicationDeactivateResponse
)


class MedicationService:
    """Service layer for medication master data operations."""
    
    def __init__(self, db_session: Session):
        """Initialize service with database session."""
        self.db = db_session
    
    def create_medication(self, medication_data: MedicationCreate) -> MedicationResponse:
        """
        Create a new medication.
        
        Args:
            medication_data: Medication creation data
            
        Returns:
            Created medication response
            
        Raises:
            HTTPException: If medication name already exists or validation fails
        """
        # Check for duplicate name (case-insensitive)
        existing = self._get_by_name(medication_data.name)
        if existing:
            # Raise plain HTTPException with only 'detail' to match contract tests expectations
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medication with name '{medication_data.name}' already exists"
            )
        
        # Normalize medication name (trim whitespace, maintain original case)
        normalized_name = medication_data.name.strip()
        
        # Create medication
        db_medication = MedicationMaster(
            name=normalized_name,
            description=medication_data.description.strip() if medication_data.description else None,
            is_active=medication_data.is_active
        )
        
        try:
            self.db.add(db_medication)
            self.db.commit()
            self.db.refresh(db_medication)
            
            return MedicationResponse.model_validate(db_medication)
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create medication: {str(e)}"
            )
    
    def get_medication_by_id(self, medication_id: int) -> Optional[MedicationResponse]:
        """
        Retrieve medication by ID.
        
        Args:
            medication_id: Medication ID
            
        Returns:
            Medication response or None if not found
        """
        medication = self.db.get(MedicationMaster, medication_id)
        if not medication:
            return None
            
        return MedicationResponse.model_validate(medication)
    
    def get_medication_by_name(self, name: str) -> Optional[MedicationResponse]:
        """
        Retrieve medication by name (case-insensitive).
        
        Args:
            name: Medication name
            
        Returns:
            Medication response or None if not found
        """
        medication = self._get_by_name(name)
        if not medication:
            return None
            
        return MedicationResponse.model_validate(medication)
    
    def get_medications(self, params: MedicationSearchParams) -> MedicationListResponse:
        """
        Get paginated list of medications with search and filtering.
        
        Args:
            params: Search and pagination parameters
            
        Returns:
            Paginated medication list response
        """
        # Base query
        query = select(MedicationMaster)
        
        # Apply active filter
        if params.active_only:
            query = query.where(MedicationMaster.is_active == True)
        
        # Apply search filter (case-insensitive on name and description)
        if params.search:
            search_pattern = f"%{params.search.lower()}%"
            query = query.where(
                or_(
                    func.lower(MedicationMaster.name).like(search_pattern),
                    func.lower(MedicationMaster.description).like(search_pattern)
                )
            )
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_row = self.db.exec(count_query).one()
        total = total_row if total_row is not None else 0
        
        # Apply pagination and ordering
        query = query.order_by(MedicationMaster.name)  # Alphabetical order
        query = query.offset((params.page - 1) * params.per_page)
        query = query.limit(params.per_page)
        
        # Execute query
        medications = self.db.exec(query).all()
        
        # Calculate pagination metadata
        total_pages = (total + params.per_page - 1) // params.per_page if total else 0
        
        return MedicationListResponse(
            items=[MedicationResponse.model_validate(med) for med in medications],
            total=total,
            page=params.page,
            per_page=params.per_page,
            pages=total_pages
        )
    
    def update_medication(
        self, 
        medication_id: int, 
        medication_data: MedicationUpdate
    ) -> Optional[MedicationResponse]:
        """
        Update existing medication.
        
        Args:
            medication_id: Medication ID to update
            medication_data: Update data
            
        Returns:
            Updated medication response or None if not found
            
        Raises:
            HTTPException: If name conflict or validation fails
        """
        # Get existing medication
        medication = self.db.get(MedicationMaster, medication_id)
        if not medication:
            return None
        
        # Check for name conflicts if name is being updated
        if medication_data.name and medication_data.name != medication.name:
            existing = self._get_by_name(medication_data.name)
            if existing and existing.id != medication_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Medication with name '{medication_data.name}' already exists"
                )
        
        # Apply updates
        update_data = medication_data.model_dump(exclude_unset=True)
        
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()
        
        if "description" in update_data and update_data["description"]:
            update_data["description"] = update_data["description"].strip()
        
        for field, value in update_data.items():
            setattr(medication, field, value)
        
        # Update timestamp
        medication.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(medication)
            
            return MedicationResponse.model_validate(medication)
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update medication: {str(e)}"
            )
    
    def deactivate_medication(self, medication_id: int) -> Optional[MedicationDeactivateResponse]:
        """
        Deactivate a medication (soft delete).
        
        Args:
            medication_id: Medication ID to deactivate
            
        Returns:
            Deactivation response or None if not found
        """
        medication = self.db.get(MedicationMaster, medication_id)
        if not medication:
            return None
        
        if not medication.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication is already deactivated"
            )
        
        # Deactivate medication
        medication.is_active = False
        medication.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            
            return MedicationDeactivateResponse(
                id=medication.id,
                message=f"Medication '{medication.name}' has been deactivated",
                deactivated_at=medication.updated_at,
                is_active=medication.is_active
            )
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deactivate medication: {str(e)}"
            )
    
    def delete_medication(self, medication_id: int) -> bool:
        """
        Permanently delete a medication (hard delete).
        
        Args:
            medication_id: Medication ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            HTTPException: If medication is referenced by logs or other constraints
        """
        medication = self.db.get(MedicationMaster, medication_id)
        if not medication:
            return False
        
        # Check for references in medication logs before deletion
        from backend.app.models.logs import MedicationLog
        
        # Check if medication is referenced in any medication logs
        existing_logs = self.db.query(MedicationLog).filter(
            MedicationLog.medication_name == medication.name
        ).first()
        
        if existing_logs:
            # If referenced in logs, deactivate instead of delete for data integrity
            medication.is_active = False
            self.db.add(medication)
            self.db.commit()
            raise HTTPException(
                status_code=409, 
                detail=f"Cannot delete medication '{medication.name}' - it is referenced in medication logs. Medication has been deactivated instead."
            )
        
        try:
            self.db.delete(medication)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete medication: {str(e)}. It may be referenced by existing logs."
            )
    
    def get_active_medications(self) -> List[MedicationResponse]:
        """
        Get all active medications for dropdown/selection lists.
        
        Returns:
            List of active medications ordered by name
        """
        query = select(MedicationMaster).where(
            MedicationMaster.is_active == True
        ).order_by(MedicationMaster.name)
        
        medications = self.db.exec(query).all()
        return [MedicationResponse.model_validate(med) for med in medications]
    
    def search_medications(self, search_term: str, active_only: bool = True) -> List[MedicationResponse]:
        """
        Search medications by name or description.
        
        Args:
            search_term: Search term
            active_only: Whether to include only active medications
            
        Returns:
            List of matching medications
        """
        query = select(MedicationMaster)
        
        # Apply active filter
        if active_only:
            query = query.where(MedicationMaster.is_active == True)
        
        # Apply search filter
        search_pattern = f"%{search_term.lower()}%"
        query = query.where(
            or_(
                func.lower(MedicationMaster.name).contains(search_pattern),
                func.lower(MedicationMaster.description).contains(search_pattern)
            )
        )
        
        query = query.order_by(MedicationMaster.name)
        
        medications = self.db.exec(query).all()
        return [MedicationResponse.model_validate(med) for med in medications]
    
    def validate_medication_exists(self, medication_name: str, active_only: bool = True) -> bool:
        """
        Validate that a medication exists and is optionally active.
        
        Args:
            medication_name: Name of medication to validate
            active_only: Whether to check only active medications
            
        Returns:
            True if medication exists and meets criteria
        """
        query = select(MedicationMaster).where(
            func.lower(MedicationMaster.name) == medication_name.lower()
        )
        
        if active_only:
            query = query.where(MedicationMaster.is_active == True)
        
        medication = self.db.exec(query).first()
        return medication is not None
    
    def get_medication_stats(self) -> Dict[str, Any]:
        """
        Get statistics about medications in the system.
        
        Returns:
            Dictionary with medication statistics
        """
        total_query = select(func.count(MedicationMaster.id))
        active_query = select(func.count(MedicationMaster.id)).where(
            MedicationMaster.is_active == True
        )
        inactive_query = select(func.count(MedicationMaster.id)).where(
            MedicationMaster.is_active == False
        )
        
        total_count = self.db.exec(total_query).first() or 0
        active_count = self.db.exec(active_query).first() or 0
        inactive_count = self.db.exec(inactive_query).first() or 0
        
        return {
            "total_medications": total_count,
            "active_medications": active_count,
            "inactive_medications": inactive_count,
            "activation_rate": round(active_count / total_count * 100, 2) if total_count > 0 else 0
        }
    
    def _get_by_name(self, name: str) -> Optional[MedicationMaster]:
        """
        Helper method to get medication by name (case-insensitive).
        
        Args:
            name: Medication name
            
        Returns:
            Medication model or None
        """
        query = select(MedicationMaster).where(
            func.lower(MedicationMaster.name) == name.lower().strip()
        )
        return self.db.exec(query).first()


def get_medication_service(db: Session) -> MedicationService:
    """
    Factory function to create medication service instance.
    
    Args:
        db: Database session
        
    Returns:
        MedicationService instance
    """
    return MedicationService(db)