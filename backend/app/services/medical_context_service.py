"""
Medical context service layer for CRUD operations and business logic.

Implements comprehensive condition and doctor management including CRUD operations,
linking, passport generation, and validation with proper error handling.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from sqlmodel import Session, select, func, or_, and_
from fastapi import HTTPException, status
import structlog

from app.models.medical_context import Condition, Doctor, DoctorConditionLink
from app.schemas.medical_context import (
    ConditionCreate,
    ConditionUpdate,
    ConditionResponse,
    DoctorCreate,
    DoctorUpdate,
    DoctorResponse,
    DoctorConditionLinkCreate,
    DoctorConditionLinkResponse,
    PassportItem,
    PassportConditionItem,
    PassportDoctorItem,
    PassportResponse
)

logger = structlog.get_logger(__name__)


class MedicalContextService:
    """Service layer for medical context (conditions and doctors) operations."""
    
    def __init__(self, db_session: Session):
        """Initialize service with database session."""
        self.db = db_session
    
    # Condition CRUD Operations
    
    def create_condition(self, condition_data: ConditionCreate, user_id: str) -> ConditionResponse:
        """
        Create a new condition for the user.
        
        Args:
            condition_data: Condition creation data
            user_id: ID of the user creating the condition
            
        Returns:
            Created condition response
            
        Raises:
            HTTPException: If condition name already exists for user or validation fails
        """
        # Check for duplicate name for this user (case-insensitive)
        existing = self._get_condition_by_name(condition_data.name, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Condition with name '{condition_data.name}' already exists for this user"
            )
        
        # Normalize condition name (trim whitespace, maintain original case)
        normalized_name = condition_data.name.strip()
        
        # Create condition
        db_condition = Condition(
            user_id=user_id,
            name=normalized_name,
            description=condition_data.description.strip() if condition_data.description else None,
            is_active=condition_data.is_active
        )
        
        try:
            self.db.add(db_condition)
            self.db.commit()
            self.db.refresh(db_condition)
            
            logger.info("condition_created", 
                       condition_id=db_condition.id, 
                       user_id=user_id, 
                       name=normalized_name)
            
            return ConditionResponse.model_validate(db_condition)
            
        except Exception as e:
            self.db.rollback()
            logger.error("condition_creation_failed", 
                        user_id=user_id, 
                        name=normalized_name, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create condition: {str(e)}"
            )
    
    def get_condition_by_id(self, condition_id: str, user_id: str) -> Optional[ConditionResponse]:
        """
        Retrieve condition by ID for the user.
        
        Args:
            condition_id: Condition identifier
            user_id: ID of the user
            
        Returns:
            Condition response if found and owned by user, None otherwise
        """
        statement = select(Condition).where(
            and_(Condition.id == condition_id, Condition.user_id == user_id)
        )
        condition = self.db.exec(statement).first()
        
        if condition:
            return ConditionResponse.model_validate(condition)
        return None
    
    def get_user_conditions(self, user_id: str, active_only: bool = False) -> List[ConditionResponse]:
        """
        Retrieve all conditions for a user.
        
        Args:
            user_id: User identifier
            active_only: If True, only return active conditions
            
        Returns:
            List of condition responses
        """
        statement = select(Condition).where(Condition.user_id == user_id)
        
        if active_only:
            statement = statement.where(Condition.is_active == True)
        
        statement = statement.order_by(Condition.created_at.desc())
        
        conditions = self.db.exec(statement).all()
        return [ConditionResponse.model_validate(condition) for condition in conditions]
    
    def update_condition(self, condition_id: str, user_id: str, update_data: ConditionUpdate) -> Optional[ConditionResponse]:
        """
        Update an existing condition.
        
        Args:
            condition_id: Condition identifier
            user_id: User identifier
            update_data: Update data
            
        Returns:
            Updated condition response if found and updated, None if not found
            
        Raises:
            HTTPException: If validation fails or duplicate name
        """
        statement = select(Condition).where(
            and_(Condition.id == condition_id, Condition.user_id == user_id)
        )
        condition = self.db.exec(statement).first()
        
        if not condition:
            return None
        
        # Check for duplicate name if name is being updated
        if update_data.name and update_data.name.strip() != condition.name:
            existing = self._get_condition_by_name(update_data.name, user_id)
            if existing and existing.id != condition_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Condition with name '{update_data.name}' already exists for this user"
                )
        
        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == "name" and value:
                value = value.strip()
            elif field == "description" and value:
                value = value.strip() if value.strip() else None
            setattr(condition, field, value)
        
        try:
            self.db.commit()
            self.db.refresh(condition)
            
            logger.info("condition_updated", 
                       condition_id=condition_id, 
                       user_id=user_id,
                       updated_fields=list(update_dict.keys()))
            
            return ConditionResponse.model_validate(condition)
            
        except Exception as e:
            self.db.rollback()
            logger.error("condition_update_failed", 
                        condition_id=condition_id, 
                        user_id=user_id, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update condition: {str(e)}"
            )
    
    def delete_condition(self, condition_id: str, user_id: str) -> bool:
        """
        Delete a condition (soft delete by setting is_active=False).
        
        Args:
            condition_id: Condition identifier
            user_id: User identifier
            
        Returns:
            True if deleted, False if not found
        """
        statement = select(Condition).where(
            and_(Condition.id == condition_id, Condition.user_id == user_id)
        )
        condition = self.db.exec(statement).first()
        
        if not condition:
            return False
        
        try:
            condition.is_active = False
            self.db.commit()
            
            logger.info("condition_deleted", 
                       condition_id=condition_id, 
                       user_id=user_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("condition_deletion_failed", 
                        condition_id=condition_id, 
                        user_id=user_id, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete condition: {str(e)}"
            )
    
    # Doctor CRUD Operations
    
    def create_doctor(self, doctor_data: DoctorCreate, user_id: str) -> DoctorResponse:
        """
        Create a new doctor for the user.
        
        Args:
            doctor_data: Doctor creation data
            user_id: ID of the user creating the doctor
            
        Returns:
            Created doctor response
            
        Raises:
            HTTPException: If validation fails
        """
        # Normalize doctor fields
        normalized_name = doctor_data.name.strip()
        normalized_specialty = doctor_data.specialty.strip()
        
        # Create doctor
        db_doctor = Doctor(
            user_id=user_id,
            name=normalized_name,
            specialty=normalized_specialty,
            contact_info=doctor_data.contact_info.strip() if doctor_data.contact_info else None,
            is_active=doctor_data.is_active
        )
        
        try:
            self.db.add(db_doctor)
            self.db.commit()
            self.db.refresh(db_doctor)
            
            logger.info("doctor_created", 
                       doctor_id=db_doctor.id, 
                       user_id=user_id, 
                       name=normalized_name,
                       specialty=normalized_specialty)
            
            return DoctorResponse.model_validate(db_doctor)
            
        except Exception as e:
            self.db.rollback()
            logger.error("doctor_creation_failed", 
                        user_id=user_id, 
                        name=normalized_name, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create doctor: {str(e)}"
            )
    
    def get_doctor_by_id(self, doctor_id: str, user_id: str) -> Optional[DoctorResponse]:
        """
        Retrieve doctor by ID for the user.
        
        Args:
            doctor_id: Doctor identifier
            user_id: ID of the user
            
        Returns:
            Doctor response if found and owned by user, None otherwise
        """
        statement = select(Doctor).where(
            and_(Doctor.id == doctor_id, Doctor.user_id == user_id)
        )
        doctor = self.db.exec(statement).first()
        
        if doctor:
            return DoctorResponse.model_validate(doctor)
        return None
    
    def get_user_doctors(self, user_id: str, active_only: bool = False, specialty: Optional[str] = None) -> List[DoctorResponse]:
        """
        Retrieve all doctors for a user.
        
        Args:
            user_id: User identifier
            active_only: If True, only return active doctors
            specialty: If provided, filter by specialty
            
        Returns:
            List of doctor responses
        """
        statement = select(Doctor).where(Doctor.user_id == user_id)
        
        if active_only:
            statement = statement.where(Doctor.is_active == True)
        
        if specialty:
            statement = statement.where(Doctor.specialty.ilike(f"%{specialty}%"))
        
        statement = statement.order_by(Doctor.name)
        
        doctors = self.db.exec(statement).all()
        return [DoctorResponse.model_validate(doctor) for doctor in doctors]
    
    def update_doctor(self, doctor_id: str, user_id: str, update_data: DoctorUpdate) -> Optional[DoctorResponse]:
        """
        Update an existing doctor.
        
        Args:
            doctor_id: Doctor identifier
            user_id: User identifier
            update_data: Update data
            
        Returns:
            Updated doctor response if found and updated, None if not found
            
        Raises:
            HTTPException: If validation fails
        """
        statement = select(Doctor).where(
            and_(Doctor.id == doctor_id, Doctor.user_id == user_id)
        )
        doctor = self.db.exec(statement).first()
        
        if not doctor:
            return None
        
        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field in ["name", "specialty"] and value:
                value = value.strip()
            elif field == "contact_info" and value:
                value = value.strip() if value.strip() else None
            setattr(doctor, field, value)
        
        try:
            self.db.commit()
            self.db.refresh(doctor)
            
            logger.info("doctor_updated", 
                       doctor_id=doctor_id, 
                       user_id=user_id,
                       updated_fields=list(update_dict.keys()))
            
            return DoctorResponse.model_validate(doctor)
            
        except Exception as e:
            self.db.rollback()
            logger.error("doctor_update_failed", 
                        doctor_id=doctor_id, 
                        user_id=user_id, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update doctor: {str(e)}"
            )
    
    def delete_doctor(self, doctor_id: str, user_id: str) -> bool:
        """
        Delete a doctor (soft delete by setting is_active=False).
        
        Args:
            doctor_id: Doctor identifier
            user_id: User identifier
            
        Returns:
            True if deleted, False if not found
        """
        statement = select(Doctor).where(
            and_(Doctor.id == doctor_id, Doctor.user_id == user_id)
        )
        doctor = self.db.exec(statement).first()
        
        if not doctor:
            return False
        
        try:
            doctor.is_active = False
            self.db.commit()
            
            logger.info("doctor_deleted", 
                       doctor_id=doctor_id, 
                       user_id=user_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("doctor_deletion_failed", 
                        doctor_id=doctor_id, 
                        user_id=user_id, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete doctor: {str(e)}"
            )
    
    # Doctor-Condition Linking Operations
    
    def link_doctor_to_condition(self, link_data: DoctorConditionLinkCreate, user_id: str) -> DoctorConditionLinkResponse:
        """
        Link a doctor to a condition.
        
        Args:
            link_data: Link creation data
            user_id: User identifier
            
        Returns:
            Created link response
            
        Raises:
            HTTPException: If doctor or condition not found, or link already exists
        """
        # Verify doctor exists and belongs to user
        doctor = self.get_doctor_by_id(link_data.doctor_id, user_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID '{link_data.doctor_id}' not found"
            )
        
        # Verify condition exists and belongs to user
        condition = self.get_condition_by_id(link_data.condition_id, user_id)
        if not condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Condition with ID '{link_data.condition_id}' not found"
            )
        
        # Check if link already exists
        existing_link = self._get_doctor_condition_link(link_data.doctor_id, link_data.condition_id)
        if existing_link:
            # Return existing link (idempotent operation)
            return DoctorConditionLinkResponse.model_validate(existing_link)
        
        # Create link
        db_link = DoctorConditionLink(
            doctor_id=link_data.doctor_id,
            condition_id=link_data.condition_id
        )
        
        try:
            self.db.add(db_link)
            self.db.commit()
            self.db.refresh(db_link)
            
            logger.info("doctor_condition_linked", 
                       doctor_id=link_data.doctor_id, 
                       condition_id=link_data.condition_id,
                       user_id=user_id)
            
            return DoctorConditionLinkResponse.model_validate(db_link)
            
        except Exception as e:
            self.db.rollback()
            logger.error("doctor_condition_link_failed", 
                        doctor_id=link_data.doctor_id, 
                        condition_id=link_data.condition_id,
                        user_id=user_id, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to link doctor to condition: {str(e)}"
            )
    
    def unlink_doctor_from_condition(self, doctor_id: str, condition_id: str, user_id: str) -> bool:
        """
        Remove link between doctor and condition.
        
        Args:
            doctor_id: Doctor identifier
            condition_id: Condition identifier
            user_id: User identifier
            
        Returns:
            True if unlinked, False if link not found
            
        Raises:
            HTTPException: If doctor or condition not found
        """
        # Verify ownership
        doctor = self.get_doctor_by_id(doctor_id, user_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID '{doctor_id}' not found"
            )
        
        condition = self.get_condition_by_id(condition_id, user_id)
        if not condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Condition with ID '{condition_id}' not found"
            )
        
        # Find and delete link
        statement = select(DoctorConditionLink).where(
            and_(
                DoctorConditionLink.doctor_id == doctor_id,
                DoctorConditionLink.condition_id == condition_id
            )
        )
        link = self.db.exec(statement).first()
        
        if not link:
            return False
        
        try:
            self.db.delete(link)
            self.db.commit()
            
            logger.info("doctor_condition_unlinked", 
                       doctor_id=doctor_id, 
                       condition_id=condition_id,
                       user_id=user_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("doctor_condition_unlink_failed", 
                        doctor_id=doctor_id, 
                        condition_id=condition_id,
                        user_id=user_id, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unlink doctor from condition: {str(e)}"
            )
    
    # Passport Operations
    
    def get_user_passport(self, user_id: str) -> PassportResponse:
        """
        Generate passport view for user showing conditions with linked doctors.
        
        Args:
            user_id: User identifier
            
        Returns:
            Complete passport response with conditions and linked doctors
        """
        try:
            # Get active conditions with their linked doctors
            statement = (
                select(Condition)
                .where(and_(Condition.user_id == user_id, Condition.is_active == True))
                .order_by(Condition.name)
            )
            conditions = self.db.exec(statement).all()
            
            passport_items = []
            unique_doctors: Set[str] = set()
            
            for condition in conditions:
                # Get linked doctors for this condition
                doctor_statement = (
                    select(Doctor)
                    .join(DoctorConditionLink)
                    .where(
                        and_(
                            DoctorConditionLink.condition_id == condition.id,
                            Doctor.user_id == user_id,
                            Doctor.is_active == True
                        )
                    )
                    .order_by(Doctor.name)
                )
                doctors = self.db.exec(doctor_statement).all()
                
                # Convert to passport format
                passport_condition = PassportConditionItem.model_validate(condition)
                passport_doctors = [PassportDoctorItem.model_validate(doctor) for doctor in doctors]
                
                # Track unique doctors
                for doctor in doctors:
                    unique_doctors.add(doctor.id)
                
                passport_items.append(PassportItem(
                    condition=passport_condition,
                    doctors=passport_doctors
                ))
            
            return PassportResponse(
                passport=passport_items,
                total_conditions=len(conditions),
                total_doctors=len(unique_doctors)
            )
            
        except Exception as e:
            logger.error("passport_generation_failed", 
                        user_id=user_id, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate passport: {str(e)}"
            )
    
    # Private helper methods
    
    def _get_condition_by_name(self, name: str, user_id: str) -> Optional[Condition]:
        """Get condition by name for user (case-insensitive)."""
        statement = select(Condition).where(
            and_(
                Condition.user_id == user_id,
                func.lower(Condition.name) == func.lower(name.strip())
            )
        )
        return self.db.exec(statement).first()
    
    def _get_doctor_condition_link(self, doctor_id: str, condition_id: str) -> Optional[DoctorConditionLink]:
        """Get existing doctor-condition link."""
        statement = select(DoctorConditionLink).where(
            and_(
                DoctorConditionLink.doctor_id == doctor_id,
                DoctorConditionLink.condition_id == condition_id
            )
        )
        return self.db.exec(statement).first()