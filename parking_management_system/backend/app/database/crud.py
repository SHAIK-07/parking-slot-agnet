from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from . import models

# User CRUD operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user_data: dict):
    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: dict):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        for key, value in user_data.items():
            setattr(db_user, key, value)
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

# Vehicle CRUD operations
def get_vehicle(db: Session, vehicle_id: int):
    return db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()

def get_vehicle_by_license_plate(db: Session, license_plate: str):
    return db.query(models.Vehicle).filter(models.Vehicle.license_plate == license_plate).first()

def get_user_vehicles(db: Session, user_id: int):
    return db.query(models.Vehicle).filter(models.Vehicle.user_id == user_id).all()

def create_vehicle(db: Session, vehicle_data: dict):
    db_vehicle = models.Vehicle(**vehicle_data)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

def update_vehicle(db: Session, vehicle_id: int, vehicle_data: dict):
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle:
        for key, value in vehicle_data.items():
            setattr(db_vehicle, key, value)
        db_vehicle.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_vehicle)
    return db_vehicle

def delete_vehicle(db: Session, vehicle_id: int):
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if db_vehicle:
        db.delete(db_vehicle)
        db.commit()
        return True
    return False

# ParkingSlot CRUD operations
def get_parking_slot(db: Session, slot_id: int):
    return db.query(models.ParkingSlot).filter(models.ParkingSlot.id == slot_id).first()

def get_parking_slot_by_number(db: Session, slot_number: str):
    return db.query(models.ParkingSlot).filter(models.ParkingSlot.slot_number == slot_number).first()

def get_available_parking_slots(db: Session, slot_type: Optional[str] = None):
    query = db.query(models.ParkingSlot).filter(models.ParkingSlot.is_available == True)
    if slot_type:
        query = query.filter(models.ParkingSlot.slot_type == slot_type)
    return query.all()

def create_parking_slot(db: Session, slot_data: dict):
    db_slot = models.ParkingSlot(**slot_data)
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def update_parking_slot(db: Session, slot_id: int, slot_data: dict):
    db_slot = db.query(models.ParkingSlot).filter(models.ParkingSlot.id == slot_id).first()
    if db_slot:
        for key, value in slot_data.items():
            setattr(db_slot, key, value)
        db_slot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_slot)
    return db_slot

def delete_parking_slot(db: Session, slot_id: int):
    db_slot = db.query(models.ParkingSlot).filter(models.ParkingSlot.id == slot_id).first()
    if db_slot:
        db.delete(db_slot)
        db.commit()
        return True
    return False

# Booking CRUD operations
def get_booking(db: Session, booking_id: int):
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()

def get_user_bookings(db: Session, user_id: int):
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).all()

def get_active_bookings_for_slot(db: Session, slot_id: int):
    return db.query(models.Booking).filter(
        models.Booking.parking_slot_id == slot_id,
        models.Booking.status == models.BookingStatus.CONFIRMED,
        models.Booking.end_time > datetime.utcnow()
    ).all()

def create_booking(db: Session, booking_data: dict):
    db_booking = models.Booking(**booking_data)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def update_booking(db: Session, booking_id: int, booking_data: dict):
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking:
        for key, value in booking_data.items():
            setattr(db_booking, key, value)
        db_booking.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_booking)
    return db_booking

def cancel_booking(db: Session, booking_id: int):
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking:
        db_booking.status = models.BookingStatus.CANCELLED
        db_booking.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_booking)
    return db_booking

# Payment CRUD operations
def get_payment(db: Session, payment_id: int):
    return db.query(models.Payment).filter(models.Payment.id == payment_id).first()

def get_payment_by_booking(db: Session, booking_id: int):
    return db.query(models.Payment).filter(models.Payment.booking_id == booking_id).first()

def create_payment(db: Session, payment_data: dict):
    db_payment = models.Payment(**payment_data)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def update_payment(db: Session, payment_id: int, payment_data: dict):
    db_payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if db_payment:
        for key, value in payment_data.items():
            setattr(db_payment, key, value)
        db_payment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_payment)
    return db_payment
