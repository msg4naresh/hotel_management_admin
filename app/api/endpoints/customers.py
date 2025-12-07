import logging

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.models.customer import CustomerCreate, CustomerDB, CustomerResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/customers",
    response_model=list[CustomerResponse],
    summary="Get all customers",
    description="Retrieve a list of all customers",
)
def get_customers(current_user: CurrentUserDep, session: SessionDep):
    customers = session.query(CustomerDB).all()
    return customers


@router.post(
    "/create-customer",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
    description="Create a new customer with the provided details",
)
def create_customer(customer: CustomerCreate, current_user: CurrentUserDep, session: SessionDep):
    # Check for duplicate email
    existing = session.query(CustomerDB).filter(CustomerDB.email == customer.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    db_customer = CustomerDB(**customer.model_dump())
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer
