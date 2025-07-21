/**
 * Grocify Charts - Interactive Data Visualization Library
 * Built with Chart.js for modern, responsive charts
 */

class GrocifyCharts {
    constructor() {
        this.charts = new Map();
        this.colorScheme = {
            primary: '#6366f1',
            secondary: '#8b5cf6',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#3b82f6',
            light: '#f8fafc',
            dark: '#1e293b'
        };
        this.gradients = {};
        this.init();
    }

    init() {
        this.setupGradients();
        this.loadChartDefaults();
    }

    setupGradients() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Primary gradient
        this.gradients.primary = ctx.createLinearGradient(0, 0, 0, 400);
        this.gradients.primary.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
        this.gradients.primary.addColorStop(1, 'rgba(99, 102, 241, 0.05)');
        
        // Success gradient
        this.gradients.success = ctx.createLinearGradient(0, 0, 0, 400);
        this.gradients.success.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
        this.gradients.success.addColorStop(1, 'rgba(16, 185, 129, 0.05)');
        
        // Warning gradient
        this.gradients.warning = ctx.createLinearGradient(0, 0, 0, 400);
        this.gradients.warning.addColorStop(0, 'rgba(245, 158, 11, 0.4)');
        this.gradients.warning.addColorStop(1, 'rgba(245, 158, 11, 0.05)');
        
        // Multi-color gradient for diverse data
        this.gradients.rainbow = ctx.createLinearGradient(0, 0, 0, 400);
        this.gradients.rainbow.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
        this.gradients.rainbow.addColorStop(0.5, 'rgba(139, 92, 246, 0.3)');
        this.gradients.rainbow.addColorStop(1, 'rgba(16, 185, 129, 0.05)');
    }

    loadChartDefaults() {
        if (typeof Chart !== 'undefined') {
            Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
            Chart.defaults.font.size = 12;
            Chart.defaults.color = '#64748b';
            Chart.defaults.borderColor = '#e2e8f0';
            Chart.defaults.backgroundColor = 'rgba(99, 102, 241, 0.1)';
            
            // Responsive defaults
            Chart.defaults.responsive = true;
            Chart.defaults.maintainAspectRatio = false;
            Chart.defaults.interaction.intersect = false;
            Chart.defaults.interaction.mode = 'index';
        }
    }

    // Revenue Chart - Line chart with area fill
    createRevenueChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = {
            labels: data.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Revenue',
                data: data.revenue || [15000, 18000, 12000, 25000, 22000, 30000],
                borderColor: this.colorScheme.primary,
                backgroundColor: this.gradients.primary,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: this.colorScheme.primary,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointHoverBackgroundColor: this.colorScheme.primary,
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 3
            }]
        };

        const config = {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue Overview',
                        font: { size: 16, weight: '600' },
                        color: '#1e293b',
                        padding: 20
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colorScheme.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: (context) => `Revenue: $${context.parsed.y.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#f1f5f9',
                            drawBorder: false
                        },
                        border: {
                            display: false
                        },
                        ticks: {
                            callback: (value) => `$${value.toLocaleString()}`
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    // Sales Distribution - Doughnut chart
    createSalesDistributionChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = {
            labels: data.labels || ['Groceries', 'Electronics', 'Clothing', 'Books', 'Sports'],
            datasets: [{
                data: data.values || [35, 25, 20, 12, 8],
                backgroundColor: [
                    this.colorScheme.primary,
                    this.colorScheme.secondary,
                    this.colorScheme.success,
                    this.colorScheme.warning,
                    this.colorScheme.info
                ],
                borderColor: '#ffffff',
                borderWidth: 3,
                hoverBorderWidth: 4,
                hoverOffset: 8
            }]
        };

        const config = {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    title: {
                        display: true,
                        text: 'Sales by Category',
                        font: { size: 16, weight: '600' },
                        color: '#1e293b',
                        padding: 20
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colorScheme.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => {
                                const percentage = ((context.parsed / context.dataset.data.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 2000
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    // Monthly Comparison - Bar chart
    createMonthlyComparisonChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = {
            labels: data.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [
                {
                    label: 'This Year',
                    data: data.thisYear || [12000, 15000, 11000, 18000, 16000, 22000],
                    backgroundColor: this.colorScheme.primary,
                    borderColor: this.colorScheme.primary,
                    borderWidth: 0,
                    borderRadius: 8,
                    borderSkipped: false
                },
                {
                    label: 'Last Year',
                    data: data.lastYear || [10000, 12000, 13000, 15000, 14000, 19000],
                    backgroundColor: this.colorScheme.secondary,
                    borderColor: this.colorScheme.secondary,
                    borderWidth: 0,
                    borderRadius: 8,
                    borderSkipped: false
                }
            ]
        };

        const config = {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Monthly Sales Comparison',
                        font: { size: 16, weight: '600' },
                        color: '#1e293b',
                        padding: 20
                    },
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colorScheme.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#f1f5f9',
                            drawBorder: false
                        },
                        border: {
                            display: false
                        },
                        ticks: {
                            callback: (value) => `$${value.toLocaleString()}`
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutBounce'
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    // Top Products - Horizontal bar chart
    createTopProductsChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = {
            labels: data.labels || ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
            datasets: [{
                label: 'Sales',
                data: data.values || [850, 720, 680, 590, 450],
                backgroundColor: [
                    this.colorScheme.primary,
                    this.colorScheme.secondary,
                    this.colorScheme.success,
                    this.colorScheme.warning,
                    this.colorScheme.info
                ],
                borderColor: '#ffffff',
                borderWidth: 2,
                borderRadius: 6
            }]
        };

        const config = {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    title: {
                        display: true,
                        text: 'Top Selling Products',
                        font: { size: 16, weight: '600' },
                        color: '#1e293b',
                        padding: 20
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colorScheme.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => `Sales: ${context.parsed.x.toLocaleString()} units`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: '#f1f5f9',
                            drawBorder: false
                        },
                        border: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        border: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1800,
                    easing: 'easeOutQuart'
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    // Inventory Status - Radar chart
    createInventoryStatusChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = {
            labels: data.labels || ['In Stock', 'Low Stock', 'Out of Stock', 'Overstocked', 'Ordered'],
            datasets: [{
                label: 'Current Status',
                data: data.current || [85, 15, 5, 10, 25],
                borderColor: this.colorScheme.primary,
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                borderWidth: 2,
                pointBackgroundColor: this.colorScheme.primary,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5
            }, {
                label: 'Target Status',
                data: data.target || [90, 10, 0, 5, 20],
                borderColor: this.colorScheme.success,
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                pointBackgroundColor: this.colorScheme.success,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        };

        const config = {
            type: 'radar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Inventory Status Overview',
                        font: { size: 16, weight: '600' },
                        color: '#1e293b',
                        padding: 20
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#f1f5f9'
                        },
                        pointLabels: {
                            font: { size: 11 },
                            color: '#64748b'
                        },
                        ticks: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutCirc'
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    // Utility methods
    updateChartData(chartId, newData) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.data = newData;
            chart.update('active');
        }
    }

    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartId);
        }
    }

    destroyAllCharts() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }

    // Responsive helper
    resizeCharts() {
        this.charts.forEach(chart => {
            chart.resize();
        });
    }

    // Export chart as image
    exportChart(chartId, filename = 'chart') {
        const chart = this.charts.get(chartId);
        if (chart) {
            const link = document.createElement('a');
            link.download = `${filename}.png`;
            link.href = chart.toBase64Image();
            link.click();
        }
    }

    // Get chart data for API integration
    getChartData(chartId) {
        const chart = this.charts.get(chartId);
        return chart ? chart.data : null;
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.grocifyCharts = new GrocifyCharts();
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.grocifyCharts) {
            window.grocifyCharts.resizeCharts();
        }
    });
});