/**
 * API Utility Functions
 *
 * This file contains utility functions for making API calls with consistent headers
 * and error handling.
 */

// API Base URL is defined in config.js

/**
 * Make an authenticated API request
 *
 * @param {string} endpoint - The API endpoint (without base URL)
 * @param {Object} options - Fetch options (method, body, etc.)
 * @returns {Promise} - Fetch promise
 */
async function apiRequest(endpoint, options = {}) {
    // Get user ID from localStorage
    const userId = localStorage.getItem('userId');
    if (!userId) {
        throw new Error('User not authenticated');
    }

    // Prepare headers
    const headers = {
        'X-User-ID': userId,
        ...options.headers
    };

    // If sending JSON data, add Content-Type header
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    // Make the request
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        // Check if response is OK
        if (!response.ok) {
            // Try to parse error response as JSON
            let errorMessage = `API error: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                } else if (errorData.message) {
                    errorMessage = errorData.message;
                } else if (typeof errorData === 'string') {
                    errorMessage = errorData;
                }
            } catch (parseError) {
                // If we can't parse JSON, use the default error message
                console.warn('Could not parse error response as JSON:', parseError);
            }

            // Create a custom error with additional properties
            const apiError = new Error(errorMessage);
            apiError.status = response.status;
            apiError.statusText = response.statusText;
            apiError.endpoint = endpoint;
            throw apiError;
        }

        // Parse JSON response
        return await response.json();
    } catch (error) {
        // Log the error with more context
        if (error.endpoint) {
            console.error(`API Error (${error.endpoint}):`, error.message, error.status || '');
        } else {
            console.error(`API Error (${endpoint}):`, error);
        }

        // Rethrow the error for the caller to handle
        throw error;
    }
}

/**
 * GET request
 *
 * @param {string} endpoint - The API endpoint
 * @param {Object} options - Additional fetch options
 * @returns {Promise} - Fetch promise
 */
async function apiGet(endpoint, options = {}) {
    return apiRequest(endpoint, { ...options, method: 'GET' });
}

/**
 * POST request
 *
 * @param {string} endpoint - The API endpoint
 * @param {Object} data - The data to send
 * @param {Object} options - Additional fetch options
 * @returns {Promise} - Fetch promise
 */
async function apiPost(endpoint, data = {}, options = {}) {
    return apiRequest(endpoint, {
        ...options,
        method: 'POST',
        body: data
    });
}

/**
 * PUT request
 *
 * @param {string} endpoint - The API endpoint
 * @param {Object} data - The data to send
 * @param {Object} options - Additional fetch options
 * @returns {Promise} - Fetch promise
 */
async function apiPut(endpoint, data = {}, options = {}) {
    return apiRequest(endpoint, {
        ...options,
        method: 'PUT',
        body: data
    });
}

/**
 * DELETE request
 *
 * @param {string} endpoint - The API endpoint
 * @param {Object} options - Additional fetch options
 * @returns {Promise} - Fetch promise
 */
async function apiDelete(endpoint, options = {}) {
    return apiRequest(endpoint, { ...options, method: 'DELETE' });
}
