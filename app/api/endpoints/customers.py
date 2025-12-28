import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.crud import customer as crud_customer
from app.models.customer import CustomerCreate, CustomerResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/customers",
    response_model=list[CustomerResponse],
    summary="Get all customers",
    description="Retrieve a paginated list of customers",
)
def get_customers(
    current_user: CurrentUserDep,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    return crud_customer.get_multi(session, skip=skip, limit=limit)


@router.post(
    "/create-customer",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
    description="Create a new customer with the provided details",
)
def create_customer(customer: CustomerCreate, current_user: CurrentUserDep, session: SessionDep):
    try:
        return crud_customer.create(session, obj_in=customer)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
