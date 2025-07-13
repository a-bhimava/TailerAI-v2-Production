/**
 * Master Dataset Management for TailerAI v2.0
 * Handles personal dataset CRUD operations and UI management
 */

class DatasetManager {
    constructor() {
        this.dataset = null;
        this.filteredData = null;
        this.searchQuery = '';
        this.currentFilter = '';
        this.viewMode = 'list';
        this.isLoading = false;
        this.autoSaveTimer = null;
        
        this.initializeDataset();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initializeDataset() {
        this.setupEventListeners();
        this.setupAutoSave();
    }

    setupEventListeners() {
        // Search and filter
        const searchInput = document.getElementById('dataset-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.handleSearch.bind(this));
        }

        const filterSelect = document.getElementById('experience-filter');
        if (filterSelect) {
            filterSelect.addEventListener('change', this.handleFilter.bind(this));
        }

        const viewModeSelect = document.getElementById('view-mode');
        if (viewModeSelect) {
            viewModeSelect.addEventListener('change', this.handleViewModeChange.bind(this));
        }

        // Listen for navigation events to load data when needed
        window.addEventListener('navigation:routeChanged', (event) => {
            if (event.detail.route === 'master-dataset') {
                this.loadDataset();
            }
        });

        // Listen for authentication events
        window.addEventListener('auth:login', () => {
            console.log('Dataset: Received auth:login event, isLoading:', this.isLoading);
            // Prevent multiple simultaneous loads
            if (this.isLoading) {
                console.log('Dataset: Already loading, skipping...');
                return;
            }
            
            // Load dataset after successful login with small delay for OAuth completion
            const currentRoute = window.navigation?.getCurrentRoute();
            console.log('Dataset: Current route:', currentRoute);
            if (currentRoute === 'master-dataset') {
                console.log('Dataset: Scheduling dataset load...');
                // Small delay to ensure OAuth profile creation is complete
                setTimeout(() => {
                    console.log('Dataset: Starting dataset load...');
                    this.loadDataset();
                }, 500);
            }
        });
    }

    setupAutoSave() {
        // Auto-save every 30 seconds if there are unsaved changes
        setInterval(() => {
            if (this.hasUnsavedChanges()) {
                this.autoSave();
            }
        }, 30000);
    }

    // =============================================================================
    // DATA LOADING
    // =============================================================================

    async loadDataset(retryCount = 0) {
        console.log('loadDataset called, retryCount:', retryCount, 'isLoading:', this.isLoading);
        
        if (this.isLoading && retryCount === 0) {
            console.log('Already loading, returning early');
            return;
        }
        
        // Check if user is authenticated before loading
        if (!window.api.isAuthenticated()) {
            console.log('Not authenticated, showing empty state');
            this.showEmptyState();
            return;
        }
        
        console.log('Starting dataset load...');
        
        this.isLoading = true;
        if (retryCount === 0) {
            this.showLoadingState();
            
            // Timeout protection - ensure loading state doesn't persist indefinitely
            setTimeout(() => {
                if (this.isLoading) {
                    console.warn('Dataset: Loading timeout, forcing stop');
                    this.isLoading = false;
                    this.hideLoadingState();
                    this.showErrorState('Loading timeout. Please refresh and try again.');
                }
            }, 15000); // 15 second timeout
        }

        try {
            console.log('Making API call to getMasterDataset...');
            const response = await window.api.getMasterDataset();
            console.log('API response received:', response);
            // Extract data from StandardResponse format
            this.dataset = response.data || response;
            console.log('Extracted dataset:', this.dataset);
            this.filteredData = this.dataset;
            console.log('Calling renderDataset...');
            this.renderDataset();
            console.log('Calling updateDatasetStats...');
            this.updateDatasetStats();
            
        } catch (error) {
            console.error('Failed to load dataset:', error);
            
            // Retry logic for user profile not found errors (common after OAuth)
            if (error.status === 404 && retryCount < 3) {
                console.log(`Dataset: Retrying dataset load in ${(retryCount + 1) * 1000}ms...`);
                setTimeout(() => {
                    this.isLoading = false;
                    this.loadDataset(retryCount + 1);
                }, (retryCount + 1) * 1000); // 1s, 2s, 3s delays
                return;
            }
            
            this.showErrorState('Failed to load your master dataset');
        } finally {
            if (retryCount === 0 || error?.status !== 404) {
                console.log('Setting isLoading to false and hiding loading state');
                this.isLoading = false;
                this.hideLoadingState();
            }
        }
    }

    // =============================================================================
    // DATASET RENDERING
    // =============================================================================

    renderDataset() {
        console.log('renderDataset() called');
        const contentDiv = document.getElementById('dataset-content');
        console.log('contentDiv found:', !!contentDiv);
        if (!contentDiv) {
            console.log('No dataset-content div found, returning');
            return;
        }

        // Check if dataset is empty
        console.log('Checking if dataset is empty...');
        if (this.isDatasetEmpty()) {
            console.log('Dataset is empty, showing empty state');
            this.showEmptyState();
            return;
        }
        
        console.log('Dataset is not empty, continuing to render...');

        // Apply current filters
        this.applyFilters();

        // Render based on view mode
        switch (this.viewMode) {
            case 'grid':
                this.renderGridView();
                break;
            case 'timeline':
                this.renderTimelineView();
                break;
            default:
                this.renderListView();
        }
    }

    isDatasetEmpty() {
        if (!this.dataset) return true;
        
        const hasWorkExperiences = this.dataset.work_experiences?.length > 0;
        const hasEducation = this.dataset.education?.length > 0;
        const hasProjects = this.dataset.projects?.length > 0;
        const hasAchievements = this.dataset.achievements?.length > 0;
        
        return !hasWorkExperiences && !hasEducation && !hasProjects && !hasAchievements;
    }

    showEmptyState() {
        const contentDiv = document.getElementById('dataset-content');
        const emptyState = document.getElementById('dataset-empty');
        
        if (contentDiv && emptyState) {
            contentDiv.innerHTML = '';
            contentDiv.appendChild(emptyState.cloneNode(true));
        }
    }

    renderListView() {
        const contentDiv = document.getElementById('dataset-content');
        if (!contentDiv) return;

        let html = '<div class="dataset-list-view">';

        // Work Experiences Section
        if (this.filteredData.work_experiences?.length > 0) {
            html += this.renderWorkExperiencesSection();
        }

        // Education Section
        if (this.filteredData.education?.length > 0) {
            html += this.renderEducationSection();
        }

        // Projects Section
        if (this.filteredData.projects?.length > 0) {
            html += this.renderProjectsSection();
        }

        // Achievements Section
        if (this.filteredData.achievements?.length > 0) {
            html += this.renderAchievementsSection();
        }

        html += '</div>';
        contentDiv.innerHTML = html;

        // Attach event listeners to rendered elements
        this.attachItemEventListeners();
    }

    renderWorkExperiencesSection() {
        let html = `
            <div class="dataset-section">
                <div class="section-header">
                    <h3>Work Experiences</h3>
                    <button class="btn btn-sm btn-primary" onclick="addWorkExperience()">
                        Add Experience
                    </button>
                </div>
                <div class="section-content">
        `;

        this.filteredData.work_experiences.forEach(exp => {
            const achievements = this.dataset.achievements?.filter(a => a.work_experience_id === exp.id) || [];
            
            html += `
                <div class="dataset-item work-experience" data-id="${exp.id}" data-type="work_experience">
                    <div class="item-header">
                        <div class="item-title">
                            <h4>${this.escapeHtml(exp.position_title)}</h4>
                            <span class="item-subtitle">${this.escapeHtml(exp.company_name)}</span>
                        </div>
                        <div class="item-actions">
                            <button class="btn-ghost btn-sm" onclick="editWorkExperience('${exp.id}')">Edit</button>
                            <button class="btn-ghost btn-sm text-red" onclick="deleteWorkExperience('${exp.id}')">Delete</button>
                        </div>
                    </div>
                    <div class="item-meta">
                        <span class="date-range">${this.formatDateRange(exp.start_date, exp.end_date)}</span>
                        <span class="location">${this.escapeHtml(exp.location || '')}</span>
                    </div>
                    <div class="item-content">
                        <p class="company-description">${this.escapeHtml(exp.company_description || '')}</p>
                        ${achievements.length > 0 ? `
                            <div class="achievements-preview">
                                <strong>Achievements (${achievements.length}):</strong>
                                <ul>
                                    ${achievements.slice(0, 3).map(a => `
                                        <li>${this.escapeHtml(a.achievement_text)}</li>
                                    `).join('')}
                                    ${achievements.length > 3 ? `<li><em>+${achievements.length - 3} more...</em></li>` : ''}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderEducationSection() {
        let html = `
            <div class="dataset-section">
                <div class="section-header">
                    <h3>Education</h3>
                    <button class="btn btn-sm btn-primary" onclick="addEducation()">
                        Add Education
                    </button>
                </div>
                <div class="section-content">
        `;

        this.filteredData.education.forEach(edu => {
            html += `
                <div class="dataset-item education" data-id="${edu.id}" data-type="education">
                    <div class="item-header">
                        <div class="item-title">
                            <h4>${this.escapeHtml(edu.degree_type)} in ${this.escapeHtml(edu.field_of_study)}</h4>
                            <span class="item-subtitle">${this.escapeHtml(edu.institution_name)}</span>
                        </div>
                        <div class="item-actions">
                            <button class="btn-ghost btn-sm" onclick="editEducation('${edu.id}')">Edit</button>
                            <button class="btn-ghost btn-sm text-red" onclick="deleteEducation('${edu.id}')">Delete</button>
                        </div>
                    </div>
                    <div class="item-meta">
                        <span class="date-range">${this.formatDate(edu.graduation_date)}</span>
                        <span class="location">${this.escapeHtml(edu.location || '')}</span>
                        ${edu.gpa ? `<span class="gpa">GPA: ${edu.gpa}/${edu.gpa_scale || 4.0}</span>` : ''}
                    </div>
                    <div class="item-content">
                        ${edu.relevant_coursework ? `<p><strong>Coursework:</strong> ${this.escapeHtml(edu.relevant_coursework)}</p>` : ''}
                        ${edu.academic_achievements ? `<p><strong>Achievements:</strong> ${this.escapeHtml(edu.academic_achievements)}</p>` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderProjectsSection() {
        let html = `
            <div class="dataset-section">
                <div class="section-header">
                    <h3>Projects</h3>
                    <button class="btn btn-sm btn-primary" onclick="addProject()">
                        Add Project
                    </button>
                </div>
                <div class="section-content">
        `;

        this.filteredData.projects.forEach(project => {
            html += `
                <div class="dataset-item project" data-id="${project.id}" data-type="project">
                    <div class="item-header">
                        <div class="item-title">
                            <h4>${this.escapeHtml(project.project_name)}</h4>
                            <span class="item-subtitle">${this.escapeHtml(project.project_type || '')}</span>
                        </div>
                        <div class="item-actions">
                            <button class="btn-ghost btn-sm" onclick="editProject('${project.id}')">Edit</button>
                            <button class="btn-ghost btn-sm text-red" onclick="deleteProject('${project.id}')">Delete</button>
                        </div>
                    </div>
                    <div class="item-meta">
                        <span class="date-range">${this.formatDateRange(project.start_date, project.end_date)}</span>
                        ${project.technologies_used ? `<span class="technologies">${this.escapeHtml(project.technologies_used)}</span>` : ''}
                    </div>
                    <div class="item-content">
                        <p>${this.escapeHtml(project.description || '')}</p>
                        ${project.project_url ? `<p><strong>URL:</strong> <a href="${this.escapeHtml(project.project_url)}" target="_blank">${this.escapeHtml(project.project_url)}</a></p>` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderAchievementsSection() {
        // Filter standalone achievements (not linked to work experience)
        const standaloneAchievements = this.filteredData.achievements?.filter(a => !a.work_experience_id) || [];
        
        if (standaloneAchievements.length === 0) return '';

        let html = `
            <div class="dataset-section">
                <div class="section-header">
                    <h3>Additional Achievements</h3>
                    <button class="btn btn-sm btn-primary" onclick="addAchievement()">
                        Add Achievement
                    </button>
                </div>
                <div class="section-content">
        `;

        standaloneAchievements.forEach(achievement => {
            html += `
                <div class="dataset-item achievement" data-id="${achievement.id}" data-type="achievement">
                    <div class="item-header">
                        <div class="item-title">
                            <h4>${this.escapeHtml(achievement.achievement_text)}</h4>
                            <span class="item-subtitle">${this.escapeHtml(achievement.category || '')}</span>
                        </div>
                        <div class="item-actions">
                            <button class="btn-ghost btn-sm" onclick="editAchievement('${achievement.id}')">Edit</button>
                            <button class="btn-ghost btn-sm text-red" onclick="deleteAchievement('${achievement.id}')">Delete</button>
                        </div>
                    </div>
                    <div class="item-meta">
                        ${achievement.date_achieved ? `<span class="date">${this.formatDate(achievement.date_achieved)}</span>` : ''}
                        ${achievement.impact_score ? `<span class="impact-score">Impact: ${achievement.impact_score}/10</span>` : ''}
                    </div>
                    <div class="item-content">
                        ${achievement.quantified_result ? `<p><strong>Result:</strong> ${this.escapeHtml(achievement.quantified_result)}</p>` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderGridView() {
        // TODO: Implement grid view
        this.renderListView(); // Fallback to list view for now
    }

    renderTimelineView() {
        // TODO: Implement timeline view
        this.renderListView(); // Fallback to list view for now
    }

    // =============================================================================
    // SEARCH AND FILTERING
    // =============================================================================

    handleSearch(event) {
        this.searchQuery = event.target.value.toLowerCase();
        this.applyFilters();
        this.renderDataset();
    }

    handleFilter(event) {
        this.currentFilter = event.target.value;
        this.applyFilters();
        this.renderDataset();
    }

    handleViewModeChange(event) {
        this.viewMode = event.target.value;
        this.renderDataset();
    }

    applyFilters() {
        if (!this.dataset) {
            this.filteredData = null;
            return;
        }

        this.filteredData = {
            work_experiences: this.filterArray(this.dataset.work_experiences, 'work'),
            education: this.filterArray(this.dataset.education, 'education'),
            projects: this.filterArray(this.dataset.projects, 'projects'),
            achievements: this.filterArray(this.dataset.achievements, 'achievements'),
            skills: this.filterArray(this.dataset.skills, 'skills')
        };
    }

    filterArray(array, type) {
        if (!array) return [];

        return array.filter(item => {
            // Apply type filter
            if (this.currentFilter && this.currentFilter !== type) {
                return false;
            }

            // Apply search filter
            if (this.searchQuery) {
                const searchableText = this.getSearchableText(item, type).toLowerCase();
                return searchableText.includes(this.searchQuery);
            }

            return true;
        });
    }

    getSearchableText(item, type) {
        switch (type) {
            case 'work':
                return `${item.position_title} ${item.company_name} ${item.company_description || ''}`;
            case 'education':
                return `${item.degree_type} ${item.field_of_study} ${item.institution_name} ${item.relevant_coursework || ''}`;
            case 'projects':
                return `${item.project_name} ${item.description || ''} ${item.technologies_used || ''}`;
            case 'achievements':
                return `${item.achievement_text} ${item.category || ''} ${item.quantified_result || ''}`;
            case 'skills':
                return `${item.skill_name} ${item.skill_category || ''}`;
            default:
                return JSON.stringify(item);
        }
    }

    // =============================================================================
    // UTILITY METHODS
    // =============================================================================

    attachItemEventListeners() {
        // Add event listeners for edit/delete buttons, drag-and-drop, etc.
        // This would be called after rendering items
    }

    updateDatasetStats() {
        // Update dashboard statistics
        if (window.dashboard && this.dataset) {
            const completeness = this.calculateCompleteness();
            window.dashboard.updateDatasetStats(completeness);
        }
    }

    calculateCompleteness() {
        if (!this.dataset) return 0;

        let totalFields = 0;
        let completedFields = 0;

        // Basic profile completion
        const profile = this.dataset.profile || {};
        const profileFields = ['full_name', 'email', 'phone', 'location'];
        totalFields += profileFields.length;
        completedFields += profileFields.filter(field => profile[field]).length;

        // Work experience completion
        const workExperiences = this.dataset.work_experiences || [];
        if (workExperiences.length > 0) {
            totalFields += 5; // Has work experience, recent position, company, dates, achievements
            completedFields += 5;
        }

        // Education completion
        const education = this.dataset.education || [];
        if (education.length > 0) {
            totalFields += 3;
            completedFields += 3;
        }

        // Skills completion
        const skills = this.dataset.skills || [];
        if (skills.length >= 5) {
            totalFields += 2;
            completedFields += 2;
        }

        return Math.round((completedFields / Math.max(totalFields, 10)) * 100);
    }

    formatDate(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short' 
            });
        } catch (error) {
            return dateString;
        }
    }

    formatDateRange(startDate, endDate) {
        const start = this.formatDate(startDate);
        const end = endDate ? this.formatDate(endDate) : 'Present';
        return `${start} - ${end}`;
    }

    escapeHtml(text) {
        if (!text) return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoadingState() {
        const contentDiv = document.getElementById('dataset-content');
        if (contentDiv) {
            contentDiv.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Loading your master dataset...</div>
                </div>
            `;
        }
    }

    hideLoadingState() {
        console.log('hideLoadingState() called');
        const contentDiv = document.getElementById('dataset-content');
        if (contentDiv) {
            // Clear the loading content - it will be replaced by renderDataset()
            const loadingState = contentDiv.querySelector('.loading-state');
            if (loadingState) {
                console.log('Removing loading state element');
                loadingState.remove();
            }
        }
    }

    showErrorState(message) {
        const contentDiv = document.getElementById('dataset-content');
        if (contentDiv) {
            contentDiv.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <h3>Error Loading Dataset</h3>
                    <p>${this.escapeHtml(message)}</p>
                    <div class="error-actions">
                        <button class="btn btn-primary" onclick="window.dataset.loadDataset()">
                            Try Again
                        </button>
                        <button class="btn btn-secondary" onclick="window.dataset.showEmptyState()">
                            Start Fresh
                        </button>
                    </div>
                    <div class="error-details">
                        <p><small>If you just signed in with Google, your profile might still be setting up. Please wait a moment and try again.</small></p>
                    </div>
                </div>
            `;
        }
    }

    // =============================================================================
    // AUTO-SAVE FUNCTIONALITY
    // =============================================================================

    hasUnsavedChanges() {
        // TODO: Implement change tracking
        return false;
    }

    async autoSave() {
        try {
            // TODO: Implement auto-save logic
            this.updateLastSavedIndicator('Auto-saved just now');
        } catch (error) {
            console.error('Auto-save failed:', error);
            this.updateLastSavedIndicator('Auto-save failed');
        }
    }

    updateLastSavedIndicator(text) {
        const indicator = document.getElementById('last-saved');
        if (indicator) {
            indicator.textContent = text;
        }
    }
}

// =============================================================================
// GLOBAL DATASET MANAGER
// =============================================================================

// Create global dataset manager instance
window.dataset = new DatasetManager();

// =============================================================================
// GLOBAL DATASET FUNCTIONS (for HTML onclick handlers)
// =============================================================================

function addExperience() {
    showAddWorkExperienceModal();
}

function addWorkExperience() {
    showAddWorkExperienceModal();
}

function addEducation() {
    showAddEducationModal();
}

function addProject() {
    showAddProjectModal();
}

function addAchievement() {
    showAddAchievementModal();
}

function editWorkExperience(id) {
    // TODO: Show edit work experience modal
    window.notifications.show('Edit functionality coming soon', 'info');
}

function deleteWorkExperience(id) {
    // TODO: Show delete confirmation
    window.notifications.show('Delete functionality coming soon', 'info');
}

function editEducation(id) {
    // TODO: Show edit education modal
    window.notifications.show('Edit functionality coming soon', 'info');
}

function deleteEducation(id) {
    // TODO: Show delete confirmation
    window.notifications.show('Delete functionality coming soon', 'info');
}

function editProject(id) {
    // TODO: Show edit project modal
    window.notifications.show('Edit functionality coming soon', 'info');
}

function deleteProject(id) {
    // TODO: Show delete confirmation
    window.notifications.show('Delete functionality coming soon', 'info');
}

function editAchievement(id) {
    // TODO: Show edit achievement modal
    window.notifications.show('Edit functionality coming soon', 'info');
}

function deleteAchievement(id) {
    // TODO: Show delete confirmation
    window.notifications.show('Delete functionality coming soon', 'info');
}

function importData() {
    window.notifications.show('Import functionality will be available in the next update', 'info');
}

function filterDataset() {
    // This function is called by the search input and filter selects
    // The actual filtering is handled by the event listeners
}

function changeViewMode() {
    // This function is called by the view mode select
    // The actual view change is handled by the event listener
}

// =============================================================================
// MODAL FUNCTIONS
// =============================================================================

function showAddWorkExperienceModal() {
    const modalHtml = `
        <div id="work-experience-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Add Work Experience</h3>
                    <button class="modal-close" onclick="closeWorkExperienceModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="work-experience-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="company-name">Company Name *</label>
                                <input type="text" id="company-name" name="company_name" required>
                            </div>
                            <div class="form-group">
                                <label for="location">Location *</label>
                                <input type="text" id="location" name="location" placeholder="City, State/Country" required>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="designation">Designation *</label>
                            <input type="text" id="designation" name="position_title" required placeholder="Your job title/position">
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="from-date">From *</label>
                                <input type="text" id="from-date" name="start_date" required placeholder="MM/YY" pattern="^(0[1-9]|1[0-2])\/[0-9]{2}$" title="Please enter date in MM/YY format">
                                <small class="form-hint">Format: MM/YY (e.g., 03/22)</small>
                            </div>
                            <div class="form-group">
                                <label for="to-date">To</label>
                                <input type="text" id="to-date" name="end_date" placeholder="MM/YY or Present" pattern="^(0[1-9]|1[0-2])\/[0-9]{2}$|^Present$" title="Please enter date in MM/YY format or 'Present'">
                                <small class="form-hint">Format: MM/YY or "Present"</small>
                                <div class="checkbox-group">
                                    <label>
                                        <input type="checkbox" id="is-current" name="is_current" onchange="toggleToDate()">
                                        I currently work here
                                    </label>
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="achievements">Achievements</label>
                            <textarea id="achievements" name="achievements" rows="6" 
                                placeholder="• Achievement 1 with quantifiable results&#10;• Achievement 2 with impact metrics&#10;• Achievement 3 demonstrating skills"></textarea>
                            <small class="form-hint">List your key achievements and accomplishments in this role. Use bullet points and include metrics where possible.</small>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="closeWorkExperienceModal()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                Add Experience
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('work-experience-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = document.getElementById('work-experience-modal');
    modal.classList.add('active');
    
    // Add form submit handler
    const form = document.getElementById('work-experience-form');
    form.addEventListener('submit', handleWorkExperienceSubmit);
    
    // Focus first input
    document.getElementById('company-name').focus();
}

function closeWorkExperienceModal() {
    const modal = document.getElementById('work-experience-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

function toggleToDate() {
    const isCurrentCheckbox = document.getElementById('is-current');
    const toDateInput = document.getElementById('to-date');
    
    if (isCurrentCheckbox.checked) {
        toDateInput.disabled = true;
        toDateInput.value = 'Present';
    } else {
        toDateInput.disabled = false;
        if (toDateInput.value === 'Present') {
            toDateInput.value = '';
        }
    }
}

async function handleWorkExperienceSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Disable form during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';
    
    try {
        const formData = new FormData(form);
        const data = {};
        
        // Convert form data to object
        for (let [key, value] of formData.entries()) {
            if (value && key !== 'is_current') {
                data[key] = value;
            }
        }
        
        // Convert MM/YY format to proper date format
        if (data.start_date) {
            data.start_date = convertMMYYToISO(data.start_date);
        }
        if (data.end_date && data.end_date !== 'Present') {
            data.end_date = convertMMYYToISO(data.end_date);
        }
        
        // Set employment type to full-time by default for backend compatibility
        data.employment_type = 'full-time';
        
        // Add work experience via API
        const response = await window.api.createWorkExperience(data);
        
        window.notifications.show('Work experience added successfully!', 'success');
        closeWorkExperienceModal();
        
        // Reload dataset to show new experience
        await window.dataset.loadDataset();
        
    } catch (error) {
        console.error('Failed to add work experience:', error);
        
        let errorMessage = 'Failed to add work experience';
        if (error instanceof APIError) {
            if (error.status === 422) {
                errorMessage = 'Please check your input data and try again';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else if (error.status === 409) {
                // Handle duplicate work experience
                errorMessage = error.details?.detail || error.message || 'This work experience already exists in your profile. Please check your existing entries.';
            } else if (error.status === 400) {
                // Handle other validation errors
                errorMessage = error.message || 'Invalid input data';
            } else {
                errorMessage = error.message || 'Failed to add work experience';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
    } finally {
        // Re-enable form
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// Helper function to convert MM/YY to ISO date
function convertMMYYToISO(mmyy) {
    if (!mmyy || mmyy === 'Present') return null;
    
    const [month, year] = mmyy.split('/');
    const fullYear = '20' + year; // Assuming all years are 20XX
    const date = new Date(fullYear, parseInt(month) - 1, 1);
    return date.toISOString();
}

function showAddAchievementModal(experienceId = null) {
    const modalHtml = `
        <div id="achievement-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Add Achievement</h3>
                    <button class="modal-close" onclick="closeAchievementModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="achievement-form">
                        <input type="hidden" id="experience-id" name="experience_id" value="${experienceId || ''}">
                        
                        <div class="form-group">
                            <label for="achievement-text">Achievement Description *</label>
                            <textarea id="achievement-text" name="achievement_text" rows="4" required
                                placeholder="Describe your achievement with specific, quantifiable results..."></textarea>
                            <small class="form-hint">
                                Use action verbs and include metrics (e.g., "Increased sales by 25% through...")
                            </small>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="achievement-category">Category *</label>
                                <select id="achievement-category" name="achievement_category" required>
                                    <option value="">Select category</option>
                                    <option value="leadership">Leadership</option>
                                    <option value="technical">Technical</option>
                                    <option value="financial">Financial</option>
                                    <option value="operational">Operational</option>
                                    <option value="strategic">Strategic</option>
                                    <option value="customer">Customer-focused</option>
                                    <option value="process">Process Improvement</option>
                                    <option value="innovation">Innovation</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="impact-level">Impact Level (1-10) *</label>
                                <select id="impact-level" name="impact_level" required>
                                    <option value="">Select impact</option>
                                    <option value="1">1 - Minor</option>
                                    <option value="2">2</option>
                                    <option value="3">3</option>
                                    <option value="4">4</option>
                                    <option value="5">5 - Moderate</option>
                                    <option value="6">6</option>
                                    <option value="7">7</option>
                                    <option value="8">8</option>
                                    <option value="9">9</option>
                                    <option value="10">10 - Major</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="business-function">Business Function</label>
                            <input type="text" id="business-function" name="business_function" 
                                placeholder="e.g., Sales, Marketing, Engineering">
                        </div>
                        
                        <div class="form-group">
                            <label for="time-period">Time Period</label>
                            <input type="text" id="time-period" name="time_period" 
                                placeholder="e.g., Q3 2023, Over 6 months">
                        </div>
                        
                        <div class="form-group">
                            <label for="keywords">Keywords (comma-separated)</label>
                            <input type="text" id="keywords" name="keywords" 
                                placeholder="leadership, project management, revenue growth">
                            <small class="form-hint">
                                Add relevant keywords that might appear in job descriptions
                            </small>
                        </div>
                        
                        <div class="form-group">
                            <label for="skills-demonstrated">Skills Demonstrated (comma-separated)</label>
                            <input type="text" id="skills-demonstrated" name="skills_demonstrated" 
                                placeholder="Python, team leadership, data analysis">
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="closeAchievementModal()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                Add Achievement
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('achievement-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = document.getElementById('achievement-modal');
    modal.classList.add('active');
    
    // Add form submit handler
    const form = document.getElementById('achievement-form');
    form.addEventListener('submit', handleAchievementSubmit);
    
    // Focus first input
    document.getElementById('achievement-text').focus();
}

function closeAchievementModal() {
    const modal = document.getElementById('achievement-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

async function handleAchievementSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Disable form during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';
    
    try {
        const formData = new FormData(form);
        const data = {};
        
        // Convert form data to object
        for (let [key, value] of formData.entries()) {
            if (value && key !== 'experience_id') {
                data[key] = value;
            }
        }
        
        // Parse arrays from comma-separated strings
        if (data.keywords) {
            data.keywords = data.keywords.split(',').map(k => k.trim()).filter(k => k);
        }
        if (data.skills_demonstrated) {
            data.skills_demonstrated = data.skills_demonstrated.split(',').map(s => s.trim()).filter(s => s);
        }
        
        // Convert impact level to number
        if (data.impact_level) {
            data.impact_level = parseInt(data.impact_level);
        }
        
        const experienceId = formData.get('experience_id');
        
        // Add achievement via API
        if (experienceId) {
            await window.api.createAchievement(data);
        } else {
            await window.api.createAchievement(data);
        }
        
        window.notifications.show('Achievement added successfully!', 'success');
        closeAchievementModal();
        
        // Reload dataset to show new achievement
        await window.dataset.loadDataset();
        
    } catch (error) {
        console.error('Failed to add achievement:', error);
        
        let errorMessage = 'Failed to add achievement';
        if (error instanceof APIError) {
            if (error.status === 422) {
                errorMessage = 'Please check your input data and try again';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else {
                errorMessage = error.message || 'Failed to add achievement';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
    } finally {
        // Re-enable form
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function showAddEducationModal() {
    const modalHtml = `
        <div id="education-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Add Education</h3>
                    <button class="modal-close" onclick="closeEducationModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="education-form">
                        <div class="form-group">
                            <label for="institution-name">Institution Name *</label>
                            <input type="text" id="institution-name" name="institution_name" required placeholder="University/College name">
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="degree-type">Degree Type *</label>
                                <select id="degree-type" name="degree_type" required>
                                    <option value="">Select degree type</option>
                                    <option value="Bachelor's">Bachelor's</option>
                                    <option value="Master's">Master's</option>
                                    <option value="PhD">PhD</option>
                                    <option value="Diploma">Diploma</option>
                                    <option value="Certificate">Certificate</option>
                                    <option value="Associate">Associate</option>
                                    <option value="High School">High School</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="field-of-study">Field of Study *</label>
                                <input type="text" id="field-of-study" name="field_of_study" required placeholder="e.g., Computer Science, Business">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="graduation-date">Graduation Date *</label>
                                <input type="text" id="graduation-date" name="graduation_date" required placeholder="MM/YY" pattern="^(0[1-9]|1[0-2])\/[0-9]{2}$" title="Please enter date in MM/YY format">
                                <small class="form-hint">Format: MM/YY (e.g., 05/23)</small>
                            </div>
                            <div class="form-group">
                                <label for="education-location">Location</label>
                                <input type="text" id="education-location" name="location" placeholder="City, State/Country">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="gpa">GPA (optional)</label>
                                <input type="number" id="gpa" name="gpa" step="0.01" min="0" max="4" placeholder="3.8">
                            </div>
                            <div class="form-group">
                                <label for="gpa-scale">GPA Scale</label>
                                <select id="gpa-scale" name="gpa_scale">
                                    <option value="4.0">4.0 Scale</option>
                                    <option value="10.0">10.0 Scale</option>
                                    <option value="100">100 Scale</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="relevant-coursework">Relevant Coursework</label>
                            <textarea id="relevant-coursework" name="relevant_coursework" rows="3" 
                                placeholder="List relevant courses, separated by commas..."></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="academic-achievements">Academic Achievements</label>
                            <textarea id="academic-achievements" name="academic_achievements" rows="3" 
                                placeholder="Dean's List, scholarships, honors, etc."></textarea>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="closeEducationModal()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                Add Education
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('education-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = document.getElementById('education-modal');
    modal.classList.add('active');
    
    // Add form submit handler
    const form = document.getElementById('education-form');
    form.addEventListener('submit', handleEducationSubmit);
    
    // Focus first input
    document.getElementById('institution-name').focus();
}

function closeEducationModal() {
    const modal = document.getElementById('education-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

async function handleEducationSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Disable form during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';
    
    try {
        const formData = new FormData(form);
        const data = {};
        
        // Convert form data to object
        for (let [key, value] of formData.entries()) {
            if (value) {
                data[key] = value;
            }
        }
        
        // Convert MM/YY format to proper date format
        if (data.graduation_date) {
            data.graduation_date = convertMMYYToISO(data.graduation_date);
        }
        
        // Convert GPA to number if provided
        if (data.gpa) {
            data.gpa = parseFloat(data.gpa);
        }
        
        // Set default GPA scale if GPA is provided but scale is not
        if (data.gpa && !data.gpa_scale) {
            data.gpa_scale = 4.0;
        }
        
        // Add education via API
        const response = await window.api.createEducation(data);
        
        window.notifications.show('Education added successfully!', 'success');
        closeEducationModal();
        
        // Reload dataset to show new education
        await window.dataset.loadDataset();
        
    } catch (error) {
        console.error('Failed to add education:', error);
        
        let errorMessage = 'Failed to add education';
        if (error instanceof APIError) {
            if (error.status === 422) {
                errorMessage = 'Please check your input data and try again';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else {
                errorMessage = error.message || 'Failed to add education';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
    } finally {
        // Re-enable form
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}


function showAddProjectModal() {
    const modalHtml = `
        <div id="project-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Add Project</h3>
                    <button class="modal-close" onclick="closeProjectModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="project-form">
                        <div class="form-group">
                            <label for="project-name">Project Name *</label>
                            <input type="text" id="project-name" name="project_name" required placeholder="Enter project name">
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="project-type">Project Type</label>
                                <select id="project-type" name="project_type">
                                    <option value="">Select type</option>
                                    <option value="Web Application">Web Application</option>
                                    <option value="Mobile App">Mobile App</option>
                                    <option value="Desktop Application">Desktop Application</option>
                                    <option value="API/Backend">API/Backend</option>
                                    <option value="Data Analysis">Data Analysis</option>
                                    <option value="Machine Learning">Machine Learning</option>
                                    <option value="Research">Research</option>
                                    <option value="Open Source">Open Source</option>
                                    <option value="Academic">Academic</option>
                                    <option value="Personal">Personal</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="project-status">Status</label>
                                <select id="project-status" name="status">
                                    <option value="Completed">Completed</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="On Hold">On Hold</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="project-start-date">Start Date</label>
                                <input type="text" id="project-start-date" name="start_date" placeholder="MM/YY" pattern="^(0[1-9]|1[0-2])\/[0-9]{2}$" title="Please enter date in MM/YY format">
                                <small class="form-hint">Format: MM/YY (e.g., 01/23)</small>
                            </div>
                            <div class="form-group">
                                <label for="project-end-date">End Date</label>
                                <input type="text" id="project-end-date" name="end_date" placeholder="MM/YY" pattern="^(0[1-9]|1[0-2])\/[0-9]{2}$" title="Please enter date in MM/YY format">
                                <small class="form-hint">Format: MM/YY (e.g., 03/23)</small>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="project-description">Description *</label>
                            <textarea id="project-description" name="description" rows="4" required
                                placeholder="Describe what the project does, its purpose, and key features..."></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="technologies-used">Technologies Used</label>
                            <input type="text" id="technologies-used" name="technologies_used" 
                                placeholder="e.g., React, Node.js, PostgreSQL, AWS">
                            <small class="form-hint">Separate multiple technologies with commas</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="project-url">Project URL</label>
                            <input type="url" id="project-url" name="project_url" 
                                placeholder="https://github.com/username/project or live demo URL">
                        </div>
                        
                        <div class="form-group">
                            <label for="project-role">Your Role</label>
                            <input type="text" id="project-role" name="role" 
                                placeholder="e.g., Full-stack Developer, Team Lead, Solo Developer">
                        </div>
                        
                        <div class="form-group">
                            <label for="key-achievements">Key Achievements</label>
                            <textarea id="key-achievements" name="key_achievements" rows="3" 
                                placeholder="• Highlight major accomplishments&#10;• Include metrics or impact where possible&#10;• Focus on technical challenges solved"></textarea>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="closeProjectModal()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                Add Project
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('project-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = document.getElementById('project-modal');
    modal.classList.add('active');
    
    // Add form submit handler
    const form = document.getElementById('project-form');
    form.addEventListener('submit', handleProjectSubmit);
    
    // Focus first input
    document.getElementById('project-name').focus();
}

function closeProjectModal() {
    const modal = document.getElementById('project-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

async function handleProjectSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Disable form during submission
    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';
    
    try {
        const formData = new FormData(form);
        const data = {};
        
        // Convert form data to object
        for (let [key, value] of formData.entries()) {
            if (value) {
                data[key] = value;
            }
        }
        
        // Convert MM/YY format to proper date format
        if (data.start_date) {
            data.start_date = convertMMYYToISO(data.start_date);
        }
        if (data.end_date) {
            data.end_date = convertMMYYToISO(data.end_date);
        }
        
        // Convert technologies string to array
        if (data.technologies_used) {
            data.technologies_used = data.technologies_used.split(',').map(tech => tech.trim()).filter(tech => tech);
        }
        
        // Add project via API
        const response = await window.api.createProject(data);
        
        window.notifications.show('Project added successfully!', 'success');
        closeProjectModal();
        
        // Reload dataset to show new project
        await window.dataset.loadDataset();
        
    } catch (error) {
        console.error('Failed to add project:', error);
        
        let errorMessage = 'Failed to add project';
        if (error instanceof APIError) {
            if (error.status === 422) {
                errorMessage = 'Please check your input data and try again';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else {
                errorMessage = error.message || 'Failed to add project';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
    } finally {
        // Re-enable form
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}
