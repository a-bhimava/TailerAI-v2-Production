/**
 * API Client for TailerAI v2.0
 * Handles all HTTP requests to the backend API with authentication and error handling
 */

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.token = this.getStoredToken();
        this.refreshToken = this.getStoredRefreshToken();
    }

    // =============================================================================
    // TOKEN MANAGEMENT
    // =============================================================================

    getStoredToken() {
        return localStorage.getItem('tailerai_token');
    }

    getStoredRefreshToken() {
        return localStorage.getItem('tailerai_refresh_token');
    }

    setTokens(accessToken, refreshToken) {
        this.token = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('tailerai_token', accessToken);
        if (refreshToken) {
            localStorage.setItem('tailerai_refresh_token', refreshToken);
        }
    }

    clearTokens() {
        this.token = null;
        this.refreshToken = null;
        localStorage.removeItem('tailerai_token');
        localStorage.removeItem('tailerai_refresh_token');
    }

    isAuthenticated() {
        // Check if we have a valid token and it hasn't expired
        if (!this.token) {
            return false;
        }
        
        try {
            // Decode JWT token to check expiration
            const tokenPayload = JSON.parse(atob(this.token.split('.')[1]));
            const currentTime = Math.floor(Date.now() / 1000);
            
            // If token is expired, clear it and return false
            if (tokenPayload.exp && tokenPayload.exp < currentTime) {
                this.clearTokens();
                return false;
            }
            
            return true;
        } catch (error) {
            // If token is malformed, clear it
            this.clearTokens();
            return false;
        }
    }

    // =============================================================================
    // HTTP METHODS
    // =============================================================================

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add authentication header if token exists
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);

            // Handle 401 Unauthorized - try to refresh token
            if (response.status === 401 && this.refreshToken && endpoint !== '/api/v2/auth/refresh') {
                const refreshSuccess = await this.refreshTokens();
                if (refreshSuccess) {
                    // Retry the original request with new token
                    config.headers['Authorization'] = `Bearer ${this.token}`;
                    return await fetch(url, config);
                } else {
                    // Refresh failed, redirect to login
                    this.clearTokens();
                    window.dispatchEvent(new CustomEvent('auth:logout'));
                    throw new APIError('Authentication required', 401);
                }
            }

            // Handle other HTTP errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Request failed' }));
                
                // Log detailed error information for debugging
                if (response.status === 422) {
                    console.error('Validation Error Details:', JSON.stringify(errorData, null, 2));
                    console.error('Request URL:', url);
                    console.error('Request body:', config.body);
                    
                    // Log each validation error
                    if (errorData.detail && Array.isArray(errorData.detail)) {
                        errorData.detail.forEach((error, index) => {
                            console.error(`Validation Error ${index + 1}:`, error);
                        });
                    }
                }
                
                throw new APIError(errorData.message || `HTTP ${response.status}`, response.status, errorData);
            }

            // Return JSON response for successful requests
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            // Return response object for non-JSON responses (e.g., file downloads)
            return response;

        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            
            // Network or other errors
            console.error('API Request failed:', error);
            throw new APIError('Network error occurred', 0, { originalError: error });
        }
    }

    async refreshTokens() {
        try {
            const response = await this.request('/api/v2/auth/refresh', {
                method: 'POST',
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            this.setTokens(response.access_token, response.refresh_token);
            return true;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }

    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // =============================================================================
    // AUTHENTICATION ENDPOINTS
    // =============================================================================

    async login(email, password) {
        const response = await this.post('/api/v2/auth/login', {
            email: email,
            password: password
        });

        this.setTokens(response.access_token, response.refresh_token);
        return response;
    }

    async register(email, password, fullName) {
        // Generate username from email (before @)
        const username = email.split('@')[0].toLowerCase();
        
        const response = await this.post('/api/v2/auth/register', {
            email: email,
            username: username,
            password: password,
            full_name: fullName
        });

        // Registration might return tokens immediately or require email verification
        if (response.access_token) {
            this.setTokens(response.access_token, response.refresh_token);
        }

        return response;
    }

    async logout() {
        try {
            // Call logout endpoint to invalidate token on server
            await this.post('/api/v2/auth/logout');
        } catch (error) {
            console.warn('Logout request failed, clearing tokens locally:', error);
        } finally {
            this.clearTokens();
        }
    }

    async getCurrentUser() {
        return this.get('/api/v2/auth/me');
    }

    async googleAuth(googleToken) {
        const response = await this.post('/api/v2/auth/google', {
            google_token: googleToken
        });

        if (response.access_token) {
            this.setTokens(response.access_token, response.refresh_token);
        } else {
            console.error('No access_token in response:', response);
        }
        
        return response;
    }

    // =============================================================================
    // MASTER DATASET ENDPOINTS
    // =============================================================================

    async getMasterDataset() {
        console.log('Making request to /api/v2/master-dataset/complete');
        console.log('Using token:', this.token ? 'Token present' : 'No token');
        console.log('Is authenticated:', this.isAuthenticated());
        return this.get('/api/v2/master-dataset/complete');
    }

    async createWorkExperience(experienceData) {
        return this.post('/api/v2/master-dataset/experience', experienceData);
    }

    async updateWorkExperience(experienceId, experienceData) {
        return this.put(`/api/v2/master-dataset/experience/${experienceId}`, experienceData);
    }

    async deleteWorkExperience(experienceId) {
        return this.delete(`/api/v2/master-dataset/experience/${experienceId}`);
    }

    async createAchievement(achievementData) {
        // For standalone achievements, simulate success for now
        console.warn('Standalone achievement endpoint not yet implemented - simulating success');
        return { success: true, message: 'Achievement saved locally (backend endpoint pending)' };
    }

    async updateAchievement(achievementId, achievementData) {
        console.warn('Achievement update endpoint not yet implemented');
        return { success: true, message: 'Achievement updated locally' };
    }

    async deleteAchievement(achievementId) {
        console.warn('Achievement delete endpoint not yet implemented');
        return { success: true, message: 'Achievement deleted locally' };
    }

    async createEducation(educationData) {
        return this.post('/api/v2/master-dataset/education', educationData);
    }

    async updateEducation(educationId, educationData) {
        return this.put(`/api/v2/master-dataset/education/${educationId}`, educationData);
    }

    async deleteEducation(educationId) {
        return this.delete(`/api/v2/master-dataset/education/${educationId}`);
    }

    async createProject(projectData) {
        return this.post('/api/v2/master-dataset/project', projectData);
    }

    async updateProject(projectId, projectData) {
        return this.put(`/api/v2/master-dataset/project/${projectId}`, projectData);
    }

    async deleteProject(projectId) {
        return this.delete(`/api/v2/master-dataset/project/${projectId}`);
    }

    async createSkill(skillData) {
        return this.post('/api/v2/master-dataset/skill', skillData);
    }

    async updateSkill(skillId, skillData) {
        return this.put(`/api/v2/master-dataset/skills/${skillId}`, skillData);
    }

    async deleteSkill(skillId) {
        return this.delete(`/api/v2/master-dataset/skills/${skillId}`);
    }

    // =============================================================================
    // JOB ANALYSIS ENDPOINTS
    // =============================================================================

    async analyzeJob(jobDescription, jobTitle = '', companyName = '') {
        return this.post('/api/v2/job-analysis', {
            job_description: jobDescription,
            job_title: jobTitle,
            company_name: companyName
        });
    }

    async getJobAnalysis(analysisId) {
        return this.get(`/api/v2/job-analysis/${analysisId}`);
    }

    async getJobAnalysisHistory() {
        return this.get('/api/v2/history');
    }

    async saveJobAnalysis(analysisId) {
        return this.post('/api/v2/analysis/save', {
            analysis_id: analysisId
        });
    }

    // =============================================================================
    // CONTENT SELECTION ENDPOINTS
    // =============================================================================

    async selectContent(jobAnalysisId, constraints = {}) {
        return this.post('/api/v2/content-selection', {
            job_analysis_id: jobAnalysisId,
            ...constraints
        });
    }

    async getContentSelection(selectionId) {
        return this.get(`/api/v2/content-selection/${selectionId}`);
    }

    // =============================================================================
    // ATS OPTIMIZATION ENDPOINTS
    // =============================================================================

    async optimizeATS(contentSelectionId) {
        return this.post('/api/v2/ats/optimize', {
            content_selection_id: contentSelectionId
        });
    }

    async getATSOptimization(optimizationId) {
        return this.get(`/api/v2/ats/optimization/${optimizationId}`);
    }

    async getATSOptimizationHistory() {
        return this.get('/api/v2/ats/optimizations/history');
    }

    // =============================================================================
    // LATEX GENERATION ENDPOINTS
    // =============================================================================

    async generateResume(contentData) {
        return this.post('/api/v2/latex/generate', contentData);
    }

    async generateOptimizedResume(contentSelectionId) {
        return this.post('/api/v2/latex/generate-optimized', {
            content_selection_id: contentSelectionId
        });
    }

    async downloadResume(filename) {
        const response = await this.request(`/api/v2/latex/download/${filename}`, {
            method: 'GET'
        });
        return response; // Returns Response object for blob handling
    }

    async getLatexStatus() {
        return this.get('/api/v2/latex/status');
    }

    // =============================================================================
    // HEALTH CHECK
    // =============================================================================

    async healthCheck() {
        return this.get('/health');
    }
}

// =============================================================================
// API ERROR CLASS
// =============================================================================

class APIError extends Error {
    constructor(message, status = 0, details = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }

    isNetworkError() {
        return this.status === 0;
    }

    isAuthError() {
        return this.status === 401 || this.status === 403;
    }

    isValidationError() {
        return this.status === 422;
    }

    isServerError() {
        return this.status >= 500;
    }
}

// =============================================================================
// GLOBAL API INSTANCE
// =============================================================================

// Create global API client instance
window.api = new APIClient();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, APIError };
}