from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)  # e.g., Pathology, Radiology, Cardiology
    description = Column(Text, nullable=True)
    sample_type = Column(String(100), nullable=True)  # e.g., Blood, Urine, Swab
    preparation_instructions = Column(Text, nullable=True)  # e.g., 10-12 hours fasting required
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    centre_tests = relationship("CentreTest", back_populates="test", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="test")
