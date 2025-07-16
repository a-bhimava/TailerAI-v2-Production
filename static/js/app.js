/**
 * Main Application Controller for TailerAI v2.0
 * Initializes and coordinates all application modules
 */

class TailerApp {
    constructor() {
        this.isInitialized = false;
        this.modules = new Map();
        this.config = {
            autoSaveInterval: 30000, // 30 seconds
            maxRetries: 3,
            retryDelay: 1000,
            debugMode: false
        };
        
        this.initialize();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    async initialize() {
        if (this.isInitialized) return;

        try {
            // Show loading screen
            this.showLoadingScreen();
            
            // Initialize core modules
            await this.initializeModules();
            
            // Set up global event handlers
            this.setupGlobalHandlers();
            
            // Check application health
            await this.performHealthCheck();
            
            // Initialize dashboard
            this.initializeDashboard();
            
            // Mark as initialized
            this.isInitialized = true;
            
            // Hide loading screen
            this.hideLoadingScreen();
            
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.hideLoadingScreen(); // Ensure loading screen is hidden even on error
            this.handleInitializationError(error);
        }
    }

    async initializeModules() {
        // Modules are already initialized via their respective files
        // We just need to register them and ensure they're ready
        
        const requiredModules = [
            'api',
            'auth', 
            'navigation',
            'notifications',
            'dataset'
        ];
        
        // Wait a moment for all modules to finish loading
        await new Promise(resolve => setTimeout(resolve, 100));
        
        for (const moduleName of requiredModules) {
            if (window[moduleName]) {
                this.modules.set(moduleName, window[moduleName]);
            } else {
                console.warn(`Module ${moduleName} not found, skipping...`);
                // Don't throw error for missing optional modules
            }
        }
    }

    setupGlobalHandlers() {
        // Handle window events
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));
        
        // Handle keyboard shortcuts
        this.setupGlobalKeyboardShortcuts();
        
        // Handle connection status updates
        this.startConnectionMonitoring();
        
        // Set up auto-save
        this.setupAutoSave();
    }

    setupGlobalKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Global shortcuts (when not in input fields)
            if (this.isInputFocused()) return;
            
            // Ctrl/Cmd + K for quick search/command palette
            if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
                event.preventDefault();
                this.showQuickSearch();
            }
            
            // Escape to close modals/dropdowns
            if (event.key === 'Escape') {
                this.closeAllModals();
            }
            
            // Ctrl/Cmd + S for save
            if ((event.ctrlKey || event.metaKey) && event.key === 's') {
                event.preventDefault();
                this.saveCurrentData();
            }
        });
    }

    // =============================================================================
    // HEALTH CHECK
    // =============================================================================

    async performHealthCheck() {
        try {
            const health = await window.api.healthCheck();
            
            if (health.status === 'unhealthy') {
                console.warn('Application health check failed:', health);
                window.notifications.warning('Some services may be experiencing issues');
            } else if (health.status === 'degraded') {
                console.info('Application running with some services initializing:', health);
            }
            
            this.updateConnectionStatus(true);
            return health;
            
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateConnectionStatus(false);
            throw new Error('Backend services are not available');
        }
    }

    // =============================================================================
    // DASHBOARD MANAGEMENT
    // =============================================================================

    initializeDashboard() {
        // Create dashboard manager if it doesn't exist
        if (!window.dashboard) {
            window.dashboard = new DashboardManager();
        }
    }

    // =============================================================================
    // CONNECTION MONITORING
    // =============================================================================

    startConnectionMonitoring() {
        // Check connection every 30 seconds
        setInterval(async () => {
            try {
                await window.api.healthCheck();
                this.updateConnectionStatus(true);
            } catch (error) {
                this.updateConnectionStatus(false);
            }
        }, 30000);
    }

    updateConnectionStatus(isConnected) {
        const statusIndicator = document.getElementById('connection-status');
        const statusText = statusIndicator?.nextElementSibling;
        
        if (statusIndicator) {
            statusIndicator.textContent = isConnected ? '🟢' : '🔴';
        }
        
        if (statusText) {
            statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
        }
        
        // Show notification for connection changes
        if (!isConnected && this.isInitialized) {
            window.notifications.warning('Connection lost. Some features may not work.');
        } else if (isConnected && this.isInitialized) {
            // Only show reconnected message if we were previously disconnected
            window.notifications.success('Connection restored', { duration: 3000 });
        }
    }

    handleOnline() {
        this.updateConnectionStatus(true);
    }

    handleOffline() {
        this.updateConnectionStatus(false);
        window.notifications.warning('You are currently offline');
    }

    // =============================================================================
    // AUTO-SAVE
    // =============================================================================

    setupAutoSave() {
        setInterval(() => {
            this.autoSave();
        }, this.config.autoSaveInterval);
    }

    async autoSave() {
        try {
            // Delegate to modules that support auto-save
            if (window.dataset && typeof window.dataset.autoSave === 'function') {
                await window.dataset.autoSave();
            }
            
        } catch (error) {
            console.error('Auto-save failed:', error);
        }
    }

    async saveCurrentData() {
        try {
            const currentRoute = window.navigation?.getCurrentRoute();
            
            switch (currentRoute) {
                case 'master-dataset':
                    if (window.dataset && typeof window.dataset.save === 'function') {
                        await window.dataset.save();
                        window.notifications.success('Dataset saved');
                    }
                    break;
                    
                default:
                    window.notifications.info('Nothing to save');
            }
            
        } catch (error) {
            console.error('Save failed:', error);
            window.notifications.error('Failed to save changes');
        }
    }

    // =============================================================================
    // UI HELPERS
    // =============================================================================

    showLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.display = 'flex';
        }
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
    }

    showQuickSearch() {
        // TODO: Implement quick search/command palette
        window.notifications.info('Quick search coming soon (Ctrl+K)');
    }

    closeAllModals() {
        // Close auth modal
        const authModal = document.getElementById('auth-modal');
        if (authModal && authModal.classList.contains('active')) {
            window.auth.closeAuthModal();
        }
        
        // Close user dropdown
        const userDropdown = document.getElementById('user-dropdown');
        if (userDropdown && userDropdown.classList.contains('active')) {
            userDropdown.classList.remove('active');
        }
        
        // Close mobile sidebar
        if (window.navigation) {
            window.navigation.closeMobileSidebar();
        }
    }

    isInputFocused() {
        const activeElement = document.activeElement;
        return activeElement && (
            activeElement.tagName === 'INPUT' ||
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.contentEditable === 'true'
        );
    }

    // =============================================================================
    // ERROR HANDLING
    // =============================================================================

    handleInitializationError(error) {
        console.error('Initialization error:', error);
        
        // Hide loading screen
        this.hideLoadingScreen();
        
        // Show error state
        const app = document.getElementById('app');
        if (app) {
            app.innerHTML = `
                <div class="init-error">
                    <div class="error-icon">⚠️</div>
                    <h2>Failed to Initialize</h2>
                    <p>TailerAI v2.0 failed to start properly.</p>
                    <p class="error-message">${escapeHtml(error.message)}</p>
                    <button class="btn btn-primary" onclick="window.location.reload()">
                        Reload Application
                    </button>
                </div>
            `;
            app.style.display = 'block';
        }
    }

    handleBeforeUnload(event) {
        // Check for unsaved changes
        const hasUnsavedChanges = this.checkForUnsavedChanges();
        
        if (hasUnsavedChanges) {
            event.preventDefault();
            event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return event.returnValue;
        }
    }

    checkForUnsavedChanges() {
        // Check each module for unsaved changes
        if (window.dataset && typeof window.dataset.hasUnsavedChanges === 'function') {
            return window.dataset.hasUnsavedChanges();
        }
        
        return false;
    }

    // =============================================================================
    // PUBLIC API
    // =============================================================================

    getModule(name) {
        return this.modules.get(name);
    }

    isReady() {
        return this.isInitialized;
    }

    async restart() {
        this.isInitialized = false;
        await this.initialize();
    }

    getConfig() {
        return { ...this.config };
    }

    setConfig(updates) {
        this.config = { ...this.config, ...updates };
    }
}

// =============================================================================
// DASHBOARD MANAGER
// =============================================================================

class DashboardManager {
    constructor() {
        this.dashboardData = {
            datasetCompleteness: 0,
            recentAnalyses: 0,
            activeApplications: 0
        };
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for navigation to dashboard
        window.addEventListener('navigation:routeChanged', (event) => {
            if (event.detail.route === 'dashboard') {
                this.loadDashboardData();
            }
        });
    }

    async loadDashboardData() {
        if (!window.auth.isAuthenticated()) return;
        
        try {
            // Load dataset completeness
            await this.updateDatasetCompleteness();
            
            // Load recent analyses count
            await this.updateRecentAnalyses();
            
            // Load active applications count
            await this.updateActiveApplications();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    async updateDatasetCompleteness() {
        try {
            if (window.dataset && typeof window.dataset.calculateCompleteness === 'function') {
                const completeness = await window.dataset.calculateCompleteness();
                this.dashboardData.datasetCompleteness = completeness;
                this.updateCompleteness(completeness);
            }
        } catch (error) {
            console.error('Failed to update dataset completeness:', error);
        }
    }

    async updateRecentAnalyses() {
        try {
            // TODO: Implement when job analysis API is available
            this.dashboardData.recentAnalyses = 0;
            this.updateAnalysesCount(0);
        } catch (error) {
            console.error('Failed to update recent analyses:', error);
        }
    }

    async updateActiveApplications() {
        try {
            // TODO: Implement when application tracking API is available
            this.dashboardData.activeApplications = 0;
            this.updateApplicationsCount(0);
        } catch (error) {
            console.error('Failed to update active applications:', error);
        }
    }

    updateCompleteness(percentage) {
        const valueElement = document.getElementById('dataset-completeness');
        const progressElement = document.getElementById('dataset-progress');
        
        if (valueElement) {
            valueElement.textContent = `${percentage}%`;
        }
        
        if (progressElement) {
            progressElement.style.width = `${percentage}%`;
        }
    }

    updateAnalysesCount(count) {
        const element = document.getElementById('recent-analyses');
        if (element) {
            element.textContent = count.toString();
        }
    }

    updateApplicationsCount(count) {
        const element = document.getElementById('active-applications');
        if (element) {
            element.textContent = count.toString();
        }
    }

    updateDatasetStats(completeness) {
        this.dashboardData.datasetCompleteness = completeness;
        this.updateCompleteness(completeness);
    }

    getDashboardData() {
        return { ...this.dashboardData };
    }
}

// =============================================================================
// RESUME GENERATION API
// =============================================================================

async function generateResumeAPI(params) {
    try {
        // Get current dataset from DatasetManager
        if (!window.dataset || !window.dataset.dataset) {
            throw new Error('No dataset available. Please ensure your profile data is loaded.');
        }
        
        const dataset = window.dataset.dataset;
        
        // Transform data to match LaTeX API format
        const workExperiences = (dataset.work_experiences || []).map(exp => {
            // Filter achievements for this work experience
            const expAchievements = (dataset.achievements || [])
                .filter(achievement => achievement.work_experience_id === exp.id)
                .map(achievement => achievement.achievement_text || achievement);
            
            return {
                experience_id: exp.id || '',
                company_name: exp.company_name || '',
                position_title: exp.position_title || '',
                location: exp.location || null,
                start_date: exp.start_date || null,
                end_date: exp.end_date || null,
                company_description: exp.company_description || null,
                achievements: expAchievements
            };
        });
        
        const education = (dataset.education || []).map(edu => ({
            institution_name: edu.institution_name || '',
            degree_type: edu.degree_type || '',
            field_of_study: edu.field_of_study || null,
            location: edu.location || null,
            graduation_date: edu.graduation_date || null,
            gpa: edu.gpa || null,
            gpa_scale: edu.gpa_scale || null,
            relevant_coursework: Array.isArray(edu.relevant_coursework) 
                ? edu.relevant_coursework.join(', ') 
                : (edu.relevant_coursework || null),
            academic_achievements: Array.isArray(edu.academic_achievements) 
                ? edu.academic_achievements.join(', ') 
                : (edu.academic_achievements || null)
        }));
        
        const skills = (dataset.skills || []).map(skill => ({
            skill_name: skill.skill_name || '',
            skill_category: skill.skill_category || null,
            proficiency_level: skill.proficiency_level || null
        }));
        
        // Temporarily disable projects to debug LaTeX compilation
        const projects = [];
        
        const certifications = dataset.certifications || [];
        
        // Debug: log the data being sent
        const requestData = {
            work_experiences: workExperiences,
            education: education,
            skills: skills,
            projects: projects,
            certifications: certifications,
            filename_prefix: params.template === 'mspm' ? 'mspm_resume' : 'resume'
        };
        
        console.log('LaTeX API Request Data:', requestData);
        console.log('Work Experiences:', workExperiences);
        // Debug achievements specifically
        workExperiences.forEach((exp, i) => {
            console.log(`Work Experience ${i} (${exp.company_name}): ${exp.achievements.length} achievements`);
            exp.achievements.forEach((ach, j) => {
                console.log(`  Achievement ${j}: ${ach.substring(0, 50)}...`);
            });
        });
        console.log('Education:', education);
        console.log('Skills:', skills);
        console.log('Projects:', projects);
        
        // Call the LaTeX generation API with correct format
        const response = await window.api.post('/api/v2/latex/generate', requestData);
        
        // Debug: log the response
        console.log('LaTeX API Response:', response);
        
        // Check if the response indicates success
        if (response.success === false) {
            throw new Error(response.message || 'Resume generation failed');
        }
        
        return response;
    } catch (error) {
        console.error('Resume generation API error:', error);
        throw error;
    }
}

// =============================================================================
// GLOBAL FUNCTIONS
// =============================================================================

function generateResume() {
    const jobTitle = document.getElementById('job-title')?.value || '';
    const companyName = document.getElementById('company-name-resume')?.value || '';
    const jobDescription = document.getElementById('job-description-simple')?.value || '';
    const template = document.getElementById('resume-template')?.value || 'mspm';
    const format = document.getElementById('resume-format')?.value || 'pdf';
    
    // Show progress
    const progressDiv = document.getElementById('resume-progress');
    const generateBtn = document.getElementById('generate-resume-btn');
    
    if (progressDiv && generateBtn) {
        progressDiv.style.display = 'block';
        generateBtn.disabled = true;
    }
    
    // Call the actual resume generation API
    generateResumeAPI({
        jobTitle,
        companyName,
        jobDescription,
        template,
        format
    }).then(response => {
        if (progressDiv && generateBtn) {
            progressDiv.style.display = 'none';
            generateBtn.disabled = false;
        }
        
        // Create appropriate message based on format
        let message = 'Resume generated successfully! Download will start shortly.';
        if (template === 'mspm') {
            message = `MSPM format resume generated as ${format.toUpperCase()}! Download starting...`;
        }
        
        window.notifications.show(message, 'success');
        
        // If we get a file URL, trigger authenticated download
        if (response.pdf_download_url) {
            downloadFileWithAuth(response.pdf_download_url);
        } else if (response.download_url) {
            downloadFileWithAuth(response.download_url);
        }
        
    }).catch(error => {
        if (progressDiv && generateBtn) {
            progressDiv.style.display = 'none';
            generateBtn.disabled = false;
        }
        
        console.error('Resume generation failed:', error);
        window.notifications.show('Failed to generate resume. Please try again.', 'error');
    });
}

// Set up the generate resume button handler when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-resume-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateResume);
    }
});

// =============================================================================
// APPLICATION STARTUP
// =============================================================================

// Initialize application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new TailerApp();
    });
} else {
    window.app = new TailerApp();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TailerApp, DashboardManager };
}