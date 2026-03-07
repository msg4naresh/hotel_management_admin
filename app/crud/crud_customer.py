from typing import Any

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.customer import CustomerBase, CustomerCreate, CustomerDB, CustomerUpdate


class CRUDCustomer(CRUDBase[CustomerDB, CustomerCreate, CustomerBase]):
    """
    CRUD operations for customers.

    Handles email and phone uniqueness validation with pessimistic locking
    to prevent race conditions during customer creation and updates.
    """

    def create(self, db: Session, *, obj_in: CustomerCreate) -> CustomerDB:
        """Create a new customer with email and phone uniqueness check."""
        # Check for existing email or phone with pessimistic lock
        existing = (
            db.query(CustomerDB)
            .filter(
                or_(
                    CustomerDB.email == obj_in.email,
                    CustomerDB.phone == obj_in.phone,
                )
            )
            .with_for_update()
            .first()
        )

        if existing:
            if existing.email == obj_in.email:
                raise ValueError(f"Email {obj_in.email} is already registered")
            raise ValueError(f"Phone number {obj_in.phone} is already registered")

        # Create new customer
        db_obj = CustomerDB(**obj_in.model_dump())
        db.add(db_obj)

        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            raise ValueError("A customer with this email or phone number already exists")

    def update(
        self, db: Session, *, db_obj: CustomerDB, obj_in: CustomerUpdate | dict[str, Any]
    ) -> CustomerDB:
        """Update a customer with email and phone uniqueness check."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Check email uniqueness if email is being changed
        new_email = update_data.get("email")
        if new_email and new_email != db_obj.email:
            existing = (
                db.query(CustomerDB)
                .filter(CustomerDB.email == new_email, CustomerDB.id != db_obj.id)
                .first()
            )
            if existing:
                raise ValueError(f"Email {new_email} is already registered")

        # Check phone uniqueness if phone is being changed
        new_phone = update_data.get("phone")
        if new_phone and new_phone != db_obj.phone:
            existing = (
                db.query(CustomerDB)
                .filter(CustomerDB.phone == new_phone, CustomerDB.id != db_obj.id)
                .first()
            )
            if existing:
                raise ValueError(f"Phone number {new_phone} is already registered")

        # Apply updates
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)

        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            raise ValueError("A customer with this email or phone number already exists")

    def get_with_lock(self, db: Session, id_: int) -> CustomerDB | None:
        """Get customer with pessimistic lock for updates."""
        return db.query(self.model).filter(self.model.id == id_).with_for_update().first()


customer = CRUDCustomer(CustomerDB)
