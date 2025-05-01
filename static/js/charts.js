// Chart.js initialization and helpers

function initializeScoreDistributionChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Students',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    precision: 0
                }
            }
        }
    });
}

function initializePerformanceChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score',
                data: data,
                fill: false,
                borderColor: 'rgba(75, 192, 192, 1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Initialize charts if they exist on the page
document.addEventListener('DOMContentLoaded', function() {
    const scoreCtx = document.getElementById('scoreDistributionChart');
    const performanceCtx = document.getElementById('performanceChart');
    
    if (scoreCtx) {
        // Data should be passed from the template
        const labels = JSON.parse(scoreCtx.getAttribute('data-labels'));
        const data = JSON.parse(scoreCtx.getAttribute('data-values'));
        initializeScoreDistributionChart(scoreCtx.getContext('2d'), labels, data);
    }
    
    if (performanceCtx) {
        // Data should be passed from the template
        const labels = JSON.parse(performanceCtx.getAttribute('data-labels'));
        const data = JSON.parse(performanceCtx.getAttribute('data-values'));
        initializePerformanceChart(performanceCtx.getContext('2d'), labels, data);
    }
});