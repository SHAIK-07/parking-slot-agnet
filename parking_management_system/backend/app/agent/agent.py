from typing import List, Dict, Any, Optional
import os
import json
import uuid
import requests
from datetime import datetime
from sqlalchemy.orm import Session

from ..memory.chat_manager import ChatMemoryManager
from ..memory.vector_store import VectorChatHistory
from ..memory.file_chat_history import FileChatHistory
from ..memory.in_memory_store import InMemoryStore

class ParkingAgent:
    def __init__(self, db: Session, user_id: str, model_name: str = "llama-3.3-70b-versatile", use_vector_store: bool = False):
        self.db = db
        self.user_id = user_id
        self.user_name = None  # Will be set from the header if available
        self.model_name = model_name
        self.api_key = os.getenv("GROQ_API_KEY")
        self.use_vector_store = use_vector_store

        # Initialize in-memory store
        self.store = InMemoryStore()

        # Get pending booking from store
        self.pending_booking = self.store.get_pending_booking(user_id)
        print(f"Retrieved pending booking from store: {self.pending_booking}")

        # Get conversation context from store
        self.conversation_context = self.store.get_conversation_context(user_id)
        print(f"Retrieved conversation context from store: {self.conversation_context}")

        # Initialize memory managers
        self.memory_manager = ChatMemoryManager(user_id=user_id)

        # Initialize chat history
        if use_vector_store:
            try:
                self.vector_store = VectorChatHistory(user_id=user_id)
                # Create a default conversation ID if not provided
                self.conversation_id = str(uuid.uuid4())
            except Exception as e:
                print(f"Error initializing vector store: {str(e)}")
                self.use_vector_store = False
                # Fall back to file-based chat history
                self.file_chat = FileChatHistory(user_id=user_id)
                self.conversation_id = str(uuid.uuid4())
        else:
            # Use file-based chat history
            self.file_chat = FileChatHistory(user_id=user_id)
            self.conversation_id = str(uuid.uuid4())

    def _call_groq_api(self, messages):
        """Call the Groq API directly."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1000
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error calling Groq API: {response.status_code} - {response.text}"

    def _handle_booking_command(self, query):
        """Handle a booking command from the user."""
        try:
            # Extract slot ID from query
            slot_id_str = query.lower().replace("book slot ", "").strip()
            slot_id = int(slot_id_str)
            print(f"Handling booking command for slot ID: {slot_id}")

            # Check if slot exists and is available
            from ..database.models import ParkingSlot
            slot = self.db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()

            if not slot:
                print(f"Slot {slot_id} not found")
                return f"Sorry, I couldn't find a parking slot with ID {slot_id}. Please check the ID and try again."

            if not slot.is_available:
                print(f"Slot {slot_id} is not available")
                return f"Sorry, parking slot {slot_id} is not available. Please choose another slot."

            # Get mall information
            from ..database.models import Mall
            mall = self.db.query(Mall).filter(Mall.id == slot.mall_id).first()
            print(f"Found mall for slot {slot_id}: {mall.name if mall else 'Unknown Mall'}")

            # Update conversation context with mall and vehicle type
            self.conversation_context["selected_mall"] = mall.name
            self.conversation_context["selected_mall_id"] = mall.id
            self.conversation_context["selected_vehicle_type"] = slot.vehicle_type.value

            # Store pending booking information
            self.pending_booking = {
                "slot_id": slot_id,
                "user_id": self.user_id,
                "vehicle_type": slot.vehicle_type.value,
                "mall_name": mall.name if mall else "Unknown Mall",
                "slot_number": slot.slot_number,
                "hourly_rate": slot.hourly_rate,
                "license_plate": self.conversation_context["selected_license_plate"],
                "time_period": self.conversation_context["selected_time_period"]
            }

            # Save to in-memory store
            self.store.set_pending_booking(self.user_id, self.pending_booking)
            self.store.set_conversation_context(self.user_id, self.conversation_context)

            print(f"Created pending booking: {self.pending_booking}")
            print(f"Updated conversation context: {self.conversation_context}")
            print(f"Saved to in-memory store for user {self.user_id}")

            # Check if we have all required information
            missing_info = []

            # Check for license plate
            if not self.conversation_context["selected_license_plate"]:
                missing_info.append("license plate number")

            # Check for time period
            if not self.conversation_context["selected_time_period"]:
                missing_info.append("booking time")

            # If information is missing, ask for it
            if missing_info:
                missing_info_str = " and ".join(missing_info)

                # Store the slot ID for later use
                self.conversation_context["pending_slot_id"] = slot_id
                self.store.set_conversation_context(self.user_id, self.conversation_context)

                return f"""
I've found slot {slot_id} at {self.pending_booking['mall_name']}.

Slot Details:
* Mall: {self.pending_booking['mall_name']}
* Slot ID: {slot_id}
* Type: {self.pending_booking['vehicle_type']}
* Number: {self.pending_booking['slot_number']}
* Rate: ₹{self.pending_booking['hourly_rate']}/hour

Before I can complete your booking, I need your {missing_info_str}.

{'' if 'license plate number' not in missing_info else 'Please provide your vehicle license plate number (e.g., KA01AB1234).'}
{'' if 'booking time' not in missing_info else 'Please specify when you want to park (e.g., "tomorrow at 5 pm", "today at 3 pm").'}
"""

            # If we have all information, proceed with confirmation
            license_plate_info = f"* License Plate: {self.pending_booking['license_plate']}" if self.pending_booking['license_plate'] else "* License Plate: Not provided (a demo plate will be used)"
            time_info = f"* Time: {self.conversation_context['selected_time_period']}" if self.conversation_context['selected_time_period'] else "* Time: Current time (default)"

            return f"""
I've found slot {slot_id} at {self.pending_booking['mall_name']}.

Slot Details:
* Mall: {self.pending_booking['mall_name']}
* Slot ID: {slot_id}
* Type: {self.pending_booking['vehicle_type']}
* Number: {self.pending_booking['slot_number']}
* Rate: ₹{self.pending_booking['hourly_rate']}/hour
{license_plate_info}
{time_info}

Please confirm if you want to proceed with booking.
If yes, I will book the slot for User ID: {self.user_id}.
If no, please let me know and I will cancel the booking request.

Please respond with "Yes" or "No".
"""
        except ValueError:
            return "Sorry, I couldn't understand the slot ID. Please use the format 'Book slot X' where X is the slot ID number."
        except Exception as e:
            print(f"Error in _handle_booking_command: {str(e)}")
            return f"Sorry, there was an error processing your booking request: {str(e)}"

    def _handle_booking_confirmation(self):
        """Handle a booking confirmation from the user."""
        try:
            # Check if there's a pending booking
            if not self.pending_booking:
                print("No pending booking found in _handle_booking_confirmation")
                return "I don't have any pending booking requests. Please start a new booking by selecting an available slot."

            # Create booking in the database
            try:
                # Make API request to create booking
                # Use full URL with localhost since this is a server-side request
                booking_url = "http://localhost:8000/bookings"
                headers = {
                    "Content-Type": "application/json",
                    "X-User-ID": str(self.user_id)
                }
                params = {
                    "slot_id": self.pending_booking["slot_id"]
                }

                # Add license plate if available
                if self.conversation_context["selected_license_plate"]:
                    params["license_plate"] = self.conversation_context["selected_license_plate"]
                    print(f"Adding license plate to booking: {self.conversation_context['selected_license_plate']}")

                # Add time information if available
                if self.conversation_context["selected_time_period"]:
                    # Parse the time period to create a proper datetime
                    import re
                    import datetime

                    time_period = self.conversation_context["selected_time_period"]
                    print(f"Processing time period: {time_period}")

                    # Get current date
                    now = datetime.datetime.now()

                    # Default values
                    booking_date = now.date()
                    booking_hour = 17  # Default to 5 PM
                    booking_minute = 0
                    duration_hours = 2  # Default duration

                    # Check for "tomorrow"
                    if "tomorrow" in time_period.lower():
                        booking_date = (now + datetime.timedelta(days=1)).date()
                        print(f"Setting date to tomorrow: {booking_date}")

                    # Extract time (e.g., "5 pm", "3:30 pm")
                    time_match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm)', time_period.lower())
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2)) if time_match.group(2) else 0
                        am_pm = time_match.group(3)

                        # Convert to 24-hour format
                        if am_pm == "pm" and hour < 12:
                            hour += 12
                        elif am_pm == "am" and hour == 12:
                            hour = 0

                        booking_hour = hour
                        booking_minute = minute
                        print(f"Extracted time: {hour}:{minute} {am_pm}")

                    # Extract duration (e.g., "2 hours", "3 hrs")
                    duration_match = re.search(r'(\d+)\s*(?:hour|hr|hrs?)', time_period.lower())
                    if duration_match:
                        duration_hours = int(duration_match.group(1))
                        print(f"Extracted duration: {duration_hours} hours")

                    # Create datetime object
                    booking_datetime = datetime.datetime(
                        booking_date.year, booking_date.month, booking_date.day,
                        booking_hour, booking_minute
                    )

                    # Calculate end time
                    end_datetime = booking_datetime + datetime.timedelta(hours=duration_hours)

                    # Format for API
                    start_time = booking_datetime.isoformat()
                    end_time = end_datetime.isoformat()
                    params["start_time"] = start_time
                    params["end_time"] = end_time
                    params["duration"] = duration_hours

                    print(f"Adding start_time: {start_time}, end_time: {end_time}, duration: {duration_hours}")

                    # Check for conflicting bookings
                    from ..database.models import Booking, BookingStatus
                    conflicting_bookings = self.db.query(Booking).filter(
                        Booking.parking_slot_id == self.pending_booking["slot_id"],
                        Booking.status == BookingStatus.CONFIRMED,
                        Booking.start_time < end_datetime,
                        Booking.end_time > booking_datetime
                    ).all()

                    if conflicting_bookings:
                        return f"""
Sorry, this slot is already booked for the requested time period.
Please try a different time or check for other available slots.
"""

                print(f"Sending booking request to {booking_url} with params: {params}")

                print(f"Creating booking with slot_id: {self.pending_booking['slot_id']}")
                response = requests.post(booking_url, headers=headers, params=params)

                if response.status_code == 200:
                    booking_data = response.json()
                    print(f"Booking created successfully: {booking_data}")

                    # Store booking details for reference
                    booking_details = {
                        "mall_name": booking_data.get('mall_name', self.pending_booking['mall_name']),
                        "slot_number": booking_data.get('slot_number', self.pending_booking['slot_number']),
                        "vehicle_type": booking_data.get('vehicle_type', self.pending_booking['vehicle_type']),
                        "total_amount": booking_data.get('total_amount', self.pending_booking['hourly_rate'] * 2),
                        "status": booking_data.get('status', 'confirmed')
                    }

                    # Clear pending booking
                    self.pending_booking = None
                    self.store.clear_pending_booking(self.user_id)
                    print(f"Cleared pending booking for user {self.user_id} from store")

                    # Return success message with popup formatting
                    return f"""
Great! Your booking has been confirmed.

Booking Details:
* Mall: {booking_details['mall_name']}
* Slot: {booking_details['slot_number']}
* Vehicle Type: {booking_details['vehicle_type']}
* Start Time: {booking_data.get('start_time', 'Not specified')}
* End Time: {booking_data.get('end_time', 'Not specified')}
* Amount: ₹{booking_details['total_amount']}
* Status: {booking_details['status']}

Your booking has been added to the Bookings tab. You can view all your bookings there.
Thank you for using our parking service!
"""
                else:
                    error_message = f"Error creating booking: {response.status_code} - {response.text}"
                    print(error_message)
                    return f"Sorry, there was an error creating your booking. Please try again later. Error: {error_message}"

            except Exception as api_error:
                print(f"API error in _handle_booking_confirmation: {str(api_error)}")
                return f"Sorry, there was an error communicating with the booking service: {str(api_error)}"

        except Exception as e:
            print(f"Error in _handle_booking_confirmation: {str(e)}")
            return f"Sorry, there was an error processing your booking confirmation: {str(e)}"

    def get_parking_rates(self, mall_id=None):
        """Tool to get parking rates from the database."""
        try:
            # If mall_id is not provided but we have one in context, use that
            if mall_id is None and self.conversation_context["selected_mall_id"]:
                mall_id = self.conversation_context["selected_mall_id"]

            # Query the database for rates
            from ..database.models import ParkingSlot, Mall, VehicleType

            # Base query
            query = self.db.query(ParkingSlot)

            # Apply mall filter if provided
            if mall_id:
                query = query.filter(ParkingSlot.mall_id == mall_id)

            # Get all slots
            slots = query.all()

            # Group rates by mall and vehicle type
            rates_by_mall = {}

            for slot in slots:
                mall = self.db.query(Mall).filter(Mall.id == slot.mall_id).first()
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

            return {
                "success": True,
                "rates": result,
                "message": f"Found rates for {len(result)} malls."
            }

        except Exception as e:
            print(f"Error in get_parking_rates: {str(e)}")
            return {
                "success": False,
                "rates": [],
                "message": f"Error retrieving parking rates: {str(e)}"
            }

    def get_available_slots(self, mall_id=None, vehicle_type=None, start_time=None, end_time=None):
        """Tool to get available parking slots from the database."""
        try:
            # If parameters are not provided but we have them in context, use those
            if mall_id is None and self.conversation_context["selected_mall_id"]:
                mall_id = self.conversation_context["selected_mall_id"]

            if vehicle_type is None and self.conversation_context["selected_vehicle_type"]:
                vehicle_type = self.conversation_context["selected_vehicle_type"]

            # Query the database for available slots
            from ..database.models import ParkingSlot, Mall, VehicleType, Booking, BookingStatus
            from datetime import datetime, timedelta

            # Base query
            query = self.db.query(ParkingSlot)

            # Apply filters
            if mall_id:
                query = query.filter(ParkingSlot.mall_id == mall_id)

            if vehicle_type:
                # Convert string to enum
                vehicle_type_enum = None
                if vehicle_type.lower() == "car":
                    vehicle_type_enum = VehicleType.CAR
                elif vehicle_type.lower() == "bike":
                    vehicle_type_enum = VehicleType.BIKE
                elif vehicle_type.lower() == "truck":
                    vehicle_type_enum = VehicleType.TRUCK

                if vehicle_type_enum:
                    query = query.filter(ParkingSlot.vehicle_type == vehicle_type_enum)

            # Get all slots matching the filters, regardless of is_available flag
            # We'll check for time-based availability instead
            slots = query.all()

            # Prepare to filter slots based on time
            # Parse times if they're strings
            if start_time and end_time:
                if isinstance(start_time, str):
                    # Convert to timezone-aware datetime
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    # Convert to timezone-naive datetime for consistent comparison
                    start_time = start_time.replace(tzinfo=None)
                if isinstance(end_time, str):
                    # Convert to timezone-aware datetime
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    # Convert to timezone-naive datetime for consistent comparison
                    end_time = end_time.replace(tzinfo=None)
            else:
                # If no time period is specified, use current time + 2 hours as default
                start_time = datetime.now()
                end_time = start_time + timedelta(hours=2)
                print(f"Using default time period: {start_time} to {end_time}")

            # For each slot, check if there are conflicting bookings
            filtered_slots = []
            for slot in slots:
                # Check for conflicting bookings
                conflicting_bookings = self.db.query(Booking).filter(
                    Booking.parking_slot_id == slot.id,
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.start_time < end_time,
                    Booking.end_time > start_time
                ).all()

                # Only include slots without conflicts
                if not conflicting_bookings:
                    filtered_slots.append(slot)

            slots = filtered_slots

            # Format slots for display
            formatted_slots = []
            for slot in slots:
                mall = self.db.query(Mall).filter(Mall.id == slot.mall_id).first()

                formatted_slots.append({
                    "id": slot.id,
                    "mall_id": slot.mall_id,
                    "mall_name": mall.name if mall else "Unknown Mall",
                    "slot_number": slot.slot_number,
                    "vehicle_type": slot.vehicle_type.value,
                    "hourly_rate": slot.hourly_rate,
                    "floor": slot.floor,
                    "section": slot.section
                })

            return {
                "success": True,
                "count": len(formatted_slots),
                "slots": formatted_slots,
                "message": f"Found {len(formatted_slots)} available slots."
            }

        except Exception as e:
            print(f"Error in get_available_slots: {str(e)}")
            return {
                "success": False,
                "count": 0,
                "slots": [],
                "message": f"Error retrieving available slots: {str(e)}"
            }

    def _format_parking_rates(self):
        """Format parking rates for display in the system message."""
        if not self.conversation_context.get("parking_rates"):
            return "No parking rates available for the selected mall."

        rates = self.conversation_context["parking_rates"]
        formatted_rates = []

        for vehicle_type, rate in rates.items():
            formatted_rates.append(f"* {vehicle_type.capitalize()}: ₹{rate}/hour")

        return "\n".join(formatted_rates) if formatted_rates else "No parking rates available."

    def get_user_bookings(self):
        """Tool to get the user's bookings directly from the database."""
        try:
            # Query the database directly
            from ..database.models import Booking, ParkingSlot, Mall, Vehicle

            # Get only confirmed bookings for this user
            from ..database.models import BookingStatus
            bookings = self.db.query(Booking).filter(
                Booking.user_id == self.user_id,
                Booking.status == BookingStatus.CONFIRMED
            ).all()
            print(f"Found {len(bookings)} confirmed bookings for user {self.user_id} directly from database")

            if not bookings:
                return {
                    "success": True,
                    "count": 0,
                    "bookings": [],
                    "message": "No bookings found for this user."
                }

            # Format bookings for display
            formatted_bookings = []
            for booking in bookings:
                # Get related data
                slot = self.db.query(ParkingSlot).filter(ParkingSlot.id == booking.parking_slot_id).first()
                mall = self.db.query(Mall).filter(Mall.id == slot.mall_id).first() if slot else None
                vehicle = self.db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()

                # Format dates
                start_time = booking.start_time.strftime('%d/%m/%Y, %I:%M %p') if booking.start_time else "Not specified"
                end_time = booking.end_time.strftime('%d/%m/%Y, %I:%M %p') if booking.end_time else "Not specified"

                formatted_bookings.append({
                    "id": booking.id,
                    "mall_name": mall.name if mall else "Unknown Mall",
                    "slot_number": slot.slot_number if slot else "Unknown",
                    "vehicle_type": vehicle.vehicle_type.value if vehicle else "Unknown",
                    "vehicle_number": vehicle.license_plate if vehicle else "No plate",
                    "start_time": start_time,
                    "end_time": end_time,
                    "total_amount": booking.total_amount,
                    "status": booking.status.value
                })

            return {
                "success": True,
                "count": len(formatted_bookings),
                "bookings": formatted_bookings,
                "message": f"Found {len(formatted_bookings)} bookings."
            }

        except Exception as e:
            print(f"Error in get_user_bookings: {str(e)}")
            return {
                "success": False,
                "count": 0,
                "bookings": [],
                "message": f"Error retrieving bookings: {str(e)}"
            }

    def _check_parking_rates(self):
        """Check parking rates and format them for display."""
        try:
            # Get mall ID from context if available
            mall_id = self.conversation_context["selected_mall_id"]
            mall_name = self.conversation_context["selected_mall"]

            # Use the tool to get rates
            result = self.get_parking_rates(mall_id)

            if not result["success"]:
                return f"Sorry, there was an error checking parking rates: {result['message']}"

            if not result["rates"]:
                return """
Sorry, I couldn't find any parking rates.
Please specify which mall you're interested in.

Available malls:
* Orion Mall
* Phoenix Mall
* UB City Mall
* Forum Mall
* Mantri Square Mall
"""

            # Format rates for display
            rates_text = ""
            for mall_data in result["rates"]:
                mall_name = mall_data["mall_name"]
                rates = mall_data["rates"]

                rates_text += f"\nRates at {mall_name}:\n"
                for vehicle_type, rate in rates.items():
                    rates_text += f"* {vehicle_type.capitalize()}: ₹{rate}/hour\n"

            return f"""
Here are the current parking rates:
{rates_text}
Would you like to:
* Book a parking slot
* Check available slots
* View your bookings
"""

        except Exception as e:
            print(f"Error in _check_parking_rates: {str(e)}")
            return f"Sorry, there was an error checking parking rates: {str(e)}"

    def _check_available_slots(self):
        """Check available slots and format them for display."""
        try:
            # Get parameters from context if available
            mall_id = self.conversation_context["selected_mall_id"]
            vehicle_type = self.conversation_context["selected_vehicle_type"]

            # Check if we have enough information
            if not mall_id:
                return """
Please specify which mall you're interested in.

Available malls:
* Orion Mall
* Phoenix Mall
* UB City Mall
* Forum Mall
* Mantri Square Mall
"""

            if not vehicle_type:
                return """
Please specify what type of vehicle you have.

Available vehicle types:
* Car
* Bike
* Truck
"""

            # Use the tool to get available slots
            result = self.get_available_slots(mall_id, vehicle_type)

            if not result["success"]:
                return f"Sorry, there was an error checking available slots: {result['message']}"

            if result["count"] == 0:
                return f"""
Sorry, there are no available {vehicle_type} slots at {self.conversation_context['selected_mall']}.

Would you like to:
* Check another mall
* Check another vehicle type
* Check parking rates
"""

            # Format slots for display
            slots_text = ""
            for i, slot in enumerate(result["slots"][:10]):  # Limit to 10 slots
                slots_text += f"""
* Slot ID: {slot['id']}
  Mall: {slot['mall_name']}
  Number: {slot['slot_number']}
  Floor: {slot['floor']}, Section: {slot['section']}
  Vehicle Type: {slot['vehicle_type']}
  Rate: ₹{slot['hourly_rate']}/hour
"""

            if len(result["slots"]) > 10:
                slots_text += f"\n... and {len(result['slots']) - 10} more slots available."

            return f"""
Here are the available {vehicle_type} slots at {self.conversation_context['selected_mall']}:
{slots_text}

To book a slot, type "Book slot [ID]" (e.g., "Book slot 5").
"""

        except Exception as e:
            print(f"Error in _check_available_slots: {str(e)}")
            return f"Sorry, there was an error checking available slots: {str(e)}"

    def _check_user_bookings(self):
        """Check the user's bookings and format them for display."""
        try:
            # Use the tool to get bookings
            result = self.get_user_bookings()

            if not result["success"]:
                return f"Sorry, there was an error checking your bookings: {result['message']}"

            if result["count"] == 0:
                return """
You have no active bookings in the system.
Would you like to:
* Create a new booking
* Check parking rates
* Find available parking slots
* Other (please specify)

Note: Cancelled bookings are automatically deleted from the system.
"""

            # Format bookings for display
            bookings_text = ""
            for booking in result["bookings"]:
                bookings_text += f"""
Booking ID: {booking['id']}
* Mall: {booking['mall_name']}
* Slot: {booking['slot_number']}
* Vehicle: {booking['vehicle_type']} ({booking['vehicle_number']})
* From: {booking['start_time']}
* To: {booking['end_time']}
* Amount: ₹{booking['total_amount']}
* Status: {booking['status']}

"""

            return f"""
Here are your current active bookings:

{bookings_text}
To cancel a booking, type "Cancel booking [ID]" where ID is the actual Booking ID number shown above.
For example: "Cancel booking 12" to cancel the booking with ID 12.

Note: Cancelled bookings are automatically deleted from the system.
"""

        except Exception as e:
            print(f"Error in _check_user_bookings: {str(e)}")
            return f"Sorry, there was an error checking your bookings: {str(e)}"

    def _handle_booking_cancellation(self, query):
        """Handle a booking cancellation command from the user."""
        try:
            # Extract booking ID from query
            booking_id_str = query.lower().replace("cancel booking ", "").strip()
            booking_id = int(booking_id_str)

            # First, check if the booking exists and belongs to the user
            from ..database.models import Booking
            booking = self.db.query(Booking).filter(
                Booking.id == booking_id,
                Booking.user_id == self.user_id
            ).first()

            if not booking:
                return f"""
Booking #{booking_id} was not found or doesn't belong to you.

Please check your bookings again with "show my bookings" to see your current active bookings.
"""

            # Delete the booking directly from the database
            try:
                # We don't need to update the slot since we're using time-based availability
                # The slot will be available for other time periods automatically

                # Delete the booking
                self.db.delete(booking)
                self.db.commit()

                print(f"Successfully deleted booking {booking_id}")

                # Return success message with a special tag that the frontend can detect to refresh bookings
                return f"""
Booking #{booking_id} has been successfully cancelled and deleted.

The parking slot is now available for others to book.
<refresh-bookings></refresh-bookings>

Please check the Bookings tab to see your updated bookings.
"""
            except Exception as db_error:
                self.db.rollback()
                print(f"Database error cancelling booking: {str(db_error)}")
                return f"""
Sorry, there was an error cancelling your booking: {str(db_error)}

Please try again later or contact customer support if the problem persists.
"""

        except ValueError:
            return "Sorry, I couldn't understand the booking ID. Please use the format 'Cancel booking X' where X is the booking ID number."
        except Exception as e:
            print(f"Error in _handle_booking_cancellation: {str(e)}")
            return f"Sorry, there was an error processing your cancellation request: {str(e)}"

    def _update_conversation_context(self, query: str):
        """Update the conversation context based on the user's query."""
        query_lower = query.lower()

        # Get the latest context from the store
        stored_context = self.store.get_conversation_context(self.user_id)
        if stored_context:
            self.conversation_context = stored_context
            print(f"Retrieved updated context from store: {self.conversation_context}")

        # Check for mall mentions
        from ..database.models import Mall
        malls = self.db.query(Mall).all()

        # First check for mall IDs (e.g., "mall 1" or "mall ID 1")
        if "mall" in query_lower and any(char.isdigit() for char in query_lower):
            # Extract digits from the query
            import re
            mall_id_matches = re.findall(r'mall\s+(?:id\s+)?(\d+)', query_lower)
            if mall_id_matches:
                try:
                    mall_id = int(mall_id_matches[0])
                    mall = self.db.query(Mall).filter(Mall.id == mall_id).first()
                    if mall:
                        self.conversation_context["selected_mall"] = mall.name
                        self.conversation_context["selected_mall_id"] = mall.id
                        print(f"Detected mall by ID: {mall.name} (ID: {mall.id})")
                except (ValueError, IndexError):
                    pass

        # If no mall ID was found, check for mall names
        mall_found = False
        for mall in malls:
            mall_name_lower = mall.name.lower()
            if mall_name_lower in query_lower:
                self.conversation_context["selected_mall"] = mall.name
                self.conversation_context["selected_mall_id"] = mall.id
                print(f"Detected mall by name: {mall.name}")
                mall_found = True
                break

        # Check for specific mall names that might not be in the database
        if not mall_found:
            mall_keywords = {
                "phoenix": "Phoenix Mall",
                "palladium": "Palladium Mall",
                "orion": "Orion Mall",
                "forum": "Forum Mall",
                "market city": "Phoenix Market City",
                "mall of asia": "Phoenix Mall of Asia"
            }

            for keyword, _ in mall_keywords.items():
                if keyword in query_lower and not self.conversation_context["selected_mall"]:
                    # Find the closest matching mall in the database
                    closest_mall = None
                    for mall in malls:
                        if keyword in mall.name.lower():
                            closest_mall = mall
                            break

                    if closest_mall:
                        self.conversation_context["selected_mall"] = closest_mall.name
                        self.conversation_context["selected_mall_id"] = closest_mall.id
                        print(f"Detected mall by keyword '{keyword}': {closest_mall.name}")
                    break

        # Check for vehicle type mentions
        vehicle_types = ["car", "truck", "bike"]
        for vehicle_type in vehicle_types:
            if vehicle_type in query_lower:
                self.conversation_context["selected_vehicle_type"] = vehicle_type
                print(f"Detected vehicle type: {vehicle_type}")
                break

        # Check for time period mentions
        time_patterns = [
            "today", "tomorrow", "next week",
            "morning", "afternoon", "evening", "night",
            "am", "pm", "hours", "hour", "hr", "hrs"
        ]
        for pattern in time_patterns:
            if pattern in query_lower:
                # Extract the full time-related phrase
                words = query_lower.split()
                for i, word in enumerate(words):
                    if pattern in word and i > 0:
                        # Try to capture phrases like "3 pm" or "2 hours"
                        time_phrase = f"{words[i-1]} {word}"
                        self.conversation_context["selected_time_period"] = time_phrase
                        print(f"Detected time period: {time_phrase}")
                        break

        # Detect license plate (common formats like KA01AB1234, MH02CD5678)
        import re
        license_plate_pattern = r'\b[A-Z]{2}\d{2}[A-Z]{1,2}\d{1,4}\b'
        license_plate_matches = re.findall(license_plate_pattern, query)
        if license_plate_matches and not self.conversation_context["selected_license_plate"]:
            self.conversation_context["selected_license_plate"] = license_plate_matches[0]
            print(f"Detected license plate: {license_plate_matches[0]}")

        # Track query type and intent
        if "available" in query_lower or "find" in query_lower or "looking for" in query_lower or "show slots" in query_lower:
            self.conversation_context["last_query_type"] = "availability"
            self.conversation_context["intent"] = "check_available_slots"
        elif "book" in query_lower or "reserve" in query_lower:
            self.conversation_context["last_query_type"] = "booking"
            self.conversation_context["intent"] = "create_booking"
        elif "cancel" in query_lower:
            self.conversation_context["last_query_type"] = "cancellation"
            self.conversation_context["intent"] = "cancel_booking"
        elif "rate" in query_lower or "price" in query_lower or "cost" in query_lower or "fee" in query_lower or "charge" in query_lower:
            self.conversation_context["last_query_type"] = "pricing"
            self.conversation_context["intent"] = "check_parking_rates"

            # If this is a pricing query, fetch the rates using our tool
            if self.conversation_context["selected_mall_id"]:
                try:
                    # Get rates for the selected mall
                    rates_result = self.get_parking_rates(self.conversation_context["selected_mall_id"])
                    if rates_result["success"] and rates_result["rates"]:
                        for mall_data in rates_result["rates"]:
                            if mall_data["mall_id"] == self.conversation_context["selected_mall_id"]:
                                self.conversation_context["parking_rates"] = mall_data["rates"]
                                print(f"Fetched parking rates for mall ID {self.conversation_context['selected_mall_id']}: {self.conversation_context['parking_rates']}")
                                break
                except Exception as e:
                    print(f"Error fetching parking rates: {str(e)}")
        elif "my booking" in query_lower or "view booking" in query_lower or "show booking" in query_lower or "show my booking" in query_lower or "check booking" in query_lower or "check my booking" in query_lower or "show bookings" in query_lower:
            self.conversation_context["last_query_type"] = "view_bookings"
            self.conversation_context["intent"] = "check_user_bookings"

        # Check if we have a pending slot ID and the user is providing missing information
        if self.conversation_context.get("pending_slot_id"):
            # If the user has provided license plate or time information, check if we can proceed with booking
            if self.conversation_context["selected_license_plate"] and self.conversation_context["selected_time_period"]:
                print(f"User has provided all required information for pending slot {self.conversation_context['pending_slot_id']}")
                self.conversation_context["intent"] = "create_booking"

        # Save updated context to store
        self.store.set_conversation_context(self.user_id, self.conversation_context)
        print(f"Saved updated context to store: {self.conversation_context}")

    def _create_booking_from_context(self):
        """Create a booking based on the conversation context."""
        try:
            # Check if we have the necessary information
            if not self.conversation_context["selected_mall_id"] or not self.conversation_context["selected_vehicle_type"]:
                return "I need to know which mall and vehicle type you're interested in before I can create a booking."

            # Check if we have license plate and time information
            if not self.conversation_context["selected_license_plate"]:
                return "Please provide your vehicle license plate number (e.g., KA01AB1234)."

            if not self.conversation_context["selected_time_period"]:
                return "Please specify when you want to park (e.g., 'tomorrow at 5 pm', 'today at 3 pm')."

            # Parse the time period to create proper datetime objects
            from datetime import datetime, timedelta
            import re

            # Get current date
            now = datetime.now()

            # Default values
            booking_date = now.date()
            booking_hour = 17  # Default to 5 PM
            booking_minute = 0
            duration_hours = 2  # Default duration

            # Parse the time period
            time_period = self.conversation_context["selected_time_period"]
            print(f"Processing time period: {time_period}")

            # Check for "tomorrow"
            if "tomorrow" in time_period.lower():
                booking_date = (now + timedelta(days=1)).date()
                print(f"Setting date to tomorrow: {booking_date}")

            # Extract time (e.g., "5 pm", "3:30 pm")
            time_match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm)', time_period.lower())
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                am_pm = time_match.group(3)

                # Convert to 24-hour format
                if am_pm == "pm" and hour < 12:
                    hour += 12
                elif am_pm == "am" and hour == 12:
                    hour = 0

                booking_hour = hour
                booking_minute = minute
                print(f"Extracted time: {hour}:{minute} {am_pm}")

            # Extract duration (e.g., "2 hours", "3 hrs")
            duration_match = re.search(r'(\d+)\s*(?:hour|hr|hrs?)', time_period.lower())
            if duration_match:
                duration_hours = int(duration_match.group(1))
                print(f"Extracted duration: {duration_hours} hours")

            # Create datetime objects
            start_time = datetime(
                booking_date.year, booking_date.month, booking_date.day,
                booking_hour, booking_minute
            )
            end_time = start_time + timedelta(hours=duration_hours)

            print(f"Calculated booking time: {start_time} to {end_time}")

            # Check if we have a pending slot ID
            slot = None
            if self.conversation_context.get("pending_slot_id"):
                # Get the slot by ID
                from ..database.models import ParkingSlot, Booking, BookingStatus
                slot = self.db.query(ParkingSlot).filter(
                    ParkingSlot.id == self.conversation_context["pending_slot_id"]
                ).first()

                if not slot:
                    # Clear the pending slot ID as it no longer exists
                    self.conversation_context["pending_slot_id"] = None
                    self.store.set_conversation_context(self.user_id, self.conversation_context)
                    return f"Sorry, the slot you were interested in is no longer available. Let me find another one for you."

                # Check for conflicting bookings
                conflicting_bookings = self.db.query(Booking).filter(
                    Booking.parking_slot_id == slot.id,
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.start_time < end_time,
                    Booking.end_time > start_time
                ).all()

                if conflicting_bookings:
                    # Clear the pending slot ID as it's not available for this time
                    self.conversation_context["pending_slot_id"] = None
                    self.store.set_conversation_context(self.user_id, self.conversation_context)
                    return f"Sorry, the slot you were interested in is already booked for the requested time period. Let me find another one for you."

            # If we don't have a slot yet, find an available one
            if not slot:
                # Find an available slot matching the criteria
                from ..database.models import ParkingSlot, VehicleType

                # Convert string vehicle type to enum
                vehicle_type_enum = None
                if self.conversation_context["selected_vehicle_type"] == "car":
                    vehicle_type_enum = VehicleType.CAR
                elif self.conversation_context["selected_vehicle_type"] == "bike":
                    vehicle_type_enum = VehicleType.BIKE
                elif self.conversation_context["selected_vehicle_type"] == "truck":
                    vehicle_type_enum = VehicleType.TRUCK

                if not vehicle_type_enum:
                    return "I couldn't understand the vehicle type. Please specify car, bike, or truck."

                # Find all slots of the right type at the right mall
                from ..database.models import Booking, BookingStatus
                slots = self.db.query(ParkingSlot).filter(
                    ParkingSlot.mall_id == self.conversation_context["selected_mall_id"],
                    ParkingSlot.vehicle_type == vehicle_type_enum
                ).all()

                # Check each slot for availability during the requested time period
                available_slots = []
                for slot in slots:
                    # Check for conflicting bookings
                    conflicting_bookings = self.db.query(Booking).filter(
                        Booking.parking_slot_id == slot.id,
                        Booking.status == BookingStatus.CONFIRMED,
                        Booking.start_time < end_time,
                        Booking.end_time > start_time
                    ).all()

                    # If no conflicts, the slot is available
                    if not conflicting_bookings:
                        available_slots.append(slot)

                if not available_slots:
                    return f"Sorry, there are no available {self.conversation_context['selected_vehicle_type']} slots at {self.conversation_context['selected_mall']} for the requested time period."

                # Use the first available slot
                slot = available_slots[0]

            # Store pending booking information
            from ..database.models import Mall
            mall = self.db.query(Mall).filter(Mall.id == slot.mall_id).first()

            self.pending_booking = {
                "slot_id": slot.id,
                "user_id": self.user_id,
                "vehicle_type": slot.vehicle_type.value,
                "mall_name": mall.name if mall else "Unknown Mall",
                "slot_number": slot.slot_number,
                "hourly_rate": slot.hourly_rate,
                "license_plate": self.conversation_context["selected_license_plate"]
            }

            # Return confirmation message
            license_plate_info = f"* License Plate: {self.pending_booking['license_plate']}" if self.pending_booking['license_plate'] else "* License Plate: Not provided (a demo plate will be used)"
            time_info = f"* Time: {self.conversation_context['selected_time_period']}" if self.conversation_context['selected_time_period'] else "* Time: Current time (default)"

            return f"""
I've found an available slot for your {self.conversation_context['selected_vehicle_type']} at {self.conversation_context['selected_mall']}.

Slot Details:
* Mall: {self.pending_booking['mall_name']}
* Slot ID: {slot.id}
* Type: {self.pending_booking['vehicle_type']}
* Number: {self.pending_booking['slot_number']}
* Rate: ₹{self.pending_booking['hourly_rate']}/hour
{license_plate_info}
{time_info}

Please confirm if you want to proceed with booking.
If yes, I will book the slot for User ID: {self.user_id}.
If no, please let me know and I will cancel the booking request.

Please respond with "Yes" or "No".
"""
        except Exception as e:
            print(f"Error in _create_booking_from_context: {str(e)}")
            return f"Sorry, there was an error processing your booking request: {str(e)}"

    def process_query(self, query: str, conversation_id: Optional[str] = None) -> str:
        """Process a user query and return the agent's response."""
        try:
            # Update conversation context based on query
            self._update_conversation_context(query)

            # Check for specific commands first
            if query.lower().startswith("book slot "):
                return self._handle_booking_command(query)
            elif query.lower().startswith("cancel booking "):
                return self._handle_booking_cancellation(query)
            elif query.lower() in ["check my bookings", "show my bookings", "view my bookings", "my bookings", "check bookings"]:
                return self._check_user_bookings()
            elif query.lower() in ["check parking rates", "show rates", "parking rates", "what are the rates", "how much does it cost"]:
                return self._check_parking_rates()
            elif query.lower() in ["check available slots", "show available slots", "available slots", "find slots", "find parking"]:
                return self._check_available_slots()
            elif query.lower() in ["yes", "confirm", "yes, please", "yes, book it"]:
                # Debug logging
                print(f"Processing confirmation. Pending booking: {self.pending_booking}")
                print(f"Conversation context: {self.conversation_context}")

                # If there's a pending booking, confirm it
                if self.pending_booking:
                    print(f"Confirming pending booking: {self.pending_booking}")
                    return self._handle_booking_confirmation()
                # If there's no pending booking but we have context, create one
                elif self.conversation_context["selected_mall_id"] and self.conversation_context["selected_vehicle_type"]:
                    print(f"Creating booking from context: Mall ID: {self.conversation_context['selected_mall_id']}, Vehicle: {self.conversation_context['selected_vehicle_type']}")
                    return self._create_booking_from_context()
                # Otherwise, we don't have enough information
                else:
                    print("Not enough information for booking")
                    return "I'm not sure what you're confirming. Please provide more details about which mall and vehicle type you're interested in."

            # If no specific command matched, check the detected intent
            elif self.conversation_context.get("intent"):
                intent = self.conversation_context["intent"]
                print(f"Using detected intent: {intent}")

                if intent == "check_available_slots":
                    return self._check_available_slots()
                elif intent == "check_parking_rates":
                    return self._check_parking_rates()
                elif intent == "check_user_bookings":
                    return self._check_user_bookings()
                elif intent == "create_booking" and self.conversation_context["selected_mall_id"] and self.conversation_context["selected_vehicle_type"]:
                    return self._create_booking_from_context()
                # For cancel_booking intent, we need a specific booking ID, so we don't handle it here

            # Set conversation ID if provided
            if conversation_id:
                self.conversation_id = conversation_id
            elif not hasattr(self, 'conversation_id'):
                # Create a new conversation ID if none exists
                self.conversation_id = str(uuid.uuid4())
                print(f"Created new conversation ID: {self.conversation_id}")

            # Get relevant history
            relevant_history = []
            try:
                if conversation_id:
                    # First try to get history for this specific conversation
                    if self.use_vector_store:
                        conversation_history = self.vector_store.get_conversation_history(conversation_id)
                    else:
                        conversation_history = self.file_chat.get_conversation_history(conversation_id)

                    if conversation_history:
                        relevant_history = [
                            f"User: {entry['user_query']}\nAgent: {entry['agent_response']}"
                            for entry in conversation_history
                        ]
                        print(f"Found {len(relevant_history)} messages in conversation history")

                # If no conversation history or it's empty, try semantic search or file-based history
                if not relevant_history:
                    if self.use_vector_store:
                        relevant_history_entries = self.vector_store.get_relevant_history(query, k=5)
                    else:
                        relevant_history_entries = self.file_chat.get_relevant_history(query, k=5)

                    relevant_history = [
                        f"User: {entry['user_query']}\nAgent: {entry['agent_response']}"
                        for entry in relevant_history_entries
                    ]
                    print(f"Found {len(relevant_history)} relevant messages from history search")

                # Fallback to traditional memory manager if needed
                if not relevant_history:
                    relevant_history = self.memory_manager.get_relevant_history(query, k=5)
                    print(f"Using memory manager history with {len(relevant_history)} messages")
            except Exception as history_error:
                print(f"Error retrieving history: {str(history_error)}")
                # Continue without history if there's an error

            # Fetch actual mall names from the database
            from ..database.models import Mall
            malls = self.db.query(Mall).all()
            mall_names = [f"* {mall.name} (ID: {mall.id})" for mall in malls]
            mall_list = "\n".join(mall_names)

            # Create system message
            system_message = f"""
            You are a helpful parking management assistant for a mall parking system. You can help users with:

            1. Finding available parking slots
            2. Checking parking rates
            3. Creating parking bookings
            4. Cancelling bookings
            5. Viewing booking history

            CRITICAL FORMATTING INSTRUCTIONS (YOU MUST FOLLOW THESE EXACTLY):
            - NEVER respond with long paragraphs
            - ALWAYS use simple asterisk (*) for bullet points like this:
              * First point
              * Second point
            - DO NOT use Unicode bullet points (•) as they may not display correctly
            - ALWAYS put each piece of information on a separate line
            - ALWAYS use numbered lists (1., 2., 3.) for sequential instructions
            - ALWAYS break your response into short, digestible sections
            - ALWAYS use line breaks between different sections of information
            - NEVER combine multiple points into a single paragraph
            - Format mall lists and options as bullet points, not as running text

            CRITICAL CONVERSATION INSTRUCTIONS:
            - NEVER ask for information that the user has already provided
            - If the user has already mentioned a mall name, DO NOT ask them to select a mall again
            - If the user has already mentioned a vehicle type, DO NOT ask them to select a vehicle type again
            - ALWAYS remember information from earlier in the conversation
            - NEVER repeat questions that have already been answered
            - If the user says "Phoenix Mall of Asia" or any other mall name, remember it and use it
            - If the user says "car", "bike", or "truck", remember it and use it

            When the user asks about parking availability, make sure to ask for ONLY the information they haven't provided yet:
            * Which mall they're interested in (if not already mentioned)
            * What type of vehicle they have (if not already mentioned)
            * The time period they're interested in (if not already mentioned)

            When creating a booking, ensure you have all the necessary information:
            * Mall location (if not already mentioned)
            * Vehicle type (if not already mentioned)
            * Preferred parking slot ID (if any)

            Our system has the following malls, each with parking slots:
            {mall_list}

            Each mall has:
            * 3 slots for trucks (₹100/hour)
            * 3 slots for cars (₹50/hour)
            * 4 slots for bikes (₹20/hour)
            """

            # Fetch available slots for reference
            from ..database.models import ParkingSlot, VehicleType

            # Get all available slots
            available_slots = self.db.query(ParkingSlot).filter(ParkingSlot.is_available == True).all()
            available_slot_info = []

            # Get slots for the selected mall and vehicle type if specified
            mall_specific_slots = []
            if self.conversation_context["selected_mall_id"] and self.conversation_context["selected_vehicle_type"]:
                print(f"Filtering slots for mall ID: {self.conversation_context['selected_mall_id']} and vehicle type: {self.conversation_context['selected_vehicle_type']}")

                # Convert string vehicle type to enum
                vehicle_type_enum = None
                if self.conversation_context["selected_vehicle_type"] == "car":
                    vehicle_type_enum = VehicleType.CAR
                elif self.conversation_context["selected_vehicle_type"] == "bike":
                    vehicle_type_enum = VehicleType.BIKE
                elif self.conversation_context["selected_vehicle_type"] == "truck":
                    vehicle_type_enum = VehicleType.TRUCK

                if vehicle_type_enum:
                    # Get all slots for this mall and vehicle type
                    mall_specific_slots = self.db.query(ParkingSlot).filter(
                        ParkingSlot.mall_id == self.conversation_context["selected_mall_id"],
                        ParkingSlot.vehicle_type == vehicle_type_enum,
                        ParkingSlot.is_available == True
                    ).all()

                    print(f"Found {len(mall_specific_slots)} available slots at mall ID {self.conversation_context['selected_mall_id']} for {self.conversation_context['selected_vehicle_type']}")

            # Add mall-specific slots first
            for slot in mall_specific_slots:
                mall = self.db.query(Mall).filter(Mall.id == slot.mall_id).first()
                if mall:
                    available_slot_info.append(
                        f"* Slot ID: {slot.id}, Mall: {mall.name}, Type: {slot.vehicle_type.value}, "
                        f"Number: {slot.slot_number}, Rate: ₹{slot.hourly_rate}/hour"
                    )

            # Then add other available slots (limited to 20 total)
            remaining_slots = 20 - len(mall_specific_slots)
            for slot in available_slots[:remaining_slots]:
                # Skip slots already included in mall-specific slots
                if slot in mall_specific_slots:
                    continue

                mall = self.db.query(Mall).filter(Mall.id == slot.mall_id).first()
                if mall:
                    available_slot_info.append(
                        f"* Slot ID: {slot.id}, Mall: {mall.name}, Type: {slot.vehicle_type.value}, "
                        f"Number: {slot.slot_number}, Rate: ₹{slot.hourly_rate}/hour"
                    )

            # Format available slots text with better organization
            if not available_slot_info:
                available_slots_text = "No slots available currently."
            else:
                # Group slots by mall for better readability
                mall_slots = {}
                for slot_info in available_slot_info:
                    mall_name = slot_info.split("Mall: ")[1].split(",")[0]
                    if mall_name not in mall_slots:
                        mall_slots[mall_name] = []
                    mall_slots[mall_name].append(slot_info)

                # Format the text with mall grouping
                available_slots_text = ""
                for mall_name, slots in mall_slots.items():
                    available_slots_text += f"\nSlots at {mall_name}:\n"
                    available_slots_text += "\n".join(slots)
                    available_slots_text += "\n"

            # Update conversation context based on query
            self._update_conversation_context(query)

            # Add user ID, name, and conversation context to system message
            user_context = f"""
            IMPORTANT USER INFORMATION:
            * Current User ID: {self.user_id}
            * User Name: {self.user_name or "User"}
            * Always use this User ID for all operations
            * Always address the user by their name when asking for information
            * Do NOT ask the user for their User ID again

            CURRENT CONVERSATION CONTEXT:
            * Selected Mall: {self.conversation_context['selected_mall'] or 'Not specified'}
            * Selected Vehicle Type: {self.conversation_context['selected_vehicle_type'] or 'Not specified'}
            * Selected License Plate: {self.conversation_context['selected_license_plate'] or 'Not specified'}
            * Selected Time Period: {self.conversation_context['selected_time_period'] or 'Not specified'}

            PARKING RATES (if available):
            {self._format_parking_rates()}

            IMPORTANT: If the user has already provided information about their mall or vehicle type,
            DO NOT ask for it again. Use the information they've already provided.

            BOOKING INSTRUCTIONS:
            When a user wants to book a parking slot, you should:
            1. If they haven't specified a mall, ask which mall they prefer
            2. If they haven't specified a vehicle type, ask what type of vehicle they have
            3. If they haven't specified a vehicle license plate, ask for their license plate number
            4. If they haven't specified a date/time, ask when they want to park
            5. If they haven't specified a duration, assume 2 hours
            6. Show them available slots matching their criteria
            7. To book a slot, tell them to use the following format: "Book slot [SLOT_ID]"
               For example: "Book slot 5"
            8. If the user says "yes" or "confirm" after you've shown them available slots,
               I will automatically find and book an appropriate slot for them

            CHECKING BOOKINGS:
            When a user wants to check their bookings, tell them to use one of these commands:
            * "Check my bookings"
            * "Show my bookings"
            * "View my bookings"
            * "My bookings"

            REQUIRED INFORMATION FOR BOOKING:
            * Mall name (one of the malls listed above)
            * Vehicle type (car, bike, or truck)
            * Vehicle license plate number (e.g., "KA01AB1234")
            * Date and time (e.g., "tomorrow at 5 pm", "today at 3 pm")
            * Duration (default is 2 hours if not specified)

            EXAMPLE BOOKING QUERY:
            "I want to book a parking slot at Orion Mall for my car with license plate KA01AB1234 tomorrow at 5 pm for 2 hours"

            IMPORTANT: When the user says "yes" or "confirm", I will:
            1. Check if there's a pending booking request
            2. If not, I'll check if I know their mall and vehicle preferences
            3. If I have this information, I'll find an available slot and book it
            4. If I don't have enough information, I'll ask for it

            CURRENTLY AVAILABLE SLOTS:
            {available_slots_text}
            """

            # Create messages array for the API call
            messages = [
                {"role": "system", "content": system_message + user_context}
            ]

            # Add conversation history to messages
            if relevant_history:
                # Add each message from history as a separate message with proper role
                for history_entry in relevant_history:
                    if history_entry.startswith("User: "):
                        user_msg = history_entry.replace("User: ", "", 1)
                        messages.append({"role": "user", "content": user_msg})
                    elif history_entry.startswith("Agent: "):
                        agent_msg = history_entry.replace("Agent: ", "", 1)
                        messages.append({"role": "assistant", "content": agent_msg})

            # Add user query
            messages.append({"role": "user", "content": query})

            # Call Groq API
            response = self._call_groq_api(messages)

            # Add interaction to memory
            self.memory_manager.add_interaction(query, response)

            # Add to chat history
            if self.use_vector_store:
                try:
                    self.vector_store.add_interaction(
                        conversation_id=self.conversation_id,
                        user_query=query,
                        agent_response=response
                    )
                    print(f"Added interaction to vector store with conversation ID: {self.conversation_id}")
                except Exception as vector_error:
                    print(f"Error adding to vector store: {str(vector_error)}")
                    # Fall back to file-based chat history
                    try:
                        self.file_chat.add_interaction(
                            conversation_id=self.conversation_id,
                            user_query=query,
                            agent_response=response
                        )
                        print(f"Added interaction to file chat history with conversation ID: {self.conversation_id}")
                    except Exception as file_error:
                        print(f"Error adding to file chat history: {str(file_error)}")
            else:
                # Use file-based chat history
                try:
                    self.file_chat.add_interaction(
                        conversation_id=self.conversation_id,
                        user_query=query,
                        agent_response=response
                    )
                    print(f"Added interaction to file chat history with conversation ID: {self.conversation_id}")
                except Exception as file_error:
                    print(f"Error adding to file chat history: {str(file_error)}")

            return response

        except Exception as e:
            error_message = f"I encountered an error while processing your request: {str(e)}"
            print(f"Error in process_query: {str(e)}")
            return error_message
