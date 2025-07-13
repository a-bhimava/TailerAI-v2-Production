/**
 * Resume Preview Module for TailerAI v2.0
 * Handles real-time LaTeX/PDF generation and preview functionality
 * Following PROJECT_BLUEPRINT.md patterns for modularity and error handling
 */

class ResumePreviewManager {
    constructor() {
        this.selectedContent = null;
        this.jobAnalysis = null;
        this.selectionMetrics = null;
        this.currentResume = null;
        this.isGenerating = false;
        this.previewMode = 'pdf'; // 'pdf' or 'latex'
        this.autoRegenerateTimer = null;
        
        // Generation settings
        this.generationSettings = {
            template: 'modern',
            fontSize: '11pt',
            margins: 'normal',
            includePhoto: false,
            colorScheme: 'blue',
            sectionOrder: ['education', 'experience', 'projects', 'skills']
        };
        
        // UI Elements
        this.contentSummaryContainer = null;
        this.previewContainer = null;
        this.settingsPanel = null;
        this.progressIndicator = null;
        this.downloadButton = null;
        this.regenerateButton = null;
        this.previewModeButtons = null;
        
        this.initialize();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initialize() {
        this.setupUIElements();
        this.setupEventListeners();
        this.loadSelectionData();
        this.checkLatexStatus();
    }

    setupUIElements() {
        this.contentSummaryContainer = document.getElementById('content-summary');
        this.previewContainer = document.getElementById('resume-preview-container');
        this.settingsPanel = document.getElementById('generation-settings');
        this.progressIndicator = document.getElementById('generation-progress');
        this.downloadButton = document.getElementById('download-resume-btn');
        this.regenerateButton = document.getElementById('regenerate-btn');
        this.previewModeButtons = document.querySelectorAll('.preview-mode-btn');
    }

    setupEventListeners() {
        // Listen for navigation events
        window.addEventListener('navigation:routeChanged', (event) => {
            if (event.detail.route === 'resume-preview') {
                this.loadSelectionData();
                this.autoGenerateResume();
            }
        });

        // Generation settings changes
        document.addEventListener('change', (event) => {
            if (event.target.classList.contains('generation-setting')) {
                this.handleSettingChange(event);
            }
        });

        // Preview mode toggle
        this.previewModeButtons?.forEach(btn => {
            btn.addEventListener('click', (e) => this.switchPreviewMode(e.target.dataset.mode));
        });

        // Action buttons
        if (this.downloadButton) {
            this.downloadButton.addEventListener('click', () => this.downloadResume());
        }

        if (this.regenerateButton) {
            this.regenerateButton.addEventListener('click', () => this.generateResume());
        }

        // Auto-regenerate on settings change (debounced)
        document.addEventListener('input', (event) => {
            if (event.target.classList.contains('generation-setting')) {
                this.scheduleAutoRegenerate();
            }
        });
    }

    // =============================================================================
    // DATA LOADING
    // =============================================================================

    loadSelectionData() {
        try {
            // Load selected content from content selection phase
            const storedContent = sessionStorage.getItem('selectedContent');
            const storedMetrics = sessionStorage.getItem('contentSelectionMetrics');
            const storedJobAnalysis = sessionStorage.getItem('currentJobAnalysis');

            if (storedContent) {
                const parsedContent = JSON.parse(storedContent);
                if (Array.isArray(parsedContent) && parsedContent.length > 0) {
                    this.selectedContent = parsedContent;
                } else {
                    console.warn('Invalid selected content structure:', parsedContent);
                    this.selectedContent = [];
                }
            }

            if (storedMetrics) {
                const parsedMetrics = JSON.parse(storedMetrics);
                if (typeof parsedMetrics === 'object' && parsedMetrics !== null) {
                    this.selectionMetrics = parsedMetrics;
                } else {
                    console.warn('Invalid metrics structure:', parsedMetrics);
                    this.selectionMetrics = {};
                }
            }

            if (storedJobAnalysis) {
                const parsedAnalysis = JSON.parse(storedJobAnalysis);
                if (typeof parsedAnalysis === 'object' && parsedAnalysis !== null) {
                    this.jobAnalysis = parsedAnalysis;
                } else {
                    console.warn('Invalid job analysis structure:', parsedAnalysis);
                    this.jobAnalysis = null;
                }
            }

            if (!this.selectedContent || this.selectedContent.length === 0) {
                this.showNoContentMessage();
                return;
            }

            this.displayContentSummary();

        } catch (error) {
            console.error('Failed to load selection data:', error);
            // Clear corrupted data
            sessionStorage.removeItem('selectedContent');
            sessionStorage.removeItem('contentSelectionMetrics');
            this.showError('LoadingError', 'Failed to load selected content data.');
            this.showNoContentMessage();
        }
    }

    async checkLatexStatus() {
        // Check if user is authenticated before checking LaTeX status
        if (!window.api.isAuthenticated()) {
            console.log('ResumePreview: User not authenticated, skipping LaTeX status check');
            return;
        }

        try {
            const status = await window.api.getLatexStatus();
            if (!status.latex_available) {
                this.showLatexUnavailableMessage();
            }
        } catch (error) {
            console.warn('Could not check LaTeX status:', error);
        }
    }

    // =============================================================================
    // CONTENT SUMMARY DISPLAY
    // =============================================================================

    displayContentSummary() {
        if (!this.contentSummaryContainer || !this.selectedContent) return;

        const metrics = this.selectionMetrics || {};
        const jobInfo = this.jobAnalysis || {};

        const summaryHTML = `
            <div class="content-summary-content">
                <div class="summary-header">
                    <h3>Resume Generation Summary</h3>
                    <div class="target-job-info">
                        <span class="job-title">${this.escapeHtml(jobInfo.position_title || 'General Resume')}</span>
                        ${jobInfo.company_name ? `<span class="company">for ${this.escapeHtml(jobInfo.company_name)}</span>` : ''}
                    </div>
                </div>
                
                <div class="summary-metrics">
                    <div class="metric-card">
                        <div class="metric-value">${this.selectedContent.length}</div>
                        <div class="metric-label">Content Items</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.estimatedWordCount || 'N/A'}</div>
                        <div class="metric-label">Est. Words</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.totalScore ? metrics.totalScore.toFixed(1) : 'N/A'}</div>
                        <div class="metric-label">Relevance Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.keywordCoverage ? (metrics.keywordCoverage * 100).toFixed(0) + '%' : 'N/A'}</div>
                        <div class="metric-label">Keyword Coverage</div>
                    </div>
                </div>
                
                <div class="content-breakdown">
                    <h4>Selected Content Breakdown</h4>
                    <div class="breakdown-grid">
                        ${this.renderContentBreakdown()}
                    </div>
                </div>
                
                <div class="summary-actions">
                    <button class="btn btn-outline btn-sm" onclick="navigateTo('content-selection')">
                        ← Modify Selection
                    </button>
                    <button class="btn btn-primary btn-sm" id="auto-generate-btn">
                        Generate Resume
                    </button>
                </div>
            </div>
        `;

        this.contentSummaryContainer.innerHTML = summaryHTML;
        
        // Reattach event listener for auto-generate button
        const autoGenerateBtn = document.getElementById('auto-generate-btn');
        if (autoGenerateBtn) {
            autoGenerateBtn.addEventListener('click', () => this.generateResume());
        }
    }

    renderContentBreakdown() {
        const breakdown = this.selectedContent.reduce((acc, item) => {
            const type = item.type.replace('_', ' ');
            acc[type] = (acc[type] || 0) + 1;
            return acc;
        }, {});

        return Object.entries(breakdown).map(([type, count]) => 
            `<div class="breakdown-item">
                <span class="breakdown-type">${this.capitalizeWords(type)}</span>
                <span class="breakdown-count">${count}</span>
            </div>`
        ).join('');
    }

    showNoContentMessage() {
        if (!this.contentSummaryContainer) return;

        this.contentSummaryContainer.innerHTML = `
            <div class="no-content-message">
                <div class="message-icon">📄</div>
                <h3>No Content Selected</h3>
                <p>Please select content from your master dataset first to generate a resume.</p>
                <button class="btn btn-primary" onclick="navigateTo('content-selection')">
                    Select Content
                </button>
            </div>
        `;
    }

    showLatexUnavailableMessage() {
        if (!this.previewContainer) return;

        this.previewContainer.innerHTML = `
            <div class="latex-unavailable-message">
                <div class="message-icon">⚠️</div>
                <h3>LaTeX Engine Unavailable</h3>
                <p>The LaTeX compilation engine is not available. Resume generation is temporarily disabled.</p>
                <p>Please contact support or try again later.</p>
            </div>
        `;
    }

    // =============================================================================
    // RESUME GENERATION
    // =============================================================================

    async autoGenerateResume() {
        if (this.selectedContent && this.selectedContent.length > 0) {
            await this.generateResume();
        }
    }

    async generateResume() {
        if (!this.selectedContent || this.selectedContent.length === 0) {
            this.showError('NoContentError', 'No content selected for resume generation.');
            return;
        }

        if (this.isGenerating) return;

        try {
            this.isGenerating = true;
            this.showProgress('Generating your optimized resume...');
            this.updateButtonStates();

            // Prepare generation data
            const generationData = {
                selected_content: this.selectedContent,
                job_analysis: this.jobAnalysis,
                settings: this.generationSettings,
                user_preferences: {
                    template: this.generationSettings.template,
                    font_size: this.generationSettings.fontSize,
                    margins: this.generationSettings.margins,
                    color_scheme: this.generationSettings.colorScheme,
                    section_order: this.generationSettings.sectionOrder
                }
            };

            const response = await window.api.generateResume(generationData);

            if (response.success) {
                this.currentResume = response;
                this.displayResumePreview(response);
                this.showSuccess('Resume generated successfully!');
            } else {
                throw new Error(response.message || 'Resume generation failed');
            }

        } catch (error) {
            this.handleGenerationError(error);
        } finally {
            this.isGenerating = false;
            this.hideProgress();
            this.updateButtonStates();
        }
    }

    handleGenerationError(error) {
        console.error('Resume generation error:', error);
        
        // Following blueprint error handling patterns
        if (error.message?.includes('LaTeX')) {
            this.showError('LaTeXCompilationError', 'Could not compile the resume. Please check your content for special characters.', 'error');
        } else if (error.status === 422) {
            this.showError('ValidationError', 'Invalid content format. Please review your selected content.');
        } else if (error.status === 429) {
            this.showError('RateLimitError', 'Too many generation requests. Please wait a moment and try again.');
        } else {
            this.showError('GenerationError', 'Unable to generate resume. Please try again or contact support.');
        }

        // Show fallback preview
        this.showFallbackPreview();
    }

    // =============================================================================
    // PREVIEW DISPLAY
    // =============================================================================

    displayResumePreview(resumeData) {
        if (!this.previewContainer) return;

        const previewHTML = `
            <div class="resume-preview-content">
                <div class="preview-header">
                    <div class="preview-controls">
                        <div class="preview-mode-selector">
                            <button class="preview-mode-btn ${this.previewMode === 'pdf' ? 'active' : ''}" data-mode="pdf">
                                PDF Preview
                            </button>
                            <button class="preview-mode-btn ${this.previewMode === 'latex' ? 'active' : ''}" data-mode="latex">
                                LaTeX Source
                            </button>
                        </div>
                        
                        <div class="preview-actions">
                            <button class="btn btn-outline btn-sm" id="zoom-out-btn">🔍-</button>
                            <button class="btn btn-outline btn-sm" id="zoom-in-btn">🔍+</button>
                            <button class="btn btn-outline btn-sm" id="fullscreen-btn">⛶</button>
                        </div>
                    </div>
                    
                    <div class="generation-info">
                        <span class="generation-time">Generated: ${new Date().toLocaleTimeString()}</span>
                        <span class="template-info">Template: ${this.generationSettings.template}</span>
                        ${resumeData.page_count ? `<span class="page-count">Pages: ${resumeData.page_count}</span>` : ''}
                    </div>
                </div>
                
                <div class="preview-content">
                    ${this.previewMode === 'pdf' ? this.renderPDFPreview(resumeData) : this.renderLatexPreview(resumeData)}
                </div>
            </div>
        `;

        this.previewContainer.innerHTML = previewHTML;
        this.attachPreviewEventListeners();
    }

    renderPDFPreview(resumeData) {
        if (resumeData.pdf_url) {
            return `
                <div class="pdf-preview-container">
                    <iframe 
                        src="${resumeData.pdf_url}#toolbar=0&navpanes=0&scrollbar=0" 
                        class="pdf-preview-frame"
                        title="Resume Preview">
                    </iframe>
                </div>
            `;
        } else {
            return `
                <div class="pdf-preview-placeholder">
                    <div class="placeholder-content">
                        <div class="placeholder-icon">📄</div>
                        <h4>PDF Preview</h4>
                        <p>Your resume is being processed...</p>
                        ${resumeData.latex_content ? '<p>LaTeX compilation in progress.</p>' : ''}
                    </div>
                </div>
            `;
        }
    }

    renderLatexPreview(resumeData) {
        const latexContent = resumeData.latex_content || '% LaTeX content not available';
        
        return `
            <div class="latex-preview-container">
                <div class="latex-preview-header">
                    <h4>LaTeX Source Code</h4>
                    <button class="btn btn-outline btn-sm" onclick="copyLatexToClipboard()">
                        Copy to Clipboard
                    </button>
                </div>
                <pre class="latex-source-code"><code class="language-latex">${this.escapeHtml(latexContent)}</code></pre>
            </div>
        `;
    }

    showFallbackPreview() {
        if (!this.previewContainer) return;

        this.previewContainer.innerHTML = `
            <div class="fallback-preview">
                <div class="fallback-content">
                    <div class="fallback-icon">📝</div>
                    <h3>Resume Generation Error</h3>
                    <p>We couldn't generate the PDF preview, but here's a text version of your selected content:</p>
                    <div class="content-preview">
                        ${this.renderTextPreview()}
                    </div>
                    <div class="fallback-actions">
                        <button class="btn btn-primary" onclick="resumePreviewManager.generateResume()">
                            Try Again
                        </button>
                        <button class="btn btn-outline" onclick="navigateTo('content-selection')">
                            Modify Content
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderTextPreview() {
        if (!this.selectedContent) return '<p>No content available</p>';

        const groupedContent = this.selectedContent.reduce((acc, item) => {
            if (!acc[item.type]) acc[item.type] = [];
            acc[item.type].push(item);
            return acc;
        }, {});

        let html = '';
        Object.entries(groupedContent).forEach(([type, items]) => {
            html += `
                <div class="content-section">
                    <h4>${this.capitalizeWords(type.replace('_', ' '))}</h4>
                    <ul>
                        ${items.map(item => `<li>${item.id}</li>`).join('')}
                    </ul>
                </div>
            `;
        });

        return html;
    }

    // =============================================================================
    // PREVIEW INTERACTIONS
    // =============================================================================

    switchPreviewMode(mode) {
        this.previewMode = mode;
        
        // Update button states
        this.previewModeButtons?.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });

        // Re-render preview if resume is available
        if (this.currentResume) {
            this.displayResumePreview(this.currentResume);
        }
    }

    attachPreviewEventListeners() {
        // Preview mode buttons
        document.querySelectorAll('.preview-mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchPreviewMode(e.target.dataset.mode));
        });

        // Zoom controls (simplified implementation)
        const zoomInBtn = document.getElementById('zoom-in-btn');
        const zoomOutBtn = document.getElementById('zoom-out-btn');
        const fullscreenBtn = document.getElementById('fullscreen-btn');

        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.adjustZoom(1.1));
        }
        
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.adjustZoom(0.9));
        }
        
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }
    }

    adjustZoom(factor) {
        const iframe = document.querySelector('.pdf-preview-frame');
        if (iframe) {
            const currentTransform = iframe.style.transform || 'scale(1)';
            const currentScale = parseFloat(currentTransform.match(/scale\(([^)]+)\)/)?.[1] || 1);
            const newScale = Math.max(0.5, Math.min(2, currentScale * factor));
            iframe.style.transform = `scale(${newScale})`;
        }
    }

    toggleFullscreen() {
        const previewContainer = document.querySelector('.resume-preview-content');
        if (previewContainer) {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                previewContainer.requestFullscreen();
            }
        }
    }

    // =============================================================================
    // SETTINGS MANAGEMENT
    // =============================================================================

    handleSettingChange(event) {
        const setting = event.target.name || event.target.dataset.setting;
        const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
        
        if (setting && this.generationSettings.hasOwnProperty(setting)) {
            this.generationSettings[setting] = value;
            this.updateSettingsDisplay();
        }
    }

    updateSettingsDisplay() {
        // Update any visual indicators for settings changes
        const settingsIndicator = document.getElementById('settings-modified-indicator');
        if (settingsIndicator) {
            settingsIndicator.style.display = 'block';
        }
    }

    scheduleAutoRegenerate() {
        // Clear existing timer
        if (this.autoRegenerateTimer) {
            clearTimeout(this.autoRegenerateTimer);
        }

        // Schedule regeneration after 2 seconds of no changes
        this.autoRegenerateTimer = setTimeout(() => {
            if (!this.isGenerating) {
                this.generateResume();
            }
        }, 2000);
    }

    // =============================================================================
    // DOWNLOAD FUNCTIONALITY
    // =============================================================================

    async downloadResume() {
        if (!this.currentResume?.pdf_filename) {
            this.showError('DownloadError', 'No resume available for download. Please generate a resume first.');
            return;
        }

        try {
            this.showProgress('Preparing download...');

            const response = await window.api.downloadResume(this.currentResume.pdf_filename);
            
            // Validate response
            if (!response || typeof response.blob !== 'function') {
                throw new Error('Invalid response format for download');
            }
            
            // Create blob and download
            const blob = await response.blob();
            
            // Validate blob
            if (!blob || blob.size === 0) {
                throw new Error('Empty or invalid file received');
            }
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = this.generateDownloadFilename();
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }, 100);

            this.showSuccess('Resume downloaded successfully!');

        } catch (error) {
            console.error('Download failed:', error);
            
            if (error.message?.includes('Invalid response')) {
                this.showError('DownloadError', 'Server returned invalid file format. Please try regenerating the resume.');
            } else if (error.message?.includes('Empty')) {
                this.showError('DownloadError', 'Downloaded file is empty. Please try regenerating the resume.');
            } else {
                this.showError('DownloadError', 'Failed to download resume. Please try again.');
            }
        } finally {
            this.hideProgress();
        }
    }

    generateDownloadFilename() {
        const jobTitle = this.jobAnalysis?.position_title || 'Resume';
        const company = this.jobAnalysis?.company_name || '';
        const date = new Date().toISOString().split('T')[0];
        
        let filename = `${jobTitle.replace(/[^a-zA-Z0-9]/g, '_')}`;
        if (company) {
            filename += `_${company.replace(/[^a-zA-Z0-9]/g, '_')}`;
        }
        filename += `_${date}.pdf`;
        
        return filename;
    }

    // =============================================================================
    // UTILITY METHODS
    // =============================================================================

    updateButtonStates() {
        if (this.downloadButton) {
            this.downloadButton.disabled = !this.currentResume?.pdf_filename;
        }
        
        if (this.regenerateButton) {
            this.regenerateButton.disabled = this.isGenerating;
            this.regenerateButton.textContent = this.isGenerating ? 'Generating...' : 'Regenerate';
        }
    }

    capitalizeWords(str) {
        return str.replace(/\b\w/g, char => char.toUpperCase());
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

    showError(errorType, message, severity = 'error') {
        console.error(`${errorType}: ${message}`);
        if (window.showNotification) {
            window.showNotification(message, severity);
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
        if (this.autoRegenerateTimer) {
            clearTimeout(this.autoRegenerateTimer);
        }
        this.selectedContent = null;
        this.currentResume = null;
    }
}

// Global instance
let resumePreviewManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Ensure API is loaded before initializing
    if (window.api) {
        resumePreviewManager = new ResumePreviewManager();
        window.resumePreviewManager = resumePreviewManager;
    } else {
        // Wait for API to be available
        const initWhenReady = () => {
            if (window.api) {
                resumePreviewManager = new ResumePreviewManager();
                window.resumePreviewManager = resumePreviewManager;
            } else {
                setTimeout(initWhenReady, 100);
            }
        };
        initWhenReady();
    }
});

// Global functions for HTML onclick handlers
function copyLatexToClipboard() {
    const latexCode = document.querySelector('.latex-source-code code');
    if (latexCode) {
        navigator.clipboard.writeText(latexCode.textContent).then(() => {
            if (window.showNotification) {
                window.showNotification('LaTeX code copied to clipboard!', 'success');
            }
        }).catch(err => {
            console.error('Failed to copy LaTeX code:', err);
        });
    }
}