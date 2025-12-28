from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.customer import CustomerBase, CustomerCreate, CustomerDB


class CRUDCustomer(CRUDBase[CustomerDB, CustomerCreate, CustomerBase]):
    """
    CRUD operations for customers.

    Handles email uniqueness validation with pessimistic locking
    to prevent race conditions during customer creation.
    """

    def create(self, db: Session, *, obj_in: CustomerCreate) -> CustomerDB:
        """Create a new customer with email uniqueness check."""
        # Check for existing email with pessimistic lock to prevent race condition
        existing = db.query(CustomerDB).filter(CustomerDB.email == obj_in.email).with_for_update().first()

        if existing:
            raise ValueError(f"Email {obj_in.email} already registered")

        # Create new customer
        db_obj = CustomerDB(**obj_in.model_dump())
        db.add(db_obj)

        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            # Fallback in case unique constraint is violated
            raise ValueError(f"Email {obj_in.email} already registered")

    def get_with_lock(self, db: Session, id_: int) -> CustomerDB | None:
        """Get customer with pessimistic lock for updates."""
        return db.query(self.model).filter(self.model.id == id_).with_for_update().first()


customer = CRUDCustomer(CustomerDB)
