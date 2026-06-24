/**
 * Edumate - Theme Toggle and Interactive Features
 * Handles dark/light theme switching and UI interactions
 */

class ThemeManager {
    constructor() {
        this.themeToggleBtn = document.getElementById('theme-toggle-btn');
        this.themeIcon = document.getElementById('theme-icon');
        this.currentTheme = this.getStoredTheme() || 'light';
        
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        this.bindEvents();
        this.updateThemeIcon();
    }
    
    bindEvents() {
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!this.getStoredTheme()) {
                    this.currentTheme = e.matches ? 'dark' : 'light';
                    this.applyTheme(this.currentTheme);
                    this.updateThemeIcon();
                }
            });
        }
    }
    
    getStoredTheme() {
        return localStorage.getItem('edumate-theme');
    }
    
    setStoredTheme(theme) {
        localStorage.setItem('edumate-theme', theme);
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        this.updateThemeIcon();
        this.setStoredTheme(this.currentTheme);
        this.showThemeNotification();
    }
    
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
    }
    
    updateThemeIcon() {
        if (this.themeIcon) {
            this.themeIcon.className = this.currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }
    
    showThemeNotification() {
        const message = this.currentTheme === 'dark' ? 'Dark mode enabled' : 'Light mode enabled';
        this.showToast(message, 'info');
    }
    
    showToast(message, type = 'info') {
        // Create toast if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const iconMap = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        
        toast.innerHTML = `
            <i class="fas fa-${iconMap[type] || 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
}

class AnimationManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupScrollAnimations();
        this.setupHoverEffects();
        this.setupLoadingAnimations();
    }
    
    setupScrollAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);
        
        // Observe elements that should animate on scroll
        const animateElements = document.querySelectorAll('.feature-card, .step, .floating-card');
        animateElements.forEach(el => {
            observer.observe(el);
        });
    }
    
    setupHoverEffects() {
        // Add hover effects to interactive elements
        const interactiveElements = document.querySelectorAll('.btn, .card, .nav-link');
        
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                el.style.transform = 'translateY(-2px)';
            });
            
            el.addEventListener('mouseleave', () => {
                el.style.transform = 'translateY(0)';
            });
        });
    }
    
    setupLoadingAnimations() {
        // Create loading spinner animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            @keyframes bounce {
                0%, 20%, 53%, 80%, 100% {
                    transform: translate3d(0,0,0);
                }
                40%, 43% {
                    transform: translate3d(0, -8px, 0);
                }
                70% {
                    transform: translate3d(0, -4px, 0);
                }
                90% {
                    transform: translate3d(0, -2px, 0);
                }
            }
            
            .animate-in {
                animation: fadeInUp 0.6s ease forwards;
            }
            
            .loading-bounce {
                animation: bounce 1s infinite;
            }
            
            .loading-pulse {
                animation: pulse 1.5s infinite;
            }
        `;
        document.head.appendChild(style);
    }
}

class FileUploadManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupDragAndDrop();
        this.setupFileValidation();
    }
    
    setupDragAndDrop() {
        const uploadAreas = document.querySelectorAll('.upload-area');
        
        uploadAreas.forEach(area => {
            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                area.classList.add('dragover');
            });
            
            area.addEventListener('dragleave', () => {
                area.classList.remove('dragover');
            });
            
            area.addEventListener('drop', (e) => {
                e.preventDefault();
                area.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFile(files[0], area);
                }
            });
        });
    }
    
    setupFileValidation() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFile(e.target.files[0], input.closest('.upload-area'));
                }
            });
        });
    }
    
    handleFile(file, uploadArea) {
        // Validate file type
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ];
        
        if (!allowedTypes.includes(file.type)) {
            this.showError('Please upload a PDF, DOCX, or TXT file');
            return false;
        }
        
        // Validate file size (16MB)
        if (file.size > 16 * 1024 * 1024) {
            this.showError('File size must be less than 16MB');
            return false;
        }
        
        return true;
    }
    
    showError(message) {
        const themeManager = new ThemeManager();
        themeManager.showToast(message, 'error');
    }
}

class ProgressManager {
    constructor() {
        this.activeProgressBars = new Map();
    }
    
    createProgressBar(container, label = 'Processing...') {
        const progressId = `progress-${Date.now()}`;
        const progressHTML = `
            <div id="${progressId}" class="progress-container">
                <div class="progress-label">${label}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-percentage">0%</div>
            </div>
        `;
        
        container.innerHTML = progressHTML;
        const progressElement = document.getElementById(progressId);
        this.activeProgressBars.set(progressId, {
            element: progressElement,
            fill: progressElement.querySelector('.progress-fill'),
            percentage: progressElement.querySelector('.progress-percentage')
        });
        
        return progressId;
    }
    
    updateProgress(progressId, percentage) {
        const progress = this.activeProgressBars.get(progressId);
        if (progress) {
            progress.fill.style.width = `${percentage}%`;
            progress.percentage.textContent = `${Math.round(percentage)}%`;
        }
    }
    
    completeProgress(progressId) {
        const progress = this.activeProgressBars.get(progressId);
        if (progress) {
            progress.fill.style.width = '100%';
            progress.percentage.textContent = '100%';
            
            setTimeout(() => {
                progress.element.remove();
                this.activeProgressBars.delete(progressId);
            }, 1000);
        }
    }
    
    removeProgress(progressId) {
        const progress = this.activeProgressBars.get(progressId);
        if (progress) {
            progress.element.remove();
            this.activeProgressBars.delete(progressId);
        }
    }
}

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }
    
    init() {
        document.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
    }
    
    register(keys, callback, description = '') {
        const keyString = Array.isArray(keys) ? keys.join('+') : keys;
        this.shortcuts.set(keyString, { callback, description });
    }
    
    handleKeydown(e) {
        const keys = [];
        
        if (e.ctrlKey || e.metaKey) keys.push('ctrl');
        if (e.altKey) keys.push('alt');
        if (e.shiftKey) keys.push('shift');
        keys.push(e.key.toLowerCase());
        
        const keyString = keys.join('+');
        const shortcut = this.shortcuts.get(keyString);
        
        if (shortcut) {
            e.preventDefault();
            shortcut.callback(e);
        }
    }
}

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
        this.init();
    }
    
    init() {
        this.createNotificationContainer();
    }
    
    createNotificationContainer() {
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }
    
    show(message, type = 'info', duration = 3000) {
        const notification = {
            id: Date.now(),
            message,
            type,
            duration
        };
        
        this.notifications.push(notification);
        this.renderNotification(notification);
        
        // Remove oldest notifications if we exceed max
        if (this.notifications.length > this.maxNotifications) {
            const oldest = this.notifications.shift();
            this.removeNotification(oldest.id);
        }
        
        // Auto remove after duration
        setTimeout(() => {
            this.removeNotification(notification.id);
        }, duration);
    }
    
    renderNotification(notification) {
        const container = document.getElementById('notification-container');
        const notificationEl = document.createElement('div');
        notificationEl.className = `notification notification-${notification.type}`;
        notificationEl.id = `notification-${notification.id}`;
        
        const iconMap = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        
        notificationEl.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${iconMap[notification.type]}"></i>
                <span>${notification.message}</span>
                <button class="notification-close" onclick="notificationManager.removeNotification(${notification.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(notificationEl);
        
        // Animate in
        setTimeout(() => {
            notificationEl.classList.add('show');
        }, 100);
    }
    
    removeNotification(id) {
        const notificationEl = document.getElementById(`notification-${id}`);
        if (notificationEl) {
            notificationEl.classList.remove('show');
            setTimeout(() => {
                if (notificationEl.parentNode) {
                    notificationEl.parentNode.removeChild(notificationEl);
                }
            }, 300);
        }
        
        // Remove from array
        this.notifications = this.notifications.filter(n => n.id !== id);
    }
}

// Initialize all managers when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme manager
    window.themeManager = new ThemeManager();
    
    // Initialize animation manager
    window.animationManager = new AnimationManager();
    
    // Initialize file upload manager
    window.fileUploadManager = new FileUploadManager();
    
    // Initialize progress manager
    window.progressManager = new ProgressManager();
    
    // Initialize keyboard shortcuts
    window.keyboardShortcuts = new KeyboardShortcuts();
    
    // Initialize notification manager
    window.notificationManager = new NotificationManager();
    
    // Register common keyboard shortcuts
    window.keyboardShortcuts.register(['ctrl', 'k'], () => {
        // Focus search or main input
        const searchInput = document.querySelector('input[type="search"], input[type="text"], textarea');
        if (searchInput) {
            searchInput.focus();
        }
    }, 'Focus search');
    
    window.keyboardShortcuts.register(['ctrl', '/'], () => {
        // Show help or shortcuts
        window.notificationManager.show('Keyboard shortcuts: Ctrl+K (focus), Ctrl+/ (help)', 'info');
    }, 'Show help');
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading states to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.classList.contains('btn-loading')) return;
            
            const originalText = this.innerHTML;
            this.classList.add('btn-loading');
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            
            // Remove loading state after 3 seconds (adjust as needed)
            setTimeout(() => {
                this.classList.remove('btn-loading');
                this.innerHTML = originalText;
            }, 3000);
        });
    });
    
    // Add ripple effect to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add CSS for ripple effect
    const rippleStyle = document.createElement('style');
    rippleStyle.textContent = `
        .btn {
            position: relative;
            overflow: hidden;
        }
        
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .btn-loading {
            pointer-events: none;
            opacity: 0.7;
        }
        
        .progress-container {
            background: var(--bg-glass);
            backdrop-filter: var(--glass-backdrop);
            border: 1px solid var(--glass-border);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .progress-label {
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }
        
        .progress-bar {
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            transition: width 0.3s ease;
        }
        
        .progress-percentage {
            text-align: right;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .notification {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-backdrop);
            border: 1px solid var(--glass-border);
            border-radius: 0.5rem;
            padding: 1rem;
            box-shadow: var(--shadow-lg);
            transform: translateX(100%);
            transition: transform var(--transition-normal);
            min-width: 300px;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .notification-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0.25rem;
            margin-left: auto;
        }
        
        .notification-close:hover {
            color: var(--text-primary);
        }
    `;
    document.head.appendChild(rippleStyle);
});

// Export for use in other scripts
window.EdumateJS = {
    ThemeManager,
    AnimationManager,
    FileUploadManager,
    ProgressManager,
    KeyboardShortcuts,
    NotificationManager
};

