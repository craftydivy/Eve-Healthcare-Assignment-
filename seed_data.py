#!/usr/bin/env python3
"""
Seed realistic diagnostic centres, tests, pricing, and initial test users.
"""
from datetime import datetime, timezone, timedelta
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.models.centre_test import CentreTest
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.services.auth_service import hash_password


def seed():
    print("🌱 Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users
        admin = db.query(User).filter(User.email == "admin@evehealthcare.com").first()
        if not admin:
            admin = User(
                email="admin@evehealthcare.com",
                hashed_password=hash_password("AdminPass123!"),
                full_name="EVE System Administrator",
                phone="+919876543210",
                role="ADMIN",
                is_active=True,
            )
            db.add(admin)
            print("  Created default admin: admin@evehealthcare.com / AdminPass123!")

        patient = db.query(User).filter(User.email == "patient@example.com").first()
        if not patient:
            patient = User(
                email="patient@example.com",
                hashed_password=hash_password("PatientPass123!"),
                full_name="Aarav Sharma",
                phone="+919123456789",
                role="PATIENT",
                is_active=True,
            )
            db.add(patient)
            print("  Created default patient: patient@example.com / PatientPass123!")

        db.flush()

        # 2. Seed Diagnostic Tests
        tests_data = [
            {
                "name": "Complete Blood Count (CBC)",
                "code": "CBC-01",
                "category": "Pathology",
                "sample_type": "Blood",
                "preparation_instructions": "No specific fasting required.",
                "description": "Evaluates overall health and checks for a wide variety of conditions like anemia, infection, and leukemia.",
            },
            {
                "name": "Lipid Profile Panel",
                "code": "LIPID-02",
                "category": "Biochemistry",
                "sample_type": "Blood",
                "preparation_instructions": "10-12 hours overnight fasting is strictly mandatory.",
                "description": "Measures cholesterol levels and triglycerides to assess cardiovascular risk.",
            },
            {
                "name": "Thyroid Profile (T3, T4, TSH)",
                "code": "THY-03",
                "category": "Endocrinology",
                "sample_type": "Blood",
                "preparation_instructions": "Morning blood draw recommended prior to taking thyroid medication.",
                "description": "Assesses thyroid gland function and metabolic hormone levels.",
            },
            {
                "name": "HbA1c (Glycated Hemoglobin)",
                "code": "HBA1C-04",
                "category": "Diabetes Care",
                "sample_type": "Blood",
                "preparation_instructions": "Fasting not required.",
                "description": "Provides an accurate measurement of average blood glucose levels over the past 2 to 3 months.",
            },
            {
                "name": "Vitamin D (25-OH) & B12 Combo",
                "code": "VIT-05",
                "category": "Wellness",
                "sample_type": "Blood",
                "preparation_instructions": "Overnight fasting recommended.",
                "description": "Measures key vitamin levels vital for bone health, neurological vitality, and energy.",
            },
            {
                "name": "Liver Function Test (LFT)",
                "code": "LFT-06",
                "category": "Pathology",
                "sample_type": "Blood",
                "preparation_instructions": "8-10 hours fasting recommended. Avoid alcohol 24h prior.",
                "description": "Measures enzymes, proteins, and bilirubin in blood to evaluate liver health.",
            },
            {
                "name": "Chest X-Ray (PA View)",
                "code": "XRAY-07",
                "category": "Radiology",
                "sample_type": "Imaging",
                "preparation_instructions": "Remove all metallic objects, jewelry, and clothing above waist.",
                "description": "Digital radiographic scan of chest, lungs, and heart.",
            },
            {
                "name": "Ultrasound Whole Abdomen & Pelvis",
                "code": "USG-08",
                "category": "Radiology",
                "sample_type": "Imaging",
                "preparation_instructions": "Fasting for 4-6 hours required; drink 1 liter water 1 hour prior for full bladder.",
                "description": "High-frequency sonic imaging of liver, gallbladder, pancreas, kidneys, spleen, and pelvic organs.",
            },
        ]

        test_records = {}
        for t in tests_data:
            existing_t = db.query(DiagnosticTest).filter(DiagnosticTest.code == t["code"]).first()
            if not existing_t:
                existing_t = DiagnosticTest(**t, is_active=True)
                db.add(existing_t)
                db.flush()
                print(f"  Added Test: {t['name']}")
            test_records[t["code"]] = existing_t

        # 3. Seed Diagnostic Centres
        centres_data = [
            {
                "name": "Apollo Diagnostics — Indiranagar",
                "address": "100 Feet Road, HAL 2nd Stage, Indiranagar",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
                "phone": "+918025201122",
                "email": "indiranagar@apollodiagnostics.com",
                "opening_time": "07:00",
                "closing_time": "21:00",
                "test_pricing": {
                    "CBC-01": (350.00, 12),
                    "LIPID-02": (650.00, 24),
                    "THY-03": (550.00, 24),
                    "HBA1C-04": (450.00, 12),
                    "VIT-05": (1400.00, 36),
                    "LFT-06": (700.00, 24),
                    "XRAY-07": (500.00, 6),
                    "USG-08": (1600.00, 12),
                }
            },
            {
                "name": "Dr Lal PathLabs — Connaught Place",
                "address": "Block E, Inner Circle, Connaught Place",
                "city": "New Delhi",
                "state": "Delhi",
                "pincode": "110001",
                "phone": "+911123415588",
                "email": "delhi.cp@lalpathlabs.com",
                "opening_time": "06:30",
                "closing_time": "20:30",
                "test_pricing": {
                    "CBC-01": (380.00, 12),
                    "LIPID-02": (700.00, 24),
                    "THY-03": (580.00, 24),
                    "HBA1C-04": (480.00, 12),
                    "VIT-05": (1500.00, 36),
                    "LFT-06": (750.00, 24),
                }
            },
            {
                "name": "Metropolis Healthcare — Bandra West",
                "address": "Waterfield Road, Bandra West",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400050",
                "phone": "+912226401928",
                "email": "bandra@metropolisindia.com",
                "opening_time": "07:00",
                "closing_time": "21:30",
                "test_pricing": {
                    "CBC-01": (420.00, 8),
                    "LIPID-02": (780.00, 18),
                    "THY-03": (620.00, 18),
                    "HBA1C-04": (520.00, 8),
                    "VIT-05": (1650.00, 24),
                    "LFT-06": (820.00, 18),
                    "XRAY-07": (600.00, 4),
                    "USG-08": (1800.00, 8),
                }
            },
            {
                "name": "SRL Diagnostics — Park Street",
                "address": "Park Street, Near Mullick Bazar",
                "city": "Kolkata",
                "state": "West Bengal",
                "pincode": "700016",
                "phone": "+913322294433",
                "email": "parkstreet@srldiagnostics.com",
                "opening_time": "07:00",
                "closing_time": "20:00",
                "test_pricing": {
                    "CBC-01": (320.00, 12),
                    "LIPID-02": (600.00, 24),
                    "THY-03": (500.00, 24),
                    "HBA1C-04": (400.00, 12),
                    "VIT-05": (1300.00, 36),
                    "LFT-06": (650.00, 24),
                }
            }
        ]

        centre_records = []
        for c in centres_data:
            pricing = c.pop("test_pricing")
            centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.name == c["name"]).first()
            if not centre:
                centre = DiagnosticCentre(**c, is_active=True)
                db.add(centre)
                db.flush()
                print(f"  Added Centre: {c['name']} ({c['city']})")

            centre_records.append(centre)

            # Link tests with pricing
            for test_code, (price, turnaround) in pricing.items():
                test_obj = test_records.get(test_code)
                if test_obj:
                    existing_ct = db.query(CentreTest).filter(
                        CentreTest.centre_id == centre.id,
                        CentreTest.test_id == test_obj.id
                    ).first()
                    if not existing_ct:
                        ct = CentreTest(
                            centre_id=centre.id,
                            test_id=test_obj.id,
                            price=price,
                            turnaround_hours=turnaround,
                            is_available=True
                        )
                        db.add(ct)

        db.flush()

        # 4. Seed a sample confirmed booking with payment
        sample_booking = db.query(Booking).filter(Booking.booking_ref == "EVE-DEMO-SAMPLE01").first()
        if not sample_booking:
            target_centre = centre_records[0]
            target_test = test_records["CBC-01"]
            appt_time = datetime.now(timezone.utc) + timedelta(days=2, hours=3)
            
            sample_booking = Booking(
                booking_ref="EVE-DEMO-SAMPLE01",
                user_id=patient.id,
                centre_id=target_centre.id,
                test_id=target_test.id,
                appointment_time=appt_time,
                amount=350.00,
                currency="INR",
                status=BookingStatus.CONFIRMED,
                patient_name="Aarav Sharma",
                patient_age=29,
                patient_gender="Male",
                patient_phone="+919123456789",
                notes="Routine pre-employment checkup"
            )
            db.add(sample_booking)
            db.flush()

            payment = Payment(
                transaction_id="txn_sim_demo_987123",
                booking_id=sample_booking.id,
                amount=350.00,
                currency="INR",
                status=PaymentStatus.SUCCESS,
                payment_method="UPI",
                gateway_reference="gw_upi_okaxis_123",
                idempotency_key="idemp_demo_key_001",
                raw_response='{"simulated": true, "method": "UPI", "status": "SUCCESS"}'
            )
            db.add(payment)
            print("  Created sample confirmed booking & payment record.")

        db.commit()
        print("✅ Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
