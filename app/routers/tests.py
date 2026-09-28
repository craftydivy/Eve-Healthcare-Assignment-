from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.test import DiagnosticTest
from app.models.user import User
from app.schemas.test import TestCreate, TestUpdate, TestResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.dependencies import require_admin, get_current_user
from app.cache import cache

router = APIRouter(prefix="/tests", tags=["Diagnostic Tests"])


@router.post("/", response_model=TestResponse, status_code=status.HTTP_201_CREATED, summary="Create Diagnostic Test")
def create_test(
    test_in: TestCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Register a new diagnostic test in the master catalog.
    (Requires Administrator privileges)
    """
    # Check for existing code or name
    existing = db.query(DiagnosticTest).filter(
        (DiagnosticTest.code == test_in.code.upper()) | (DiagnosticTest.name.ilike(test_in.name))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A diagnostic test with name '{test_in.name}' or code '{test_in.code}' already exists."
        )

    test = DiagnosticTest(
        name=test_in.name,
        code=test_in.code.upper(),
        category=test_in.category,
        description=test_in.description,
        sample_type=test_in.sample_type,
        preparation_instructions=test_in.preparation_instructions,
        is_active=True,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    cache.delete_prefix("tests_list:")
    return test


@router.get("/", response_model=PaginatedResponse[TestResponse], summary="List Diagnostic Tests")
def list_tests(
    category: Optional[str] = Query(None, description="Filter by category (e.g., Pathology, Radiology)"),
    search: Optional[str] = Query(None, description="Search term for test name or code"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all available diagnostic tests with search and category filtering.
    """
    query = db.query(DiagnosticTest).filter(DiagnosticTest.is_active == True)

    if category:
        query = query.filter(DiagnosticTest.category.ilike(f"%{category}%"))

    if search:
        query = query.filter(
            (DiagnosticTest.name.ilike(f"%{search}%")) |
            (DiagnosticTest.code.ilike(f"%{search}%")) |
            (DiagnosticTest.description.ilike(f"%{search}%"))
        )

    total = query.count()
    items = query.order_by(DiagnosticTest.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse[TestResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{test_id}", response_model=TestResponse, summary="Get Diagnostic Test by ID")
def get_test(test_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific diagnostic test."""
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic test with ID {test_id} not found."
        )
    return test


@router.put("/{test_id}", response_model=TestResponse, summary="Update Diagnostic Test")
def update_test(
    test_id: int,
    test_in: TestUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Update details of a diagnostic test. (Admin only)"""
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic test with ID {test_id} not found."
        )

    for field, value in test_in.model_dump(exclude_unset=True).items():
        if field == "code" and value:
            value = value.upper()
        setattr(test, field, value)

    db.commit()
    db.refresh(test)
    cache.delete_prefix("tests_list:")
    return test


@router.delete("/{test_id}", response_model=MessageResponse, summary="Deactivate Diagnostic Test")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Soft delete / deactivate a diagnostic test. (Admin only)"""
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic test with ID {test_id} not found."
        )
    test.is_active = False
    db.commit()
    cache.delete_prefix("tests_list:")
    return MessageResponse(message=f"Diagnostic test '{test.name}' successfully deactivated.")
