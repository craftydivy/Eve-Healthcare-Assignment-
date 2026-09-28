from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.cache import cache
from app.schemas.common import HealthResponse

router = APIRouter(tags=["System & Health"])


@router.get("/health", response_model=HealthResponse, summary="System Health Check")
def health_check(db: Session = Depends(get_db)):
    """Check connectivity to PostgreSQL/SQLite database and Redis/Cache layer."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    cache_status = "redis_connected" if cache.is_redis else "in_memory_fallback_active"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.VERSION,
        database=db_status,
        cache=cache_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
