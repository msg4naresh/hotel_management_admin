import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.crud import customer as crud_customer
from app.models.customer import CustomerCreate, CustomerResponse, CustomerUpdate

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


@router.put(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
    summary="Update a customer",
    description="Update an existing customer's details",
)
def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    db_customer = crud_customer.get(session, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )
    try:
        return crud_customer.update(session, db_obj=db_customer, obj_in=customer_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
