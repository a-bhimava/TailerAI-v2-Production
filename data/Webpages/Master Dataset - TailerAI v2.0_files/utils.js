/**
 * Utility Functions for TailerAI v2.0
 * Common helper functions and utilities
 */

// =============================================================================
// DOM UTILITIES
// =============================================================================

const DOM = {
    /**
     * Get element by ID with error handling
     */
    get(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    },

    /**
     * Query selector with error handling
     */
    query(selector, parent = document) {
        try {
            return parent.querySelector(selector);
        } catch (error) {
            console.warn(`Invalid selector: ${selector}`, error);
            return null;
        }
    },

    /**
     * Query all with error handling
     */
    queryAll(selector, parent = document) {
        try {
            return Array.from(parent.querySelectorAll(selector));
        } catch (error) {
            console.warn(`Invalid selector: ${selector}`, error);
            return [];
        }
    },

    /**
     * Create element with attributes and content
     */
    create(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (content) {
            element.innerHTML = content;
        }
        
        return element;
    },

    /**
     * Show/hide elements
     */
    show(element, display = 'block') {
        if (element) {
            element.style.display = display;
        }
    },

    hide(element) {
        if (element) {
            element.style.display = 'none';
        }
    },

    /**
     * Toggle element visibility
     */
    toggle(element, forceShow = null) {
        if (!element) return;
        
        const isHidden = element.style.display === 'none' || 
                        window.getComputedStyle(element).display === 'none';
        
        if (forceShow === true || (forceShow === null && isHidden)) {
            this.show(element);
        } else {
            this.hide(element);
        }
    },

    /**
     * Add event listener with automatic cleanup
     */
    on(element, event, handler, options = {}) {
        if (!element) return null;
        
        element.addEventListener(event, handler, options);
        
        // Return cleanup function
        return () => {
            element.removeEventListener(event, handler, options);
        };
    }
};

// =============================================================================
// STRING UTILITIES
// =============================================================================

const StringUtils = {
    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        if (!text) return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Remove HTML tags from string
     */
    stripHtml(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    },

    /**
     * Truncate string with ellipsis
     */
    truncate(text, maxLength, suffix = '...') {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + suffix;
    },

    /**
     * Convert string to title case
     */
    toTitleCase(text) {
        if (!text) return '';
        
        return text.replace(/\w\S*/g, (txt) => 
            txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
        );
    },

    /**
     * Convert string to kebab-case
     */
    toKebabCase(text) {
        if (!text) return '';
        
        return text
            .replace(/([a-z])([A-Z])/g, '$1-$2')
            .replace(/\s+/g, '-')
            .toLowerCase();
    },

    /**
     * Generate random string
     */
    randomString(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// =============================================================================
// DATE UTILITIES
// =============================================================================

const DateUtils = {
    /**
     * Format date with options
     */
    format(date, options = {}) {
        if (!date) return '';
        
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        
        try {
            const dateObj = typeof date === 'string' ? new Date(date) : date;
            return dateObj.toLocaleDateString('en-US', { ...defaultOptions, ...options });
        } catch (error) {
            console.warn('Invalid date:', date);
            return '';
        }
    },

    /**
     * Format date range
     */
    formatRange(startDate, endDate) {
        const start = this.format(startDate, { year: 'numeric', month: 'short' });
        const end = endDate ? this.format(endDate, { year: 'numeric', month: 'short' }) : 'Present';
        return `${start} - ${end}`;
    },

    /**
     * Get relative time (e.g., "2 hours ago")
     */
    getRelativeTime(date) {
        if (!date) return '';
        
        const now = new Date();
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        const diffMs = now - dateObj;
        
        const diffSeconds = Math.floor(diffMs / 1000);
        const diffMinutes = Math.floor(diffSeconds / 60);
        const diffHours = Math.floor(diffMinutes / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffSeconds < 60) return 'just now';
        if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return this.format(date);
    },

    /**
     * Check if date is today
     */
    isToday(date) {
        if (!date) return false;
        
        const today = new Date();
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        
        return today.toDateString() === dateObj.toDateString();
    },

    /**
     * Get ISO date string for input[type="date"]
     */
    toISODateString(date) {
        if (!date) return '';
        
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        return dateObj.toISOString().split('T')[0];
    }
};

// =============================================================================
// VALIDATION UTILITIES
// =============================================================================

const Validation = {
    /**
     * Email validation
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Phone validation (basic)
     */
    isValidPhone(phone) {
        const phoneRegex = /^[\+]?[\d\s\-\(\)]{10,}$/;
        return phoneRegex.test(phone);
    },

    /**
     * URL validation
     */
    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    /**
     * Password strength check
     */
    checkPasswordStrength(password) {
        const criteria = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };
        
        const score = Object.values(criteria).filter(Boolean).length;
        
        return {
            score,
            criteria,
            strength: score < 3 ? 'weak' : score < 5 ? 'medium' : 'strong'
        };
    },

    /**
     * Required field validation
     */
    isRequired(value) {
        return value !== null && value !== undefined && value.toString().trim() !== '';
    },

    /**
     * Number range validation
     */
    isInRange(value, min, max) {
        const num = parseFloat(value);
        return !isNaN(num) && num >= min && num <= max;
    }
};

// =============================================================================
// PERFORMANCE UTILITIES
// =============================================================================

const Performance = {
    /**
     * Debounce function
     */
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    },

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Measure execution time
     */
    time(label, func) {
        return async (...args) => {
            const start = performance.now();
            const result = await func(...args);
            const end = performance.now();
            console.log(`${label}: ${(end - start).toFixed(2)}ms`);
            return result;
        };
    },

    /**
     * Simple memoization
     */
    memoize(func, keyGenerator = (...args) => JSON.stringify(args)) {
        const cache = new Map();
        
        return (...args) => {
            const key = keyGenerator(...args);
            
            if (cache.has(key)) {
                return cache.get(key);
            }
            
            const result = func(...args);
            cache.set(key, result);
            return result;
        };
    }
};

// =============================================================================
// STORAGE UTILITIES
// =============================================================================

const Storage = {
    /**
     * Safe localStorage operations
     */
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.warn('Failed to save to localStorage:', error);
            return false;
        }
    },

    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('Failed to read from localStorage:', error);
            return defaultValue;
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.warn('Failed to remove from localStorage:', error);
            return false;
        }
    },

    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.warn('Failed to clear localStorage:', error);
            return false;
        }
    },

    /**
     * Check if localStorage is available
     */
    isAvailable() {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch {
            return false;
        }
    }
};

// =============================================================================
// DEVICE UTILITIES
// =============================================================================

const Device = {
    /**
     * Check if mobile device
     */
    isMobile() {
        return window.innerWidth <= 767;
    },

    /**
     * Check if tablet device
     */
    isTablet() {
        return window.innerWidth > 767 && window.innerWidth <= 1024;
    },

    /**
     * Check if desktop device
     */
    isDesktop() {
        return window.innerWidth > 1024;
    },

    /**
     * Check if touch device
     */
    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    },

    /**
     * Get device type string
     */
    getType() {
        if (this.isMobile()) return 'mobile';
        if (this.isTablet()) return 'tablet';
        return 'desktop';
    },

    /**
     * Check if user prefers reduced motion
     */
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },

    /**
     * Check if user prefers dark mode
     */
    prefersDarkMode() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
};

// =============================================================================
// FILE UTILITIES
// =============================================================================

const FileUtils = {
    /**
     * Read file as text
     */
    readAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    },

    /**
     * Read file as data URL
     */
    readAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    },

    /**
     * Download data as file
     */
    download(data, filename, type = 'text/plain') {
        const blob = new Blob([data], { type });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
    },

    /**
     * Get file extension
     */
    getExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    },

    /**
     * Check if file type is allowed
     */
    isAllowedType(file, allowedTypes) {
        const extension = this.getExtension(file.name);
        const mimeType = file.type;
        
        return allowedTypes.some(type => 
            type === extension || 
            type === mimeType || 
            (type.endsWith('/*') && mimeType.startsWith(type.slice(0, -1)))
        );
    }
};

// =============================================================================
// EXPORT UTILITIES
// =============================================================================

// Make utilities available globally
window.DOM = DOM;
window.StringUtils = StringUtils;
window.DateUtils = DateUtils;
window.Validation = Validation;
window.Performance = Performance;
window.Storage = Storage;
window.Device = Device;
window.FileUtils = FileUtils;

// =============================================================================
// GLOBAL UTILITY FUNCTIONS
// =============================================================================

// Commonly used functions available globally
function debounce(func, wait, immediate = false) {
    return Performance.debounce(func, wait, immediate);
}

function throttle(func, limit) {
    return Performance.throttle(func, limit);
}

function formatDate(date, options = {}) {
    return DateUtils.format(date, options);
}

function escapeHtml(text) {
    return StringUtils.escapeHtml(text);
}

function generateId(prefix = 'id') {
    return `${prefix}_${StringUtils.randomString(8)}`;
}

// =============================================================================
// JOB ANALYSIS SPECIFIC FUNCTIONS
// =============================================================================

/**
 * Switch between text input and file upload tabs in job analysis
 */
function switchInputTab(tabType) {
    const textTab = document.getElementById('text-input-tab');
    const fileTab = document.getElementById('file-input-tab');
    const textBtn = document.querySelector('[onclick="switchInputTab(\'text\')"]');
    const fileBtn = document.querySelector('[onclick="switchInputTab(\'file\')"]');
    
    if (tabType === 'text') {
        textTab?.classList.add('active');
        fileTab?.classList.remove('active');
        textBtn?.classList.add('active');
        fileBtn?.classList.remove('active');
    } else {
        textTab?.classList.remove('active');
        fileTab?.classList.add('active');
        textBtn?.classList.remove('active');
        fileBtn?.classList.add('active');
    }
}

/**
 * Update character count for job description input
 */
function updateCharacterCount() {
    const textarea = document.getElementById('job-description-input');
    const counter = document.getElementById('character-count');
    
    if (textarea && counter) {
        const count = textarea.value.length;
        counter.textContent = `${count} characters`;
        
        // Update color based on minimum requirement
        if (count >= 50) {
            counter.style.color = '#22c55e'; // green
        } else {
            counter.style.color = '#6b7280'; // gray
        }
    }
}

// =============================================================================
// CONTENT SELECTION SPECIFIC FUNCTIONS
// =============================================================================

/**
 * Clear all content selections - global function for HTML onclick
 */
function clearAllSelections() {
    if (window.contentSelectionManager) {
        window.contentSelectionManager.clearAllSelections();
    }
}

/**
 * Update optimization settings display values
 */
function updateOptimizationSettings() {
    // Update target word count display
    const wordCountSlider = document.getElementById('target-word-count');
    const wordCountDisplay = document.querySelector('.range-value');
    if (wordCountSlider && wordCountDisplay) {
        wordCountDisplay.textContent = `${wordCountSlider.value} words`;
    }
    
    // Update weight displays
    document.querySelectorAll('.weight-slider').forEach(slider => {
        const valueDisplay = slider.parentElement.querySelector('.weight-value');
        if (valueDisplay) {
            valueDisplay.textContent = `${slider.value}%`;
        }
    });
}

// Add event listeners for optimization settings when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Target word count slider
    const wordCountSlider = document.getElementById('target-word-count');
    if (wordCountSlider) {
        wordCountSlider.addEventListener('input', updateOptimizationSettings);
    }
    
    // Weight sliders
    document.querySelectorAll('.weight-slider').forEach(slider => {
        slider.addEventListener('input', updateOptimizationSettings);
    });
    
    // Setup drag and drop for section ordering
    setupSectionOrderDragAndDrop();
});

// =============================================================================
// RESUME PREVIEW SPECIFIC FUNCTIONS
// =============================================================================

/**
 * Setup drag and drop functionality for section ordering
 */
function setupSectionOrderDragAndDrop() {
    let draggedElement = null;
    
    document.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('order-item')) {
            draggedElement = e.target;
            e.target.classList.add('dragging');
        }
    });
    
    document.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('order-item')) {
            e.target.classList.remove('dragging');
            draggedElement = null;
        }
    });
    
    document.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (e.target.classList.contains('order-item') && draggedElement) {
            const container = e.target.parentElement;
            const afterElement = getDragAfterElement(container, e.clientY);
            if (afterElement == null) {
                container.appendChild(draggedElement);
            } else {
                container.insertBefore(draggedElement, afterElement);
            }
        }
    });
}

/**
 * Get the element after which the dragged element should be inserted
 */
function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.order-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}