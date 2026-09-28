from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(128), unique=True, index=True, nullable=False)
    event_type = Column(String(64), nullable=False)  # e.g., "payment.status.updated"
    booking_id = Column(Integer, index=True, nullable=True)
    transaction_id = Column(String(100), index=True, nullable=True)
    status = Column(String(30), nullable=False)  # "PROCESSED", "IGNORED_DUPLICATE", "FAILED"
    payload = Column(Text, nullable=False)
    response_payload = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
