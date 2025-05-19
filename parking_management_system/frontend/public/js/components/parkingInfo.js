// Parking Info Component
class ParkingInfoComponent {
    constructor() {
        this.container = document.getElementById('parkingInfoPanel');
        this.render();
        this.bindEvents();
        this.activeTab = 'info';

        // Set default date to today
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        // Set default time to current hour + 1
        const defaultHour = (today.getHours() + 1) % 24;
        const defaultTime = `${String(defaultHour).padStart(2, '0')}:00`;

        this.availableSlotsFilter = {
            mall: '1', // Default to first mall
            vehicleType: 'car', // Default to car
            date: tomorrow.toISOString().split('T')[0], // Default to tomorrow
            time: defaultTime, // Default to next hour
            duration: 2 // Default to 2 hours
        };

        this.malls = [];
        this.fetchMalls();

        // Initialize date and time fields after rendering
        this.initializeDateTimeFields();
    }

    initializeDateTimeFields() {
        // Set default values for date and time fields
        const bookingDate = document.getElementById('bookingDate');
        const bookingTime = document.getElementById('bookingTime');
        const bookingDuration = document.getElementById('bookingDuration');

        if (bookingDate) {
            bookingDate.value = this.availableSlotsFilter.date;

            // Set min date to today
            const today = new Date();
            bookingDate.min = today.toISOString().split('T')[0];
        }

        if (bookingTime) {
            bookingTime.value = this.availableSlotsFilter.time;

            // Add event listener to properly format time
            bookingTime.addEventListener('change', () => {
                // Ensure time is properly formatted as HH:MM
                const timeValue = bookingTime.value;
                if (timeValue) {
                    const [hours, minutes] = timeValue.split(':');
                    const formattedTime = `${hours.padStart(2, '0')}:${minutes ? minutes.padStart(2, '0') : '00'}`;
                    bookingTime.value = formattedTime;
                    this.availableSlotsFilter.time = formattedTime;
                    console.log('Time updated to:', formattedTime);
                }
            });
        }

        if (bookingDuration) {
            bookingDuration.value = this.availableSlotsFilter.duration;
        }

        console.log('Date/time fields initialized:', {
            date: this.availableSlotsFilter.date,
            time: this.availableSlotsFilter.time,
            duration: this.availableSlotsFilter.duration
        });
    }

    render() {
        this.container.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <h2 class="text-xl font-semibold">Chat Assistant</h2>
                </div>

                <div class="panel-body p-4">
                    <div class="bg-blue-50 p-4 rounded-lg border border-blue-100 mb-4">
                        <h3 class="text-lg font-semibold text-blue-700 mb-2">
                            <i class="fas fa-comments mr-2"></i> Chat with our Assistant
                        </h3>
                        <p class="mb-3">
                            Use the chat interface to:
                        </p>
                        <ul class="list-disc pl-5 space-y-1">
                            <li>Find available parking slots</li>
                            <li>Book a parking slot</li>
                            <li>Check your bookings</li>
                            <li>Cancel a booking</li>
                        </ul>
                    </div>

                    <div class="bg-yellow-50 p-4 rounded-lg border border-yellow-100">
                        <h3 class="text-lg font-semibold text-yellow-700 mb-2">
                            <i class="fas fa-lightbulb mr-2"></i> Navigation
                        </h3>
                        <p class="mb-3">
                            You can also use the navigation bar to:
                        </p>
                        <ul class="list-disc pl-5 space-y-1">
                            <li><a href="info.html" class="text-blue-600 hover:underline">Info</a> - Learn about our parking system</li>
                            <li><a href="available-slots.html" class="text-blue-600 hover:underline">Available Slots</a> - Find and book slots manually</li>
                            <li><a href="bookings.html" class="text-blue-600 hover:underline">Bookings</a> - View and manage your bookings</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    bindEvents() {
        // No event bindings needed for the simplified panel
    }

    // This method is kept for compatibility with existing code
    // but doesn't do anything in the new design
    setActiveTab(tabName) {
        this.activeTab = tabName;
        console.log(`Tab navigation is now handled by separate pages. Requested tab: ${tabName}`);
    }

    fetchBookings() {
        const bookingsList = document.getElementById('bookingsList');
        bookingsList.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-spinner fa-spin text-blue-500 text-2xl"></i>
                <p class="mt-2 text-gray-600">Loading your bookings...</p>
            </div>
        `;

        // Get the current user ID
        const currentUserId = localStorage.getItem('userId');
        if (!currentUserId) {
            bookingsList.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-red-500">Please log in to view your bookings.</p>
                </div>
            `;
            return;
        }

        // Fetch bookings from API
        const bookingsUrl = `${API_BASE_URL}/bookings?user_id=${currentUserId}`;
        console.log(`Fetching bookings from: ${bookingsUrl}`);

        fetch(bookingsUrl, {
            headers: {
                'X-User-ID': currentUserId
            }
        })
            .then(response => {
                console.log('Bookings response status:', response.status);
                return response.json();
            })
            .then(bookings => {
                console.log('Bookings data received:', bookings);

                if (bookings.length === 0) {
                    bookingsList.innerHTML = `
                        <div class="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                            <i class="fas fa-calendar-times text-gray-400 text-3xl mb-2"></i>
                            <p class="text-gray-600">You don't have any bookings yet.</p>
                            <p class="mt-2 text-sm text-blue-600">
                                Use the chat assistant to make a booking.
                            </p>
                        </div>
                    `;
                    return;
                }

                bookingsList.innerHTML = '';
                bookings.forEach((booking, index) => {
                    console.log(`Processing booking ${index + 1}/${bookings.length}:`, booking);
                    this.renderBookingCard(booking);
                });
            })
            .catch(error => {
                console.error('Error fetching bookings:', error);
                bookingsList.innerHTML = `
                    <div class="text-center py-8 bg-red-50 rounded-lg border border-red-200">
                        <i class="fas fa-exclamation-circle text-red-500 text-3xl mb-2"></i>
                        <p class="text-red-600">Error loading bookings.</p>
                        <p class="mt-2 text-sm text-red-500">
                            Please try again later or contact support.
                        </p>
                    </div>
                `;
            });
    }

    renderBookingCard(booking) {
        const bookingsList = document.getElementById('bookingsList');
        const bookingCard = document.createElement('div');

        // Set background color based on vehicle type
        let bgColor = '';
        let vehicleIcon = '';
        if (booking.vehicle_type === 'car') {
            bgColor = 'bg-blue-50 border-blue-200';
            vehicleIcon = '<i class="fas fa-car text-blue-500 mr-1"></i>';
        } else if (booking.vehicle_type === 'truck') {
            bgColor = 'bg-green-50 border-green-200';
            vehicleIcon = '<i class="fas fa-truck text-green-500 mr-1"></i>';
        } else if (booking.vehicle_type === 'bike') {
            bgColor = 'bg-purple-50 border-purple-200';
            vehicleIcon = '<i class="fas fa-motorcycle text-purple-500 mr-1"></i>';
        }

        // Format dates
        const startDate = new Date(booking.start_time || booking.booking_time);
        const endDate = booking.end_time ? new Date(booking.end_time) : new Date(startDate.getTime() + 2*60*60*1000);

        // Log the booking time details for debugging
        console.log('Booking time details:', {
            bookingId: booking.id,
            rawStartTime: booking.start_time || booking.booking_time,
            rawEndTime: booking.end_time,
            parsedStartDate: startDate.toISOString(),
            parsedEndDate: endDate.toISOString()
        });

        // Format dates for display - use local date and time format with 12-hour clock
        const formatOptions = {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            hour12: true
        };
        const formattedStartDate = startDate.toLocaleString(undefined, formatOptions);
        const formattedEndDate = endDate.toLocaleString(undefined, formatOptions);

        // Check if booking can be cancelled (only confirmed bookings can be cancelled)
        const canCancel = booking.status.toLowerCase() === 'confirmed';
        const isCancelled = booking.status.toLowerCase() === 'cancelled';

        // Create booking card
        bookingCard.className = `p-4 mb-4 rounded-lg border ${bgColor} hover:shadow-md transition-shadow duration-200`;
        bookingCard.dataset.bookingId = booking.id;
        bookingCard.innerHTML = `
            <div class="flex flex-col">
                <div class="flex justify-between items-start">
                    <div class="font-medium flex items-center">
                        ${vehicleIcon} ${booking.mall_name} - Slot ${booking.slot_number}
                    </div>
                    <div class="font-bold text-lg">₹${booking.amount || booking.total_amount}</div>
                </div>

                <div class="flex justify-between items-center mt-2">
                    <div class="text-sm text-gray-600">
                        <div><i class="far fa-calendar-alt mr-1"></i> From: ${formattedStartDate}</div>
                        <div><i class="far fa-calendar-alt mr-1"></i> To: ${formattedEndDate}</div>
                    </div>
                    <div class="text-xs px-2 py-1 rounded-full ${this.getStatusClass(booking.status)}">
                        ${booking.status}
                    </div>
                </div>

                <div class="mt-2 text-sm">
                    <span class="font-medium">Vehicle:</span> ${booking.vehicle_number || 'Not specified'}
                </div>

                <div class="mt-3 flex justify-end gap-2">
                    ${canCancel ? `
                    <button type="button" class="cancel-booking-btn text-xs bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200">
                        <i class="fas fa-times-circle mr-1"></i> Cancel
                    </button>
                    ` : ''}
                    ${isCancelled ? `
                    <button type="button" class="delete-booking-btn text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200">
                        <i class="fas fa-trash-alt mr-1"></i> Delete
                    </button>
                    ` : ''}
                </div>
            </div>
        `;

        // Add cancel button event listener if booking can be cancelled
        if (canCancel) {
            const cancelBtn = bookingCard.querySelector('.cancel-booking-btn');
            cancelBtn.addEventListener('click', () => {
                this.cancelBooking(booking.id);
            });
        }

        // Add delete button event listener if booking is cancelled
        if (isCancelled) {
            const deleteBtn = bookingCard.querySelector('.delete-booking-btn');
            deleteBtn.addEventListener('click', () => {
                this.deleteBooking(booking.id);
            });
        }

        bookingsList.appendChild(bookingCard);
    }

    cancelBooking(bookingId) {
        if (!confirm('Are you sure you want to cancel this booking?')) {
            return;
        }

        const userId = localStorage.getItem('userId');
        if (!userId) {
            console.error('No user ID found in localStorage');
            alert('Please log in to cancel a booking');
            return;
        }

        // Show loading state
        const bookingCard = document.querySelector(`[data-booking-id="${bookingId}"]`);
        if (bookingCard) {
            const cancelBtn = bookingCard.querySelector('.cancel-booking-btn');
            if (cancelBtn) {
                cancelBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Cancelling...';
                cancelBtn.disabled = true;
                cancelBtn.classList.add('opacity-50');
            }
        } else {
            console.warn(`Booking card with ID ${bookingId} not found in DOM`);
        }

        console.log(`Attempting to cancel booking ${bookingId} for user ${userId}`);

        // Call API to cancel booking
        const cancelUrl = `${API_BASE_URL}/bookings/${bookingId}/cancel`;
        console.log(`Sending cancel request to: ${cancelUrl}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId
            }
        });

        // Add a small delay to ensure UI updates before making the request
        setTimeout(() => {
            fetch(cancelUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': userId
                }
            })
            .then(response => {
                console.log('Cancel booking response status:', response.status);

                // Even if we get an error response, try to parse it for more details
                return response.json().then(data => {
                    console.log('Cancel booking response data:', data);
                    if (!response.ok) {
                        // Add the status code to the error for better debugging
                        throw new Error(`Failed to cancel booking: ${response.status} - ${data.detail || 'Unknown error'}`);
                    }
                    return data;
                }).catch(err => {
                    // Handle JSON parsing errors
                    console.error('Error parsing JSON response:', err);
                    if (!response.ok) {
                        throw new Error(`Failed to cancel booking: ${response.status} - Could not parse response`);
                    }
                    return { message: 'Success (no JSON response)' };
                });
            })
            .then(data => {
                console.log('Cancel booking success:', data);

                // Refresh bookings list
                this.fetchBookings();

                // Also refresh available slots to show the slot as available again
                this.fetchAvailableSlots();

                // Show success message
                alert('Booking cancelled successfully');

                // Notify the agent about the manual cancellation
                if (window.chatInterfaceComponent) {
                    // Get booking details from the DOM if available
                    let bookingDetails = '';
                    if (bookingCard) {
                        const mallName = bookingCard.querySelector('.font-medium')?.textContent.trim() || 'Unknown Mall';
                        const slotNumber = mallName.split('-')[1]?.trim() || 'Unknown Slot';
                        bookingDetails = ` for ${slotNumber} at ${mallName.split('-')[0]?.trim()}`;
                    }

                    window.chatInterfaceComponent.addAssistantMessage(`
                        <div class="cancellation-confirmation">
                            <p><i class="fas fa-check-circle text-green-500 mr-1"></i> <strong>Manual Cancellation Confirmed</strong></p>
                            <p class="mt-2">I've recorded your manual cancellation of booking #${bookingId}${bookingDetails}.</p>
                            <p class="mt-1">The parking slot is now available for others to book.</p>
                            <p class="mt-3">Your bookings have been updated in the Bookings tab.</p>
                        </div>
                    `, 'html');
                }
            })
            .catch(error => {
                console.error('Error cancelling booking:', error);

                // Show a more detailed error message
                let errorMessage = 'Failed to cancel booking. Please try again.';

                // Extract more specific error message if available
                if (error.message && error.message.includes('Failed to cancel booking:')) {
                    errorMessage = error.message;
                }

                alert(errorMessage);

                // Reset button state
                if (bookingCard) {
                    const cancelBtn = bookingCard.querySelector('.cancel-booking-btn');
                    if (cancelBtn) {
                        cancelBtn.innerHTML = '<i class="fas fa-times-circle mr-1"></i> Cancel';
                        cancelBtn.disabled = false;
                        cancelBtn.classList.remove('opacity-50');
                    }
                }
            });
        }, 100); // 100ms delay
    }

    deleteBooking(bookingId) {
        if (!confirm('Are you sure you want to delete this cancelled booking from your history?')) {
            return;
        }

        const userId = localStorage.getItem('userId');
        if (!userId) {
            console.error('No user ID found in localStorage');
            alert('Please log in to delete a booking');
            return;
        }

        // Show loading state
        const bookingCard = document.querySelector(`[data-booking-id="${bookingId}"]`);
        if (bookingCard) {
            const deleteBtn = bookingCard.querySelector('.delete-booking-btn');
            if (deleteBtn) {
                deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Deleting...';
                deleteBtn.disabled = true;
                deleteBtn.classList.add('opacity-50');
            }
        } else {
            console.warn(`Booking card with ID ${bookingId} not found in DOM`);
        }

        // Call API to delete booking
        const deleteUrl = `${API_BASE_URL}/bookings/${bookingId}`;
        console.log(`Sending delete request to: ${deleteUrl}`);

        fetch(deleteUrl, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId
            }
        })
        .then(response => {
            console.log('Delete booking response status:', response.status);

            // Try to parse the response as JSON
            return response.json().then(data => {
                if (!response.ok) {
                    throw new Error(`Failed to delete booking: ${response.status} - ${data.detail || 'Unknown error'}`);
                }
                return data;
            }).catch(err => {
                // Handle JSON parsing errors
                if (!response.ok) {
                    throw new Error(`Failed to delete booking: ${response.status}`);
                }
                return { message: 'Success (no JSON response)' };
            });
        })
        .then(data => {
            console.log('Delete booking success:', data);

            if (bookingCard) {
                // Add fade-out animation
                bookingCard.style.transition = 'opacity 0.5s ease-out';
                bookingCard.style.opacity = '0';

                // Remove from DOM after animation completes
                setTimeout(() => {
                    bookingCard.remove();

                    // Show success message
                    alert('Booking deleted from history');

                    // Check if there are no more bookings
                    const bookingsList = document.getElementById('bookingsList');
                    if (bookingsList && bookingsList.children.length === 0) {
                        bookingsList.innerHTML = `
                            <div class="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                                <i class="fas fa-calendar-times text-gray-400 text-3xl mb-2"></i>
                                <p class="text-gray-600">You don't have any bookings yet.</p>
                                <p class="mt-2 text-sm text-blue-600">
                                    Use the chat assistant to make a booking.
                                </p>
                            </div>
                        `;
                    }
                }, 500);
            }

            // Refresh bookings list
            this.fetchBookings();

            // Notify the agent about the manual deletion
            if (window.chatInterfaceComponent) {
                window.chatInterfaceComponent.addAssistantMessage(`
                    <div class="deletion-confirmation">
                        <p><i class="fas fa-check-circle text-green-500 mr-1"></i> <strong>Booking Deleted</strong></p>
                        <p class="mt-2">I've removed booking #${bookingId} from your history.</p>
                        <p class="mt-3">Your bookings have been updated in the Bookings tab.</p>
                    </div>
                `, 'html');
            }
        })
        .catch(error => {
            console.error('Error deleting booking:', error);

            // Show error message
            alert(error.message || 'Failed to delete booking. Please try again.');

            // Reset button state
            if (bookingCard) {
                const deleteBtn = bookingCard.querySelector('.delete-booking-btn');
                if (deleteBtn) {
                    deleteBtn.innerHTML = '<i class="fas fa-trash-alt mr-1"></i> Delete';
                    deleteBtn.disabled = false;
                    deleteBtn.classList.remove('opacity-50');
                }
            }
        });
    }

    getStatusClass(status) {
        switch (status.toLowerCase()) {
            case 'active':
            case 'confirmed':
                return 'bg-green-100 text-green-800';
            case 'completed':
                return 'bg-blue-100 text-blue-800';
            case 'cancelled':
                return 'bg-red-100 text-red-800';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    fetchMalls() {
        // Fetch malls from API
        fetch(`${API_BASE_URL}/malls/`)
            .then(response => response.json())
            .then(malls => {
                this.malls = malls;
                this.populateMallFilter();

                // Fetch available slots after malls are loaded
                this.fetchAvailableSlots();
            })
            .catch(error => {
                console.error('Error fetching malls:', error);
            });
    }

    populateMallFilter() {
        const mallFilter = document.getElementById('mallFilter');
        const vehicleTypeFilter = document.getElementById('vehicleTypeFilter');
        if (!mallFilter) return;

        // Clear all existing options
        mallFilter.innerHTML = '';

        // Add mall options
        this.malls.forEach(mall => {
            const option = document.createElement('option');
            option.value = mall.id;
            option.textContent = mall.name;
            mallFilter.appendChild(option);
        });

        // Set default selected values
        if (mallFilter && this.malls.length > 0) {
            mallFilter.value = this.availableSlotsFilter.mall;
        }

        if (vehicleTypeFilter) {
            vehicleTypeFilter.value = this.availableSlotsFilter.vehicleType;
        }
    }

    fetchAvailableSlots() {
        const availableSlotsList = document.getElementById('availableSlotsList');
        if (!availableSlotsList) return;

        // Show loading indicator
        availableSlotsList.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-spinner fa-spin text-blue-500 text-2xl"></i>
                <p class="mt-2 text-gray-600">Loading available slots...</p>
            </div>
        `;

        // Build URL with filters
        let url = `${API_BASE_URL}/available-slots`;
        const params = new URLSearchParams();

        // Always include booked slots
        params.append('include_booked', 'true');

        if (this.availableSlotsFilter.vehicleType) {
            params.append('vehicle_type', this.availableSlotsFilter.vehicleType);
        }

        // Add date and time parameters if available
        if (this.availableSlotsFilter.date && this.availableSlotsFilter.time) {
            // Create start date/time
            const startDateTime = new Date(this.availableSlotsFilter.date + 'T' + this.availableSlotsFilter.time);
            params.append('start_time', startDateTime.toISOString());

            // Calculate end date/time based on duration
            const endDateTime = this.calculateEndTime(
                this.availableSlotsFilter.date,
                this.availableSlotsFilter.time,
                this.availableSlotsFilter.duration
            );
            params.append('end_time', endDateTime.toISOString());
        }

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        console.log('Fetching available slots with URL:', url);

        // Fetch available slots
        fetch(url)
            .then(response => response.json())
            .then(slots => {
                // Filter by mall if needed
                if (this.availableSlotsFilter.mall) {
                    slots = slots.filter(slot => slot.mall_id.toString() === this.availableSlotsFilter.mall);
                }

                if (slots.length === 0) {
                    availableSlotsList.innerHTML = `
                        <div class="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                            <i class="fas fa-parking text-gray-400 text-3xl mb-2"></i>
                            <p class="text-gray-600">No available slots match your criteria.</p>
                            <p class="mt-2 text-sm text-blue-600">
                                Try changing your filters or check back later.
                            </p>
                        </div>
                    `;
                    return;
                }

                // Group slots by mall
                const slotsByMall = {};
                slots.forEach(slot => {
                    if (!slotsByMall[slot.mall_name]) {
                        slotsByMall[slot.mall_name] = [];
                    }
                    slotsByMall[slot.mall_name].push(slot);
                });

                // Render slots grouped by mall
                availableSlotsList.innerHTML = '';
                Object.keys(slotsByMall).forEach(mallName => {
                    this.renderMallSlots(mallName, slotsByMall[mallName]);
                });
            })
            .catch(error => {
                console.error('Error fetching available slots:', error);
                availableSlotsList.innerHTML = `
                    <div class="text-center py-8 bg-red-50 rounded-lg border border-red-200">
                        <i class="fas fa-exclamation-circle text-red-500 text-3xl mb-2"></i>
                        <p class="text-red-600">Error loading available slots.</p>
                        <p class="mt-2 text-sm text-red-500">
                            Please try again later or contact support.
                        </p>
                    </div>
                `;
            });
    }

    renderMallSlots(mallName, slots) {
        const availableSlotsList = document.getElementById('availableSlotsList');

        // Create mall section
        const mallSection = document.createElement('div');
        mallSection.className = 'mb-6';

        // Mall header
        const mallHeader = document.createElement('h4');
        mallHeader.className = 'font-medium text-lg text-gray-800 mb-3 border-b pb-2';
        mallHeader.textContent = mallName;
        mallSection.appendChild(mallHeader);

        // Slots container - horizontal scrolling
        const slotsContainer = document.createElement('div');
        slotsContainer.className = 'slots-horizontal-container';

        // Add slots to horizontal container
        slots.forEach(slot => {
            slotsContainer.appendChild(this.createSlotCard(slot));
        });

        mallSection.appendChild(slotsContainer);
        availableSlotsList.appendChild(mallSection);
    }

    createSlotCard(slot) {
        const slotCard = document.createElement('div');

        // Set background color based on vehicle type and availability
        let bgColor = '';
        let vehicleIcon = '';
        let isBooked = slot.booking_status === 'BOOKED' || !slot.is_available;

        if (slot.vehicle_type === 'car') {
            bgColor = isBooked ? 'bg-gray-100 border-gray-200' : 'bg-blue-50 border-blue-200';
            vehicleIcon = '<i class="fas fa-car ' + (isBooked ? 'text-gray-500' : 'text-blue-500') + ' mr-1"></i>';
        } else if (slot.vehicle_type === 'truck') {
            bgColor = isBooked ? 'bg-gray-100 border-gray-200' : 'bg-green-50 border-green-200';
            vehicleIcon = '<i class="fas fa-truck ' + (isBooked ? 'text-gray-500' : 'text-green-500') + ' mr-1"></i>';
        } else if (slot.vehicle_type === 'bike') {
            bgColor = isBooked ? 'bg-gray-100 border-gray-200' : 'bg-purple-50 border-purple-200';
            vehicleIcon = '<i class="fas fa-motorcycle ' + (isBooked ? 'text-gray-500' : 'text-purple-500') + ' mr-1"></i>';
        }

        slotCard.className = `slot-card-horizontal ${bgColor} hover:shadow-md transition-shadow duration-200`;

        // Create the header with status badge if booked
        let headerContent = `${vehicleIcon} Slot ${slot.slot_number}`;
        if (isBooked) {
            headerContent += `<span class="ml-2 px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full">Booked</span>`;
        }

        slotCard.innerHTML = `
            <div class="slot-card-header">
                ${headerContent}
            </div>
            <div class="slot-card-details">
                <div class="text-sm">Floor: ${slot.floor}</div>
                <div class="text-sm">Section: ${slot.section}</div>
                <div class="font-bold mt-1">₹${slot.hourly_rate}/hr</div>
            </div>
            <div class="slot-card-action">
                ${isBooked ?
                    `<button type="button" class="w-full text-center bg-gray-300 text-gray-600 py-1 px-2 rounded text-sm cursor-not-allowed" disabled>
                        <i class="fas fa-ban mr-1"></i> Booked
                    </button>` :
                    `<button type="button" class="book-slot-btn w-full text-center bg-blue-600 text-white py-1 px-2 rounded text-sm hover:bg-blue-700" data-slot-id="${slot.id}">
                        <i class="fas fa-ticket-alt mr-1"></i> Book
                    </button>`
                }
            </div>
        `;

        // Add event listener for booking only if the slot is available
        if (!isBooked) {
            const bookButton = slotCard.querySelector('.book-slot-btn');
            if (bookButton) {
                bookButton.addEventListener('click', () => {
                    this.bookSlot(slot.id);
                });
            }
        }

        return slotCard;
    }

    bookSlot(slotId) {
        // Get current user ID
        const userId = localStorage.getItem('userId');
        if (!userId) {
            alert('Please log in to book a slot');
            return;
        }

        // Get booking details
        const bookingDate = this.availableSlotsFilter.date;
        const bookingTime = this.availableSlotsFilter.time;
        const bookingDuration = parseInt(this.availableSlotsFilter.duration);

        if (!bookingDate || !bookingTime) {
            alert('Please select a date and time for your booking');
            return;
        }

        // Create booking summary for confirmation
        const slot = this.findSlotById(slotId);
        const mallName = slot ? slot.mall_name : 'the selected mall';
        const slotNumber = slot ? slot.slot_number : slotId;
        const vehicleType = this.availableSlotsFilter.vehicleType;

        // Format date and time for display
        const formattedDate = new Date(bookingDate + 'T' + bookingTime).toLocaleString();
        const endTime = this.calculateEndTime(bookingDate, bookingTime, bookingDuration);
        const formattedEndTime = endTime.toLocaleString();

        // Confirm booking with details
        const confirmMessage = `Please confirm your booking:

Mall: ${mallName}
Slot: ${slotNumber}
Vehicle Type: ${vehicleType}
Start: ${formattedDate}
End: ${formattedEndTime}
Duration: ${bookingDuration} hour(s)`;

        if (!confirm(confirmMessage)) {
            return;
        }

        // Show loading state
        const bookButton = document.querySelector(`[data-slot-id="${slotId}"]`);
        if (bookButton) {
            bookButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Booking...';
            bookButton.disabled = true;
            bookButton.classList.add('opacity-50');
        }

        // Prepare booking data
        const startDateTime = new Date(bookingDate + 'T' + bookingTime);

        // Log the actual time being used for debugging
        console.log('Booking time details:', {
            inputDate: bookingDate,
            inputTime: bookingTime,
            parsedDateTime: startDateTime.toISOString(),
            localTime: startDateTime.toLocaleString()
        });

        const endDateTime = this.calculateEndTime(bookingDate, bookingTime, bookingDuration);

        // Build query parameters
        const params = new URLSearchParams();
        params.append('slot_id', slotId);
        params.append('start_time', startDateTime.toISOString());
        params.append('end_time', endDateTime.toISOString());
        params.append('duration', bookingDuration);

        console.log('Booking slot with parameters:', {
            slotId,
            startTime: startDateTime.toISOString(),
            endTime: endDateTime.toISOString(),
            duration: bookingDuration
        });

        // Call API to book slot
        fetch(`${API_BASE_URL}/bookings?${params.toString()}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId
            }
        })
        .then(response => {
            console.log('Booking response status:', response.status);

            // Try to parse the response even if it's an error
            return response.json().then(data => {
                if (!response.ok) {
                    throw new Error(`Failed to book slot: ${response.status} - ${data.detail || 'Unknown error'}`);
                }
                return data;
            });
        })
        .then(data => {
            console.log('Booking success:', data);

            // Show success message
            alert('Slot booked successfully!');

            // Refresh both available slots and bookings
            this.fetchAvailableSlots();
            this.fetchBookings();

            // Switch to bookings tab to show the new booking
            this.setActiveTab('bookings');

            // Notify chat interface to update
            if (window.chatInterfaceComponent) {
                // Format dates with 12-hour clock
                const formatOptions = {
                    year: 'numeric',
                    month: 'numeric',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: 'numeric',
                    hour12: true
                };
                const startTime = new Date(data.start_time).toLocaleString(undefined, formatOptions);
                const endTime = new Date(data.end_time).toLocaleString(undefined, formatOptions);

                window.chatInterfaceComponent.addAssistantMessage(`
                    <div class="booking-confirmation">
                        <p><i class="fas fa-check-circle text-green-500 mr-1"></i> <strong>Manual Booking Confirmed!</strong></p>
                        <p class="mt-2">I've recorded your manual booking for Slot ${data.slot_number} at ${data.mall_name}.</p>
                        <p class="mt-1"><strong>Start:</strong> ${startTime}</p>
                        <p class="mt-1"><strong>End:</strong> ${endTime}</p>
                        <p class="mt-1"><strong>Total:</strong> ₹${data.total_amount}</p>
                        <p class="mt-3">You can view and manage this booking in the Bookings tab.</p>
                    </div>
                `, 'html');
            }
        })
        .catch(error => {
            console.error('Error booking slot:', error);

            // Show a more detailed error message
            let errorMessage = 'Failed to book slot. Please try again.';

            // Extract more specific error message if available
            if (error.message && error.message.includes('Failed to book slot:')) {
                errorMessage = error.message;
            }

            alert(errorMessage);

            // Reset button state
            if (bookButton) {
                bookButton.innerHTML = '<i class="fas fa-ticket-alt mr-1"></i> Book';
                bookButton.disabled = false;
                bookButton.classList.remove('opacity-50');
            }
        });
    }

    findSlotById(slotId) {
        // Find a slot by its ID in the current slots data
        const availableSlotsList = document.getElementById('availableSlotsList');
        if (!availableSlotsList) return null;

        // Find the button with the matching slot ID
        const slotButton = availableSlotsList.querySelector(`[data-slot-id="${slotId}"]`);
        if (!slotButton) return null;

        // Get the slot card element
        const slotCard = slotButton.closest('.slot-card-horizontal');
        if (!slotCard) return null;

        // Extract slot information from the card
        const slotNumber = slotCard.querySelector('.slot-card-header').textContent.trim().replace('Slot ', '');
        const mallName = slotCard.closest('.mb-6').querySelector('h4').textContent.trim();

        return {
            id: slotId,
            slot_number: slotNumber,
            mall_name: mallName
        };
    }

    calculateEndTime(date, time, durationHours) {
        // Calculate the end time based on start date, time and duration
        try {
            // Ensure we have valid inputs
            if (!date || !time || !durationHours) {
                console.error('Missing required parameters for calculateEndTime:', { date, time, durationHours });
                // Return a default end time (2 hours from now)
                const defaultEnd = new Date();
                defaultEnd.setHours(defaultEnd.getHours() + 2);
                return defaultEnd;
            }

            // Parse duration as integer
            const duration = parseInt(durationHours);
            if (isNaN(duration) || duration <= 0) {
                console.error('Invalid duration:', durationHours);
                // Default to 2 hours
                durationHours = 2;
            }

            // Create a proper ISO datetime string
            const isoDateTimeString = `${date}T${time}`;
            console.log('Creating date from:', isoDateTimeString);

            // Create the start date object
            const startDateTime = new Date(isoDateTimeString);

            // Validate the start date
            if (isNaN(startDateTime.getTime())) {
                console.error('Invalid start date/time:', { date, time, isoDateTimeString });
                // Return a default end time (2 hours from now)
                const defaultEnd = new Date();
                defaultEnd.setHours(defaultEnd.getHours() + 2);
                return defaultEnd;
            }

            // Create a new date object for the end time
            const endDateTime = new Date(startDateTime);

            // Add the duration in hours
            endDateTime.setHours(endDateTime.getHours() + duration);

            console.log('Time calculation:', {
                startDate: date,
                startTime: time,
                duration: durationHours,
                startDateTime: startDateTime.toISOString(),
                endDateTime: endDateTime.toISOString(),
                startLocal: startDateTime.toLocaleString(),
                endLocal: endDateTime.toLocaleString(),
                startTimestamp: startDateTime.getTime(),
                endTimestamp: endDateTime.getTime(),
                durationMs: endDateTime.getTime() - startDateTime.getTime()
            });

            // Verify that end time is after start time
            if (endDateTime <= startDateTime) {
                console.error('End time is not after start time:', { startDateTime, endDateTime });
                // Force end time to be 2 hours after start time
                endDateTime.setHours(startDateTime.getHours() + 2);
            }

            return endDateTime;
        } catch (error) {
            console.error('Error in calculateEndTime:', error);
            // Return a default end time (2 hours from now)
            const defaultEnd = new Date();
            defaultEnd.setHours(defaultEnd.getHours() + 2);
            return defaultEnd;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.parkingInfoComponent = new ParkingInfoComponent();
});