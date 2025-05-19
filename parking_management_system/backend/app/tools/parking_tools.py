from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database import crud, models
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class ParkingSlotInquiryInput(BaseModel):
    slot_type: Optional[str] = Field(None, description="Type of parking slot (standard, handicapped, electric, etc.)")
    start_time: Optional[str] = Field(None, description="Start time for parking in ISO format (YYYY-MM-DDTHH:MM:SS)")
    end_time: Optional[str] = Field(None, description="End time for parking in ISO format (YYYY-MM-DDTHH:MM:SS)")

class ParkingSlotInquiryTool(BaseTool):
    name = "parking_slot_inquiry"
    description = "Check availability and pricing of parking slots"
    args_schema = ParkingSlotInquiryInput
    
    def __init__(self, db: Session):
        super().__init__()
        self.db = db
    
    def _run(self, slot_type: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None) -> str:
        try:
            # Parse datetime strings if provided
            start_datetime = datetime.fromisoformat(start_time) if start_time else datetime.utcnow()
            end_datetime = datetime.fromisoformat(end_time) if end_time else start_datetime + timedelta(hours=1)
            
            # Get available parking slots
            available_slots = crud.get_available_parking_slots(self.db, slot_type)
            
            if not available_slots:
                return f"No available parking slots found for type: {slot_type or 'any'}"
            
            # Check if slots are actually available for the requested time period
            truly_available_slots = []
            for slot in available_slots:
                # Check if there are any active bookings for this slot during the requested time period
                conflicting_bookings = self.db.query(models.Booking).filter(
                    models.Booking.parking_slot_id == slot.id,
                    models.Booking.status == models.BookingStatus.CONFIRMED,
                    models.Booking.start_time < end_datetime,
                    models.Booking.end_time > start_datetime
                ).all()
                
                if not conflicting_bookings:
                    truly_available_slots.append(slot)
            
            if not truly_available_slots:
                return f"No available parking slots found for the requested time period"
            
            # Calculate duration in hours
            duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
            
            # Format response
            response = f"Available parking slots for {start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')}:\n\n"
            
            for slot in truly_available_slots:
                # Calculate cost based on duration
                if duration_hours <= 24:
                    cost = slot.hourly_rate * duration_hours
                    rate_type = "hourly"
                else:
                    days = duration_hours / 24
                    cost = slot.daily_rate * days
                    rate_type = "daily"
                
                response += f"Slot #{slot.slot_number} (Floor: {slot.floor}, Section: {slot.section})\n"
                response += f"Type: {slot.slot_type}\n"
                response += f"Rate: ${slot.hourly_rate}/hour or ${slot.daily_rate}/day\n"
                response += f"Estimated cost ({rate_type}): ${cost:.2f}\n\n"
            
            return response
            
        except Exception as e:
            return f"Error checking parking slot availability: {str(e)}"
    
    async def _arun(self, slot_type: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None) -> str:
        # For async compatibility
        return self._run(slot_type, start_time, end_time)

class ParkingRateInquiryTool(BaseTool):
    name = "parking_rate_inquiry"
    description = "Get information about parking rates"
    
    def __init__(self, db: Session):
        super().__init__()
        self.db = db
    
    def _run(self) -> str:
        try:
            # Get all parking slots to extract rate information
            slots = self.db.query(models.ParkingSlot).all()
            
            if not slots:
                return "No parking slots found in the system."
            
            # Group slots by type to show rates for each type
            slot_types = {}
            for slot in slots:
                if slot.slot_type not in slot_types:
                    slot_types[slot.slot_type] = {
                        "hourly_rate": slot.hourly_rate,
                        "daily_rate": slot.daily_rate,
                        "monthly_rate": slot.monthly_rate
                    }
            
            # Format response
            response = "Parking Rates Information:\n\n"
            
            for slot_type, rates in slot_types.items():
                response += f"Type: {slot_type}\n"
                response += f"Hourly Rate: ${rates['hourly_rate']:.2f}\n"
                response += f"Daily Rate: ${rates['daily_rate']:.2f}\n"
                response += f"Monthly Rate: ${rates['monthly_rate']:.2f}\n\n"
            
            return response
            
        except Exception as e:
            return f"Error retrieving parking rates: {str(e)}"
    
    async def _arun(self) -> str:
        # For async compatibility
        return self._run()
