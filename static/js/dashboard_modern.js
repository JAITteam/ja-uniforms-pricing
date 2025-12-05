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
            const response = await fetch('/api/recent-styles');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update UI with new data
            const container = document.getElementById('recent-styles-list');
            if (!container) return;
            
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
    
    // ===== GET ALL STYLE IDS (Helper) =====
    function getAllStyleIds() {
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
    
    // ===== EXPORT MODAL FUNCTIONS =====
    var allStylesData = [];

    window.openExportModal = function() {
        var modal = document.getElementById('exportModal');
        if (modal) {
            modal.classList.add('active');
            loadAllStyles();
        }
    };

    function closeExportModal() {
        var modal = document.getElementById('exportModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    function loadAllStyles() {
        var exportList = document.getElementById('exportStylesList');
        if (!exportList) return;
        
        exportList.innerHTML = '<div class="export-loading">Loading styles...</div>';
        
        fetch('/api/all-styles-for-export')
            .then(function(response) { return response.json(); })
            .then(function(data) {
                allStylesData = data;
                renderExportList(data);
            })
            .catch(function(error) {
                console.error('Error loading styles:', error);
                exportList.innerHTML = '<div class="no-results">Error loading styles. Please try again.</div>';
            });
    }

    function renderExportList(styles) {
        var exportList = document.getElementById('exportStylesList');
        exportList.innerHTML = '';
        
        if (styles.length === 0) {
            exportList.innerHTML = '<div class="no-results">No styles found</div>';
            return;
        }
        
        styles.forEach(function(style) {
            var item = document.createElement('div');
            item.className = 'export-style-item';
            item.setAttribute('data-search', (style.vendor_style + ' ' + style.style_name).toLowerCase());
            item.innerHTML = 
                '<label>' +
                    '<input type="checkbox" class="export-style-checkbox" value="' + style.id + '">' +
                    '<div class="export-style-info">' +
                        '<strong>' + style.vendor_style + '</strong>' +
                        '<span>' + style.style_name + '</span>' +
                        '<small>' + style.gender + ' &bull; $' + style.cost.toFixed(2) + '</small>' +
                    '</div>' +
                '</label>';
            exportList.appendChild(item);
        });
        
        document.querySelectorAll('.export-style-checkbox').forEach(function(cb) {
            cb.addEventListener('change', updateExportCount);
        });
        
        var totalCountEl = document.getElementById('exportTotalCount');
        if (totalCountEl) totalCountEl.textContent = styles.length;
        updateExportCount();
    }

    function filterExportList() {
        var searchInput = document.getElementById('exportSearch');
        if (!searchInput) return;
        
        var searchValue = searchInput.value.toLowerCase();
        document.querySelectorAll('.export-style-item').forEach(function(item) {
            var searchData = item.getAttribute('data-search') || '';
            item.style.display = searchData.indexOf(searchValue) !== -1 ? '' : 'none';
        });
    }

    function toggleExportSelectAll() {
        var selectAll = document.getElementById('exportSelectAll');
        if (!selectAll) return;
        
        document.querySelectorAll('.export-style-checkbox').forEach(function(cb) {
            if (cb.closest('.export-style-item').style.display !== 'none') {
                cb.checked = selectAll.checked;
            }
        });
        updateExportCount();
    }

    function updateExportCount() {
        var checked = document.querySelectorAll('.export-style-checkbox:checked').length;
        var countEl = document.getElementById('exportSelectedCount');
        if (countEl) countEl.textContent = checked;
    }

    function exportSelectedFromModal() {
        var checkboxes = document.querySelectorAll('.export-style-checkbox:checked');
        var checked = [];
        checkboxes.forEach(function(cb) { checked.push(parseInt(cb.value)); });
        
        if (checked.length === 0) {
            alert('Please select at least one style to export');
            return;
        }
        
        closeExportModal();
        
        var csrfMeta = document.querySelector('meta[name="csrf-token"]');
        var csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
        
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/export-sap-format';
        
        var csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'style_ids';
        input.value = JSON.stringify(checked);
        form.appendChild(input);
        
        document.body.appendChild(form);
        form.submit();
    }

    // Bind export modal events
    function setupExportModal() {
        var closeBtn = document.getElementById('closeExportBtn');
        var cancelBtn = document.getElementById('cancelExportBtn');
        var searchInput = document.getElementById('exportSearch');
        var selectAllCb = document.getElementById('exportSelectAll');
        var doExportBtn = document.getElementById('doExportBtn');
        var exportModal = document.getElementById('exportModal');

        if (closeBtn) closeBtn.addEventListener('click', closeExportModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeExportModal);
        if (searchInput) searchInput.addEventListener('keyup', filterExportList);
        if (selectAllCb) selectAllCb.addEventListener('change', toggleExportSelectAll);
        if (doExportBtn) doExportBtn.addEventListener('click', exportSelectedFromModal);
        if (exportModal) {
            exportModal.addEventListener('click', function(e) {
                if (e.target === this) closeExportModal();
            });
        }
    }
    
    // ===== INITIALIZE =====
    updateGreeting();
    updateDateTime();
    updateLastUpdated();
    updateRelativeTimes();
    setupMoreActionsMenu();
    setupExportModal();
    
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