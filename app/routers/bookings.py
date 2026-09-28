from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.booking import BookingStatus
from app.schemas.booking import BookingCreate, BookingResponse, BookingStatusUpdate
from app.schemas.common import PaginatedResponse
from app.services.booking_service import create_booking, get_booking_by_id, list_bookings, cancel_booking
from app.dependencies import get_current_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, summary="Book a Diagnostic Test")
def book_test(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Book a diagnostic test at a centre.
    - Requires authenticated user
    - Freezes the test price at the time of booking
    - Creates booking in PENDING status
    - Validates appointment time is in future and within centre operating hours
    """
    booking = create_booking(db, current_user, booking_in)
    return booking


@router.get("/", response_model=PaginatedResponse[BookingResponse], summary="List Bookings")
def get_user_bookings(
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status (PENDING, CONFIRMED, FAILED, CANCELLED)"),
    centre_id: Optional[int] = Query(None, description="Filter by centre ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve bookings.
    - Regular patients only see their own bookings.
    - Administrators can see all bookings across the platform.
    """
    items, total = list_bookings(
        db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
        centre_id=centre_id,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse[BookingResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{booking_id}", response_model=BookingResponse, summary="Get Booking Details")
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve booking details by ID.
    Enforces authorization: users cannot view other patients' bookings.
    """
    booking = get_booking_by_id(db, booking_id, current_user)
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse, summary="Cancel Booking")
def cancel_user_booking(
    booking_id: int,
    notes: Optional[str] = Query(None, description="Reason for cancellation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel an existing booking in PENDING or CONFIRMED state.
    Enforces authorization and valid state transitions.
    """
    booking = cancel_booking(db, booking_id, current_user, notes=notes)
    return booking
