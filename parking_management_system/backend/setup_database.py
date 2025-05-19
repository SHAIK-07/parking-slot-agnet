"""
Consolidated database setup script for the Parking Management System.
This script creates all necessary tables and populates them with sample data.
"""

import os
import sys
from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the database models
from app.database.database import Base, engine
from app.database.models import (
    Mall, ParkingSlot, VehicleType, User, Vehicle, Booking, BookingStatus, Payment, PaymentStatus, UserRole
)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

def create_tables():
    """Create all tables defined in the models."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

def check_if_table_exists(table_name):
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def add_sample_malls():
    """Add sample mall data to the database."""
    if session.query(Mall).count() > 0:
        print("Malls already exist in the database. Skipping mall creation.")
        return

    print("Adding sample malls...")
    malls = [
        {
            "name": "Phoenix Mall of Asia",
            "address": "1 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560001",
            "contact_number": "080-12345678",
            "email": "info@phoenixasia.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "Phoenix Market City",
            "address": "2 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560002",
            "contact_number": "080-23456789",
            "email": "info@phoenixmarket.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "UB City Mall",
            "address": "3 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560003",
            "contact_number": "080-34567890",
            "email": "info@ubcity.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "Nexus Mall",
            "address": "4 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560004",
            "contact_number": "080-45678901",
            "email": "info@nexusmall.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "Mantri Square Mall",
            "address": "5 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560005",
            "contact_number": "080-56789012",
            "email": "info@mantrisquare.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "Orion Mall",
            "address": "6 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560006",
            "contact_number": "080-67890123",
            "email": "info@orionmall.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "GT World Mall",
            "address": "7 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560007",
            "contact_number": "080-78901234",
            "email": "info@gtworld.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "Forum Mall",
            "address": "8 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560008",
            "contact_number": "080-89012345",
            "email": "info@forummall.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "Garuda Mall",
            "address": "9 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560009",
            "contact_number": "080-90123456",
            "email": "info@garudamall.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        },
        {
            "name": "Vega City Mall",
            "address": "10 Mall Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "zip_code": "560010",
            "contact_number": "080-01234567",
            "email": "info@vegacity.com",
            "opening_time": "10:00 AM",
            "closing_time": "10:00 PM"
        }
    ]

    for mall_data in malls:
        mall = Mall(**mall_data)
        session.add(mall)
    
    try:
        session.commit()
        print(f"Added {len(malls)} malls to the database.")
    except IntegrityError:
        session.rollback()
        print("Error adding malls. Rolling back.")

def add_sample_parking_slots():
    """Add sample parking slots for each mall."""
    if session.query(ParkingSlot).count() > 0:
        print("Parking slots already exist in the database. Skipping slot creation.")
        return

    print("Adding sample parking slots...")
    malls = session.query(Mall).all()
    
    # Rates for different vehicle types
    rates = {
        VehicleType.CAR: 50.0,
        VehicleType.TRUCK: 100.0,
        VehicleType.BIKE: 20.0
    }
    
    # Sections for different floors
    sections = ["A", "B", "C", "D"]
    
    slots_added = 0
    
    for mall in malls:
        # Each mall has 3 floors
        for floor in range(1, 4):
            section = sections[floor % len(sections)]
            
            # 3 slots for trucks on each floor
            for i in range(1, 4):
                slot_number = f"T{floor}{i}"
                slot = ParkingSlot(
                    mall_id=mall.id,
                    slot_number=slot_number,
                    floor=floor,
                    section=section,
                    vehicle_type=VehicleType.TRUCK,
                    is_available=True,
                    hourly_rate=rates[VehicleType.TRUCK]
                )
                session.add(slot)
                slots_added += 1
            
            # 3 slots for cars on each floor
            for i in range(1, 4):
                slot_number = f"C{floor}{i}"
                slot = ParkingSlot(
                    mall_id=mall.id,
                    slot_number=slot_number,
                    floor=floor,
                    section=section,
                    vehicle_type=VehicleType.CAR,
                    is_available=True,
                    hourly_rate=rates[VehicleType.CAR]
                )
                session.add(slot)
                slots_added += 1
            
            # 4 slots for bikes on each floor
            for i in range(1, 5):
                slot_number = f"B{floor}{i}"
                slot = ParkingSlot(
                    mall_id=mall.id,
                    slot_number=slot_number,
                    floor=floor,
                    section=section,
                    vehicle_type=VehicleType.BIKE,
                    is_available=True,
                    hourly_rate=rates[VehicleType.BIKE]
                )
                session.add(slot)
                slots_added += 1
    
    try:
        session.commit()
        print(f"Added {slots_added} parking slots to the database.")
    except IntegrityError:
        session.rollback()
        print("Error adding parking slots. Rolling back.")

def add_sample_users():
    """Add sample users to the database."""
    if session.query(User).count() > 0:
        print("Users already exist in the database. Skipping user creation.")
        return

    print("Adding sample users...")
    users = [
        {
            "email": "admin@example.com",
            "hashed_password": "hashed_password_for_admin",  # In a real app, use proper password hashing
            "first_name": "Admin",
            "last_name": "User",
            "phone_number": "1234567890",
            "role": UserRole.ADMIN
        },
        {
            "email": "user1@example.com",
            "hashed_password": "hashed_password_for_user1",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "2345678901",
            "role": UserRole.USER
        },
        {
            "email": "user2@example.com",
            "hashed_password": "hashed_password_for_user2",
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_number": "3456789012",
            "role": UserRole.USER
        }
    ]

    for user_data in users:
        user = User(**user_data)
        session.add(user)
    
    try:
        session.commit()
        print(f"Added {len(users)} users to the database.")
    except IntegrityError:
        session.rollback()
        print("Error adding users. Rolling back.")

def add_sample_vehicles():
    """Add sample vehicles for users."""
    if session.query(Vehicle).count() > 0:
        print("Vehicles already exist in the database. Skipping vehicle creation.")
        return

    print("Adding sample vehicles...")
    users = session.query(User).filter(User.role == UserRole.USER).all()
    
    vehicles = [
        {
            "user_id": users[0].id,
            "license_plate": "KA01AB1234",
            "make": "Toyota",
            "model": "Corolla",
            "color": "White",
            "vehicle_type": VehicleType.CAR
        },
        {
            "user_id": users[0].id,
            "license_plate": "KA01CD5678",
            "make": "Honda",
            "model": "Activa",
            "color": "Black",
            "vehicle_type": VehicleType.BIKE
        },
        {
            "user_id": users[1].id,
            "license_plate": "KA01EF9012",
            "make": "Tata",
            "model": "Ace",
            "color": "Blue",
            "vehicle_type": VehicleType.TRUCK
        }
    ]

    for vehicle_data in vehicles:
        vehicle = Vehicle(**vehicle_data)
        session.add(vehicle)
    
    try:
        session.commit()
        print(f"Added {len(vehicles)} vehicles to the database.")
    except IntegrityError:
        session.rollback()
        print("Error adding vehicles. Rolling back.")

def main():
    """Main function to set up the database."""
    print("Starting database setup...")
    
    # Create tables if they don't exist
    create_tables()
    
    # Add sample data
    add_sample_malls()
    add_sample_parking_slots()
    add_sample_users()
    add_sample_vehicles()
    
    print("Database setup completed successfully.")

if __name__ == "__main__":
    main()
