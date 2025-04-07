// Main JavaScript file for StockGPT
document.addEventListener('DOMContentLoaded', function() {
    console.log('StockGPT application loaded');
    
    // Initialize tooltips if any
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', showTooltip);
        tooltip.addEventListener('mouseleave', hideTooltip);
    });
    
    // Initialize any charts that don't use Chart.js
    initializeCharts();
});

function showTooltip(event) {
    const tooltip = event.target;
    const tooltipText = tooltip.getAttribute('data-tooltip');
    
    const tooltipElement = document.createElement('div');
    tooltipElement.className = 'tooltip';
    tooltipElement.textContent = tooltipText;
    
    document.body.appendChild(tooltipElement);
    
    const rect = tooltip.getBoundingClientRect();
    tooltipElement.style.top = `${rect.top - tooltipElement.offsetHeight - 10}px`;
    tooltipElement.style.left = `${rect.left + (rect.width - tooltipElement.offsetWidth) / 2}px`;
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function initializeCharts() {
    // Add any non-Chart.js chart initialization here
    // For example, if you're using D3.js or other charting libraries
}

// Helper function to format numbers
function formatNumber(number) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number);
}

// Helper function to format percentages
function formatPercentage(number) {
    return new Intl.NumberFormat('en-IN', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(number / 100);
}

// Helper function to format dates
function formatDate(date) {
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
} 