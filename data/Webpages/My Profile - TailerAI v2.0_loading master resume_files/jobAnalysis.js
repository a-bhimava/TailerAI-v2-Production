/**
 * Job Analysis Module for TailerAI v2.0
 * Handles job description analysis with AI-powered insights
 * Following PROJECT_BLUEPRINT.md patterns for modularity and error handling
 */

class JobAnalysisManager {
    constructor() {
        this.currentAnalysis = null;
        this.analysisHistory = [];
        this.isAnalyzing = false;
        this.analysisCache = new Map();
        this.maxCacheSize = 10; // Limit cache size to prevent memory leaks
        
        // UI Elements
        this.jobTextArea = null;
        this.fileUpload = null;
        this.analyzeButton = null;
        this.resultsContainer = null;
        this.progressIndicator = null;
        this.historyContainer = null;
        
        this.initialize();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initialize() {
        this.setupUIElements();
        this.setupEventListeners();
        this.loadAnalysisHistory();
    }

    setupUIElements() {
        // Get UI elements (will be created when we update the HTML)
        this.jobTextArea = document.getElementById('job-description-input');
        this.fileUpload = document.getElementById('job-file-upload');
        this.analyzeButton = document.getElementById('analyze-job-btn');
        this.resultsContainer = document.getElementById('analysis-results');
        this.progressIndicator = document.getElementById('analysis-progress');
        this.historyContainer = document.getElementById('analysis-history');
        
        // Check if we're in a context where these elements should exist
        const currentView = document.querySelector('.view.active');
        const isJobAnalysisView = currentView && currentView.id === 'job-analysis-view';
        
        // Only log warnings if we're actually in the job analysis view
        if (isJobAnalysisView) {
            const requiredElements = {
                'job-description-input': this.jobTextArea,
                'job-file-upload': this.fileUpload,
                'analyze-job-btn': this.analyzeButton,
                'analysis-results': this.resultsContainer,
                'analysis-progress': this.progressIndicator,
                'analysis-history': this.historyContainer
            };
            
            Object.entries(requiredElements).forEach(([id, element]) => {
                if (!element) {
                    console.warn(`JobAnalysis: Element with ID '${id}' not found in job analysis view`);
                }
            });
        }
    }

    setupEventListeners() {
        // Analyze button click
        if (this.analyzeButton) {
            this.analyzeButton.addEventListener('click', () => this.analyzeJob());
        }

        // File upload handler
        if (this.fileUpload) {
            this.fileUpload.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // Text area input validation
        if (this.jobTextArea) {
            this.jobTextArea.addEventListener('input', () => {
                this.validateInput();
                updateCharacterCount();
            });
        }

        // History item clicks
        if (this.historyContainer) {
            this.historyContainer.addEventListener('click', (e) => this.handleHistoryClick(e));
        }
    }

    // =============================================================================
    // INPUT VALIDATION & FILE HANDLING
    // =============================================================================

    validateInput() {
        const text = this.jobTextArea?.value?.trim() || '';
        const isValid = text.length >= 50; // Minimum job description length
        
        if (this.analyzeButton) {
            this.analyzeButton.disabled = !isValid || this.isAnalyzing;
            this.analyzeButton.textContent = this.isAnalyzing ? 'Analyzing...' : 'Analyze Job';
        }

        return isValid;
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type (following blueprint error handling)
        const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('FileUploadError', 'Please upload a TXT, PDF, or DOCX file.');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            this.showError('FileUploadError', 'File size must be less than 5MB.');
            return;
        }

        try {
            this.showProgress('Reading file...');
            const text = await this.extractTextFromFile(file);
            
            if (this.jobTextArea) {
                this.jobTextArea.value = text;
                this.validateInput();
            }
            
            this.hideProgress();
            this.showSuccess('File loaded successfully!');
        } catch (error) {
            this.hideProgress();
            this.showError('ParsingError', 'Could not parse the uploaded file. Please try another document.');
            console.error('File parsing error:', error);
        }
    }

    async extractTextFromFile(file) {
        if (file.type === 'text/plain') {
            return await file.text();
        }
        
        // For PDF and DOCX files, we'd need to send to backend for parsing
        // This is a simplified version - in production, use backend parsing
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await window.api.post('/api/v2/upload/parse', formData);
        return response.data.text;
    }

    // =============================================================================
    // JOB ANALYSIS
    // =============================================================================

    async analyzeJob() {
        if (!this.validateInput() || this.isAnalyzing) return;

        const jobText = this.jobTextArea.value.trim();
        
        // Check cache first
        const cacheKey = this.generateCacheKey(jobText);
        if (this.analysisCache.has(cacheKey)) {
            this.displayAnalysisResults(this.analysisCache.get(cacheKey));
            return;
        }

        try {
            this.isAnalyzing = true;
            this.showProgress('Analyzing job description with AI...');
            this.validateInput(); // Update button state

            const analysisData = {
                job_text: jobText,
                job_url: null // Could be added later for URL-based analysis
            };

            const response = await window.api.post('/api/v2/analysis/job-analysis', analysisData);
            
            if (response.success) {
                this.currentAnalysis = {
                    ...response,
                    created_at: new Date().toISOString(),
                    id: response.analysis_id
                };
                this.addToCache(cacheKey, this.currentAnalysis);
                this.addToHistory(this.currentAnalysis);
                this.displayAnalysisResults(this.currentAnalysis);
                this.showSuccess('Job analysis completed successfully!');
            } else {
                throw new Error(response.message || 'Analysis failed');
            }

        } catch (error) {
            this.handleAnalysisError(error);
        } finally {
            this.isAnalyzing = false;
            this.hideProgress();
            this.validateInput(); // Update button state
        }
    }

    generateCacheKey(jobText) {
        // Simple hash function for caching
        let hash = 0;
        for (let i = 0; i < jobText.length; i++) {
            const char = jobText.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return hash.toString();
    }

    addToCache(key, value) {
        // Clean up cache if it's getting too large
        if (this.analysisCache.size >= this.maxCacheSize) {
            const firstKey = this.analysisCache.keys().next().value;
            this.analysisCache.delete(firstKey);
        }
        this.analysisCache.set(key, value);
    }

    handleAnalysisError(error) {
        console.error('Job analysis error:', error);
        
        // Following blueprint error handling patterns
        if (error.message?.includes('AI service')) {
            this.showError('AI_API_Error', 'AI analysis is temporarily unavailable. Using basic keyword analysis.', 'warning');
            // Could implement fallback analysis here
        } else if (error.status === 422) {
            this.showError('ValidationError', 'Please check your job description format and try again.');
        } else if (error.status === 429) {
            this.showError('RateLimitError', 'Too many requests. Please wait a moment and try again.');
        } else {
            this.showError('AnalysisError', 'Unable to analyze job description. Please try again later.');
        }
    }

    // =============================================================================
    // RESULTS DISPLAY
    // =============================================================================

    displayAnalysisResults(analysis) {
        if (!this.resultsContainer) return;

        const resultHTML = `
            <div class="analysis-results-content">
                <div class="analysis-header">
                    <h3>Analysis Results</h3>
                    <div class="analysis-meta">
                        <span class="confidence-score">Confidence: ${(analysis.confidence_score * 100).toFixed(1)}%</span>
                        <span class="analysis-date">${new Date(analysis.created_at).toLocaleDateString()}</span>
                    </div>
                </div>

                <div class="analysis-sections">
                    <div class="analysis-section">
                        <h4>🏢 Company Information</h4>
                        <div class="info-grid">
                            <div class="info-item">
                                <label>Company:</label>
                                <span>${analysis.company_name || 'Not specified'}</span>
                            </div>
                            <div class="info-item">
                                <label>Position:</label>
                                <span>${analysis.position_title || 'Not specified'}</span>
                            </div>
                            <div class="info-item">
                                <label>Industry:</label>
                                <span>${analysis.industry || 'Not specified'}</span>
                            </div>
                            <div class="info-item">
                                <label>Seniority:</label>
                                <span>${analysis.seniority_level || 'Not specified'}</span>
                            </div>
                        </div>
                    </div>

                    <div class="analysis-section">
                        <h4>🔑 Required Skills</h4>
                        <div class="skills-container">
                            ${this.renderSkillsList(analysis.required_skills)}
                        </div>
                    </div>

                    <div class="analysis-section">
                        <h4>💡 Preferred Skills</h4>
                        <div class="skills-container">
                            ${this.renderSkillsList(analysis.preferred_skills)}
                        </div>
                    </div>

                    <div class="analysis-section">
                        <h4>🎯 Important Keywords</h4>
                        <div class="keywords-container">
                            ${this.renderKeywordsList(analysis.important_keywords, analysis.keyword_frequency)}
                        </div>
                    </div>

                    <div class="analysis-section">
                        <h4>🔍 ATS Keywords</h4>
                        <div class="ats-keywords-container">
                            ${this.renderATSKeywords(analysis.ats_keywords)}
                        </div>
                    </div>

                    <div class="analysis-actions">
                        <button class="btn btn-primary" onclick="jobAnalysisManager.proceedToContentSelection()">
                            Select Content for This Job
                        </button>
                        <button class="btn btn-secondary" onclick="jobAnalysisManager.saveAnalysis()">
                            Save Analysis
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.resultsContainer.innerHTML = resultHTML;
        this.resultsContainer.style.display = 'block';
        
        // Scroll to results
        this.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    renderSkillsList(skillsJson) {
        try {
            // Handle both array and string inputs
            let skills;
            if (Array.isArray(skillsJson)) {
                skills = skillsJson;
            } else if (typeof skillsJson === 'string') {
                skills = skillsJson.trim() ? JSON.parse(skillsJson) : [];
            } else {
                skills = [];
            }
            
            if (!Array.isArray(skills) || !skills.length) {
                return '<p class="no-data">No skills identified</p>';
            }
            
            return skills.map((skill, index) => 
                `<span class="skill-tag" data-skill="${this.escapeHtml(skill)}">
                    <span class="skill-rank">${index + 1}</span>
                    ${this.escapeHtml(skill)}
                </span>`
            ).join('');
        } catch (error) {
            console.error('Error parsing skills data:', error, skillsJson);
            return '<p class="error-text">Error parsing skills data</p>';
        }
    }

    renderKeywordsList(keywordsJson, frequencyJson) {
        try {
            // Handle array or string input for keywords
            let keywords;
            if (Array.isArray(keywordsJson)) {
                keywords = keywordsJson;
            } else if (typeof keywordsJson === 'string') {
                keywords = keywordsJson.trim() ? JSON.parse(keywordsJson) : [];
            } else {
                keywords = [];
            }
            
            // Handle object or string input for frequency
            let frequency;
            if (typeof frequencyJson === 'object' && frequencyJson !== null) {
                frequency = frequencyJson;
            } else if (typeof frequencyJson === 'string') {
                frequency = frequencyJson.trim() ? JSON.parse(frequencyJson) : {};
            } else {
                frequency = {};
            }
            
            if (!Array.isArray(keywords) || !keywords.length) {
                return '<p class="no-data">No keywords identified</p>';
            }
            
            return keywords.map(keyword => {
                const freq = frequency[keyword] || 1;
                return `<span class="keyword-tag" data-keyword="${this.escapeHtml(keyword)}" data-frequency="${freq}">
                    ${this.escapeHtml(keyword)}
                    <span class="frequency-badge">${freq}</span>
                </span>`;
            }).join('');
        } catch (error) {
            console.error('Error parsing keywords data:', error, keywordsJson, frequencyJson);
            return '<p class="error-text">Error parsing keywords data</p>';
        }
    }

    renderATSKeywords(atsKeywordsJson) {
        try {
            // Handle array or string input
            let atsKeywords;
            if (Array.isArray(atsKeywordsJson)) {
                atsKeywords = atsKeywordsJson;
            } else if (typeof atsKeywordsJson === 'string') {
                atsKeywords = atsKeywordsJson.trim() ? JSON.parse(atsKeywordsJson) : [];
            } else {
                atsKeywords = [];
            }
            
            if (!Array.isArray(atsKeywords) || !atsKeywords.length) {
                return '<p class="no-data">No ATS keywords identified</p>';
            }
            
            return atsKeywords.map(keyword => 
                `<span class="ats-keyword-tag">${this.escapeHtml(keyword)}</span>`
            ).join('');
        } catch (error) {
            console.error('Error parsing ATS keywords data:', error, atsKeywordsJson);
            return '<p class="error-text">Error parsing ATS keywords data</p>';
        }
    }

    // =============================================================================
    // HISTORY MANAGEMENT
    // =============================================================================

    async loadAnalysisHistory() {
        // Check if user is authenticated before loading
        if (!window.api.isAuthenticated()) {
            console.log('JobAnalysis: User not authenticated, skipping history load');
            this.analysisHistory = [];
            this.displayHistory();
            return;
        }

        try {
            const response = await window.api.getJobAnalysisHistory();
            if (response.success) {
                this.analysisHistory = response.data || [];
                this.displayHistory();
            }
        } catch (error) {
            // Silently handle auth errors - user can still use the interface without login
            if (error.status === 403 || error.status === 401) {
                this.analysisHistory = [];
                this.displayHistory();
            } else {
                console.error('Failed to load analysis history:', error);
            }
        }
    }

    addToHistory(analysis) {
        this.analysisHistory.unshift(analysis);
        // Keep only last 10 analyses in memory
        if (this.analysisHistory.length > 10) {
            this.analysisHistory = this.analysisHistory.slice(0, 10);
        }
        this.displayHistory();
    }

    displayHistory() {
        if (!this.historyContainer) return;

        if (!this.analysisHistory.length) {
            this.historyContainer.innerHTML = '<p class="no-data">No previous analyses</p>';
            return;
        }

        const historyHTML = this.analysisHistory.map(analysis => `
            <div class="history-item" data-analysis-id="${analysis.id}">
                <div class="history-header">
                    <h5>${analysis.company_name || 'Unknown Company'} - ${analysis.position_title || 'Unknown Position'}</h5>
                    <span class="history-date">${new Date(analysis.created_at).toLocaleDateString()}</span>
                </div>
                <div class="history-preview">
                    <span class="confidence">Confidence: ${(analysis.confidence_score * 100).toFixed(1)}%</span>
                    <span class="industry">${analysis.industry || 'Unknown Industry'}</span>
                </div>
            </div>
        `).join('');

        this.historyContainer.innerHTML = historyHTML;
    }

    handleHistoryClick(event) {
        const historyItem = event.target.closest('.history-item');
        if (!historyItem) return;

        const analysisId = historyItem.dataset.analysisId;
        const analysis = this.analysisHistory.find(a => a.id === analysisId);
        
        if (analysis) {
            this.currentAnalysis = analysis;
            this.displayAnalysisResults(analysis);
        }
    }

    // =============================================================================
    // ACTIONS & NAVIGATION
    // =============================================================================

    proceedToContentSelection() {
        if (!this.currentAnalysis) {
            this.showError('NoAnalysisError', 'Please complete job analysis first.');
            return;
        }

        // Store current analysis for content selection
        sessionStorage.setItem('currentJobAnalysis', JSON.stringify(this.currentAnalysis));
        
        // Navigate to content selection view
        if (window.navigateTo) {
            window.navigateTo('content-selection');
        }
    }

    async saveAnalysis() {
        if (!this.currentAnalysis) return;

        try {
            const response = await window.api.saveJobAnalysis(this.currentAnalysis.id);
            
            if (response.success) {
                this.showSuccess('Analysis saved successfully!');
            }
        } catch (error) {
            this.showError('SaveError', 'Failed to save analysis. Please try again.');
        }
    }

    // =============================================================================
    // UI HELPERS
    // =============================================================================

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

    showError(errorType, message, severity = 'error') {
        console.error(`${errorType}: ${message}`);
        
        if (window.showNotification) {
            window.showNotification(message, severity);
        } else {
            alert(`Error: ${message}`);
        }
    }

    showSuccess(message) {
        if (window.showNotification) {
            window.showNotification(message, 'success');
        }
    }

    // =============================================================================
    // CLEANUP
    // =============================================================================

    destroy() {
        // Clean up event listeners and clear data
        this.currentAnalysis = null;
        this.analysisHistory = [];
        this.analysisCache.clear();
    }
}

// Global instance
let jobAnalysisManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Ensure API is loaded before initializing
    if (window.api) {
        jobAnalysisManager = new JobAnalysisManager();
    } else {
        // Wait for API to be available
        const initWhenReady = () => {
            if (window.api) {
                jobAnalysisManager = new JobAnalysisManager();
            } else {
                setTimeout(initWhenReady, 100);
            }
        };
        initWhenReady();
    }
});