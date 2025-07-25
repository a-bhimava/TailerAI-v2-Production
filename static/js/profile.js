/**
 * Profile Management for TailerAI v2.0
 * Handles user profile editing and contact information management
 */

class ProfileManager {
    constructor() {
        this.currentProfile = null;
        this.isEditing = false;
        this.initializeProfile();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initializeProfile() {
        this.setupEventListeners();
        this.loadUserProfile();
    }

    setupEventListeners() {
        // Save profile button
        const saveBtn = document.getElementById('save-profile-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', this.saveProfile.bind(this));
        }

        // Cancel button
        const cancelBtn = document.getElementById('cancel-profile-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', this.cancelEdit.bind(this));
        }

        // Real-time preview updates
        const formInputs = [
            'profile-full-name',
            'profile-phone', 
            'profile-email',
            'profile-linkedin',
            'profile-location'
        ];

        formInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', this.updatePreview.bind(this));
            }
        });
    }

    // =============================================================================
    // PROFILE DATA MANAGEMENT
    // =============================================================================

    async loadUserProfile() {
        try {
            showNotification('Loading profile...', 'info');
            
            const response = await authenticatedFetch('/api/v2/master-dataset/profile');
            
            if (response.ok) {
                const data = await response.json();
                this.currentProfile = data.profile;
                this.populateForm(this.currentProfile);
                this.updatePreview();
                this.updateAccountInfo();
                showNotification('Profile loaded successfully', 'success');
            } else {
                throw new Error('Failed to load profile');
            }
        } catch (error) {
            console.error('Error loading profile:', error);
            showNotification('Failed to load profile. Please refresh the page.', 'error');
        }
    }

    populateForm(profile) {
        // Populate form fields
        const fields = {
            'profile-full-name': profile.full_name || '',
            'profile-email': profile.email || '',
            'profile-phone': profile.phone || '',
            'profile-linkedin': profile.linkedin_url || '',
            'profile-location': profile.location || ''
        };

        Object.entries(fields).forEach(([fieldId, value]) => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = value;
            }
        });
    }

    async saveProfile() {
        try {
            const saveBtn = document.getElementById('save-profile-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = 'Saving...';
            saveBtn.disabled = true;

            // Gather form data
            const formData = {
                full_name: document.getElementById('profile-full-name').value.trim(),
                email: document.getElementById('profile-email').value.trim(),
                phone: document.getElementById('profile-phone').value.trim(),
                linkedin_url: document.getElementById('profile-linkedin').value.trim(),
                location: document.getElementById('profile-location').value.trim()
            };

            // Validate required fields
            if (!formData.full_name) {
                throw new Error('Full name is required');
            }
            if (!formData.email) {
                throw new Error('Email is required');
            }

            // Validate LinkedIn URL format
            if (formData.linkedin_url && !this.isValidLinkedInUrl(formData.linkedin_url)) {
                throw new Error('Please enter a valid LinkedIn URL (e.g., https://linkedin.com/in/yourname)');
            }

            // Save to backend
            const response = await authenticatedFetch('/api/v2/master-dataset/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const updatedData = await response.json();
                this.currentProfile = updatedData.profile;
                this.updatePreview();
                this.updateAccountInfo();
                showNotification('Profile saved successfully! Your resume headers will now include complete contact information.', 'success');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to save profile');
            }

        } catch (error) {
            console.error('Error saving profile:', error);
            showNotification(error.message || 'Failed to save profile. Please try again.', 'error');
        } finally {
            const saveBtn = document.getElementById('save-profile-btn');
            saveBtn.textContent = 'Save Changes';
            saveBtn.disabled = false;
        }
    }

    cancelEdit() {
        if (this.currentProfile) {
            this.populateForm(this.currentProfile);
            this.updatePreview();
            showNotification('Changes cancelled', 'info');
        }
    }

    // =============================================================================
    // PREVIEW AND UI UPDATES
    // =============================================================================

    updatePreview() {
        const name = document.getElementById('profile-full-name').value.trim() || 'Your Name';
        const email = document.getElementById('profile-email').value.trim();
        const phone = document.getElementById('profile-phone').value.trim();
        const linkedin = document.getElementById('profile-linkedin').value.trim();
        const location = document.getElementById('profile-location').value.trim();

        // Update name preview
        const previewName = document.getElementById('preview-name');
        if (previewName) {
            previewName.textContent = name.toUpperCase();
        }

        // Build contact line (same logic as LaTeX service)
        const contactParts = [];
        
        if (phone) contactParts.push(phone);
        if (email) contactParts.push(email);
        if (linkedin) {
            const linkedinDisplay = linkedin.replace('https://', '').replace('http://', '');
            contactParts.push(linkedinDisplay);
        }
        if (location) contactParts.push(location);

        const contactLine = contactParts.length > 0 ? contactParts.join(' | ') : 'Contact information will appear here';

        // Update contact preview
        const previewContact = document.getElementById('preview-contact');
        if (previewContact) {
            previewContact.textContent = contactLine;
            
            // Add styling based on completeness
            if (contactParts.length >= 3) {
                previewContact.classList.add('complete');
                previewContact.classList.remove('incomplete');
            } else {
                previewContact.classList.add('incomplete');
                previewContact.classList.remove('complete');
            }
        }
    }

    updateAccountInfo() {
        if (!this.currentProfile) return;

        // Update member since date
        const memberSinceEl = document.getElementById('member-since');
        if (memberSinceEl && this.currentProfile.created_at) {
            const createdDate = new Date(this.currentProfile.created_at);
            memberSinceEl.textContent = createdDate.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }

        // Update profile completion
        this.updateProfileCompletion();
    }

    updateProfileCompletion() {
        if (!this.currentProfile) return;

        const requiredFields = ['full_name', 'email', 'phone', 'linkedin_url', 'location'];
        const completedFields = requiredFields.filter(field => 
            this.currentProfile[field] && this.currentProfile[field].trim() !== ''
        );

        const completionPercentage = Math.round((completedFields.length / requiredFields.length) * 100);

        // Update completion bar
        const fillEl = document.getElementById('profile-completion-fill');
        const textEl = document.getElementById('profile-completion-text');

        if (fillEl) {
            fillEl.style.width = `${completionPercentage}%`;
        }
        if (textEl) {
            textEl.textContent = `${completionPercentage}%`;
        }

        // Add completion status class
        const completionBar = document.querySelector('.completion-bar');
        if (completionBar) {
            completionBar.className = 'completion-bar';
            if (completionPercentage === 100) {
                completionBar.classList.add('complete');
            } else if (completionPercentage >= 60) {
                completionBar.classList.add('good');
            } else {
                completionBar.classList.add('needs-work');
            }
        }
    }

    // =============================================================================
    // VALIDATION HELPERS
    // =============================================================================

    isValidLinkedInUrl(url) {
        const linkedinPattern = /^https?:\/\/(www\.)?linkedin\.com\/in\/[\w-]+\/?$/;
        return linkedinPattern.test(url);
    }

    // =============================================================================
    // PUBLIC API
    // =============================================================================

    getCurrentProfile() {
        return this.currentProfile;
    }

    refreshProfile() {
        return this.loadUserProfile();
    }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

// Global instance
let profileManager = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('profile-view')) {
        profileManager = new ProfileManager();
    }
});

// Make available globally
window.ProfileManager = ProfileManager;
window.getProfileManager = () => profileManager;