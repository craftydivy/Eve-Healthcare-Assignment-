import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.models.centre_test import CentreTest
from app.models.booking import Booking, BookingStatus
from app.services.auth_service import hash_password, create_access_token
from app.cache import cache

# Use a separate SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_eve_healthcare.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)
    
    yield db
    
    db.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    cache.clear()
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()


@pytest.fixture
def test_users(db_session):
    admin = User(
        email="test_admin@eve.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Test Admin",
        phone="+919999999991",
        role="ADMIN",
        is_active=True
    )
    patient1 = User(
        email="patient1@eve.com",
        hashed_password=hash_password("Patient123!"),
        full_name="Patient One",
        phone="+919999999992",
        role="PATIENT",
        is_active=True
    )
    patient2 = User(
        email="patient2@eve.com",
        hashed_password=hash_password("Patient123!"),
        full_name="Patient Two",
        phone="+919999999993",
        role="PATIENT",
        is_active=True
    )
    db_session.add_all([admin, patient1, patient2])
    db_session.commit()
    
    admin_token = create_access_token({"sub": str(admin.id), "email": admin.email, "role": admin.role})
    patient1_token = create_access_token({"sub": str(patient1.id), "email": patient1.email, "role": patient1.role})
    patient2_token = create_access_token({"sub": str(patient2.id), "email": patient2.email, "role": patient2.role})
    
    return {
        "admin": admin,
        "patient1": patient1,
        "patient2": patient2,
        "admin_token": admin_token,
        "patient1_token": patient1_token,
        "patient2_token": patient2_token,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "patient1_headers": {"Authorization": f"Bearer {patient1_token}"},
        "patient2_headers": {"Authorization": f"Bearer {patient2_token}"},
    }


@pytest.fixture
def sample_centre_and_test(db_session):
    centre = DiagnosticCentre(
        name="Test Metropolis Lab",
        address="123 Hospital Road",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        phone="+912222222222",
        opening_time="07:00",
        closing_time="20:00",
        is_active=True
    )
    test = DiagnosticTest(
        name="Comprehensive Blood Test",
        code="CBT-01",
        category="Pathology",
        sample_type="Blood",
        preparation_instructions="10 hours fasting",
        is_active=True
    )
    db_session.add_all([centre, test])
    db_session.flush()

    centre_test = CentreTest(
        centre_id=centre.id,
        test_id=test.id,
        price=Decimal("500.00"),
        turnaround_hours=24,
        is_available=True
    )
    db_session.add(centre_test)
    db_session.commit()

    return {"centre": centre, "test": test, "centre_test": centre_test}
