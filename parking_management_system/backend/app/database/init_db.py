from sqlalchemy.orm import Session
from . import models
from datetime import datetime

# List of mall names
MALL_NAMES = [
    "Phoenix Mall of Asia",
    "Phoenix Market City",
    "UB City Mall",
    "Nexus Mall",
    "Mantri Square Mall",
    "Orion Mall",
    "Lulu Mall",
    "VR Mall",
    "Royal Meenakshi Mall",
    "Nexus Shantiniketan Mall"
]

# Vehicle type distribution per mall (3 for trucks, 3 for cars, 4 for bikes)
VEHICLE_DISTRIBUTION = {
    models.VehicleType.TRUCK: 3,
    models.VehicleType.CAR: 3,
    models.VehicleType.BIKE: 4
}

# Hourly rates by vehicle type
HOURLY_RATES = {
    models.VehicleType.TRUCK: 100.0,
    models.VehicleType.CAR: 50.0,
    models.VehicleType.BIKE: 20.0
}

def init_db(db: Session):
    """Initialize the database with sample data"""

    # Check if data already exists
    if db.query(models.User).count() > 0 or db.query(models.Mall).count() > 0:
        print("Database already initialized. Skipping...")
        return

    # Create sample users
    admin_user = models.User(
        email="admin@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        first_name="Admin",
        last_name="User",
        phone_number="1234567890",
        role=models.UserRole.ADMIN
    )
    db.add(admin_user)

    for i in range(1, 4):
        user = models.User(
            email=f"user{i}@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
            first_name=f"User{i}",
            last_name="Test",
            phone_number=f"98765{i}4321",
            role=models.UserRole.USER
        )
        db.add(user)

    db.commit()

    # Create sample vehicles
    vehicles = [
        models.Vehicle(
            user_id=1,
            license_plate="TN01AB1234",
            make="Toyota",
            model="Innova",
            color="White",
            vehicle_type=models.VehicleType.CAR
        ),
        models.Vehicle(
            user_id=2,
            license_plate="KA02CD5678",
            make="Honda",
            model="Activa",
            color="Black",
            vehicle_type=models.VehicleType.BIKE
        ),
        models.Vehicle(
            user_id=3,
            license_plate="MH03EF9012",
            make="Tata",
            model="Prima",
            color="Blue",
            vehicle_type=models.VehicleType.TRUCK
        ),
        models.Vehicle(
            user_id=4,
            license_plate="DL04GH3456",
            make="Maruti",
            model="Swift",
            color="Red",
            vehicle_type=models.VehicleType.CAR
        )
    ]

    for vehicle in vehicles:
        db.add(vehicle)

    db.commit()

    # Create malls
    for i, mall_name in enumerate(MALL_NAMES, 1):
        mall = models.Mall(
            name=mall_name,
            address=f"{i} Mall Road",
            city="Bangalore",
            state="Karnataka",
            zip_code=f"56000{i}",
            contact_number=f"080-12345{i}",
            email=f"info@{mall_name.lower().replace(' ', '')}.com",
            opening_time="10:00 AM",
            closing_time="10:00 PM"
        )
        db.add(mall)

    db.commit()

    # Create parking slots for each mall
    malls = db.query(models.Mall).all()

    for mall in malls:
        slot_number = 1

        for vehicle_type, count in VEHICLE_DISTRIBUTION.items():
            for _ in range(count):
                parking_slot = models.ParkingSlot(
                    mall_id=mall.id,
                    slot_number=f"{slot_number}",
                    floor=1,
                    section=f"Section {vehicle_type.value.capitalize()}",
                    vehicle_type=vehicle_type,
                    is_available=True,
                    hourly_rate=HOURLY_RATES[vehicle_type]
                )
                db.add(parking_slot)
                slot_number += 1

    db.commit()
    print("Database initialized successfully!")

if __name__ == "__main__":
    from .database import SessionLocal

    db = SessionLocal()
    init_db(db)
    db.close()
