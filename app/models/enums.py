from enum import Enum


class BookingStatus(str, Enum):
    PREBOOKED = "prebooked"
    CONFIRMED = "confirmed"  # After payment/confirmation
    CHECKED_IN = "checked_in"  # Customer has arrived
    CHECKED_OUT = "checked_out"  # Customer has left
    NO_SHOW = "no_show"  # Customer didn't show up
    CANCELLED = "cancelled"  # Booking was cancelled


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"


class Building(str, Enum):
    BUILDING_1 = "building_1"
    BUILDING_2 = "building_2"
    BUILDING_3 = "building_3"


class RoomType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    DELUX = "delux"
    PREMIUM = "premium"


class RoomStatus(str, Enum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    NOT_CLEANED = "not_cleaned"
