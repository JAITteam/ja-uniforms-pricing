/* ============================================
   DASHBOARD CHARTS - Chart.js Integration
   Real charts with live data from API
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    
    // Store chart instances for updates
    let costBreakdownChart = null;
    
    // Load chart data from API
    loadChartData();
    loadStylesDropdown();
    
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
    
    // ===== LOAD STYLES FOR DROPDOWN =====
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
