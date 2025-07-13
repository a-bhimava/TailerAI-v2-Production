/**
 * Content Selection Module for TailerAI v2.0
 * Handles AI-powered content selection with interactive scoring and optimization
 * Following PROJECT_BLUEPRINT.md patterns for modularity and error handling
 */

class ContentSelectionManager {
    constructor() {
        this.currentJobAnalysis = null;
        this.masterDataset = null;
        this.selectedContent = null;
        this.contentScores = new Map();
        this.isProcessing = false;
        this.optimizationSettings = {
            targetWordCount: 450,
            onePageOptimization: true,
            priorityWeighting: {
                skills: 0.3,
                achievements: 0.4,
                experience: 0.2,
                keywords: 0.1
            }
        };
        
        // UI Elements
        this.jobSummaryContainer = null;
        this.contentContainer = null;
        this.scorePreviewContainer = null;
        this.optimizationPanel = null;
        this.progressIndicator = null;
        this.proceedButton = null;
        
        this.initialize();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initialize() {
        this.setupUIElements();
        this.setupEventListeners();
        this.loadJobAnalysis();
        this.loadMasterDataset();
    }

    setupUIElements() {
        this.jobSummaryContainer = document.getElementById('job-analysis-summary');
        this.contentContainer = document.getElementById('content-selection-grid');
        this.scorePreviewContainer = document.getElementById('selection-score-preview');
        this.optimizationPanel = document.getElementById('optimization-settings');
        this.progressIndicator = document.getElementById('content-selection-progress');
        this.proceedButton = document.getElementById('proceed-to-preview-btn');
    }

    setupEventListeners() {
        // Listen for navigation events
        window.addEventListener('navigation:routeChanged', (event) => {
            if (event.detail.route === 'content-selection') {
                this.loadJobAnalysis();
                this.loadMasterDataset();
            }
        });

        // Auto-selection button
        const autoSelectBtn = document.getElementById('auto-select-btn');
        if (autoSelectBtn) {
            autoSelectBtn.addEventListener('click', () => this.performAutoSelection());
        }

        // Manual selection toggles
        document.addEventListener('change', (event) => {
            if (event.target.classList.contains('content-item-checkbox')) {
                this.handleContentToggle(event);
            }
        });

        // Optimization settings changes
        document.addEventListener('input', (event) => {
            if (event.target.classList.contains('optimization-setting')) {
                this.handleOptimizationChange(event);
            }
        });

        // Proceed button
        if (this.proceedButton) {
            this.proceedButton.addEventListener('click', () => this.proceedToPreview());
        }
    }

    // =============================================================================
    // DATA LOADING
    // =============================================================================

    async loadJobAnalysis() {
        try {
            // First try to get from sessionStorage (from job analysis)
            const storedAnalysis = sessionStorage.getItem('currentJobAnalysis');
            if (storedAnalysis) {
                const parsedAnalysis = JSON.parse(storedAnalysis);
                // Validate the analysis structure
                if (this.validateJobAnalysis(parsedAnalysis)) {
                    this.currentJobAnalysis = parsedAnalysis;
                    this.displayJobSummary();
                    return;
                } else {
                    console.warn('Invalid job analysis structure:', parsedAnalysis);
                }
            }

            // If no stored analysis, show message to analyze job first
            this.showNoJobAnalysisMessage();
        } catch (error) {
            console.error('Failed to load job analysis:', error);
            sessionStorage.removeItem('currentJobAnalysis'); // Clear corrupted data
            this.showError('LoadingError', 'Failed to load job analysis data.');
            this.showNoJobAnalysisMessage();
        }
    }

    validateJobAnalysis(analysis) {
        // Check if analysis has required fields
        return analysis && 
               typeof analysis === 'object' &&
               analysis.analysis_id &&
               (analysis.position_title || analysis.company_name);
    }

    async loadMasterDataset() {
        if (this.isProcessing) return;

        try {
            this.isProcessing = true;
            this.showProgress('Loading your master dataset...');

            this.masterDataset = await window.api.getMasterDataset();
            
            if (this.isDatasetEmpty()) {
                this.showEmptyDatasetMessage();
            } else {
                this.renderContentSelection();
            }

        } catch (error) {
            // Handle auth errors gracefully - show empty state instead of error
            if (error.status === 403) {
                this.masterDataset = { data: { counts: { work_experiences: 0, achievements: 0, skills: 0, education: 0 } } };
                this.showEmptyDatasetMessage();
            } else {
                console.error('Failed to load master dataset:', error);
                this.showError('DatasetError', 'Failed to load your personal dataset.');
            }
        } finally {
            this.isProcessing = false;
            this.hideProgress();
        }
    }

    isDatasetEmpty() {
        if (!this.masterDataset) return true;
        
        const hasContent = (
            (this.masterDataset.work_experiences?.length > 0) ||
            (this.masterDataset.achievements?.length > 0) ||
            (this.masterDataset.projects?.length > 0) ||
            (this.masterDataset.education?.length > 0) ||
            (this.masterDataset.skills?.length > 0)
        );
        
        return !hasContent;
    }

    // =============================================================================
    // JOB ANALYSIS DISPLAY
    // =============================================================================

    displayJobSummary() {
        if (!this.jobSummaryContainer || !this.currentJobAnalysis) return;

        const analysis = this.currentJobAnalysis;
        const summaryHTML = `
            <div class="job-summary-content">
                <div class="job-header">
                    <div class="job-title-company">
                        <h3>${this.escapeHtml(analysis.position_title || 'Unknown Position')}</h3>
                        <p class="company-name">${this.escapeHtml(analysis.company_name || 'Unknown Company')}</p>
                    </div>
                    <div class="job-meta">
                        <span class="industry-tag">${this.escapeHtml(analysis.industry || 'Unknown Industry')}</span>
                        <span class="confidence-score">Confidence: ${(analysis.confidence_score * 100).toFixed(1)}%</span>
                    </div>
                </div>
                
                <div class="job-highlights">
                    <div class="highlight-section">
                        <h4>Key Requirements</h4>
                        <div class="tags-container">
                            ${this.renderSkillTags(analysis.required_skills, 'required')}
                        </div>
                    </div>
                    
                    <div class="highlight-section">
                        <h4>Important Keywords</h4>
                        <div class="tags-container">
                            ${this.renderKeywordTags(analysis.important_keywords)}
                        </div>
                    </div>
                </div>
                
                <div class="analysis-actions">
                    <button class="btn btn-outline btn-sm" onclick="navigateTo('job-analysis')">
                        Edit Analysis
                    </button>
                    <button class="btn btn-primary btn-sm" id="auto-select-btn">
                        Auto-Select Content
                    </button>
                </div>
            </div>
        `;

        this.jobSummaryContainer.innerHTML = summaryHTML;
        
        // Reattach event listener for auto-select button
        const autoSelectBtn = document.getElementById('auto-select-btn');
        if (autoSelectBtn) {
            autoSelectBtn.addEventListener('click', () => this.performAutoSelection());
        }
    }

    showNoJobAnalysisMessage() {
        if (!this.jobSummaryContainer) return;

        this.jobSummaryContainer.innerHTML = `
            <div class="no-analysis-message">
                <div class="message-icon">🔍</div>
                <h3>No Job Analysis Found</h3>
                <p>Please analyze a job description first to enable content selection.</p>
                <button class="btn btn-primary" onclick="navigateTo('job-analysis')">
                    Analyze Job Description
                </button>
            </div>
        `;
    }

    // =============================================================================
    // CONTENT SELECTION RENDERING
    // =============================================================================

    renderContentSelection() {
        if (!this.contentContainer || !this.masterDataset) return;

        let contentHTML = '';

        // Work Experiences Section
        if (this.masterDataset.work_experiences?.length > 0) {
            contentHTML += this.renderWorkExperiencesSection();
        }

        // Achievements Section
        if (this.masterDataset.achievements?.length > 0) {
            contentHTML += this.renderAchievementsSection();
        }

        // Projects Section
        if (this.masterDataset.projects?.length > 0) {
            contentHTML += this.renderProjectsSection();
        }

        // Education Section
        if (this.masterDataset.education?.length > 0) {
            contentHTML += this.renderEducationSection();
        }

        // Skills Section
        if (this.masterDataset.skills?.length > 0) {
            contentHTML += this.renderSkillsSection();
        }

        this.contentContainer.innerHTML = contentHTML;
        this.attachContentEventListeners();
        this.updateScorePreview();
    }

    renderWorkExperiencesSection() {
        const experiences = this.masterDataset.work_experiences;
        
        let html = `
            <div class="content-section" data-section="work-experiences">
                <div class="section-header">
                    <h3>Work Experiences</h3>
                    <div class="section-controls">
                        <button class="btn btn-sm btn-outline" onclick="selectAllInSection('work-experiences')">
                            Select All
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="clearAllInSection('work-experiences')">
                            Clear All
                        </button>
                    </div>
                </div>
                <div class="content-grid">
        `;

        experiences.forEach(exp => {
            const score = this.calculateContentScore(exp, 'work_experience');
            const isSelected = this.isContentSelected(exp.id, 'work_experience');
            
            html += `
                <div class="content-item ${isSelected ? 'selected' : ''}" data-id="${exp.id}" data-type="work_experience">
                    <div class="content-item-header">
                        <input type="checkbox" class="content-item-checkbox" ${isSelected ? 'checked' : ''}>
                        <div class="content-info">
                            <h4>${this.escapeHtml(exp.position_title)}</h4>
                            <p class="content-subtitle">${this.escapeHtml(exp.company_name)}</p>
                            <span class="content-period">${this.formatDateRange(exp.start_date, exp.end_date)}</span>
                        </div>
                        <div class="content-score">
                            <div class="score-circle ${this.getScoreClass(score)}">
                                ${score.toFixed(1)}
                            </div>
                        </div>
                    </div>
                    <div class="content-item-body">
                        <p class="content-description">${this.escapeHtml(exp.company_description || 'No description available')}</p>
                        ${this.renderExperienceAchievements(exp.id)}
                        <div class="content-keywords">
                            ${this.renderMatchedKeywords(exp, score)}
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderAchievementsSection() {
        // Only show standalone achievements (not linked to work experience)
        const achievements = this.masterDataset.achievements?.filter(a => !a.work_experience_id) || [];
        
        if (achievements.length === 0) return '';

        let html = `
            <div class="content-section" data-section="achievements">
                <div class="section-header">
                    <h3>Standalone Achievements</h3>
                    <div class="section-controls">
                        <button class="btn btn-sm btn-outline" onclick="selectAllInSection('achievements')">
                            Select All
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="clearAllInSection('achievements')">
                            Clear All
                        </button>
                    </div>
                </div>
                <div class="content-grid">
        `;

        achievements.forEach(achievement => {
            const score = this.calculateContentScore(achievement, 'achievement');
            const isSelected = this.isContentSelected(achievement.id, 'achievement');
            
            html += `
                <div class="content-item ${isSelected ? 'selected' : ''}" data-id="${achievement.id}" data-type="achievement">
                    <div class="content-item-header">
                        <input type="checkbox" class="content-item-checkbox" ${isSelected ? 'checked' : ''}>
                        <div class="content-info">
                            <h4>${this.escapeHtml(achievement.achievement_text)}</h4>
                            <p class="content-subtitle">${this.escapeHtml(achievement.category || 'General Achievement')}</p>
                            ${achievement.date_achieved ? `<span class="content-period">${this.formatDate(achievement.date_achieved)}</span>` : ''}
                        </div>
                        <div class="content-score">
                            <div class="score-circle ${this.getScoreClass(score)}">
                                ${score.toFixed(1)}
                            </div>
                        </div>
                    </div>
                    <div class="content-item-body">
                        ${achievement.quantified_result ? `<p class="quantified-result"><strong>Result:</strong> ${this.escapeHtml(achievement.quantified_result)}</p>` : ''}
                        ${achievement.impact_score ? `<p class="impact-score">Impact Score: ${achievement.impact_score}/10</p>` : ''}
                        <div class="content-keywords">
                            ${this.renderMatchedKeywords(achievement, score)}
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderProjectsSection() {
        const projects = this.masterDataset.projects;
        
        let html = `
            <div class="content-section" data-section="projects">
                <div class="section-header">
                    <h3>Projects</h3>
                    <div class="section-controls">
                        <button class="btn btn-sm btn-outline" onclick="selectAllInSection('projects')">
                            Select All
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="clearAllInSection('projects')">
                            Clear All
                        </button>
                    </div>
                </div>
                <div class="content-grid">
        `;

        projects.forEach(project => {
            const score = this.calculateContentScore(project, 'project');
            const isSelected = this.isContentSelected(project.id, 'project');
            
            html += `
                <div class="content-item ${isSelected ? 'selected' : ''}" data-id="${project.id}" data-type="project">
                    <div class="content-item-header">
                        <input type="checkbox" class="content-item-checkbox" ${isSelected ? 'checked' : ''}>
                        <div class="content-info">
                            <h4>${this.escapeHtml(project.project_name)}</h4>
                            <p class="content-subtitle">${this.escapeHtml(project.project_type || 'Project')}</p>
                            <span class="content-period">${this.formatDateRange(project.start_date, project.end_date)}</span>
                        </div>
                        <div class="content-score">
                            <div class="score-circle ${this.getScoreClass(score)}">
                                ${score.toFixed(1)}
                            </div>
                        </div>
                    </div>
                    <div class="content-item-body">
                        <p class="content-description">${this.escapeHtml(project.description || 'No description available')}</p>
                        ${project.technologies_used ? `<p class="technologies"><strong>Technologies:</strong> ${this.escapeHtml(project.technologies_used)}</p>` : ''}
                        <div class="content-keywords">
                            ${this.renderMatchedKeywords(project, score)}
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderEducationSection() {
        const education = this.masterDataset.education;
        
        let html = `
            <div class="content-section" data-section="education">
                <div class="section-header">
                    <h3>Education</h3>
                    <div class="section-controls">
                        <button class="btn btn-sm btn-outline" onclick="selectAllInSection('education')">
                            Select All
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="clearAllInSection('education')">
                            Clear All
                        </button>
                    </div>
                </div>
                <div class="content-grid">
        `;

        education.forEach(edu => {
            const score = this.calculateContentScore(edu, 'education');
            const isSelected = this.isContentSelected(edu.id, 'education');
            
            html += `
                <div class="content-item ${isSelected ? 'selected' : ''}" data-id="${edu.id}" data-type="education">
                    <div class="content-item-header">
                        <input type="checkbox" class="content-item-checkbox" ${isSelected ? 'checked' : ''}>
                        <div class="content-info">
                            <h4>${this.escapeHtml(edu.degree_type)} in ${this.escapeHtml(edu.field_of_study)}</h4>
                            <p class="content-subtitle">${this.escapeHtml(edu.institution_name)}</p>
                            <span class="content-period">${this.formatDate(edu.graduation_date)}</span>
                        </div>
                        <div class="content-score">
                            <div class="score-circle ${this.getScoreClass(score)}">
                                ${score.toFixed(1)}
                            </div>
                        </div>
                    </div>
                    <div class="content-item-body">
                        ${edu.relevant_coursework ? `<p><strong>Coursework:</strong> ${this.escapeHtml(edu.relevant_coursework)}</p>` : ''}
                        ${edu.gpa ? `<p><strong>GPA:</strong> ${edu.gpa}/${edu.gpa_scale || 4.0}</p>` : ''}
                        <div class="content-keywords">
                            ${this.renderMatchedKeywords(edu, score)}
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderSkillsSection() {
        const skills = this.masterDataset.skills;
        
        let html = `
            <div class="content-section" data-section="skills">
                <div class="section-header">
                    <h3>Skills</h3>
                    <div class="section-controls">
                        <button class="btn btn-sm btn-outline" onclick="selectAllInSection('skills')">
                            Select All
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="clearAllInSection('skills')">
                            Clear All
                        </button>
                    </div>
                </div>
                <div class="skills-grid">
        `;

        skills.forEach(skill => {
            const score = this.calculateContentScore(skill, 'skill');
            const isSelected = this.isContentSelected(skill.id, 'skill');
            
            html += `
                <div class="skill-item ${isSelected ? 'selected' : ''}" data-id="${skill.id}" data-type="skill">
                    <input type="checkbox" class="content-item-checkbox" ${isSelected ? 'checked' : ''}>
                    <div class="skill-info">
                        <span class="skill-name">${this.escapeHtml(skill.skill_name)}</span>
                        <span class="skill-score ${this.getScoreClass(score)}">${score.toFixed(1)}</span>
                    </div>
                    ${skill.proficiency_level ? `<span class="skill-level">${this.escapeHtml(skill.proficiency_level)}</span>` : ''}
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    // =============================================================================
    // SCORING & MATCHING
    // =============================================================================

    calculateContentScore(content, contentType) {
        if (!this.currentJobAnalysis) return 0;

        const analysis = this.currentJobAnalysis;
        let score = 0;
        
        // Get searchable text for the content item
        const contentText = this.getContentSearchableText(content, contentType);
        
        // Required skills matching (high weight)
        const requiredSkillsMatch = this.calculateSkillsMatch(contentText, analysis.required_skills);
        score += requiredSkillsMatch * 40;
        
        // Preferred skills matching (medium weight)
        const preferredSkillsMatch = this.calculateSkillsMatch(contentText, analysis.preferred_skills);
        score += preferredSkillsMatch * 25;
        
        // Important keywords matching (medium weight)
        const keywordsMatch = this.calculateKeywordsMatch(contentText, analysis.important_keywords);
        score += keywordsMatch * 20;
        
        // ATS keywords matching (medium weight)
        const atsMatch = this.calculateKeywordsMatch(contentText, analysis.ats_keywords);
        score += atsMatch * 15;
        
        // Store the score for later use
        this.contentScores.set(`${contentType}_${content.id}`, score);
        
        return Math.min(score, 100); // Cap at 100
    }

    calculateSkillsMatch(contentText, skillsJson) {
        try {
            // Handle various input types
            let skills;
            if (Array.isArray(skillsJson)) {
                skills = skillsJson;
            } else if (typeof skillsJson === 'string') {
                skills = skillsJson.trim() ? JSON.parse(skillsJson) : [];
            } else {
                skills = [];
            }
            
            if (!Array.isArray(skills) || !skills.length) return 0;
            if (!contentText || typeof contentText !== 'string') return 0;
            
            const contentLower = contentText.toLowerCase();
            const matchedSkills = skills.filter(skill => {
                if (typeof skill !== 'string') return false;
                return contentLower.includes(skill.toLowerCase());
            });
            
            return matchedSkills.length / skills.length;
        } catch (error) {
            console.error('Error calculating skills match:', error, skillsJson);
            return 0;
        }
    }

    calculateKeywordsMatch(contentText, keywordsJson) {
        try {
            // Handle various input types
            let keywords;
            if (Array.isArray(keywordsJson)) {
                keywords = keywordsJson;
            } else if (typeof keywordsJson === 'string') {
                keywords = keywordsJson.trim() ? JSON.parse(keywordsJson) : [];
            } else {
                keywords = [];
            }
            
            if (!Array.isArray(keywords) || !keywords.length) return 0;
            if (!contentText || typeof contentText !== 'string') return 0;
            
            const contentLower = contentText.toLowerCase();
            const matchedKeywords = keywords.filter(keyword => {
                if (typeof keyword !== 'string') return false;
                return contentLower.includes(keyword.toLowerCase());
            });
            
            return matchedKeywords.length / keywords.length;
        } catch (error) {
            console.error('Error calculating keywords match:', error, keywordsJson);
            return 0;
        }
    }

    getContentSearchableText(content, contentType) {
        switch (contentType) {
            case 'work_experience':
                return `${content.position_title} ${content.company_name} ${content.company_description || ''}`;
            case 'achievement':
                return `${content.achievement_text} ${content.category || ''} ${content.quantified_result || ''}`;
            case 'project':
                return `${content.project_name} ${content.description || ''} ${content.technologies_used || ''}`;
            case 'education':
                return `${content.degree_type} ${content.field_of_study} ${content.institution_name} ${content.relevant_coursework || ''}`;
            case 'skill':
                return `${content.skill_name} ${content.skill_category || ''}`;
            default:
                return JSON.stringify(content);
        }
    }

    // =============================================================================
    // AUTO SELECTION & OPTIMIZATION
    // =============================================================================

    async performAutoSelection() {
        if (!this.currentJobAnalysis || !this.masterDataset) {
            this.showError('MissingDataError', 'Job analysis and dataset must be loaded first.');
            return;
        }

        try {
            this.showProgress('Performing AI-powered content selection...');

            const response = await window.api.post('/api/v2/analysis/content-selection', {
                job_analysis_id: this.currentJobAnalysis.analysis_id
            });

            if (response.success) {
                this.applyAutoSelection(response);
                this.showSuccess('Auto-selection completed successfully!');
            } else {
                throw new Error(response.message || 'Auto-selection failed');
            }

        } catch (error) {
            console.error('Auto-selection failed:', error);
            this.showError('AutoSelectionError', 'AI selection failed. Using manual scoring fallback.');
            this.performFallbackSelection();
        } finally {
            this.hideProgress();
        }
    }

    applyAutoSelection(response) {
        // Clear current selection
        this.clearAllSelections();
        
        // Apply selections from API response
        try {
            if (response.selected_achievements) {
                response.selected_achievements.forEach(item => {
                    this.selectContent(item.content_id, 'achievement', true);
                });
            }
            
            if (response.selected_work_experiences) {
                response.selected_work_experiences.forEach(item => {
                    this.selectContent(item.content_id, 'work_experience', true);
                });
            }
            
            if (response.selected_projects) {
                response.selected_projects.forEach(item => {
                    this.selectContent(item.content_id, 'project', true);
                });
            }
            
            if (response.selected_education) {
                response.selected_education.forEach(item => {
                    this.selectContent(item.content_id, 'education', true);
                });
            }
            
            if (response.selected_skills) {
                response.selected_skills.forEach(item => {
                    this.selectContent(item.content_id, 'skill', true);
                });
            }
            
            this.updateScorePreview();
            this.renderContentSelection(); // Re-render to show selections
        } catch (error) {
            console.error('Error applying auto-selection:', error);
            this.performFallbackSelection();
        }
    }

    performFallbackSelection() {
        // Clear current selection
        this.clearAllSelections();
        
        // Select top-scoring items with word count constraint
        const scoredItems = this.getAllScoredItems();
        const sortedItems = scoredItems.sort((a, b) => b.score - a.score);
        
        let totalWordCount = 0;
        const targetWordCount = this.optimizationSettings.targetWordCount;
        
        for (const item of sortedItems) {
            const estimatedWords = this.estimateWordCount(item);
            
            if (totalWordCount + estimatedWords <= targetWordCount) {
                this.selectContent(item.id, item.type, true);
                totalWordCount += estimatedWords;
            }
            
            if (totalWordCount >= targetWordCount * 0.9) break; // 90% of target
        }
        
        this.updateScorePreview();
        this.renderContentSelection(); // Re-render to show selections
    }

    // =============================================================================
    // CONTENT SELECTION MANAGEMENT
    // =============================================================================

    handleContentToggle(event) {
        const checkbox = event.target;
        const contentItem = checkbox.closest('.content-item, .skill-item');
        const contentId = contentItem.dataset.id;
        const contentType = contentItem.dataset.type;
        
        this.selectContent(contentId, contentType, checkbox.checked);
        this.updateScorePreview();
    }

    selectContent(contentId, contentType, isSelected) {
        if (!this.selectedContent) {
            this.selectedContent = new Set();
        }
        
        const key = `${contentType}_${contentId}`;
        
        if (isSelected) {
            this.selectedContent.add(key);
        } else {
            this.selectedContent.delete(key);
        }
        
        // Update UI
        const contentItem = document.querySelector(`[data-id="${contentId}"][data-type="${contentType}"]`);
        if (contentItem) {
            contentItem.classList.toggle('selected', isSelected);
            const checkbox = contentItem.querySelector('.content-item-checkbox');
            if (checkbox) {
                checkbox.checked = isSelected;
            }
        }
    }

    isContentSelected(contentId, contentType) {
        if (!this.selectedContent) return false;
        return this.selectedContent.has(`${contentType}_${contentId}`);
    }

    clearAllSelections() {
        this.selectedContent = new Set();
        
        // Update UI
        document.querySelectorAll('.content-item, .skill-item').forEach(item => {
            item.classList.remove('selected');
            const checkbox = item.querySelector('.content-item-checkbox');
            if (checkbox) checkbox.checked = false;
        });
        
        this.updateScorePreview();
    }

    // =============================================================================
    // SCORE PREVIEW & OPTIMIZATION
    // =============================================================================

    updateScorePreview() {
        if (!this.scorePreviewContainer) return;
        
        const selectedItems = this.getSelectedItems();
        const totalScore = this.calculateTotalScore(selectedItems);
        const estimatedWordCount = this.calculateTotalWordCount(selectedItems);
        const keywordCoverage = this.calculateKeywordCoverage(selectedItems);
        
        const previewHTML = `
            <div class="score-preview-content">
                <div class="score-metrics">
                    <div class="metric">
                        <div class="metric-value ${this.getScoreClass(totalScore)}">${totalScore.toFixed(1)}</div>
                        <div class="metric-label">Overall Score</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value ${estimatedWordCount > 500 ? 'high' : estimatedWordCount < 400 ? 'low' : 'medium'}">${estimatedWordCount}</div>
                        <div class="metric-label">Est. Words</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value ${this.getScoreClass(keywordCoverage * 100)}">${(keywordCoverage * 100).toFixed(1)}%</div>
                        <div class="metric-label">Keyword Coverage</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value ${selectedItems.length > 0 ? 'medium' : 'low'}">${selectedItems.length}</div>
                        <div class="metric-label">Items Selected</div>
                    </div>
                </div>
                
                <div class="optimization-status">
                    ${this.renderOptimizationStatus(estimatedWordCount, totalScore, keywordCoverage)}
                </div>
                
                <div class="selection-breakdown">
                    ${this.renderSelectionBreakdown(selectedItems)}
                </div>
            </div>
        `;
        
        this.scorePreviewContainer.innerHTML = previewHTML;
        
        // Update proceed button state
        if (this.proceedButton) {
            this.proceedButton.disabled = selectedItems.length === 0;
        }
    }

    // =============================================================================
    // UTILITY METHODS
    // =============================================================================

    renderSkillTags(skillsJson, type = '') {
        try {
            const skills = Array.isArray(skillsJson) ? skillsJson : JSON.parse(skillsJson || '[]');
            return skills.slice(0, 5).map(skill => 
                `<span class="tag ${type}">${this.escapeHtml(skill)}</span>`
            ).join('');
        } catch (error) {
            return '<span class="tag error">Error parsing skills</span>';
        }
    }

    renderKeywordTags(keywordsJson) {
        try {
            const keywords = Array.isArray(keywordsJson) ? keywordsJson : JSON.parse(keywordsJson || '[]');
            return keywords.slice(0, 8).map(keyword => 
                `<span class="tag keyword">${this.escapeHtml(keyword)}</span>`
            ).join('');
        } catch (error) {
            return '<span class="tag error">Error parsing keywords</span>';
        }
    }

    getScoreClass(score) {
        if (score >= 80) return 'high';
        if (score >= 60) return 'medium';
        if (score >= 40) return 'low';
        return 'very-low';
    }

    formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
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

    showProgress(message) {
        if (this.progressIndicator) {
            this.progressIndicator.innerHTML = `
                <div class="progress-content">
                    <div class="spinner"></div>
                    <span>${message}</span>
                </div>
            `;
            this.progressIndicator.style.display = 'block';
        }
    }

    hideProgress() {
        if (this.progressIndicator) {
            this.progressIndicator.style.display = 'none';
        }
    }

    showError(errorType, message) {
        console.error(`${errorType}: ${message}`);
        if (window.showNotification) {
            window.showNotification(message, 'error');
        }
    }

    showSuccess(message) {
        if (window.showNotification) {
            window.showNotification(message, 'success');
        }
    }

    showEmptyDatasetMessage() {
        if (this.contentContainer) {
            const isAuthenticated = window.api.isAuthenticated();
            const message = isAuthenticated 
                ? `<div class="empty-dataset-message">
                    <div class="message-icon">📝</div>
                    <h3>No Personal Data Found</h3>
                    <p>Please add your work experiences, achievements, and skills to your master dataset first.</p>
                    <button class="btn btn-primary" onclick="navigateTo('master-dataset')">
                        Build Your Dataset
                    </button>
                </div>`
                : `<div class="empty-dataset-message">
                    <div class="message-icon">🔐</div>
                    <h3>Sign In Required</h3>
                    <p>Please sign in to access your personal master dataset and content selection features.</p>
                    <button class="btn btn-primary" onclick="window.auth.showModal()">
                        Sign In
                    </button>
                    <p class="guest-note">You can still analyze job descriptions without signing in.</p>
                </div>`;
            
            this.contentContainer.innerHTML = message;
        }
    }

    proceedToPreview() {
        if (!this.selectedContent || this.selectedContent.size === 0) {
            this.showError('NoContentError', 'Please select at least one content item to proceed.');
            return;
        }

        // Store selection for resume preview
        const selectedItems = this.getSelectedItems();
        sessionStorage.setItem('selectedContent', JSON.stringify(selectedItems));
        sessionStorage.setItem('contentSelectionMetrics', JSON.stringify({
            totalScore: this.calculateTotalScore(selectedItems),
            estimatedWordCount: this.calculateTotalWordCount(selectedItems),
            keywordCoverage: this.calculateKeywordCoverage(selectedItems)
        }));

        // Navigate to resume preview
        if (window.navigateTo) {
            window.navigateTo('resume-preview');
        }
    }

    attachContentEventListeners() {
        // Reattach section control buttons
        document.querySelectorAll('[onclick^="selectAllInSection"], [onclick^="clearAllInSection"]').forEach(btn => {
            const onclick = btn.getAttribute('onclick');
            btn.removeAttribute('onclick');
            
            if (onclick.includes('selectAllInSection')) {
                const section = onclick.match(/'([^']+)'/)[1];
                btn.addEventListener('click', () => this.selectAllInSection(section));
            } else if (onclick.includes('clearAllInSection')) {
                const section = onclick.match(/'([^']+)'/)[1];
                btn.addEventListener('click', () => this.clearAllInSection(section));
            }
        });
    }

    selectAllInSection(sectionName) {
        const section = document.querySelector(`[data-section="${sectionName}"]`);
        if (!section) return;
        
        section.querySelectorAll('.content-item-checkbox').forEach(checkbox => {
            if (!checkbox.checked) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }

    clearAllInSection(sectionName) {
        const section = document.querySelector(`[data-section="${sectionName}"]`);
        if (!section) return;
        
        section.querySelectorAll('.content-item-checkbox').forEach(checkbox => {
            if (checkbox.checked) {
                checkbox.checked = false;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }

    // Placeholder methods for missing functionality
    renderExperienceAchievements(experienceId) {
        const achievements = this.masterDataset.achievements?.filter(a => a.work_experience_id === experienceId) || [];
        if (achievements.length === 0) return '';
        
        return `
            <div class="experience-achievements">
                <strong>Achievements (${achievements.length}):</strong>
                <ul>
                    ${achievements.slice(0, 2).map(a => `<li>${this.escapeHtml(a.achievement_text)}</li>`).join('')}
                    ${achievements.length > 2 ? `<li><em>+${achievements.length - 2} more...</em></li>` : ''}
                </ul>
            </div>
        `;
    }

    renderMatchedKeywords(content, score) {
        // Simplified version - would show which keywords matched
        return `<span class="keywords-match">Keywords matched: ${Math.floor(score/10)}</span>`;
    }

    getSelectedItems() {
        if (!this.selectedContent) return [];
        return Array.from(this.selectedContent).map(key => {
            const [type, id] = key.split('_');
            return { type, id, key };
        });
    }

    getAllScoredItems() {
        const items = [];
        this.contentScores.forEach((score, key) => {
            const [type, id] = key.split('_');
            items.push({ type, id, score, key });
        });
        return items;
    }

    calculateTotalScore(selectedItems) {
        if (!selectedItems.length) return 0;
        const totalScore = selectedItems.reduce((sum, item) => {
            return sum + (this.contentScores.get(item.key) || 0);
        }, 0);
        return totalScore / selectedItems.length;
    }

    calculateTotalWordCount(selectedItems) {
        return selectedItems.reduce((sum, item) => {
            return sum + this.estimateWordCount(item);
        }, 0);
    }

    estimateWordCount(item) {
        // Rough estimation based on content type
        switch (item.type) {
            case 'work_experience': return 80;
            case 'achievement': return 25;
            case 'project': return 60;
            case 'education': return 40;
            case 'skill': return 2;
            default: return 20;
        }
    }

    calculateKeywordCoverage(selectedItems) {
        if (!this.currentJobAnalysis) return 0;
        // Simplified calculation
        return Math.min(selectedItems.length * 0.15, 1);
    }

    renderOptimizationStatus(wordCount, score, coverage) {
        const issues = [];
        if (wordCount > 500) issues.push('Word count too high');
        if (wordCount < 350) issues.push('Word count too low');
        if (score < 70) issues.push('Low relevance score');
        if (coverage < 0.6) issues.push('Poor keyword coverage');
        
        if (issues.length === 0) {
            return '<div class="status-good">✅ Selection looks optimized!</div>';
        }
        
        return `<div class="status-issues">⚠️ Issues: ${issues.join(', ')}</div>`;
    }

    renderSelectionBreakdown(selectedItems) {
        const breakdown = selectedItems.reduce((acc, item) => {
            acc[item.type] = (acc[item.type] || 0) + 1;
            return acc;
        }, {});
        
        return Object.entries(breakdown).map(([type, count]) => 
            `<span class="breakdown-item">${type.replace('_', ' ')}: ${count}</span>`
        ).join(' • ');
    }
}

// Global instance
let contentSelectionManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Ensure API is loaded before initializing
    if (window.api) {
        contentSelectionManager = new ContentSelectionManager();
        window.contentSelectionManager = contentSelectionManager;
    } else {
        // Wait for API to be available
        const initWhenReady = () => {
            if (window.api) {
                contentSelectionManager = new ContentSelectionManager();
                window.contentSelectionManager = contentSelectionManager;
            } else {
                setTimeout(initWhenReady, 100);
            }
        };
        initWhenReady();
    }
});

// Global functions for HTML onclick handlers
function selectAllInSection(sectionName) {
    if (contentSelectionManager) {
        contentSelectionManager.selectAllInSection(sectionName);
    }
}

function clearAllInSection(sectionName) {
    if (contentSelectionManager) {
        contentSelectionManager.clearAllInSection(sectionName);
    }
}