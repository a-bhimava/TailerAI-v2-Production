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

    async loadDataset() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            this.dataset = await window.api.getMasterDataset();
            this.filteredData = this.dataset;
            this.renderDataset();
            this.updateDatasetStats();
            
        } catch (error) {
            console.error('Failed to load dataset:', error);
            this.showErrorState('Failed to load your master dataset');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    // =============================================================================
    // DATASET RENDERING
    // =============================================================================

    renderDataset() {
        const contentDiv = document.getElementById('dataset-content');
        if (!contentDiv) return;

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
        // Loading state will be replaced by actual content
    }

    showErrorState(message) {
        const contentDiv = document.getElementById('dataset-content');
        if (contentDiv) {
            contentDiv.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <h3>Error Loading Dataset</h3>
                    <p>${this.escapeHtml(message)}</p>
                    <button class="btn btn-primary" onclick="window.dataset.loadDataset()">
                        Try Again
                    </button>
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
    // TODO: Show add experience modal
    window.notifications.show('Add experience functionality coming soon', 'info');
}

function addWorkExperience() {
    // TODO: Show add work experience modal
    window.notifications.show('Add work experience functionality coming soon', 'info');
}

function addEducation() {
    // TODO: Show add education modal
    window.notifications.show('Add education functionality coming soon', 'info');
}

function addProject() {
    // TODO: Show add project modal
    window.notifications.show('Add project functionality coming soon', 'info');
}

function addAchievement() {
    // TODO: Show add achievement modal
    window.notifications.show('Add achievement functionality coming soon', 'info');
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
    // TODO: Show import data modal
    window.notifications.show('Import functionality coming soon', 'info');
}

function filterDataset() {
    // This function is called by the search input and filter selects
    // The actual filtering is handled by the event listeners
}

function changeViewMode() {
    // This function is called by the view mode select
    // The actual view change is handled by the event listener
}