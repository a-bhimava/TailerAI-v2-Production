/**
 * Authentication Management for TailerAI v2.0
 * Handles user authentication, session management, and auth UI
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthModalOpen = false;
        this.isLoginMode = true;
        this.initializeAuth();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    async initializeAuth() {
        // Check if user is already authenticated
        if (window.api.isAuthenticated()) {
            try {
                await this.loadCurrentUser();
                this.showAuthenticatedApp();
            } catch (error) {
                console.error('Failed to load current user:', error);
                this.showAuthModal();
            }
        } else {
            this.showAuthModal();
        }

        // Set up event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Auth form submission
        const authForm = document.getElementById('auth-form');
        if (authForm) {
            authForm.addEventListener('submit', this.handleAuthSubmit.bind(this));
        }

        // Auth modal events
        document.addEventListener('click', (e) => {
            if (e.target.id === 'auth-modal') {
                this.closeAuthModal();
            }
        });

        // Global auth events
        window.addEventListener('auth:logout', this.handleLogout.bind(this));
        window.addEventListener('auth:login', this.handleLoginSuccess.bind(this));

        // User menu toggle
        const userMenu = document.getElementById('user-menu');
        if (userMenu) {
            userMenu.addEventListener('click', this.toggleUserMenu.bind(this));
        }

        // Close user menu when clicking outside
        document.addEventListener('click', (e) => {
            const userMenu = document.getElementById('user-menu');
            const userDropdown = document.getElementById('user-dropdown');
            
            if (userMenu && userDropdown && !userMenu.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }

    // =============================================================================
    // USER MANAGEMENT
    // =============================================================================

    async loadCurrentUser() {
        try {
            this.currentUser = await window.api.getCurrentUser();
            this.updateUserUI();
            return this.currentUser;
        } catch (error) {
            console.error('Failed to load current user:', error);
            throw error;
        }
    }

    updateUserUI() {
        if (!this.currentUser) return;

        // Update user initials
        const userInitials = document.getElementById('user-initials');
        if (userInitials) {
            const initials = this.getInitials(this.currentUser.full_name || this.currentUser.email);
            userInitials.textContent = initials;
        }

        // Update user name and email in dropdown
        const userName = document.getElementById('user-name');
        const userEmail = document.getElementById('user-email');
        
        if (userName) {
            userName.textContent = this.currentUser.full_name || 'User';
        }
        
        if (userEmail) {
            userEmail.textContent = this.currentUser.email;
        }
    }

    getInitials(name) {
        if (!name) return 'U';
        
        return name
            .split(' ')
            .map(part => part.charAt(0).toUpperCase())
            .slice(0, 2)
            .join('');
    }

    // =============================================================================
    // AUTH MODAL MANAGEMENT
    // =============================================================================

    showAuthModal() {
        const modal = document.getElementById('auth-modal');
        const app = document.getElementById('app');
        
        if (modal) {
            modal.classList.add('active');
            this.isAuthModalOpen = true;
        }
        
        if (app) {
            app.style.display = 'none';
        }
    }

    closeAuthModal() {
        const modal = document.getElementById('auth-modal');
        
        if (modal) {
            modal.classList.remove('active');
            this.isAuthModalOpen = false;
        }
    }

    showAuthenticatedApp() {
        const modal = document.getElementById('auth-modal');
        const app = document.getElementById('app');
        const loadingScreen = document.getElementById('loading-screen');
        
        if (modal) {
            modal.classList.remove('active');
            this.isAuthModalOpen = false;
        }
        
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
        
        if (app) {
            app.style.display = 'block';
        }
    }

    toggleAuthMode() {
        this.isLoginMode = !this.isLoginMode;
        this.updateAuthModalUI();
    }

    updateAuthModalUI() {
        const title = document.getElementById('auth-title');
        const submitBtn = document.getElementById('auth-submit');
        const switchText = document.getElementById('auth-switch-text');
        const switchBtn = document.getElementById('auth-switch-btn');
        const confirmPasswordGroup = document.getElementById('confirm-password-group');

        if (this.isLoginMode) {
            if (title) title.textContent = 'Sign In';
            if (submitBtn) submitBtn.textContent = 'Sign In';
            if (switchText) switchText.textContent = "Don't have an account?";
            if (switchBtn) switchBtn.textContent = 'Create Account';
            if (confirmPasswordGroup) confirmPasswordGroup.style.display = 'none';
        } else {
            if (title) title.textContent = 'Create Account';
            if (submitBtn) submitBtn.textContent = 'Create Account';
            if (switchText) switchText.textContent = 'Already have an account?';
            if (switchBtn) switchBtn.textContent = 'Sign In';
            if (confirmPasswordGroup) confirmPasswordGroup.style.display = 'block';
        }
    }

    // =============================================================================
    // AUTH FORM HANDLING
    // =============================================================================

    async handleAuthSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const email = formData.get('email');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirm-password');

        // Basic validation
        if (!email || !password) {
            window.notifications.show('Please fill in all required fields', 'error');
            return;
        }

        if (!this.isLoginMode) {
            if (password !== confirmPassword) {
                window.notifications.show('Passwords do not match', 'error');
                return;
            }
            
            if (password.length < 8) {
                window.notifications.show('Password must be at least 8 characters long', 'error');
                return;
            }
        }

        // Disable form during submission
        const submitBtn = document.getElementById('auth-submit');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = this.isLoginMode ? 'Signing In...' : 'Creating Account...';

        try {
            if (this.isLoginMode) {
                await this.login(email, password);
            } else {
                await this.register(email, password);
            }
        } catch (error) {
            console.error('Auth error:', error);
            
            let errorMessage = 'Authentication failed';
            if (error instanceof APIError) {
                if (error.status === 401) {
                    errorMessage = 'Invalid email or password';
                } else if (error.status === 422) {
                    // Handle 422 validation errors properly
                    if (error.details && error.details.detail) {
                        if (Array.isArray(error.details.detail)) {
                            // FastAPI validation errors are arrays
                            errorMessage = error.details.detail.map(err => err.msg || err.message || String(err)).join(', ');
                        } else if (typeof error.details.detail === 'string') {
                            errorMessage = error.details.detail;
                        } else {
                            errorMessage = String(error.details.detail);
                        }
                    } else {
                        errorMessage = 'Invalid input data. Please check your information.';
                    }
                } else if (error.status === 409) {
                    errorMessage = 'An account with this email already exists';
                } else if (error.isServerError()) {
                    errorMessage = 'Server error. Please try again later.';
                } else if (error.isNetworkError()) {
                    errorMessage = 'Network error. Please check your connection.';
                } else {
                    errorMessage = error.message || 'Authentication failed';
                }
            } else {
                errorMessage = error.message || 'Authentication failed';
            }
            
            window.notifications.show(errorMessage, 'error');
        } finally {
            // Re-enable form
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    async login(email, password) {
        try {
            const response = await window.api.login(email, password);
            await this.handleLoginSuccess();
            window.notifications.show('Successfully signed in!', 'success');
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    async register(email, password) {
        try {
            // Extract name from email for basic registration
            const fullName = email.split('@')[0].replace(/[._]/g, ' ');
            
            const response = await window.api.register(email, password, fullName);
            
            if (response.access_token) {
                // Auto-login after successful registration
                await this.handleLoginSuccess();
                window.notifications.show('Account created successfully!', 'success');
            } else {
                // Email verification required
                window.notifications.show('Account created! Please check your email for verification.', 'info');
                this.toggleAuthMode(); // Switch to login mode
            }
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    }

    async handleLoginSuccess() {
        try {
            await this.loadCurrentUser();
            this.showAuthenticatedApp();
            
            // Initialize dashboard data
            if (window.dashboard) {
                await window.dashboard.loadDashboardData();
            }
            
            // Navigate to master dataset (main page)
            if (window.navigation) {
                window.navigation.navigateTo('master-dataset');
            }
            
        } catch (error) {
            console.error('Post-login initialization failed:', error);
            window.notifications.show('Login successful, but failed to load user data', 'warning');
        }
    }

    async handleLogout() {
        try {
            await window.api.logout();
        } catch (error) {
            console.error('Logout request failed:', error);
        } finally {
            this.currentUser = null;
            this.showAuthModal();
            window.notifications.show('You have been signed out', 'info');
        }
    }

    // =============================================================================
    // USER MENU
    // =============================================================================

    toggleUserMenu(event) {
        event.stopPropagation();
        const userDropdown = document.getElementById('user-dropdown');
        
        if (userDropdown) {
            userDropdown.classList.toggle('active');
        }
    }

    // =============================================================================
    // PUBLIC METHODS
    // =============================================================================

    isAuthenticated() {
        return !!this.currentUser && window.api.isAuthenticated();
    }

    getCurrentUser() {
        return this.currentUser;
    }

    async refreshUserData() {
        if (this.isAuthenticated()) {
            await this.loadCurrentUser();
        }
    }

    // =============================================================================
    // GOOGLE OAUTH METHODS
    // =============================================================================

    async handleGoogleSignIn(response) {
        try {
            if (!response || !response.credential) {
                throw new Error('Invalid Google response: missing credential');
            }

            console.log('Google Sign-In response received');
            const googleToken = response.credential;
            
            // Show loading state
            const googleContainer = document.querySelector('.google-auth-container');
            if (googleContainer) {
                googleContainer.style.opacity = '0.7';
                googleContainer.style.pointerEvents = 'none';
            }
            
            // Call our backend OAuth endpoint
            await window.api.googleAuth(googleToken);
            await this.handleLoginSuccess();
            window.notifications.show('Successfully signed in with Google!', 'success');
            
        } catch (error) {
            console.error('Google Sign-In failed:', error);
            
            let errorMessage = 'Google Sign-In failed';
            if (error instanceof APIError) {
                if (error.status === 401) {
                    errorMessage = 'Google authentication failed. Please try again.';
                } else if (error.status === 422) {
                    errorMessage = 'Invalid Google token. Please try again.';
                } else if (error.isNetworkError()) {
                    errorMessage = 'Network error. Please check your connection.';
                } else if (error.isServerError()) {
                    errorMessage = 'Server error. Please try again later.';
                } else {
                    errorMessage = error.message || 'Google Sign-In failed';
                }
            } else {
                errorMessage = error.message || 'Google Sign-In failed';
            }
            
            window.notifications.show(errorMessage, 'error');
            
        } finally {
            // Restore UI state
            const googleContainer = document.querySelector('.google-auth-container');
            if (googleContainer) {
                googleContainer.style.opacity = '';
                googleContainer.style.pointerEvents = '';
            }
        }
    }
}

// =============================================================================
// GLOBAL AUTH MANAGER
// =============================================================================

// Create global auth manager instance
window.auth = new AuthManager();

// =============================================================================
// GLOBAL AUTH FUNCTIONS (for HTML onclick handlers)
// =============================================================================

function toggleAuthMode() {
    window.auth.toggleAuthMode();
}

function closeAuthModal() {
    window.auth.closeAuthModal();
}

async function logout() {
    await window.auth.handleLogout();
}

async function handleGoogleSignIn(response) {
    await window.auth.handleGoogleSignIn(response);
}

function handleGoogleSignInError(error) {
    console.error('Google Sign-In error:', error);
    window.notifications.show('Google Sign-In configuration error. Please check that localhost:8002 is added to your Google OAuth authorized origins.', 'error');
}

function initiateGoogleRedirect() {
    const clientId = '1008899385069-rjplcqd5q2ml6504f5epmd720uth9tme.apps.googleusercontent.com';
    const redirectUri = `${window.location.origin}/auth/google/callback`;
    const scope = 'openid email profile';
    const responseType = 'code';
    const state = Math.random().toString(36).substring(2, 15);
    
    // Store state for validation
    sessionStorage.setItem('google_oauth_state', state);
    
    const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
        `client_id=${encodeURIComponent(clientId)}&` +
        `redirect_uri=${encodeURIComponent(redirectUri)}&` +
        `scope=${encodeURIComponent(scope)}&` +
        `response_type=${encodeURIComponent(responseType)}&` +
        `state=${encodeURIComponent(state)}`;
    
    window.location.href = googleAuthUrl;
}