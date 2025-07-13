/**
 * Notification System for TailerAI v2.0
 * Handles toast notifications, alerts, and user feedback
 */

class NotificationManager {
    constructor() {
        this.notifications = new Map();
        this.nextId = 1;
        this.maxNotifications = 5;
        this.defaultDuration = 5000; // 5 seconds
        this.container = null;
        
        this.initializeNotifications();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initializeNotifications() {
        this.createContainer();
        this.setupGlobalErrorHandling();
    }

    createContainer() {
        this.container = document.getElementById('notifications');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notifications';
            this.container.className = 'notifications-container';
            document.body.appendChild(this.container);
        }
    }

    setupGlobalErrorHandling() {
        // Handle uncaught JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.show('An unexpected error occurred', 'error');
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.show('An unexpected error occurred', 'error');
        });

        // Handle API errors
        window.addEventListener('api:error', (event) => {
            const error = event.detail;
            let message = 'Request failed';
            
            if (error instanceof APIError) {
                if (error.isNetworkError()) {
                    message = 'Network error. Please check your connection.';
                } else if (error.isServerError()) {
                    message = 'Server error. Please try again later.';
                } else {
                    message = error.message;
                }
            }
            
            this.show(message, 'error');
        });
    }

    // =============================================================================
    // NOTIFICATION CREATION
    // =============================================================================

    show(message, type = 'info', options = {}) {
        const id = this.nextId++;
        const notification = this.createNotification(id, message, type, options);
        
        // Remove oldest notifications if we exceed the limit
        this.enforceMaxNotifications();
        
        // Add to container and show
        this.container.appendChild(notification.element);
        this.notifications.set(id, notification);
        
        // Trigger show animation
        setTimeout(() => {
            notification.element.classList.add('show');
        }, 100);
        
        // Auto-remove after duration (unless persistent)
        if (!options.persistent) {
            const duration = options.duration || this.getDurationForType(type);
            setTimeout(() => {
                this.remove(id);
            }, duration);
        }
        
        return id;
    }

    createNotification(id, message, type, options) {
        const element = document.createElement('div');
        element.className = `notification ${type}`;
        element.setAttribute('data-notification-id', id);
        
        const icon = this.getIconForType(type);
        const title = options.title || this.getTitleForType(type);
        
        element.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                ${title ? `<div class="notification-title">${this.escapeHtml(title)}</div>` : ''}
                <div class="notification-message">${this.escapeHtml(message)}</div>
            </div>
            <button class="notification-close" aria-label="Close notification">&times;</button>
        `;
        
        // Add close button functionality
        const closeBtn = element.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.remove(id);
        });
        
        // Add click-to-dismiss (optional)
        if (options.clickToDismiss !== false) {
            element.addEventListener('click', (e) => {
                if (e.target !== closeBtn) {
                    this.remove(id);
                }
            });
        }
        
        return {
            id,
            element,
            type,
            message,
            createdAt: Date.now()
        };
    }

    // =============================================================================
    // NOTIFICATION TYPES
    // =============================================================================

    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', { 
            duration: 8000, // Errors stay longer
            ...options 
        });
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    loading(message, options = {}) {
        return this.show(message, 'loading', { 
            persistent: true,
            clickToDismiss: false,
            ...options 
        });
    }

    // =============================================================================
    // NOTIFICATION MANAGEMENT
    // =============================================================================

    remove(id) {
        const notification = this.notifications.get(id);
        if (!notification) return false;
        
        // Fade out animation
        notification.element.classList.remove('show');
        
        // Remove from DOM after animation
        setTimeout(() => {
            if (notification.element.parentNode) {
                notification.element.parentNode.removeChild(notification.element);
            }
            this.notifications.delete(id);
        }, 300);
        
        return true;
    }

    removeAll() {
        const ids = Array.from(this.notifications.keys());
        ids.forEach(id => this.remove(id));
    }

    removeByType(type) {
        const notifications = Array.from(this.notifications.values());
        const toRemove = notifications.filter(n => n.type === type);
        toRemove.forEach(n => this.remove(n.id));
    }

    update(id, message, type = null) {
        const notification = this.notifications.get(id);
        if (!notification) return false;
        
        const messageElement = notification.element.querySelector('.notification-message');
        if (messageElement) {
            messageElement.textContent = message;
            notification.message = message;
        }
        
        if (type && type !== notification.type) {
            notification.element.className = `notification ${type} show`;
            notification.type = type;
            
            // Update icon
            const iconElement = notification.element.querySelector('.notification-icon');
            if (iconElement) {
                iconElement.textContent = this.getIconForType(type);
            }
        }
        
        return true;
    }

    enforceMaxNotifications() {
        const notifications = Array.from(this.notifications.values());
        if (notifications.length >= this.maxNotifications) {
            // Remove oldest non-persistent notification
            const oldestRemovable = notifications
                .sort((a, b) => a.createdAt - b.createdAt)
                .find(n => !n.persistent);
                
            if (oldestRemovable) {
                this.remove(oldestRemovable.id);
            }
        }
    }

    // =============================================================================
    // UTILITY METHODS
    // =============================================================================

    getIconForType(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️',
            loading: '⏳'
        };
        return icons[type] || icons.info;
    }

    getTitleForType(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: null, // No title for info
            loading: 'Loading'
        };
        return titles[type];
    }

    getDurationForType(type) {
        const durations = {
            success: 4000,
            error: 8000,
            warning: 6000,
            info: 5000,
            loading: 0 // Persistent by default
        };
        return durations[type] || this.defaultDuration;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // =============================================================================
    // SPECIALIZED NOTIFICATIONS
    // =============================================================================

    confirmAction(message, onConfirm, onCancel = null) {
        const confirmId = this.show(message, 'warning', {
            persistent: true,
            clickToDismiss: false,
            title: 'Confirm Action'
        });
        
        // Add custom buttons
        const notification = this.notifications.get(confirmId);
        if (notification) {
            const buttonsHtml = `
                <div class="notification-buttons">
                    <button class="btn btn-sm btn-primary confirm-btn">Confirm</button>
                    <button class="btn btn-sm btn-secondary cancel-btn">Cancel</button>
                </div>
            `;
            
            notification.element.querySelector('.notification-content').insertAdjacentHTML('beforeend', buttonsHtml);
            
            // Add button event listeners
            const confirmBtn = notification.element.querySelector('.confirm-btn');
            const cancelBtn = notification.element.querySelector('.cancel-btn');
            
            confirmBtn.addEventListener('click', () => {
                this.remove(confirmId);
                if (onConfirm) onConfirm();
            });
            
            cancelBtn.addEventListener('click', () => {
                this.remove(confirmId);
                if (onCancel) onCancel();
            });
        }
        
        return confirmId;
    }

    showProgress(message, progress = 0) {
        const progressId = this.show(message, 'loading', {
            persistent: true,
            clickToDismiss: false
        });
        
        // Add progress bar
        const notification = this.notifications.get(progressId);
        if (notification) {
            const progressHtml = `
                <div class="notification-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <div class="progress-text">${Math.round(progress)}%</div>
                </div>
            `;
            
            notification.element.querySelector('.notification-content').insertAdjacentHTML('beforeend', progressHtml);
        }
        
        return progressId;
    }

    updateProgress(id, progress, message = null) {
        const notification = this.notifications.get(id);
        if (!notification) return false;
        
        const progressFill = notification.element.querySelector('.progress-fill');
        const progressText = notification.element.querySelector('.progress-text');
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }
        
        if (message) {
            this.update(id, message);
        }
        
        // Auto-remove when complete
        if (progress >= 100) {
            setTimeout(() => {
                this.remove(id);
            }, 2000);
        }
        
        return true;
    }

    // =============================================================================
    // API INTEGRATION HELPERS
    // =============================================================================

    handleApiError(error) {
        let message = 'An error occurred';
        
        if (error instanceof APIError) {
            if (error.isNetworkError()) {
                message = 'Network error. Please check your connection.';
            } else if (error.isAuthError()) {
                message = 'Authentication required. Please sign in.';
            } else if (error.isValidationError()) {
                message = error.details?.detail || 'Invalid input data';
            } else if (error.isServerError()) {
                message = 'Server error. Please try again later.';
            } else {
                message = error.message;
            }
        } else {
            message = error.message || 'An unexpected error occurred';
        }
        
        this.error(message);
    }

    handleApiSuccess(message = 'Operation completed successfully') {
        this.success(message);
    }
}

// =============================================================================
// GLOBAL NOTIFICATION MANAGER
// =============================================================================

// Create global notification manager instance
window.notifications = new NotificationManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}