from datetime import timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.auth import UserSignup, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import register_user, authenticate_user, create_access_token
from app.dependencies import get_current_user
from app.rate_limiter import limiter
from starlette.requests import Request

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="User Signup")
def signup(request: Request, user_data: UserSignup, db: Session = Depends(get_db)):
    """
    Register a new patient or administrator user account.
    - **email**: Valid unique email address
    - **password**: Secure password (at least 6 characters)
    - **full_name**: User's full name
    - **phone**: Optional contact number
    - **role**: PATIENT (default) or ADMIN
    """
    user = register_user(db, user_data)
    return user


@router.post("/login", response_model=TokenResponse, summary="User Login")
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and generate JWT Bearer access token.
    """
    user = authenticate_user(db, login_data.email, login_data.password)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )


@router.get("/me", response_model=UserResponse, summary="Current User Profile")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile details of the currently authenticated user.
    """
    return current_user
