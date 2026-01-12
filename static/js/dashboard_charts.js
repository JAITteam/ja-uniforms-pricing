/* ============================================
   DASHBOARD CHARTS - Chart.js Integration
   Real charts with live data from API
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    
    // Store chart instances for updates
    let costBreakdownChart = null;
    let compareStylesChart = null;
    
    // Load chart data from API
    loadChartData();
    loadStylesDropdown();
    loadCompareStylesDropdowns();
    
    async function loadChartData() {
        try {
            const response = await fetch('/api/dashboard-charts');
            if (!response.ok) throw new Error('Failed to load chart data');
            
            const data = await response.json();
            
            // Render all charts
            renderCostDistributionChart(data.cost_distribution);
            renderTopFabricsChart(data.top_fabrics);
            renderCostBreakdownChart(data.cost_breakdown, 'All Styles (Average)');
            renderActivityTrendChart(data.activity_trend);
            renderQuickInsights(data.insights);
            
        } catch (error) {
            console.error('Error loading chart data:', error);
        }
    }
    
    // ===== LOAD STYLES FOR COST BREAKDOWN DROPDOWN =====
    async function loadStylesDropdown() {
        try {
            const response = await fetch('/api/styles-list-simple');
            if (!response.ok) return;
            
            const styles = await response.json();
            const dropdown = document.getElementById('costBreakdownStyleSelect');
            if (!dropdown) return;
            
            dropdown.innerHTML = '<option value="all">All Styles (Average)</option>';
            
            styles.forEach(style => {
                const option = document.createElement('option');
                option.value = style.id;
                option.textContent = style.vendor_style + ' - ' + style.style_name;
                dropdown.appendChild(option);
            });
            
            dropdown.addEventListener('change', async function() {
                await updateCostBreakdown(this.value);
            });
            
        } catch (error) {
            console.error('Error loading styles dropdown:', error);
        }
    }
    
    // ===== LOAD STYLES FOR COMPARE DROPDOWNS =====
    async function loadCompareStylesDropdowns() {
        try {
            const response = await fetch('/api/styles-list-simple');
            if (!response.ok) return;
            
            const styles = await response.json();
            const dropdown1 = document.getElementById('compareStyle1');
            const dropdown2 = document.getElementById('compareStyle2');
            
            if (!dropdown1 || !dropdown2) return;
            
            // Populate both dropdowns
            [dropdown1, dropdown2].forEach((dropdown, index) => {
                dropdown.innerHTML = '<option value="">Select Style ' + (index + 1) + '...</option>';
                styles.forEach(style => {
                    const option = document.createElement('option');
                    option.value = style.id;
                    option.textContent = style.vendor_style;
                    dropdown.appendChild(option);
                });
            });
            
            // Add change event listeners
            dropdown1.addEventListener('change', updateCompareChart);
            dropdown2.addEventListener('change', updateCompareChart);
            
            // Initialize with empty chart message
            renderCompareStylesPlaceholder();
            
        } catch (error) {
            console.error('Error loading compare dropdowns:', error);
        }
    }
    
    // ===== UPDATE COMPARE STYLES CHART =====
    async function updateCompareChart() {
        const style1 = document.getElementById('compareStyle1').value;
        const style2 = document.getElementById('compareStyle2').value;
        
        // Need at least one style selected
        if (!style1 && !style2) {
            renderCompareStylesPlaceholder();
            return;
        }
        
        const selectedIds = [style1, style2].filter(id => id).join(',');
        
        try {
            const response = await fetch('/api/compare-styles?style_ids=' + selectedIds);
            if (!response.ok) throw new Error('Failed to load comparison');
            
            const data = await response.json();
            renderCompareStylesChart(data.styles);
            
        } catch (error) {
            console.error('Error updating compare chart:', error);
        }
    }
    
    // ===== RENDER COMPARE STYLES PLACEHOLDER =====
    function renderCompareStylesPlaceholder() {
        const container = document.getElementById('compareChartContainer');
        if (!container) return;
        
        if (compareStylesChart) {
            compareStylesChart.destroy();
            compareStylesChart = null;
        }
        
        container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #9CA3AF; font-size: 13px; text-align: center;">Select styles above<br>to compare costs</div>';
    }
    
    // ===== RENDER COMPARE STYLES CHART =====
    function renderCompareStylesChart(styles) {
        const container = document.getElementById('compareChartContainer');
        if (!container || !styles || styles.length === 0) return;
        
        // Destroy existing chart
        if (compareStylesChart) {
            compareStylesChart.destroy();
        }
        
        // Create canvas
        container.innerHTML = '<canvas id="compareStylesCanvas"></canvas>';
        const ctx = document.getElementById('compareStylesCanvas').getContext('2d');
        
        // Prepare data
        const labels = ['Fabric', 'Labor', 'Notions', 'Total'];
        const colors = [
            { bg: 'rgba(102, 126, 234, 0.8)', border: 'rgba(102, 126, 234, 1)' },
            { bg: 'rgba(17, 153, 142, 0.8)', border: 'rgba(17, 153, 142, 1)' },
            { bg: 'rgba(240, 147, 251, 0.8)', border: 'rgba(240, 147, 251, 1)' }
        ];
        
        const datasets = styles.map((style, index) => ({
            label: style.name,
            data: [style.fabric, style.labor, style.notions, style.total],
            backgroundColor: colors[index].bg,
            borderColor: colors[index].border,
            borderWidth: 2,
            borderRadius: 4
        }));
        
        compareStylesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 8,
                            usePointStyle: true,
                            font: { size: 10 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        padding: 10,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { 
                            font: { size: 10 },
                            callback: function(value) {
                                return '$' + value;
                            }
                        },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        ticks: { font: { size: 10 } },
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    // ===== UPDATE COST BREAKDOWN FOR SELECTED STYLE =====
    async function updateCostBreakdown(styleId) {
        try {
            const response = await fetch('/api/style-cost-breakdown?style_id=' + styleId);
            if (!response.ok) throw new Error('Failed to load style breakdown');
            
            const data = await response.json();
            renderCostBreakdownChart(data, data.style_name, data.total_cost);
            
        } catch (error) {
            console.error('Error updating cost breakdown:', error);
        }
    }
    
    // ===== COST DISTRIBUTION BAR CHART =====
    function renderCostDistributionChart(data) {
        const container = document.getElementById('costDistributionChart');
        if (!container || !data) return;
        
        container.innerHTML = '<canvas id="costDistCanvas"></canvas>';
        const ctx = document.getElementById('costDistCanvas').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Styles',
                    data: data.values,
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)',
                        'rgba(17, 153, 142, 0.8)',
                        'rgba(56, 239, 125, 0.8)',
                        'rgba(255, 216, 155, 0.8)',
                        'rgba(240, 147, 251, 0.8)'
                    ],
                    borderColor: [
                        'rgba(102, 126, 234, 1)',
                        'rgba(118, 75, 162, 1)',
                        'rgba(17, 153, 142, 1)',
                        'rgba(56, 239, 125, 1)',
                        'rgba(255, 216, 155, 1)',
                        'rgba(240, 147, 251, 1)'
                    ],
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + ' styles';
                            }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
    
    // ===== TOP FABRICS HORIZONTAL BAR CHART =====
    function renderTopFabricsChart(data) {
        const container = document.getElementById('topFabricsChart');
        if (!container || !data) return;
        
        container.innerHTML = '<canvas id="topFabricsCanvas"></canvas>';
        const ctx = document.getElementById('topFabricsCanvas').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Used in styles',
                    data: data.values,
                    backgroundColor: 'rgba(17, 153, 142, 0.8)',
                    borderColor: 'rgba(17, 153, 142, 1)',
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                return 'Used in ' + context.parsed.x + ' styles';
                            }
                        }
                    }
                },
                scales: {
                    x: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { grid: { display: false } }
                }
            }
        });
    }
    
    // ===== COST BREAKDOWN PIE CHART =====
    function renderCostBreakdownChart(data, styleName, totalCost) {
        const canvas = document.getElementById('costBreakdownChartCanvas');
        if (!canvas || !data) return;
        
        if (costBreakdownChart) {
            costBreakdownChart.destroy();
        }
        
        const titleEl = document.getElementById('costBreakdownTitle');
        if (titleEl && styleName) {
            titleEl.textContent = styleName.length > 35 ? styleName.substring(0, 35) + '...' : styleName;
        }
        
        const totalEl = document.getElementById('costBreakdownTotal');
        if (totalEl && totalCost !== undefined) {
            totalEl.textContent = 'Total: $' + totalCost.toFixed(2);
        }
        
        const ctx = canvas.getContext('2d');
        
        costBreakdownChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.85)',
                        'rgba(17, 153, 142, 0.85)',
                        'rgba(255, 216, 155, 0.85)',
                        'rgba(240, 147, 251, 0.85)'
                    ],
                    borderColor: [
                        'rgba(102, 126, 234, 1)',
                        'rgba(17, 153, 142, 1)',
                        'rgba(255, 216, 155, 1)',
                        'rgba(240, 147, 251, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 10, usePointStyle: true, font: { size: 10 } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                return context.label + ': $' + context.parsed.toFixed(2) + ' (' + pct + '%)';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // ===== ACTIVITY TREND LINE CHART =====
    function renderActivityTrendChart(data) {
        const container = document.getElementById('activityTrendChart');
        if (!container || !data) return;
        
        container.innerHTML = '<canvas id="activityTrendCanvas"></canvas>';
        const ctx = document.getElementById('activityTrendCanvas').getContext('2d');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Styles Created',
                    data: data.values,
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + ' styles created';
                            }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
    
    // ===== QUICK INSIGHTS =====
    function renderQuickInsights(data) {
        const container = document.getElementById('quickInsightsList');
        if (!container || !data) return;
        
        container.innerHTML = data.map(insight => '<li>' + insight + '</li>').join('');
    }
    
    console.log('Dashboard charts initialized');
});