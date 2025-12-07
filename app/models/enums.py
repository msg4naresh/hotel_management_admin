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
