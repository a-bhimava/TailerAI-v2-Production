/**
 * Navigation Management for TailerAI v2.0
 * Handles SPA routing, breadcrumbs, and view transitions
 */

class NavigationManager {
    constructor() {
        this.currentRoute = 'dashboard';
        this.previousRoute = null;
        this.routes = {
            'dashboard': {
                title: 'Dashboard',
                breadcrumb: ['Dashboard'],
                icon: '📊'
            },
            'master-dataset': {
                title: 'Master Dataset',
                breadcrumb: ['Master Dataset'],
                icon: '📋'
            },
            'job-analysis': {
                title: 'Job Analysis',
                breadcrumb: ['Job Analysis'],
                icon: '🔍'
            },
            'content-selection': {
                title: 'Content Selection',
                breadcrumb: ['Content Selection'],
                icon: '🎯'
            },
            'ats-optimization': {
                title: 'ATS Optimization',
                breadcrumb: ['ATS Optimization'],
                icon: '⚡'
            },
            'resume-preview': {
                title: 'Resume Preview',
                breadcrumb: ['Resume Preview'],
                icon: '📄'
            },
            'applications': {
                title: 'Applications',
                breadcrumb: ['Application Tracking'],
                icon: '📬'
            },
            'profile': {
                title: 'Profile Settings',
                breadcrumb: ['Profile Settings'],
                icon: '⚙️'
            }
        };
        
        this.initializeNavigation();
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initializeNavigation() {
        this.setupEventListeners();
        this.handleInitialRoute();
    }

    setupEventListeners() {
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', this.toggleSidebar.bind(this));
        }

        // Handle browser back/forward buttons
        window.addEventListener('popstate', this.handlePopState.bind(this));

        // Mobile sidebar overlay
        this.setupMobileSidebar();
    }

    setupMobileSidebar() {
        // Create mobile overlay if it doesn't exist
        if (!document.querySelector('.sidebar-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.addEventListener('click', this.closeMobileSidebar.bind(this));
            document.body.appendChild(overlay);
        }
    }

    handleInitialRoute() {
        // Check URL for initial route (if using hash routing)
        const hash = window.location.hash.substring(1);
        if (hash && this.routes[hash]) {
            this.navigateTo(hash, false);
        } else {
            this.navigateTo('dashboard', false);
        }
    }

    handlePopState(event) {
        const route = event.state?.route || 'dashboard';
        this.navigateTo(route, false);
    }

    // =============================================================================
    // ROUTE MANAGEMENT
    // =============================================================================

    navigateTo(route, updateHistory = true) {
        // Validate route
        if (!this.routes[route]) {
            console.warn(`Invalid route: ${route}`);
            return false;
        }

        // Don't navigate if already on the same route
        if (this.currentRoute === route) {
            return false;
        }

        // Store previous route
        this.previousRoute = this.currentRoute;
        this.currentRoute = route;

        // Update URL and browser history
        if (updateHistory) {
            const url = `${window.location.pathname}#${route}`;
            window.history.pushState({ route }, '', url);
        }

        // Update UI
        this.updateActiveNavigation();
        this.updateBreadcrumb();
        this.showView(route);
        this.updatePageTitle();

        // Close mobile sidebar if open
        this.closeMobileSidebar();

        // Trigger route change event
        window.dispatchEvent(new CustomEvent('navigation:routeChanged', {
            detail: { 
                route, 
                previousRoute: this.previousRoute,
                routeData: this.routes[route]
            }
        }));

        return true;
    }

    updateActiveNavigation() {
        // Update sidebar navigation
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-route') === this.currentRoute) {
                link.classList.add('active');
            }
        });
    }

    updateBreadcrumb() {
        const breadcrumb = document.getElementById('breadcrumb');
        if (!breadcrumb) return;

        const routeData = this.routes[this.currentRoute];
        if (!routeData) return;

        // Clear existing breadcrumb
        breadcrumb.innerHTML = '';

        // Add breadcrumb items
        routeData.breadcrumb.forEach((item, index) => {
            const breadcrumbItem = document.createElement('span');
            breadcrumbItem.className = 'breadcrumb-item';
            
            if (index === routeData.breadcrumb.length - 1) {
                breadcrumbItem.classList.add('active');
            }
            
            breadcrumbItem.textContent = item;
            breadcrumb.appendChild(breadcrumbItem);
        });
    }

    showView(route) {
        // Hide all views
        const views = document.querySelectorAll('.view');
        views.forEach(view => {
            view.classList.remove('active');
        });

        // Show target view
        const targetView = document.getElementById(`${route}-view`);
        if (targetView) {
            setTimeout(() => {
                targetView.classList.add('active');
            }, 50); // Small delay for smooth transition
        }

        // Load view-specific data
        this.loadViewData(route);
    }

    updatePageTitle() {
        const routeData = this.routes[this.currentRoute];
        if (routeData) {
            document.title = `${routeData.title} - TailerAI v2.0`;
        }
    }

    async loadViewData(route) {
        try {
            switch (route) {
                case 'dashboard':
                    if (window.dashboard) {
                        await window.dashboard.loadDashboardData();
                    }
                    break;
                
                case 'master-dataset':
                    if (window.dataset) {
                        await window.dataset.loadDataset();
                    }
                    break;
                
                // Add other view data loading as needed
                default:
                    break;
            }
        } catch (error) {
            console.error(`Failed to load data for ${route}:`, error);
            window.notifications.show(`Failed to load ${route} data`, 'error');
        }
    }

    // =============================================================================
    // SIDEBAR MANAGEMENT
    // =============================================================================

    toggleSidebar() {
        const appShell = document.querySelector('.app-shell');
        const sidebar = document.getElementById('sidebar');
        
        if (window.innerWidth <= 767) {
            // Mobile: toggle sidebar overlay
            this.toggleMobileSidebar();
        } else {
            // Desktop: toggle sidebar collapse
            if (appShell) {
                appShell.classList.toggle('sidebar-collapsed');
            }
        }
    }

    toggleMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar && overlay) {
            const isOpen = sidebar.classList.contains('mobile-open');
            
            if (isOpen) {
                this.closeMobileSidebar();
            } else {
                this.openMobileSidebar();
            }
        }
    }

    openMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar) sidebar.classList.add('mobile-open');
        if (overlay) overlay.classList.add('active');
        
        // Prevent body scroll when sidebar is open
        document.body.style.overflow = 'hidden';
    }

    closeMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar) sidebar.classList.remove('mobile-open');
        if (overlay) overlay.classList.remove('active');
        
        // Restore body scroll
        document.body.style.overflow = '';
    }

    // =============================================================================
    // RESPONSIVE HANDLING
    // =============================================================================

    handleResize() {
        // Close mobile sidebar when switching to desktop view
        if (window.innerWidth > 767) {
            this.closeMobileSidebar();
        }
    }

    // =============================================================================
    // UTILITY METHODS
    // =============================================================================

    getCurrentRoute() {
        return this.currentRoute;
    }

    getPreviousRoute() {
        return this.previousRoute;
    }

    getRouteData(route = null) {
        const targetRoute = route || this.currentRoute;
        return this.routes[targetRoute];
    }

    isValidRoute(route) {
        return !!this.routes[route];
    }

    // =============================================================================
    // NAVIGATION SHORTCUTS
    // =============================================================================

    goBack() {
        if (this.previousRoute) {
            this.navigateTo(this.previousRoute);
        } else {
            this.navigateTo('dashboard');
        }
    }

    goToDashboard() {
        this.navigateTo('dashboard');
    }

    goToMasterDataset() {
        this.navigateTo('master-dataset');
    }

    goToJobAnalysis() {
        this.navigateTo('job-analysis');
    }

    // =============================================================================
    // KEYBOARD SHORTCUTS
    // =============================================================================

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Only handle shortcuts when not in input fields
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }

            // Alt/Option + number keys for quick navigation
            if (event.altKey) {
                switch (event.key) {
                    case '1':
                        event.preventDefault();
                        this.navigateTo('dashboard');
                        break;
                    case '2':
                        event.preventDefault();
                        this.navigateTo('master-dataset');
                        break;
                    case '3':
                        event.preventDefault();
                        this.navigateTo('job-analysis');
                        break;
                    case '4':
                        event.preventDefault();
                        this.navigateTo('content-selection');
                        break;
                    case '5':
                        event.preventDefault();
                        this.navigateTo('ats-optimization');
                        break;
                    case '6':
                        event.preventDefault();
                        this.navigateTo('resume-preview');
                        break;
                    case '7':
                        event.preventDefault();
                        this.navigateTo('applications');
                        break;
                }
            }

            // ESC to close mobile sidebar
            if (event.key === 'Escape') {
                this.closeMobileSidebar();
            }
        });
    }
}

// =============================================================================
// GLOBAL NAVIGATION MANAGER
// =============================================================================

// Create global navigation manager instance
window.navigation = new NavigationManager();

// Setup keyboard shortcuts
window.navigation.setupKeyboardShortcuts();

// Handle window resize
window.addEventListener('resize', () => {
    window.navigation.handleResize();
});

// =============================================================================
// GLOBAL NAVIGATION FUNCTIONS (for HTML onclick handlers)
// =============================================================================

function navigateTo(route) {
    return window.navigation.navigateTo(route);
}

function toggleSidebar() {
    window.navigation.toggleSidebar();
}

function goBack() {
    window.navigation.goBack();
}