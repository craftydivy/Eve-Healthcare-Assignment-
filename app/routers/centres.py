from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.models.centre_test import CentreTest
from app.models.user import User
from app.schemas.centre import CentreCreate, CentreUpdate, CentreResponse, CentreListItemResponse
from app.schemas.centre_test import CentreTestCreate, CentreTestUpdate, CentreTestResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.dependencies import require_admin
from app.cache import cache

router = APIRouter(prefix="/centres", tags=["Diagnostic Centres"])


@router.post("/", response_model=CentreResponse, status_code=status.HTTP_201_CREATED, summary="Create Diagnostic Centre")
def create_centre(
    centre_in: CentreCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Register a new diagnostic centre and optionally attach initial test offerings.
    (Requires Administrator privileges)
    """
    centre = DiagnosticCentre(
        name=centre_in.name,
        address=centre_in.address,
        city=centre_in.city,
        state=centre_in.state,
        pincode=centre_in.pincode,
        phone=centre_in.phone,
        email=centre_in.email,
        opening_time=centre_in.opening_time,
        closing_time=centre_in.closing_time,
        is_active=True,
    )
    db.add(centre)
    db.flush()

    # Attach initial tests if provided
    if centre_in.tests:
        for t in centre_in.tests:
            test_exists = db.query(DiagnosticTest).filter(DiagnosticTest.id == t.test_id).first()
            if test_exists:
                ct = CentreTest(
                    centre_id=centre.id,
                    test_id=t.test_id,
                    price=t.price,
                    turnaround_hours=t.turnaround_hours,
                    is_available=t.is_available,
                )
                db.add(ct)

    db.commit()
    db.refresh(centre)
    cache.delete_prefix("centres_")
    return centre


@router.get("/", response_model=PaginatedResponse[CentreResponse], summary="List Diagnostic Centres")
def list_centres(
    city: Optional[str] = Query(None, description="Filter centres by city"),
    test_id: Optional[int] = Query(None, description="Filter centres offering a specific test ID"),
    search: Optional[str] = Query(None, description="Search centres by name or location"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Retrieve diagnostic centres with their available tests and pricing.
    Supports filtering by city, test offerings, and location text search.
    """
    cache_key = f"centres_list:{city}:{test_id}:{search}:{page}:{page_size}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    query = db.query(DiagnosticCentre).options(
        joinedload(DiagnosticCentre.centre_tests).joinedload(CentreTest.test)
    ).filter(DiagnosticCentre.is_active == True)

    if city:
        query = query.filter(DiagnosticCentre.city.ilike(f"%{city}%"))

    if search:
        query = query.filter(
            (DiagnosticCentre.name.ilike(f"%{search}%")) |
            (DiagnosticCentre.address.ilike(f"%{search}%")) |
            (DiagnosticCentre.city.ilike(f"%{search}%"))
        )

    if test_id:
        query = query.join(DiagnosticCentre.centre_tests).filter(
            CentreTest.test_id == test_id,
            CentreTest.is_available == True
        )

    total = query.count()
    items = query.order_by(DiagnosticCentre.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    result = PaginatedResponse[CentreResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    cache.set(cache_key, result.model_dump(mode="json"), ttl=60)
    return result


@router.get("/{centre_id}", response_model=CentreResponse, summary="Get Centre Details with Tests & Prices")
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full details for a specific diagnostic centre, including all
    available diagnostic tests and their prices.
    """
    cache_key = f"centres_detail:{centre_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    centre = db.query(DiagnosticCentre).options(
        joinedload(DiagnosticCentre.centre_tests).joinedload(CentreTest.test)
    ).filter(DiagnosticCentre.id == centre_id).first()

    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic centre with ID {centre_id} not found."
        )

    response_data = CentreResponse.model_validate(centre)
    cache.set(cache_key, response_data.model_dump(mode="json"), ttl=120)
    return response_data


@router.put("/{centre_id}", response_model=CentreResponse, summary="Update Diagnostic Centre")
def update_centre(
    centre_id: int,
    centre_in: CentreUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Update details of a diagnostic centre. (Admin only)"""
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic centre with ID {centre_id} not found."
        )

    for field, value in centre_in.model_dump(exclude_unset=True).items():
        setattr(centre, field, value)

    db.commit()
    db.refresh(centre)
    cache.delete_prefix("centres_")
    return centre


@router.post("/{centre_id}/tests", response_model=CentreTestResponse, status_code=status.HTTP_201_CREATED, summary="Add Test to Centre")
def add_test_to_centre(
    centre_id: int,
    test_offering: CentreTestCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Offer a diagnostic test at a centre with a specific price and turnaround time.
    (Admin only)
    """
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Centre {centre_id} not found.")

    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_offering.test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Diagnostic test {test_offering.test_id} not found.")

    # Check if already offered
    existing = db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id,
        CentreTest.test_id == test_offering.test_id
    ).first()
    if existing:
        # Update price and availability
        existing.price = test_offering.price
        existing.turnaround_hours = test_offering.turnaround_hours
        existing.is_available = test_offering.is_available
        db.commit()
        db.refresh(existing)
        cache.delete_prefix("centres_")
        return existing

    ct = CentreTest(
        centre_id=centre_id,
        test_id=test_offering.test_id,
        price=test_offering.price,
        turnaround_hours=test_offering.turnaround_hours,
        is_available=test_offering.is_available,
    )
    db.add(ct)
    db.commit()
    db.refresh(ct)
    cache.delete_prefix("centres_")
    return ct


@router.put("/{centre_id}/tests/{test_id}", response_model=CentreTestResponse, summary="Update Test Price at Centre")
def update_test_at_centre(
    centre_id: int,
    test_id: int,
    update_data: CentreTestUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Update test price or availability at a specific centre. (Admin only)"""
    ct = db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id,
        CentreTest.test_id == test_id
    ).first()
    if not ct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} is not configured at centre {centre_id}."
        )

    for field, val in update_data.model_dump(exclude_unset=True).items():
        setattr(ct, field, val)

    db.commit()
    db.refresh(ct)
    cache.delete_prefix("centres_")
    return ct


@router.delete("/{centre_id}/tests/{test_id}", response_model=MessageResponse, summary="Remove Test from Centre")
def remove_test_from_centre(
    centre_id: int,
    test_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Remove a test offering from a centre. (Admin only)"""
    ct = db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id,
        CentreTest.test_id == test_id
    ).first()
    if not ct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} is not offered at centre {centre_id}."
        )

    db.delete(ct)
    db.commit()
    cache.delete_prefix("centres_")
    return MessageResponse(message="Test successfully removed from centre offerings.")
