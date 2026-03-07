import calendar
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func

from app.api.dependencies.common import CurrentUserDep, SessionDep
from app.models.bookings import BookingDB
from app.models.enums import BookingStatus

router = APIRouter()


# --- Enums & Schemas ---


class ReportPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class DateRange(BaseModel):
    start: date
    end: date


class ReportSummary(BaseModel):
    total_check_ins: int
    total_check_outs: int
    total_bookings: int
    total_collection: Decimal
    total_revenue: Decimal
    cancellations: int
    avg_room_rate: Decimal


class ChartData(BaseModel):
    labels: list[str]
    check_ins: list[int]
    revenue: list[Decimal]
    collection: list[Decimal]


class StatusBreakdown(BaseModel):
    checked_in: int
    checked_out: int
    confirmed: int
    prebooked: int
    cancelled: int


class ReportResponse(BaseModel):
    period: str
    date_range: DateRange
    summary: ReportSummary
    chart_data: ChartData
    status_breakdown: StatusBreakdown


# --- Helpers ---


def _get_date_range(period: ReportPeriod, ref_date: date) -> tuple[date, date]:
    """Return inclusive (start, end) for the given period."""
    if period == ReportPeriod.DAILY:
        return ref_date, ref_date
    elif period == ReportPeriod.WEEKLY:
        # Sun–Sat week containing ref_date (Sunday = weekday 6 in Python)
        day_of_week = ref_date.weekday()  # Mon=0 ... Sun=6
        # Shift so Sunday=0: (day_of_week + 1) % 7
        days_since_sunday = (day_of_week + 1) % 7
        start = ref_date - timedelta(days=days_since_sunday)
        end = start + timedelta(days=6)
        return start, end
    elif period == ReportPeriod.MONTHLY:
        start = ref_date.replace(day=1)
        last_day = calendar.monthrange(ref_date.year, ref_date.month)[1]
        end = ref_date.replace(day=last_day)
        return start, end
    else:  # YEARLY
        return date(ref_date.year, 1, 1), date(ref_date.year, 12, 31)


def _get_labels(period: ReportPeriod, start: date, end: date) -> list[str]:
    """Return chart labels for the period."""
    if period == ReportPeriod.DAILY:
        return ["12A-4A", "4A-8A", "8A-12P", "12P-4P", "4P-8P", "8P-12A"]
    elif period == ReportPeriod.WEEKLY:
        return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    elif period == ReportPeriod.MONTHLY:
        labels = []
        day = 1
        last_day = end.day
        while day <= last_day:
            bucket_end = min(day + 6, last_day)
            labels.append(f"{day}-{bucket_end}")
            day = bucket_end + 1
        return labels
    else:  # YEARLY
        return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _get_bucket_index(period: ReportPeriod, start: date, d: date) -> int:
    """Map a date to its bucket index within the period."""
    if period == ReportPeriod.DAILY:
        # For daily, we don't bucket by date — handled separately
        return 0
    elif period == ReportPeriod.WEEKLY:
        # Sunday=0 ... Saturday=6
        return (d.weekday() + 1) % 7
    elif period == ReportPeriod.MONTHLY:
        return (d.day - 1) // 7
    else:  # YEARLY
        return d.month - 1


# --- Endpoint ---


@router.get(
    "/reports/summary",
    response_model=ReportResponse,
    summary="Get report summary",
    description="Get booking report with summary, chart data, and status breakdown for daily/weekly/monthly/yearly periods",
)
def get_report_summary(
    current_user: CurrentUserDep,
    session: SessionDep,
    period: ReportPeriod = Query(..., description="Report period: daily, weekly, monthly, yearly"),
    date_param: date = Query(..., alias="date", description="Reference date (YYYY-MM-DD)"),
):
    start, end = _get_date_range(period, date_param)
    labels = _get_labels(period, start, end)
    num_buckets = len(labels)

    # All bookings in the date range (by scheduled_check_in)
    bookings = (
        session.query(BookingDB)
        .filter(
            BookingDB.scheduled_check_in >= start,
            BookingDB.scheduled_check_in <= end,
        )
        .all()
    )

    # --- Summary ---
    total_check_ins = 0
    total_check_outs = 0
    total_bookings = len(bookings)
    total_collection = Decimal("0")
    total_revenue = Decimal("0")
    cancellations = 0

    # --- Status breakdown ---
    status_counts: dict[str, int] = {
        "checked_in": 0,
        "checked_out": 0,
        "confirmed": 0,
        "prebooked": 0,
        "cancelled": 0,
    }

    # --- Chart data buckets ---
    check_ins_buckets = [0] * num_buckets
    revenue_buckets = [Decimal("0")] * num_buckets
    collection_buckets = [Decimal("0")] * num_buckets

    for b in bookings:
        amt_total = Decimal(str(b.total_amount or 0))
        amt_paid = Decimal(str(b.amount_paid or 0))

        total_revenue += amt_total
        total_collection += amt_paid

        # Check-ins: checked_in or checked_out (means they did check in)
        if b.booking_status in (BookingStatus.CHECKED_IN.value, BookingStatus.CHECKED_OUT.value):
            total_check_ins += 1

        # Check-outs: actual_check_out in range
        if b.booking_status == BookingStatus.CHECKED_OUT.value and b.actual_check_out and start <= b.actual_check_out <= end:
            total_check_outs += 1

        # Cancellations
        if b.booking_status == BookingStatus.CANCELLED.value:
            cancellations += 1

        # Status breakdown
        if b.booking_status in status_counts:
            status_counts[b.booking_status] += 1

        # Chart bucketing (by scheduled_check_in date)
        bucket = _get_bucket_index(period, start, b.scheduled_check_in)
        bucket = min(bucket, num_buckets - 1)  # Safety clamp

        if b.booking_status in (BookingStatus.CHECKED_IN.value, BookingStatus.CHECKED_OUT.value):
            check_ins_buckets[bucket] += 1
        revenue_buckets[bucket] += amt_total
        collection_buckets[bucket] += amt_paid

    avg_room_rate = (total_revenue / total_bookings) if total_bookings > 0 else Decimal("0")

    return ReportResponse(
        period=period.value,
        date_range=DateRange(start=start, end=end),
        summary=ReportSummary(
            total_check_ins=total_check_ins,
            total_check_outs=total_check_outs,
            total_bookings=total_bookings,
            total_collection=total_collection,
            total_revenue=total_revenue,
            cancellations=cancellations,
            avg_room_rate=avg_room_rate,
        ),
        chart_data=ChartData(
            labels=labels,
            check_ins=check_ins_buckets,
            revenue=revenue_buckets,
            collection=collection_buckets,
        ),
        status_breakdown=StatusBreakdown(
            checked_in=status_counts["checked_in"],
            checked_out=status_counts["checked_out"],
            confirmed=status_counts["confirmed"],
            prebooked=status_counts["prebooked"],
            cancelled=status_counts["cancelled"],
        ),
    )
