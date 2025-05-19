document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    const userId = localStorage.getItem('userId');
    if (userId) {
        // Redirect to main application
        window.location.href = 'index.html';
        return;
    }

    // Login button click handler
    const loginButton = document.getElementById('loginButton');
    const userIdInput = document.getElementById('userId');
    const userNameInput = document.getElementById('userName');
    const loginError = document.getElementById('loginError');

    loginButton.addEventListener('click', function() {
        handleLogin();
    });

    // Also handle Enter key press
    userIdInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleLogin();
        }
    });

    // Demo user buttons
    const demoUserButtons = document.querySelectorAll('.demo-user-button');
    demoUserButtons.forEach(button => {
        button.addEventListener('click', function() {
            const demoUserId = this.getAttribute('data-userid');
            const demoUserName = this.getAttribute('data-username');
            userIdInput.value = demoUserId;
            userNameInput.value = demoUserName;
            handleLogin();
        });
    });

    function handleLogin() {
        const userId = userIdInput.value.trim();
        const userName = userNameInput.value.trim();

        if (!userId) {
            showError('Please enter a User ID');
            return;
        }

        if (!userName) {
            showError('Please enter your name');
            return;
        }

        // Validate user ID (simple validation for demo)
        if (!/^[a-zA-Z0-9_-]+$/.test(userId)) {
            showError('User ID can only contain letters, numbers, underscores, and hyphens');
            return;
        }

        // Store user ID and name in localStorage
        localStorage.setItem('userId', userId);
        localStorage.setItem('userName', userName);

        // Check if user exists in the backend
        validateUser(userId)
            .then(valid => {
                if (valid) {
                    // Redirect to main application
                    window.location.href = 'index.html';
                } else {
                    showError('Invalid User ID. Please try again.');
                    localStorage.removeItem('userId');
                }
            })
            .catch(error => {
                console.error('Error validating user:', error);
                // Show a more helpful error message
                showError('Could not connect to the server. Please check your connection and try again.');
                localStorage.removeItem('userId');
            });
    }

    function showError(message) {
        loginError.textContent = message;
        loginError.style.opacity = 1;

        // Shake animation for error
        userIdInput.classList.add('shake');
        setTimeout(() => {
            userIdInput.classList.remove('shake');
        }, 500);
    }

    async function validateUser(userId) {
        try {
            // For demo purposes, we'll consider all user IDs valid
            // In a real application, you would validate against your backend
            return true;

            // Example of how to validate with backend:
            // const response = await fetch(`${API_BASE_URL}/users/validate`, {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json'
            //     },
            //     body: JSON.stringify({ userId })
            // });
            // return response.ok;
        } catch (error) {
            console.error('Error validating user:', error);
            return true; // For demo, return true even on error
        }
    }
});
