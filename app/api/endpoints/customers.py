from fastapi import APIRouter, Depends, HTTPException, status
from app.models.customer import CustomerResponse, CustomerCreate, CustomerDB
from app.models.users import UserDB
from app.api.dependencies.auth_deps import get_current_user
from app.db.base_db import get_session
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/customers",
         response_model=list[CustomerResponse],
         summary="Get all customers",
         description="Retrieve a list of all customers")
def get_customers(current_user: UserDB = Depends(get_current_user)):
    try:
        with get_session() as session:
            customers = session.query(CustomerDB).all()
            return customers
    except Exception as e:
        logger.exception("Error retrieving customers")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customers"
        )


@router.post("/create-customer", 
          response_model=CustomerResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Create a new customer",
          description="Create a new customer with the provided details")
def create_customer(
    customer: CustomerCreate,
    current_user: UserDB = Depends(get_current_user)
):
    try:
        with get_session() as session:
            # Check for duplicate email
            existing = session.query(CustomerDB).filter(
                CustomerDB.email == customer.email
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            db_customer = CustomerDB(
                **customer.model_dump()
            )
            session.add(db_customer)
            session.commit()
            session.refresh(db_customer)
            return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating customer")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )
    

