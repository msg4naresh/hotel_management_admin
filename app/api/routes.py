from fastapi import APIRouter

from app.api.endpoints import auth, bookings, customers, documents, health, rooms

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(bookings.router, tags=["bookings"])
api_router.include_router(customers.router, tags=["customers"])
api_router.include_router(rooms.router, tags=["rooms"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(health.router, tags=["health"])
