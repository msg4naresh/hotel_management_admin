from fastapi import APIRouter
from app.api.endpoints import auth, bookings, customers, rooms, documents

api_router = APIRouter()

api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(bookings.router, tags=["bookings"])
api_router.include_router(customers.router, tags=["customers"])
api_router.include_router(rooms.router, tags=["rooms"])
api_router.include_router(documents.router, tags=["documents"]) 