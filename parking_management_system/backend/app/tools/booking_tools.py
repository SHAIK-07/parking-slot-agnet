from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..database import crud, models
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class BookingCreationInput(BaseModel):
    user_id: int = Field(..., description="ID of the user making the booking")
    vehicle_id: int = Field(..., description="ID of the vehicle for the booking")
    parking_slot_id: int = Field(..., description="ID of the parking slot to book")
    start_time: str = Field(..., description="Start time for booking in ISO format (YYYY-MM-DDTHH:MM:SS)")
    end_time: str = Field(..., description="End time for booking in ISO format (YYYY-MM-DDTHH:MM:SS)")

class BookingCreationTool(BaseTool):
    name = "create_booking"
    description = "Create a new parking slot booking"
    args_schema = BookingCreationInput
    
    def __init__(self, db: Session):
        super().__init__()
        self.db = db
    
    def _run(self, user_id: int, vehicle_id: int, parking_slot_id: int, start_time: str, end_time: str) -> str:
        try:
            # Parse datetime strings
            start_datetime = datetime.fromisoformat(start_time)
            end_datetime = datetime.fromisoformat(end_time)
            
            # Validate user exists
            user = crud.get_user(self.db, user_id)
            if not user:
                return f"User with ID {user_id} not found"
            
            # Validate vehicle exists and belongs to user
            vehicle = crud.get_vehicle(self.db, vehicle_id)
            if not vehicle:
                return f"Vehicle with ID {vehicle_id} not found"
            if vehicle.user_id != user_id:
                return f"Vehicle with ID {vehicle_id} does not belong to user with ID {user_id}"
            
            # Validate parking slot exists and is available
            parking_slot = crud.get_parking_slot(self.db, parking_slot_id)
            if not parking_slot:
                return f"Parking slot with ID {parking_slot_id} not found"
            if not parking_slot.is_available:
                return f"Parking slot with ID {parking_slot_id} is not available"
            
            # Check for conflicting bookings
            conflicting_bookings = crud.get_active_bookings_for_slot(self.db, parking_slot_id)
            for booking in conflicting_bookings:
                if (booking.start_time < end_datetime and booking.end_time > start_datetime):
                    return f"Parking slot is already booked for the requested time period"
            
            # Calculate total amount
            duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
            if duration_hours <= 24:
                total_amount = parking_slot.hourly_rate * duration_hours
            else:
                days = duration_hours / 24
                total_amount = parking_slot.daily_rate * days
            
            # Create booking
            booking_data = {
                "user_id": user_id,
                "vehicle_id": vehicle_id,
                "parking_slot_id": parking_slot_id,
                "start_time": start_datetime,
                "end_time": end_datetime,
                "status": models.BookingStatus.CONFIRMED,
                "total_amount": total_amount
            }
            
            booking = crud.create_booking(self.db, booking_data)
            
            return f"Booking created successfully. Booking ID: {booking.id}, Total Amount: ${booking.total_amount:.2f}"
            
        except Exception as e:
            return f"Error creating booking: {str(e)}"
    
    async def _arun(self, user_id: int, vehicle_id: int, parking_slot_id: int, start_time: str, end_time: str) -> str:
        # For async compatibility
        return self._run(user_id, vehicle_id, parking_slot_id, start_time, end_time)

class BookingCancellationInput(BaseModel):
    booking_id: int = Field(..., description="ID of the booking to cancel")
    user_id: int = Field(..., description="ID of the user who made the booking")

class BookingCancellationTool(BaseTool):
    name = "cancel_booking"
    description = "Cancel an existing parking slot booking"
    args_schema = BookingCancellationInput
    
    def __init__(self, db: Session):
        super().__init__()
        self.db = db
    
    def _run(self, booking_id: int, user_id: int) -> str:
        try:
            # Get booking
            booking = crud.get_booking(self.db, booking_id)
            
            if not booking:
                return f"Booking with ID {booking_id} not found"
            
            # Verify user owns the booking
            if booking.user_id != user_id:
                return f"Booking with ID {booking_id} does not belong to user with ID {user_id}"
            
            # Check if booking can be cancelled
            if booking.status == models.BookingStatus.CANCELLED:
                return f"Booking with ID {booking_id} is already cancelled"
            
            if booking.status == models.BookingStatus.COMPLETED:
                return f"Booking with ID {booking_id} is already completed and cannot be cancelled"
            
            # Cancel booking
            cancelled_booking = crud.cancel_booking(self.db, booking_id)
            
            # Update parking slot availability
            parking_slot = crud.get_parking_slot(self.db, booking.parking_slot_id)
            if parking_slot:
                crud.update_parking_slot(self.db, parking_slot.id, {"is_available": True})
            
            return f"Booking with ID {booking_id} has been cancelled successfully"
            
        except Exception as e:
            return f"Error cancelling booking: {str(e)}"
    
    async def _arun(self, booking_id: int, user_id: int) -> str:
        # For async compatibility
        return self._run(booking_id, user_id)

class BookingInquiryInput(BaseModel):
    user_id: int = Field(..., description="ID of the user to get bookings for")

class BookingInquiryTool(BaseTool):
    name = "get_user_bookings"
    description = "Get all bookings for a user"
    args_schema = BookingInquiryInput
    
    def __init__(self, db: Session):
        super().__init__()
        self.db = db
    
    def _run(self, user_id: int) -> str:
        try:
            # Validate user exists
            user = crud.get_user(self.db, user_id)
            if not user:
                return f"User with ID {user_id} not found"
            
            # Get user bookings
            bookings = crud.get_user_bookings(self.db, user_id)
            
            if not bookings:
                return f"No bookings found for user with ID {user_id}"
            
            # Format response
            response = f"Bookings for user {user.first_name} {user.last_name} (ID: {user_id}):\n\n"
            
            for booking in bookings:
                # Get parking slot details
                parking_slot = crud.get_parking_slot(self.db, booking.parking_slot_id)
                
                # Get vehicle details
                vehicle = crud.get_vehicle(self.db, booking.vehicle_id)
                
                response += f"Booking ID: {booking.id}\n"
                response += f"Status: {booking.status.value}\n"
                response += f"Vehicle: {vehicle.make} {vehicle.model} ({vehicle.license_plate})\n"
                response += f"Parking Slot: #{parking_slot.slot_number} (Floor: {parking_slot.floor}, Section: {parking_slot.section})\n"
                response += f"Start Time: {booking.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                response += f"End Time: {booking.end_time.strftime('%Y-%m-%d %H:%M')}\n"
                response += f"Total Amount: ${booking.total_amount:.2f}\n\n"
            
            return response
            
        except Exception as e:
            return f"Error retrieving bookings: {str(e)}"
    
    async def _arun(self, user_id: int) -> str:
        # For async compatibility
        return self._run(user_id)
