/* ============================================
   MODERN DASHBOARD JAVASCRIPT
   Auto-refresh, smart greetings, time updates
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== SMART GREETING =====
    function updateGreeting() {
        const greetingElement = document.getElementById('greeting');
        if (!greetingElement) return;
        
        const hour = new Date().getHours();
        
        // Extract current username from the greeting (set by Jinja2 template)
        const currentText = greetingElement.textContent;
        const userNameMatch = currentText.match(/,\s*([^!]+)!/);
        const userName = userNameMatch ? userNameMatch[1] : 'Admin';
        
        let greeting = '';
        let emoji = '';
        
        if (hour >= 5 && hour < 12) {
            greeting = 'Good morning';
            emoji = '☀️';
        } else if (hour >= 12 && hour < 18) {
            greeting = 'Good afternoon';
            emoji = '👋';
        } else if (hour >= 18 && hour < 22) {
            greeting = 'Good evening';
            emoji = '🌙';
        } else {
            greeting = 'Good night';
            emoji = '🌟';
        }
        
        // Check if first login (you can use localStorage or session)
        const lastVisit = localStorage.getItem('lastDashboardVisit');
        const now = new Date().getTime();
        const isFirstToday = !lastVisit || (now - lastVisit) > 6 * 60 * 60 * 1000; // 6 hours
        
        if (isFirstToday) {
            greetingElement.innerHTML = `${greeting}, ${userName}! ${emoji}`;
            localStorage.setItem('lastDashboardVisit', now);
        } else {
            greetingElement.innerHTML = `Welcome back, ${userName}! ${emoji}`;
        }
    }
        
    // ===== UPDATE DATE/TIME =====
    function updateDateTime() {
        const dateElement = document.getElementById('current-date');
        if (!dateElement) return;
        
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        const date = new Date().toLocaleDateString('en-US', options);
        dateElement.textContent = date;
    }
    
    // ===== UPDATE "LAST UPDATED" TIMESTAMP =====
    function updateLastUpdated() {
        const lastUpdatedElement = document.getElementById('last-updated');
        if (!lastUpdatedElement) return;
        
        const now = new Date();
        lastUpdatedElement.textContent = `Last updated: ${now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        })}`;
    }
    
    // ===== RELATIVE TIME FOR RECENT STYLES =====
    function updateRelativeTimes() {
        const timeElements = document.querySelectorAll('[data-timestamp]');
        
        timeElements.forEach(element => {
            const timestamp = parseInt(element.getAttribute('data-timestamp'));
            if (!timestamp) return;
            
            const now = Date.now();
            const diff = now - timestamp;
            
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            let relativeTime = '';
            
            if (seconds < 60) {
                relativeTime = 'just now';
            } else if (minutes < 60) {
                relativeTime = `${minutes} min${minutes !== 1 ? 's' : ''} ago`;
            } else if (hours < 24) {
                relativeTime = `${hours} hour${hours !== 1 ? 's' : ''} ago`;
            } else if (days === 1) {
                relativeTime = 'yesterday';
            } else if (days < 7) {
                relativeTime = `${days} days ago`;
            } else {
                relativeTime = 'over a week ago';
            }
            
            element.textContent = relativeTime;
        });
    }
    
    // ===== REFRESH RECENT STYLES =====
    async function refreshRecentStyles() {
        try {
            // Make API call to get recent styles
            // This is a placeholder - implement your actual API endpoint
            const response = await fetch('/api/recent-styles');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update UI with new data
            const container = document.getElementById('recent-styles-list');
            if (!container) return;
            
            // Re-render recent styles (you'll implement this based on your data structure)
            console.log('✅ Recent styles refreshed');
            
            // Update relative times
            updateRelativeTimes();
            updateLastUpdated();
            
        } catch (error) {
            console.error('Error refreshing recent styles:', error);
        }
    }
    
    // ===== REFRESH STATS =====
    async function refreshStats() {
        try {
            // Make API call to get updated stats
            // This is a placeholder - implement your actual API endpoint
            const response = await fetch('/api/dashboard-stats');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update stat cards with animation
            if (data.total_styles) {
                animateValue('stat-total-styles', data.total_styles);
            }
            if (data.avg_cost) {
                animateValue('stat-avg-cost', data.avg_cost, true);
            }
            
            console.log('✅ Stats refreshed');
            updateLastUpdated();
            
        } catch (error) {
            console.error('Error refreshing stats:', error);
        }
    }
    
    // ===== ANIMATE NUMBER CHANGES =====
    function animateValue(elementId, endValue, isCurrency = false) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const startValue = parseFloat(element.textContent.replace(/[^0-9.-]/g, '')) || 0;
        const duration = 1000; // 1 second
        const startTime = Date.now();
        
        function update() {
            const now = Date.now();
            const progress = Math.min((now - startTime) / duration, 1);
            
            const currentValue = startValue + (endValue - startValue) * progress;
            
            if (isCurrency) {
                element.textContent = `$${currentValue.toFixed(2)}`;
            } else {
                element.textContent = Math.round(currentValue);
            }
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        update();
    }
    
    // ===== EXPORT ALL FUNCTIONALITY =====
    function setupExportButton() {
        const exportBtn = document.getElementById('export-all-btn');
        if (!exportBtn) return;
        
        exportBtn.addEventListener('click', async function() {
            // Show confirmation
            if (!confirm('Export all styles to SAP B1 format?\n\nThis will download a CSV file with all size/color combinations.')) {
                return;
            }
            
            // Show loading state
            const originalText = exportBtn.innerHTML;
            exportBtn.innerHTML = '⏳ Exporting...';
            exportBtn.disabled = true;
            
            try {
                // Get all style IDs (you'll need to implement this based on your data)
                const styleIds = getAllStyleIds();
                
                // Create form and submit
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/export-sap-format';
                
                // Add CSRF token
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
                if (csrfToken) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrf_token';
                    csrfInput.value = csrfToken;
                    form.appendChild(csrfInput);
                }
                
                // Add style IDs
                const idsInput = document.createElement('input');
                idsInput.type = 'hidden';
                idsInput.name = 'style_ids';
                idsInput.value = JSON.stringify(styleIds);
                form.appendChild(idsInput);
                
                document.body.appendChild(form);
                form.submit();
                document.body.removeChild(form);
                
                // Reset button after 2 seconds
                setTimeout(() => {
                    exportBtn.innerHTML = originalText;
                    exportBtn.disabled = false;
                }, 2000);
                
            } catch (error) {
                console.error('Export error:', error);
                alert('Export failed. Please try again.');
                exportBtn.innerHTML = originalText;
                exportBtn.disabled = false;
            }
        });
    }
    
    // ===== GET ALL STYLE IDS (Helper) =====
    function getAllStyleIds() {
        // This should get all style IDs from your page
        // Placeholder implementation
        const styleElements = document.querySelectorAll('[data-style-id]');
        return Array.from(styleElements).map(el => el.getAttribute('data-style-id'));
    }
    
    // ===== MORE ACTIONS MENU =====
    function setupMoreActionsMenu() {
        const moreBtn = document.getElementById('more-actions-btn');
        const moreMenu = document.getElementById('more-actions-menu');
        
        if (!moreBtn || !moreMenu) return;
        
        moreBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            moreMenu.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (moreMenu && !moreMenu.contains(e.target) && e.target !== moreBtn) {
                moreMenu.classList.remove('active');
            }
        });
    }
    
    // ===== INITIALIZE =====
    updateGreeting();
    updateDateTime();
    updateLastUpdated();
    updateRelativeTimes();
    setupExportButton();
    setupMoreActionsMenu();
    
    // ===== AUTO-REFRESH INTERVALS =====
    
    // Refresh recent styles every 30 seconds
    setInterval(() => {
        refreshRecentStyles();
        updateRelativeTimes();
    }, 30000);
    
    // Refresh stats every 5 minutes
    setInterval(() => {
        refreshStats();
    }, 300000);
    
    // Update relative times every 10 seconds
    setInterval(() => {
        updateRelativeTimes();
    }, 10000);
    
    // Update "last updated" timestamp every second
    setInterval(() => {
        const lastUpdatedElement = document.getElementById('last-updated');
        if (lastUpdatedElement) {
            const text = lastUpdatedElement.textContent;
            const match = text.match(/(\d+):(\d+)/);
            if (match) {
                const now = new Date();
                const updateTime = new Date();
                updateTime.setHours(parseInt(match[1]), parseInt(match[2]), 0);
                
                const diff = Math.floor((now - updateTime) / 1000);
                
                if (diff < 60) {
                    lastUpdatedElement.textContent = `Last updated: ${diff} second${diff !== 1 ? 's' : ''} ago`;
                }
            }
        }
    }, 1000);
    
    console.log('✅ Modern Dashboard initialized');
    console.log('🔄 Auto-refresh: Recent styles (30s) | Stats (5min)');
});

// ===== CHART.JS INITIALIZATION (if using charts) =====
// Uncomment and customize when implementing charts

/*
function initCharts() {
    // Cost Distribution Chart
    const costDistCtx = document.getElementById('costDistributionChart');
    if (costDistCtx) {
        new Chart(costDistCtx, {
            type: 'bar',
            data: {
                labels: ['$0-$20', '$20-$40', '$40-$60', '$60-$80', '$80+'],
                datasets: [{
                    label: 'Styles',
                    data: [5, 12, 8, 5, 2],
                    backgroundColor: 'rgba(102, 126, 234, 0.5)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Top Fabrics Chart
    const topFabricsCtx = document.getElementById('topFabricsChart');
    if (topFabricsCtx) {
        new Chart(topFabricsCtx, {
            type: 'horizontalBar',
            data: {
                labels: ['XANADU', 'Cotton', 'Polyester', 'Denim', 'Silk'],
                datasets: [{
                    label: 'Usage',
                    data: [15, 12, 10, 8, 5],
                    backgroundColor: 'rgba(17, 153, 142, 0.5)',
                    borderColor: 'rgba(17, 153, 142, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// Call this after DOM is loaded
// initCharts();
*/