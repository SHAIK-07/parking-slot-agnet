from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from .database.database import engine, Base, get_db, init_database
from .database.models import Mall, ParkingSlot, VehicleType, Vehicle, Booking, BookingStatus, User, UserRole
from .agent.agent import ParkingAgent
from .routers import chat_history

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize database with sample data
init_database()

# Create FastAPI app
app = FastAPI(title="Parking Management System API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_history.router)

# Define request and response models
class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class MallResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    state: str
    contact_number: str
    opening_time: str
    closing_time: str

class ParkingSlotResponse(BaseModel):
    id: int
    slot_number: str
    floor: int
    section: str
    vehicle_type: str
    is_available: bool
    hourly_rate: float
    mall_id: int
    mall_name: str
    booking_status: Optional[str] = None
    booking_id: Optional[int] = None
    booking_start_time: Optional[str] = None
    booking_end_time: Optional[str] = None
    vehicle_number: Optional[str] = None
    features: Optional[List[str]] = None
    location: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    mall_name: str
    slot_number: str
    vehicle_type: str
    vehicle_number: Optional[str] = None
    start_time: str
    end_time: str
    total_amount: float
    status: str
    floor: Optional[int] = None
    section: Optional[str] = None
    duration_hours: Optional[float] = None
    created_at: Optional[str] = None

# Define endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to the Parking Management System API"}

@app.get("/health-check")
def health_check():
    """Health check endpoint to verify the API is running"""
    return {"status": "ok", "message": "API is running"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    x_user_id: str = Header(..., description="User ID for conversation tracking"),
    x_user_name: Optional[str] = Header(None, description="User name for personalized responses"),
    db: Session = Depends(get_db)
):
    try:
        # Create agent for user with vector store disabled to avoid download issues
        agent = ParkingAgent(db=db, user_id=x_user_id, use_vector_store=False)

        # Set user name if provided
        if x_user_name:
            agent.user_name = x_user_name

        # Process query with optional conversation ID
        try:
            response = agent.process_query(
                query=request.query,
                conversation_id=request.conversation_id
            )
        except Exception as agent_error:
            print(f"Agent error: {str(agent_error)}")
            # Fallback to direct processing without memory
            if request.query.lower().startswith("book slot "):
                response = agent._handle_booking_command(request.query)
            elif request.query.lower() in ["yes", "confirm", "yes, please", "yes, book it"]:
                response = agent._handle_booking_confirmation()
            elif request.query.lower().startswith("cancel booking "):
                response = agent._handle_booking_cancellation(request.query)
            else:
                response = agent._call_groq_api([{"role": "user", "content": request.query}])

        # Return the response
        return ChatResponse(response=response)

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.get("/malls/", response_model=List[MallResponse])
def get_malls(db: Session = Depends(get_db)):
    """Get all malls"""
    malls = db.query(Mall).all()
    return malls

@app.get("/malls/{mall_id}/parking-slots", response_model=List[ParkingSlotResponse])
def get_mall_parking_slots(mall_id: int, vehicle_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get parking slots for a specific mall, optionally filtered by vehicle type"""
    query = db.query(ParkingSlot).join(Mall).filter(ParkingSlot.mall_id == mall_id)

    if vehicle_type:
        try:
            vehicle_type_enum = VehicleType(vehicle_type.lower())
            query = query.filter(ParkingSlot.vehicle_type == vehicle_type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid vehicle type: {vehicle_type}")

    slots = query.all()

    # Get mall name for each slot
    mall = db.query(Mall).filter(Mall.id == mall_id).first()
    if not mall:
        raise HTTPException(status_code=404, detail=f"Mall with ID {mall_id} not found")

    # Create response with mall name included
    result = []
    for slot in slots:
        result.append({
            "id": slot.id,
            "slot_number": slot.slot_number,
            "floor": slot.floor,
            "section": slot.section,
            "vehicle_type": slot.vehicle_type.value,
            "is_available": slot.is_available,
            "hourly_rate": slot.hourly_rate,
            "mall_id": mall.id,
            "mall_name": mall.name
        })

    return result

@app.get("/available-slots", response_model=List[ParkingSlotResponse])
def get_available_slots(
    vehicle_type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    include_booked: bool = False,  # Parameter to include booked slots
    mall_id: Optional[int] = None,  # New parameter to filter by mall
    db: Session = Depends(get_db)
):
    """Get all parking slots, optionally filtered by vehicle type, mall, and time period.
    Can include booked slots with their booking status."""
    try:
        # Get all slots matching vehicle type, regardless of availability
        query = db.query(ParkingSlot)

        # Apply vehicle type filter if provided
        if vehicle_type:
            try:
                vehicle_type_enum = VehicleType(vehicle_type.lower())
                query = query.filter(ParkingSlot.vehicle_type == vehicle_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid vehicle type: {vehicle_type}")

        # Apply mall filter if provided
        if mall_id:
            query = query.filter(ParkingSlot.mall_id == mall_id)

        # Execute query to get all matching slots
        all_slots = query.all()

        # Initialize variables for time filtering
        start_datetime = None
        end_datetime = None

        # Parse time parameters if provided
        if start_time and end_time:
            try:
                # Convert to timezone-aware datetime
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

                # Convert to timezone-naive datetime for consistent comparison
                start_datetime = start_datetime.replace(tzinfo=None)
                end_datetime = end_datetime.replace(tzinfo=None)

                print(f"Filtering slots for time period: {start_datetime} to {end_datetime}")
            except Exception as e:
                print(f"Error parsing dates: {str(e)}")
                # Continue without time filtering if there's an error

        # Create response with mall name and booking status included
        result = []
        for slot in all_slots:
            try:
                # Get mall for this slot
                mall = db.query(Mall).filter(Mall.id == slot.mall_id).first()
                if not mall:
                    # Skip slots with no associated mall
                    continue

                # Get vehicle type value safely
                vehicle_type_value = slot.vehicle_type.value if hasattr(slot.vehicle_type, 'value') else str(slot.vehicle_type)

                # Check for conflicting bookings
                booking_status = None
                booking_id = None
                booking_times = None

                # If time parameters are provided, check for conflicts in that time period
                if start_datetime and end_datetime:
                    conflicting_bookings = db.query(Booking).filter(
                        Booking.parking_slot_id == slot.id,
                        Booking.status == BookingStatus.CONFIRMED,
                        Booking.start_time < end_datetime,
                        Booking.end_time > start_datetime
                    ).all()
                else:
                    # If no time period is specified, check for current bookings
                    # This is just to show current status, not for actual availability checking
                    now = datetime.now()
                    conflicting_bookings = db.query(Booking).filter(
                        Booking.parking_slot_id == slot.id,
                        Booking.status == BookingStatus.CONFIRMED,
                        Booking.start_time <= now,
                        Booking.end_time >= now
                    ).all()

                # If there are conflicting bookings, mark as booked
                if conflicting_bookings:
                    booking_status = "BOOKED"
                    booking_id = conflicting_bookings[0].id
                    booking_times = {
                        "start_time": conflicting_bookings[0].start_time.isoformat(),
                        "end_time": conflicting_bookings[0].end_time.isoformat()
                    }

                    # Skip this slot if we don't want to include booked slots
                    if not include_booked:
                        continue

                # Get vehicle information if booked
                vehicle_number = None
                if booking_status == "BOOKED" and booking_id:
                    booking = db.query(Booking).filter(Booking.id == booking_id).first()
                    if booking and booking.vehicle_id:
                        vehicle = db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()
                        if vehicle:
                            vehicle_number = vehicle.license_plate

                # Add slot to results
                slot_data = {
                    "id": slot.id,
                    "slot_number": slot.slot_number,
                    "floor": slot.floor,
                    "section": slot.section,
                    "vehicle_type": vehicle_type_value,
                    "is_available": booking_status is None,  # Available if no current booking
                    "hourly_rate": slot.hourly_rate,
                    "mall_id": mall.id,
                    "mall_name": mall.name,
                    "booking_status": booking_status,
                    "booking_id": booking_id,
                    "vehicle_number": vehicle_number,
                    "features": ["CCTV", "Covered"] if slot.id % 2 == 0 else ["Open"],
                    "location": mall.address if hasattr(mall, 'address') else None
                }

                # Add booking times if available
                if booking_times:
                    slot_data["booking_start_time"] = booking_times["start_time"]
                    slot_data["booking_end_time"] = booking_times["end_time"]

                result.append(slot_data)
            except Exception as e:
                # Log the error but continue processing other slots
                print(f"Error processing slot {slot.id}: {str(e)}")
                continue

        return result
    except Exception as e:
        print(f"Error in get_available_slots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Create booking endpoint
@app.post("/bookings", response_model=BookingResponse)
def create_booking(
    slot_id: int,
    x_user_id: str = Header(..., description="User ID for booking"),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    duration: Optional[int] = None,
    license_plate: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new booking for a parking slot"""
    try:
        # Check if slot exists
        slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail=f"Parking slot with ID {slot_id} not found")

        # Parse start and end times if provided
        booking_start_time = None
        booking_end_time = None

        if start_time:
            try:
                # Convert to timezone-aware datetime
                booking_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                # Convert to timezone-naive datetime for consistent comparison
                booking_start_time = booking_start_time.replace(tzinfo=None)
            except Exception as e:
                print(f"Error parsing start_time: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid start time format: {start_time}")

        if end_time:
            try:
                # Convert to timezone-aware datetime
                booking_end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                # Convert to timezone-naive datetime for consistent comparison
                booking_end_time = booking_end_time.replace(tzinfo=None)
            except Exception as e:
                print(f"Error parsing end_time: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid end time format: {end_time}")

        # Check for conflicting bookings if times are provided
        if booking_start_time and booking_end_time:
            conflicting_bookings = db.query(Booking).filter(
                Booking.parking_slot_id == slot_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.start_time < booking_end_time,
                Booking.end_time > booking_start_time
            ).all()

            if conflicting_bookings:
                raise HTTPException(
                    status_code=400,
                    detail=f"Slot {slot.slot_number} is already booked during the requested time period"
                )

        # Get user (for demo purposes, create a user if not exists)
        user = db.query(User).filter(User.id == x_user_id).first()
        if not user:
            # Create a simple user for demo
            user = User(
                id=x_user_id,
                email=f"user{x_user_id}@example.com",
                hashed_password="demo_password",
                first_name="Demo",
                last_name="User",
                phone_number="1234567890",
                role=UserRole.USER
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create a vehicle for the user if needed (for demo)
        if license_plate:
            # Try to find vehicle with the provided license plate
            vehicle = db.query(Vehicle).filter(
                Vehicle.user_id == user.id,
                Vehicle.license_plate == license_plate
            ).first()

            # If not found, create a new vehicle with the provided license plate
            if not vehicle:
                vehicle = Vehicle(
                    user_id=user.id,
                    license_plate=license_plate,
                    make="User Provided",
                    model="Vehicle",
                    color="Not Specified",
                    vehicle_type=slot.vehicle_type
                )
                db.add(vehicle)
                db.commit()
                db.refresh(vehicle)
        else:
            # Try to find any vehicle of the right type
            vehicle = db.query(Vehicle).filter(
                Vehicle.user_id == user.id,
                Vehicle.vehicle_type == slot.vehicle_type
            ).first()

            # If not found, create a demo vehicle
            if not vehicle:
                # Create a simple vehicle for demo
                vehicle = Vehicle(
                    user_id=user.id,
                    license_plate=f"DEMO-{user.id}-{slot.vehicle_type.value}",
                    make="Demo",
                    model="Model",
                    color="Blue",
                    vehicle_type=slot.vehicle_type
                )
                db.add(vehicle)
                db.commit()
                db.refresh(vehicle)

        # Use provided times or default to current time + 2 hours
        if not booking_start_time:
            # Use current time
            booking_start_time = datetime.now()

            # Round to the nearest hour for better readability
            minutes = booking_start_time.minute
            if minutes < 30:
                # Round down to the hour
                booking_start_time = booking_start_time.replace(minute=0, second=0, microsecond=0)
            else:
                # Round up to the next hour
                booking_start_time = booking_start_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

            print(f"Using rounded current time: {booking_start_time}")
        else:
            # If the start time is in the past, use current time
            if booking_start_time < datetime.now():
                print(f"Start time {booking_start_time} is in the past, using current time")
                booking_start_time = datetime.now()

                # Round to the nearest hour
                minutes = booking_start_time.minute
                if minutes < 30:
                    booking_start_time = booking_start_time.replace(minute=0, second=0, microsecond=0)
                else:
                    booking_start_time = booking_start_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        if not booking_end_time:
            if duration:
                booking_end_time = booking_start_time + timedelta(hours=int(duration))
            else:
                booking_end_time = booking_start_time + timedelta(hours=2)  # Default 2-hour booking

        print(f"Final booking times: {booking_start_time} to {booking_end_time}")

        # Calculate duration in hours for pricing
        duration_seconds = (booking_end_time - booking_start_time).total_seconds()

        # Ensure duration is positive
        if duration_seconds <= 0:
            print(f"Warning: Negative or zero duration detected: {duration_seconds} seconds")
            print(f"Start time: {booking_start_time}, End time: {booking_end_time}")
            # Default to 2 hours if duration is negative or zero
            duration_seconds = 2 * 3600
            # Adjust end time to be after start time
            booking_end_time = booking_start_time + timedelta(seconds=duration_seconds)

        duration_hours = duration_seconds / 3600
        print(f"Duration hours: {duration_hours}")

        # Calculate total amount based on hourly rate
        total_amount = slot.hourly_rate * duration_hours

        booking = Booking(
            user_id=user.id,
            vehicle_id=vehicle.id,
            parking_slot_id=slot.id,
            start_time=booking_start_time,
            end_time=booking_end_time,
            status=BookingStatus.CONFIRMED,
            total_amount=total_amount
        )

        # We don't need to update slot.is_available anymore since we're using time-based availability
        # The slot is still available for other time periods

        db.add(booking)
        db.commit()
        db.refresh(booking)

        # Get mall for response
        mall = db.query(Mall).filter(Mall.id == slot.mall_id).first()

        # Calculate duration in hours
        duration_hours = (booking.end_time - booking.start_time).total_seconds() / 3600

        return {
            "id": booking.id,
            "mall_name": mall.name if mall else "Unknown Mall",
            "slot_number": slot.slot_number,
            "vehicle_type": slot.vehicle_type.value,
            "vehicle_number": vehicle.license_plate,
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "total_amount": booking.total_amount,
            "status": booking.status.value,
            "floor": slot.floor,
            "section": slot.section,
            "duration_hours": round(duration_hours, 2),
            "created_at": booking.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in create_booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Bookings endpoint
@app.get("/bookings", response_model=List[BookingResponse])
def get_bookings(user_id: str, include_cancelled: bool = False, db: Session = Depends(get_db)):
    """Get all bookings for a user, with option to exclude cancelled bookings"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # For demo purposes, we'll return mock bookings if user doesn't exist
            return []

        # Get bookings for user, optionally filtering out cancelled bookings
        query = db.query(Booking).filter(Booking.user_id == user_id)
        if not include_cancelled:
            query = query.filter(Booking.status != BookingStatus.CANCELLED)

        bookings = query.all()

        # Format bookings for response
        result = []
        for booking in bookings:
            # Get parking slot
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == booking.parking_slot_id).first()
            if not slot:
                continue

            # Get mall
            mall = db.query(Mall).filter(Mall.id == slot.mall_id).first()
            if not mall:
                continue

            # Get vehicle
            vehicle = db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()
            if not vehicle:
                continue

            # Calculate duration in hours
            duration_hours = (booking.end_time - booking.start_time).total_seconds() / 3600 if booking.end_time else 0

            result.append({
                "id": booking.id,
                "mall_name": mall.name,
                "slot_number": slot.slot_number,
                "vehicle_type": vehicle.vehicle_type.value,
                "vehicle_number": vehicle.license_plate,
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat() if booking.end_time else None,
                "total_amount": booking.total_amount if booking.total_amount is not None else 0.0,
                "status": booking.status.value,
                "floor": slot.floor,
                "section": slot.section,
                "duration_hours": round(duration_hours, 2),
                "created_at": booking.created_at.isoformat()
            })

        return result
    except Exception as e:
        print(f"Error in get_bookings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Cancel booking endpoint
@app.post("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    x_user_id: str = Header(..., description="User ID for booking"),
    db: Session = Depends(get_db)
):
    """Cancel a booking"""
    try:
        # Check if booking exists
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

        # Check if user owns the booking
        if str(booking.user_id) != x_user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to cancel this booking")

        # Check if booking can be cancelled
        if booking.status == BookingStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Completed bookings cannot be cancelled")

        # We don't need to update slot availability anymore since we're using time-based availability
        # Just delete the booking and the slot will be available for that time period

        # Delete the booking directly instead of just marking it as cancelled
        db.delete(booking)
        db.commit()

        return {
            "id": booking_id,
            "message": "Booking cancelled and deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in cancel_booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Delete booking endpoint
@app.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: int,
    x_user_id: str = Header(..., description="User ID for booking"),
    db: Session = Depends(get_db)
):
    """Delete a booking (only allowed for cancelled bookings)"""
    try:
        # Check if booking exists
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

        # Check if user owns the booking
        if str(booking.user_id) != x_user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this booking")

        # Allow deletion of any booking (not just cancelled ones)
        # Make the parking slot available if the booking is active
        if booking.status == BookingStatus.CONFIRMED:
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == booking.parking_slot_id).first()
            if slot:
                slot.is_available = True
                slot.updated_at = datetime.now()

        # Delete the booking
        db.delete(booking)
        db.commit()

        return {
            "id": booking_id,
            "message": "Booking deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in delete_booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get parking rates endpoint
@app.get("/parking-rates")
def get_parking_rates(mall_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get parking rates for all vehicle types, optionally filtered by mall"""
    try:
        # Base query for parking slots
        query = db.query(ParkingSlot)

        # Apply mall filter if provided
        if mall_id:
            query = query.filter(ParkingSlot.mall_id == mall_id)

            # Check if mall exists
            mall = db.query(Mall).filter(Mall.id == mall_id).first()
            if not mall:
                raise HTTPException(status_code=404, detail=f"Mall with ID {mall_id} not found")

        # Get all slots
        slots = query.all()

        # Group rates by mall and vehicle type
        rates_by_mall = {}

        for slot in slots:
            mall = db.query(Mall).filter(Mall.id == slot.mall_id).first()
            if not mall:
                continue

            mall_name = mall.name
            vehicle_type = slot.vehicle_type.value
            hourly_rate = slot.hourly_rate

            if mall_name not in rates_by_mall:
                rates_by_mall[mall_name] = {
                    "mall_id": mall.id,
                    "mall_name": mall_name,
                    "rates": {}
                }

            if vehicle_type not in rates_by_mall[mall_name]["rates"]:
                rates_by_mall[mall_name]["rates"][vehicle_type] = hourly_rate

        # Convert to list for response
        result = list(rates_by_mall.values())

        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_parking_rates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
