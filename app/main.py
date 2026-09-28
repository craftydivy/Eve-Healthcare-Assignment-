import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.logging_config import logger
from app.rate_limiter import limiter
from app.routers import auth, centres, tests, bookings, payments, health

# Ensure database tables exist
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing EVE Healthcare database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
    yield
    logger.info("Shutting down EVE Healthcare service.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
# EVE Healthcare — Diagnostic Test Bookings & Simulated Payments API

Production-ready backend service providing:
* 🔐 **Authentication**: User signup, login, and JWT-based authentication with role-based access control.
* 🏥 **Diagnostic Centres & Tests**: Comprehensive catalog and centre-specific test offerings with pricing.
* 📅 **Booking System**: State-machine backed diagnostic bookings (PENDING, CONFIRMED, FAILED, CANCELLED).
* 💳 **Simulated Payments**: Realistic payment simulation transitioning booking states.
* ⚡ **Idempotent Webhooks**: Robust webhook processing with deduplication, signature verification, and race-condition safety.
* 🚀 **Bonus Capabilities**: Redis caching, Celery async tasks, Docker Compose, structured logging, and rate limiting.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Attach SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and Structured Logging Middleware
@app.middleware("http")
async def logging_and_request_id_middleware(request: Request, call_next):
    """Add request tracing with X-Request-ID headers and structured logging."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    
    # Don't clutter logs for static assets or health checks
    if not request.url.path.startswith("/static") and request.url.path != "/health":
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({process_time:.2f}ms)",
            extra={"request_id": request_id}
        )
    return response


# Include Routers with both /api/v1 and root prefixes for spec compatibility
app.include_router(health.router)

# Mount endpoints directly (e.g. POST /payments/, POST /payments/webhook/, etc.)
app.include_router(auth.router)
app.include_router(centres.router)
app.include_router(tests.router)
app.include_router(bookings.router)
app.include_router(payments.router)

# Also mount under /api/v1 for API versioning
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(centres.router, prefix=settings.API_V1_PREFIX)
app.include_router(tests.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookings.router, prefix=settings.API_V1_PREFIX)
app.include_router(payments.router, prefix=settings.API_V1_PREFIX)

# Mount static directory for Frontend Dashboard
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
@app.get("/login", include_in_schema=False)
@app.get("/signup", include_in_schema=False)
def serve_dashboard():
    """Serve the interactive diagnostic booking and webhook testing dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        content={
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "documentation": "/docs",
            "health": "/health"
        }
    )
