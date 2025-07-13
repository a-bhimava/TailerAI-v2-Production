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
            // Prevent multiple simultaneous loads
            if (this.isLoading) {
                return;
            }
            
            // Load dataset after successful login with small delay for OAuth completion
            const currentRoute = window.navigation?.getCurrentRoute();
            if (currentRoute === 'master-dataset') {
                // Small delay to ensure OAuth profile creation is complete
                setTimeout(() => {
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
        if (this.isLoading && retryCount === 0) {
            return;
        }
        
        // Check if user is authenticated before loading
        if (!window.api.isAuthenticated()) {
            this.showEmptyState();
            return;
        }
        
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
            const response = await window.api.getMasterDataset();
            
            // Log the full response for debugging
            console.log('Full API response:', response);
            
            // Check if response indicates an error
            if (response.success === false) {
                console.error('API returned error:', response.message);
                if (response.errors && response.errors.length > 0) {
                    console.error('Error details:', response.errors);
                    console.error('First error detail:', response.errors[0]);
                }
                throw new Error(response.message || 'Failed to load dataset');
            }
            
            // Extract data from StandardResponse format
            this.dataset = response.data || response;
            this.filteredData = this.dataset;
            this.renderDataset();
            this.updateDatasetStats();
            
        } catch (error) {
            console.error('Failed to load dataset:', error);
            
            // Retry logic for user profile not found errors (common after OAuth)
            if (error.status === 404 && retryCount < 3) {
                setTimeout(() => {
                    this.isLoading = false;
                    this.loadDataset(retryCount + 1);
                }, (retryCount + 1) * 1000); // 1s, 2s, 3s delays
                return;
            }
            
            this.showErrorState('Failed to load your master dataset');
        } finally {
            if (retryCount === 0 || error?.status !== 404) {
                this.isLoading = false;
                this.hideLoadingState();
            }
        }
    }

    // =============================================================================
    // DATASET RENDERING
    // =============================================================================

    renderDataset() {
        const contentDiv = document.getElementById('dataset-content');
        if (!contentDiv) {
            return;
        }

        // Check if dataset is empty
        if (this.isDatasetEmpty()) {
            this.showEmptyState();
            return;
        }

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
        const contentDiv = document.getElementById('dataset-content');
        if (contentDiv) {
            // Clear the loading content - it will be replaced by renderDataset()
            const loadingState = contentDiv.querySelector('.loading-state');
            if (loadingState) {
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
    // Get work experience details for editing
    const workExp = window.dataset.dataset?.work_experiences?.find(exp => exp.id === id);
    
    if (!workExp) {
        window.notifications.show('Work experience not found', 'error');
        return;
    }
    
    showEditWorkExperienceModal(id, workExp);
}

function deleteWorkExperience(id) {
    // Get work experience details for confirmation
    const workExp = window.dataset.dataset?.work_experiences?.find(exp => exp.id === id);
    
    if (!workExp) {
        window.notifications.show('Work experience not found', 'error');
        return;
    }
    
    showDeleteWorkExperienceConfirmation(id, workExp);
}

function showDeleteWorkExperienceConfirmation(id, workExp) {
    const modalHtml = `
        <div id="delete-confirmation-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Confirm Deletion</h3>
                    <button class="modal-close" onclick="closeDeleteConfirmationModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="delete-warning">
                        <div class="warning-icon">⚠️</div>
                        <div class="warning-content">
                            <h4>Are you sure you want to delete this work experience?</h4>
                            <div class="experience-details">
                                <strong>${workExp.position_title}</strong> at <strong>${workExp.company_name}</strong>
                                <br>
                                <small>${formatDateRange(workExp.start_date, workExp.end_date)}</small>
                            </div>
                            <p class="warning-text">
                                This action cannot be undone. All associated achievements will also be permanently deleted.
                            </p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeDeleteConfirmationModal()">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-danger" onclick="confirmDeleteWorkExperience('${id}')">
                        Delete Permanently
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('delete-confirmation-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = document.getElementById('delete-confirmation-modal');
    modal.classList.add('active');
}

function closeDeleteConfirmationModal() {
    const modal = document.getElementById('delete-confirmation-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

async function confirmDeleteWorkExperience(id) {
    const deleteBtn = document.querySelector('#delete-confirmation-modal .btn-danger');
    const originalText = deleteBtn.textContent;
    
    // Disable button during deletion
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    
    try {
        // Call delete API
        const response = await window.api.deleteWorkExperience(id);
        
        if (response.success) {
            window.notifications.show('Work experience deleted successfully', 'success');
            closeDeleteConfirmationModal();
            
            // Reload dataset to reflect changes
            await window.dataset.loadDataset();
        } else {
            throw new Error(response.message || 'Failed to delete work experience');
        }
        
    } catch (error) {
        console.error('Failed to delete work experience:', error);
        
        let errorMessage = 'Failed to delete work experience';
        if (error instanceof APIError) {
            if (error.status === 404) {
                errorMessage = 'Work experience not found or already deleted';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else if (error.status === 403) {
                errorMessage = 'You do not have permission to delete this work experience';
            } else {
                errorMessage = error.message || 'Failed to delete work experience';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
        
        // Re-enable button
        deleteBtn.disabled = false;
        deleteBtn.textContent = originalText;
    }
}

// Helper function to format date range for display
function formatDateRange(startDate, endDate) {
    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    };
    
    const start = formatDate(startDate);
    const end = endDate ? formatDate(endDate) : 'Present';
    
    return `${start} - ${end}`;
}

function showDeleteEducationConfirmation(id, education) {
    const modalHtml = `
        <div id="delete-confirmation-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Confirm Deletion</h3>
                    <button class="modal-close" onclick="closeDeleteConfirmationModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="delete-warning">
                        <div class="warning-icon">⚠️</div>
                        <div class="warning-content">
                            <h4>Are you sure you want to delete this education entry?</h4>
                            <div class="experience-details">
                                <strong>${education.degree_type}</strong> in <strong>${education.field_of_study}</strong>
                                <br>
                                <small>${education.institution_name}</small>
                            </div>
                            <p class="warning-text">
                                This action cannot be undone.
                            </p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeDeleteConfirmationModal()">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-danger" onclick="confirmDeleteEducation('${id}')">
                        Delete Permanently
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('delete-confirmation-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal by adding active class
    const modal = document.getElementById('delete-confirmation-modal');
    if (modal) {
        // Add the active class to make it visible (CSS requirement)
        modal.classList.add('active');
    }
}

async function confirmDeleteEducation(id) {
    const deleteBtn = document.querySelector('#delete-confirmation-modal .btn-danger');
    const originalText = deleteBtn.textContent;
    
    // Disable button during deletion
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    
    try {
        // Call delete API
        const response = await window.api.deleteEducation(id);
        
        if (response.success) {
            window.notifications.show('Education entry deleted successfully', 'success');
            closeDeleteConfirmationModal();
            
            // Reload dataset to reflect changes
            await window.dataset.loadDataset();
        } else {
            throw new Error(response.message || 'Failed to delete education entry');
        }
        
    } catch (error) {
        console.error('Failed to delete education entry:', error);
        
        let errorMessage = 'Failed to delete education entry';
        if (error instanceof APIError) {
            if (error.status === 404) {
                errorMessage = 'Education entry not found or already deleted';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else if (error.status === 403) {
                errorMessage = 'You do not have permission to delete this education entry';
            } else {
                errorMessage = error.message || 'Failed to delete education entry';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
        
        // Re-enable button
        deleteBtn.disabled = false;
        deleteBtn.textContent = originalText;
    }
}

function showDeleteProjectConfirmation(id, project) {
    const modalHtml = `
        <div id="delete-confirmation-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Confirm Deletion</h3>
                    <button class="modal-close" onclick="closeDeleteConfirmationModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="delete-warning">
                        <div class="warning-icon">⚠️</div>
                        <div class="warning-content">
                            <h4>Are you sure you want to delete this project?</h4>
                            <div class="experience-details">
                                <strong>${project.project_name}</strong>
                                <br>
                                <small>${project.project_type || 'Project'}</small>
                            </div>
                            <p class="warning-text">
                                This action cannot be undone.
                            </p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeDeleteConfirmationModal()">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-danger" onclick="confirmDeleteProject('${id}')">
                        Delete Permanently
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('delete-confirmation-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = document.getElementById('delete-confirmation-modal');
    modal.style.display = 'flex';
}

async function confirmDeleteProject(id) {
    const deleteBtn = document.querySelector('#delete-confirmation-modal .btn-danger');
    const originalText = deleteBtn.textContent;
    
    // Disable button during deletion
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    
    try {
        // Call delete API
        const response = await window.api.deleteProject(id);
        
        if (response.success) {
            window.notifications.show('Project deleted successfully', 'success');
            closeDeleteConfirmationModal();
            
            // Reload dataset to reflect changes
            await window.dataset.loadDataset();
        } else {
            throw new Error(response.message || 'Failed to delete project');
        }
        
    } catch (error) {
        console.error('Failed to delete project:', error);
        
        let errorMessage = 'Failed to delete project';
        if (error instanceof APIError) {
            if (error.status === 404) {
                errorMessage = 'Project not found or already deleted';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else if (error.status === 403) {
                errorMessage = 'You do not have permission to delete this project';
            } else {
                errorMessage = error.message || 'Failed to delete project';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
        
        // Re-enable button
        deleteBtn.disabled = false;
        deleteBtn.textContent = originalText;
    }
}

function editEducation(id) {
    // Get education details for editing
    const education = window.dataset.dataset?.education?.find(edu => edu.id === id);
    
    if (!education) {
        window.notifications.show('Education entry not found', 'error');
        return;
    }
    
    showEditEducationModal(id, education);
}

function deleteEducation(id) {
    // Get education details for confirmation
    const education = window.dataset.dataset?.education?.find(edu => edu.id === id);
    
    if (!education) {
        window.notifications.show('Education entry not found', 'error');
        return;
    }
    
    showDeleteEducationConfirmation(id, education);
}

function editProject(id) {
    // Get project details for editing
    const project = window.dataset.dataset?.projects?.find(proj => proj.id === id);
    
    if (!project) {
        window.notifications.show('Project not found', 'error');
        return;
    }
    
    showEditProjectModal(id, project);
}

function deleteProject(id) {
    // Get project details for confirmation
    const project = window.dataset.dataset?.projects?.find(proj => proj.id === id);
    
    if (!project) {
        window.notifications.show('Project not found', 'error');
        return;
    }
    
    showDeleteProjectConfirmation(id, project);
}

function editAchievement(id) {
    // TODO: Show edit achievement modal
    window.notifications.show('Edit functionality coming soon', 'info');
}

function deleteAchievement(id) {
    // TODO: Show delete confirmation
    window.notifications.show('Delete functionality coming soon', 'info');
}

// =============================================================================
// EDIT MODAL FUNCTIONS
// =============================================================================

function showEditEducationModal(id, education) {
    const modalHtml = `
        <div id="edit-education-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Edit Education Entry</h3>
                    <button class="modal-close" onclick="closeEditEducationModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="edit-education-form">
                        <div class="form-group">
                            <label for="edit-institution-name">Institution Name *</label>
                            <input type="text" id="edit-institution-name" name="institution_name" 
                                   value="${education.institution_name || ''}" required>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-degree-type">Degree Type *</label>
                                <select id="edit-degree-type" name="degree_type" required>
                                    <option value="Bachelor's" ${education.degree_type === "Bachelor's" ? 'selected' : ''}>Bachelor's</option>
                                    <option value="Master's" ${education.degree_type === "Master's" ? 'selected' : ''}>Master's</option>
                                    <option value="PhD" ${education.degree_type === 'PhD' ? 'selected' : ''}>PhD</option>
                                    <option value="Associate" ${education.degree_type === 'Associate' ? 'selected' : ''}>Associate</option>
                                    <option value="Certificate" ${education.degree_type === 'Certificate' ? 'selected' : ''}>Certificate</option>
                                    <option value="Diploma" ${education.degree_type === 'Diploma' ? 'selected' : ''}>Diploma</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="edit-field-of-study">Field of Study *</label>
                                <input type="text" id="edit-field-of-study" name="field_of_study" 
                                       value="${education.field_of_study || ''}" required>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-start-date">Start Date</label>
                                <input type="date" id="edit-start-date" name="start_date" 
                                       value="${education.start_date ? education.start_date.split('T')[0] : ''}">
                            </div>
                            <div class="form-group">
                                <label for="edit-graduation-date">Graduation Date</label>
                                <input type="date" id="edit-graduation-date" name="graduation_date" 
                                       value="${education.end_date ? education.end_date.split('T')[0] : education.graduation_date ? education.graduation_date.split('T')[0] : ''}">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-gpa">GPA</label>
                                <input type="number" id="edit-gpa" name="gpa" step="0.01" min="0" max="10"
                                       value="${education.gpa || ''}">
                            </div>
                            <div class="form-group">
                                <label for="edit-gpa-scale">GPA Scale</label>
                                <select id="edit-gpa-scale" name="gpa_scale">
                                    <option value="4.0" ${education.gpa_scale == 4.0 ? 'selected' : ''}>4.0</option>
                                    <option value="5.0" ${education.gpa_scale == 5.0 ? 'selected' : ''}>5.0</option>
                                    <option value="10.0" ${education.gpa_scale == 10.0 ? 'selected' : ''}>10.0</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-location">Location</label>
                            <input type="text" id="edit-location" name="location" 
                                   value="${education.location || ''}" 
                                   placeholder="City, State/Country">
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-relevant-coursework">Relevant Coursework</label>
                            <textarea id="edit-relevant-coursework" name="relevant_coursework" 
                                      placeholder="List relevant courses separated by commas">${Array.isArray(education.relevant_coursework) ? education.relevant_coursework.join(', ') : education.relevant_coursework || ''}</textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-academic-achievements">Academic Achievements</label>
                            <textarea id="edit-academic-achievements" name="academic_achievements" 
                                      placeholder="Dean's List, Academic Honors, etc.">${Array.isArray(education.academic_achievements) ? education.academic_achievements.join(', ') : education.academic_achievements || ''}</textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-honors-awards">Honors & Awards</label>
                            <textarea id="edit-honors-awards" name="honors_awards" 
                                      placeholder="Scholarships, awards, recognitions">${Array.isArray(education.honors_awards) ? education.honors_awards.join(', ') : education.honors_awards || ''}</textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeEditEducationModal()">Cancel</button>
                    <button type="button" class="btn-primary" onclick="saveEducationChanges('${id}')">Save Changes</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing modal
    const existingModal = document.getElementById('edit-education-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal by adding active class
    const modal = document.getElementById('edit-education-modal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeEditEducationModal() {
    const modal = document.getElementById('edit-education-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

async function saveEducationChanges(id) {
    const saveBtn = document.querySelector('#edit-education-modal .btn-primary');
    const originalText = saveBtn.textContent;
    
    // Disable button during save
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        // Collect form data
        const form = document.getElementById('edit-education-form');
        const formData = new FormData(form);
        const educationData = {};
        
        for (let [key, value] of formData.entries()) {
            // Only process non-empty values
            if (value && value.trim() && value.trim().length > 0) {
                // Handle text fields (coursework, achievements, honors) - keep as strings
                if (key === 'relevant_coursework' || key === 'academic_achievements' || key === 'honors_awards') {
                    // Backend expects strings, not arrays
                    educationData[key] = value.trim();
                } else if (key === 'gpa' || key === 'gpa_scale') {
                    const numValue = parseFloat(value);
                    if (!isNaN(numValue)) {
                        educationData[key] = numValue;
                    }
                } else if (key === 'start_date' || key === 'graduation_date') {
                    try {
                        // Map graduation_date to end_date for API compatibility
                        const fieldName = key === 'graduation_date' ? 'end_date' : key;
                        educationData[fieldName] = new Date(value).toISOString();
                    } catch (e) {
                        console.warn(`Invalid date value for ${key}:`, value);
                    }
                } else {
                    // Only include string values that meet minimum length requirements
                    if (value.trim().length >= 1) {
                        educationData[key] = value.trim();
                    }
                }
            }
        }
        
        // Debug: log what data is being sent
        console.log('Sending education data:', educationData);
        
        // Call update API
        const response = await window.api.updateEducation(id, educationData);
        
        if (response.success) {
            window.notifications.show('Education entry updated successfully', 'success');
            closeEditEducationModal();
            
            // Reload dataset to show changes
            await window.dataset.loadDataset();
        } else {
            throw new Error(response.message || 'Failed to update education entry');
        }
        
    } catch (error) {
        console.error('Error updating education:', error);
        
        let errorMessage = 'Failed to update education entry';
        if (error instanceof APIError) {
            if (error.status === 404) {
                errorMessage = 'Education entry not found';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else if (error.status === 403) {
                errorMessage = 'You do not have permission to edit this education entry';
            } else {
                errorMessage = error.message || 'Failed to update education entry';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
        
        // Re-enable button
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }
}

function showEditWorkExperienceModal(id, workExp) {
    const modalHtml = `
        <div id="edit-work-experience-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Edit Work Experience</h3>
                    <button class="modal-close" onclick="closeEditWorkExperienceModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="edit-work-experience-form">
                        <div class="form-group">
                            <label for="edit-company-name">Company Name *</label>
                            <input type="text" id="edit-company-name" name="company_name" 
                                   value="${workExp.company_name || ''}" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-position-title">Position Title *</label>
                            <input type="text" id="edit-position-title" name="position_title" 
                                   value="${workExp.position_title || ''}" required>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-department">Department</label>
                                <input type="text" id="edit-department" name="department" 
                                       value="${workExp.department || ''}">
                            </div>
                            <div class="form-group">
                                <label for="edit-employment-type">Employment Type</label>
                                <select id="edit-employment-type" name="employment_type">
                                    <option value="full-time" ${workExp.employment_type === 'full-time' ? 'selected' : ''}>Full-time</option>
                                    <option value="part-time" ${workExp.employment_type === 'part-time' ? 'selected' : ''}>Part-time</option>
                                    <option value="internship" ${workExp.employment_type === 'internship' ? 'selected' : ''}>Internship</option>
                                    <option value="contract" ${workExp.employment_type === 'contract' ? 'selected' : ''}>Contract</option>
                                    <option value="freelance" ${workExp.employment_type === 'freelance' ? 'selected' : ''}>Freelance</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-start-date">Start Date *</label>
                                <input type="date" id="edit-start-date" name="start_date" 
                                       value="${workExp.start_date ? workExp.start_date.split('T')[0] : ''}" required>
                            </div>
                            <div class="form-group">
                                <label for="edit-end-date">End Date</label>
                                <input type="date" id="edit-end-date" name="end_date" 
                                       value="${workExp.end_date ? workExp.end_date.split('T')[0] : ''}"
                                       ${workExp.is_current ? 'disabled' : ''}>
                            </div>
                        </div>
                        
                        <div class="checkbox-group">
                            <label>
                                <input type="checkbox" id="edit-is-current" name="is_current" 
                                       ${workExp.is_current ? 'checked' : ''} 
                                       onchange="toggleEndDate(this, 'edit-end-date')">
                                I currently work here
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-location">Location</label>
                            <input type="text" id="edit-location" name="location" 
                                   value="${workExp.location || ''}" 
                                   placeholder="City, State/Country">
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-job-description">Job Description</label>
                            <textarea id="edit-job-description" name="job_description" 
                                      placeholder="Describe your role and responsibilities">${workExp.job_description || ''}</textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeEditWorkExperienceModal()">Cancel</button>
                    <button type="button" class="btn-primary" onclick="saveWorkExperienceChanges('${id}')">Save Changes</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing modal
    const existingModal = document.getElementById('edit-work-experience-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal by adding active class
    const modal = document.getElementById('edit-work-experience-modal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeEditWorkExperienceModal() {
    const modal = document.getElementById('edit-work-experience-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

async function saveWorkExperienceChanges(id) {
    const saveBtn = document.querySelector('#edit-work-experience-modal .btn-primary');
    const originalText = saveBtn.textContent;
    
    // Disable button during save
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        // Collect form data
        const form = document.getElementById('edit-work-experience-form');
        const formData = new FormData(form);
        const experienceData = {};
        
        for (let [key, value] of formData.entries()) {
            // Handle date fields
            if (key === 'start_date' || key === 'end_date') {
                if (value && value.trim() && value.trim().length > 0) {
                    try {
                        experienceData[key] = new Date(value).toISOString();
                    } catch (e) {
                        console.warn(`Invalid date value for ${key}:`, value);
                    }
                }
            }
            // Handle fields that should always be included (even if empty)
            else if (key === 'job_description' || key === 'department' || key === 'company_description' || key === 'role_summary') {
                // Always include these fields, even if empty (backend will handle conversion)
                experienceData[key] = value ? value.trim() : '';
            }
            // Handle other fields (only include if not empty)
            else if (value && value.trim() && value.trim().length > 0) {
                experienceData[key] = value.trim();
            }
        }
        
        // Handle is_current checkbox
        const isCurrentCheckbox = document.getElementById('edit-is-current');
        experienceData.is_current = isCurrentCheckbox.checked;
        
        // If current position, remove end_date
        if (experienceData.is_current) {
            experienceData.end_date = null;
        }
        
        // Debug: log what data is being sent
        console.log('Sending work experience data:', experienceData);
        
        // Call update API
        const response = await window.api.updateWorkExperience(id, experienceData);
        
        if (response.success) {
            window.notifications.show('Work experience updated successfully', 'success');
            closeEditWorkExperienceModal();
            
            // Reload dataset to show changes
            await window.dataset.loadDataset();
        } else {
            throw new Error(response.message || 'Failed to update work experience');
        }
        
    } catch (error) {
        console.error('Error updating work experience:', error);
        
        let errorMessage = 'Failed to update work experience';
        if (error instanceof APIError) {
            if (error.status === 404) {
                errorMessage = 'Work experience not found';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else if (error.status === 403) {
                errorMessage = 'You do not have permission to edit this work experience';
            } else {
                errorMessage = error.message || 'Failed to update work experience';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
        
        // Re-enable button
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }
}

function toggleEndDate(checkbox, endDateId) {
    const endDateInput = document.getElementById(endDateId);
    if (checkbox.checked) {
        endDateInput.disabled = true;
        endDateInput.value = '';
    } else {
        endDateInput.disabled = false;
    }
}

function showEditProjectModal(id, project) {
    const modalHtml = `
        <div id="edit-project-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Edit Project</h3>
                    <button class="modal-close" onclick="closeEditProjectModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="edit-project-form">
                        <div class="form-group">
                            <label for="edit-project-name">Project Name *</label>
                            <input type="text" id="edit-project-name" name="project_name" 
                                   value="${project.project_name || ''}" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-project-type">Project Type</label>
                            <select id="edit-project-type" name="project_type">
                                <option value="" ${!project.project_type ? 'selected' : ''}>Select type</option>
                                <option value="Web Application" ${project.project_type === 'Web Application' ? 'selected' : ''}>Web Application</option>
                                <option value="Mobile Application" ${project.project_type === 'Mobile Application' ? 'selected' : ''}>Mobile Application</option>
                                <option value="Desktop Application" ${project.project_type === 'Desktop Application' ? 'selected' : ''}>Desktop Application</option>
                                <option value="API/Backend" ${project.project_type === 'API/Backend' ? 'selected' : ''}>API/Backend</option>
                                <option value="Data Analysis" ${project.project_type === 'Data Analysis' ? 'selected' : ''}>Data Analysis</option>
                                <option value="Machine Learning" ${project.project_type === 'Machine Learning' ? 'selected' : ''}>Machine Learning</option>
                                <option value="Research" ${project.project_type === 'Research' ? 'selected' : ''}>Research</option>
                                <option value="Other" ${project.project_type === 'Other' ? 'selected' : ''}>Other</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-project-description">Project Description</label>
                            <textarea id="edit-project-description" name="project_description" 
                                      placeholder="Describe what this project does and its purpose">${project.project_description || project.description || ''}</textarea>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-project-start-date">Start Date</label>
                                <input type="date" id="edit-project-start-date" name="start_date" 
                                       value="${project.start_date ? project.start_date.split('T')[0] : ''}">
                            </div>
                            <div class="form-group">
                                <label for="edit-project-end-date">End Date</label>
                                <input type="date" id="edit-project-end-date" name="end_date" 
                                       value="${project.end_date ? project.end_date.split('T')[0] : ''}">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-technologies-used">Technologies Used</label>
                            <input type="text" id="edit-technologies-used" name="technologies_used" 
                                   value="${project.technologies_used || ''}" 
                                   placeholder="e.g., React, Node.js, Python, etc.">
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-project-url">Project URL</label>
                                <input type="url" id="edit-project-url" name="project_url" 
                                       value="${project.project_url || ''}" 
                                       placeholder="https://example.com">
                            </div>
                            <div class="form-group">
                                <label for="edit-repository-url">Repository URL</label>
                                <input type="url" id="edit-repository-url" name="repository_url" 
                                       value="${project.repository_url || ''}" 
                                       placeholder="https://github.com/username/repo">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="edit-project-role">Your Role</label>
                                <input type="text" id="edit-project-role" name="role" 
                                       value="${project.role || ''}" 
                                       placeholder="e.g., Lead Developer, Team Member">
                            </div>
                            <div class="form-group">
                                <label for="edit-team-size">Team Size</label>
                                <input type="number" id="edit-team-size" name="team_size" min="1" max="100"
                                       value="${project.team_size || ''}" 
                                       placeholder="Number of team members">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-key-achievements">Key Achievements</label>
                            <textarea id="edit-key-achievements" name="key_achievements" 
                                      placeholder="What did you accomplish? What problems did you solve?">${project.key_achievements || ''}</textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="edit-project-metrics">Metrics & Results</label>
                            <textarea id="edit-project-metrics" name="metrics" 
                                      placeholder="Performance improvements, user adoption, cost savings, etc.">${project.metrics || ''}</textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeEditProjectModal()">Cancel</button>
                    <button type="button" class="btn-primary" onclick="saveProjectChanges('${id}')">Save Changes</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing modal
    const existingModal = document.getElementById('edit-project-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal by adding active class
    const modal = document.getElementById('edit-project-modal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeEditProjectModal() {
    const modal = document.getElementById('edit-project-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

async function saveProjectChanges(id) {
    const saveBtn = document.querySelector('#edit-project-modal .btn-primary');
    const originalText = saveBtn.textContent;
    
    // Disable button during save
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        // Collect form data
        const form = document.getElementById('edit-project-form');
        const formData = new FormData(form);
        const projectData = {};
        
        for (let [key, value] of formData.entries()) {
            // Handle fields that should always be included (even if empty)
            if (key === 'project_description' || key === 'project_name') {
                // Always include these fields, even if empty (backend will handle validation)
                projectData[key] = value ? value.trim() : '';
            }
            // Only process non-empty values for other fields
            else if (value && value.trim() && value.trim().length > 0) {
                if (key === 'start_date' || key === 'end_date') {
                    try {
                        projectData[key] = new Date(value).toISOString();
                    } catch (e) {
                        console.warn(`Invalid date value for ${key}:`, value);
                    }
                } else if (key === 'team_size') {
                    const numValue = parseInt(value);
                    if (!isNaN(numValue) && numValue > 0) {
                        projectData[key] = numValue;
                    }
                } else {
                    // Only include string values that meet minimum length requirements
                    if (value.trim().length >= 1) {
                        projectData[key] = value.trim();
                    }
                }
            }
        }
        
        // Debug: log the project data being sent
        console.log('Project data being sent to API:', projectData);
        
        // Call update API
        const response = await window.api.updateProject(id, projectData);
        
        if (response.success) {
            window.notifications.show('Project updated successfully', 'success');
            closeEditProjectModal();
            
            // Reload dataset to show changes
            await window.dataset.loadDataset();
        } else {
            throw new Error(response.message || 'Failed to update project');
        }
        
    } catch (error) {
        console.error('Error updating project:', error);
        
        let errorMessage = 'Failed to update project';
        if (error instanceof APIError) {
            if (error.status === 404) {
                errorMessage = 'Project not found';
            } else if (error.status === 401) {
                errorMessage = 'Please sign in again';
            } else if (error.status === 403) {
                errorMessage = 'You do not have permission to edit this project';
            } else {
                errorMessage = error.message || 'Failed to update project';
            }
        }
        
        window.notifications.show(errorMessage, 'error');
        
        // Re-enable button
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }
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
            if (key !== 'is_current') {
                // Always include job_description, department, and other text fields even if empty
                if (key === 'job_description' || key === 'department' || key === 'company_description' || key === 'role_summary') {
                    data[key] = value || '';
                }
                // Only include other fields if they have values
                else if (value) {
                    data[key] = value;
                }
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
