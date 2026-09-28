import uuid
from datetime import datetime, timezone, time
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.booking import Booking, BookingStatus
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.models.centre_test import CentreTest
from app.models.user import User
from app.schemas.booking import BookingCreate


def generate_booking_ref() -> str:
    """Generate human-readable unique booking reference like EVE-20260928-A1B2C3."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"EVE-{now_str}-{random_suffix}"


def create_booking(db: Session, user: User, data: BookingCreate) -> Booking:
    """Create a new diagnostic test booking."""
    # 1. Verify centre exists and is active
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.id == data.centre_id,
        DiagnosticCentre.is_active == True
    ).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic centre with ID {data.centre_id} not found or is currently inactive."
        )

    # 2. Verify test exists and is active
    test = db.query(DiagnosticTest).filter(
        DiagnosticTest.id == data.test_id,
        DiagnosticTest.is_active == True
    ).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic test with ID {data.test_id} not found or is currently inactive."
        )

    # 3. Verify centre offers this test
    centre_test = db.query(CentreTest).filter(
        CentreTest.centre_id == data.centre_id,
        CentreTest.test_id == data.test_id,
        CentreTest.is_available == True
    ).first()
    if not centre_test:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Test '{test.name}' is not currently offered or available at '{centre.name}'."
        )

    # 4. Operating hours check
    try:
        open_h, open_m = map(int, centre.opening_time.split(":"))
        close_h, close_m = map(int, centre.closing_time.split(":"))
        appt_time = data.appointment_time.time()
        centre_open = time(open_h, open_m)
        centre_close = time(close_h, close_m)
        if not (centre_open <= appt_time <= centre_close):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Appointment time {appt_time.strftime('%H:%M')} is outside centre operating hours ({centre.opening_time} to {centre.closing_time})."
            )
    except ValueError:
        pass  # If time parsing fails, allow through

    # 5. Create booking with frozen price and initial PENDING status
    booking_ref = generate_booking_ref()
    booking = Booking(
        booking_ref=booking_ref,
        user_id=user.id,
        centre_id=data.centre_id,
        test_id=data.test_id,
        appointment_time=data.appointment_time,
        amount=centre_test.price,
        currency="INR",
        status=BookingStatus.PENDING,
        patient_name=data.patient_name,
        patient_age=data.patient_age,
        patient_gender=data.patient_gender,
        patient_phone=data.patient_phone or user.phone,
        notes=data.notes,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_by_id(db: Session, booking_id: int, current_user: User) -> Booking:
    """Retrieve booking by ID with ownership/authorization checks."""
    booking = db.query(Booking).options(
        joinedload(Booking.centre),
        joinedload(Booking.test)
    ).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found."
        )

    # Authorization check: user must own booking unless admin/staff
    if current_user.role not in ["ADMIN", "STAFF"] and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this booking."
        )

    return booking


def list_bookings(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[BookingStatus] = None,
    centre_id: Optional[int] = None,
) -> Tuple[List[Booking], int]:
    """List bookings with pagination and filters."""
    query = db.query(Booking).options(
        joinedload(Booking.centre),
        joinedload(Booking.test)
    )

    # Regular users can only see their own bookings
    if current_user.role not in ["ADMIN", "STAFF"]:
        query = query.filter(Booking.user_id == current_user.id)

    if status_filter:
        query = query.filter(Booking.status == status_filter)

    if centre_id:
        query = query.filter(Booking.centre_id == centre_id)

    total = query.count()
    items = query.order_by(Booking.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def cancel_booking(db: Session, booking_id: int, current_user: User, notes: Optional[str] = None) -> Booking:
    """Cancel a booking if in valid state."""
    booking = get_booking_by_id(db, booking_id, current_user)

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking has already been cancelled."
        )

    if booking.status == BookingStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a booking that is in FAILED status."
        )

    booking.status = BookingStatus.CANCELLED
    if notes:
        booking.notes = f"{booking.notes or ''} [Cancelled: {notes}]".strip()
    
    db.commit()
    db.refresh(booking)
    return booking
