/* ==================== GRAPHS PAGE ==================== */

let pieChart = null;
let barChart = null;
let studentPerformanceChart = null;

document.addEventListener('DOMContentLoaded', function() {
    loadGraphData();
    
    // Refresh graphs every 5 seconds
    setInterval(loadGraphData, 5000);
});

function loadGraphData() {
    fetch('/api/results')
        .then(response => response.json())
        .then(data => {
            const results = data.data || [];
            
            if (results.length === 0) {
                showNoDataMessage();
                return;
            }

            hideNoDataMessage();

            // Process data
            let passCount = 0;
            let failCount = 0;

            results.forEach(row => {
                const marks = String(row.Total_Marks || '').toLowerCase();
                if (marks.includes('pass')) {
                    passCount++;
                } else if (marks.length > 0) {
                    failCount++;
                }
            });

            // Update stats
            document.getElementById('totalStudents').textContent = results.length;
            document.getElementById('passCount').textContent = passCount;
            document.getElementById('failCount').textContent = failCount;

            const passRate = results.length > 0 ? ((passCount / results.length) * 100).toFixed(1) : 0;
            document.getElementById('passPercentage').textContent = passRate + '%';

            // Render charts
            renderPieChart(passCount, failCount);
            renderBarChart(passCount, failCount, results.length);
            renderStudentPerformanceChart(results);
        })
        .catch(error => {
            console.error('Error loading graph data:', error);
            showNoDataMessage();
        });
}

function renderPieChart(passCount, failCount) {
    const ctx = document.getElementById('pieChart');
    if (!ctx) return;

    // Destroy existing chart
    if (pieChart) {
        pieChart.destroy();
    }

    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Passed', 'Failed/Absent'],
            datasets: [{
                data: [passCount, failCount],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(239, 68, 68, 1)',
                ],
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#f8fafc',
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 14
                        },
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    borderColor: '#4f46e5',
                    borderWidth: 1,
                }
            }
        }
    });
}

function renderBarChart(passCount, failCount, total) {
    const ctx = document.getElementById('barChart');
    if (!ctx) return;

    // Destroy existing chart
    if (barChart) {
        barChart.destroy();
    }

    const absentCount = total - passCount - failCount;

    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Passed', 'Failed', 'Absent'],
            datasets: [{
                label: 'Number of Students',
                data: [passCount, failCount, absentCount],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(239, 68, 68, 0.7)',
                    'rgba(148, 163, 184, 0.7)',
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(148, 163, 184, 1)',
                ],
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#f8fafc',
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 14
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    borderColor: '#4f46e5',
                    borderWidth: 1,
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: "'Poppins', sans-serif",
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: "'Poppins', sans-serif",
                        }
                    }
                }
            }
        }
    });
}

function renderStudentPerformanceChart(results) {
    const ctx = document.getElementById('studentPerformanceChart');
    if (!ctx) return;

    // Destroy existing chart
    if (studentPerformanceChart) {
        studentPerformanceChart.destroy();
    }

    // Prepare data - sort by roll number or name in descending order
    const studentData = results
        .filter(row => row.Roll_Number && row.Name)
        .map(row => ({
            rollNumber: row.Roll_Number,
            name: row.Name || 'Unknown',
            marks: row.Total_Marks || 'N/A'
        }))
        .sort((a, b) => {
            // Sort by roll number descending
            return parseInt(b.rollNumber) - parseInt(a.rollNumber);
        })
        .slice(0, 15); // Show top 15 students

    const labels = studentData.map(s => s.rollNumber);
    const names = studentData.map(s => s.name);
    
    // Create gradient colors for attractiveness
    const colors = [
        'rgba(79, 70, 229, 0.8)',  // Indigo
        'rgba(59, 130, 246, 0.8)', // Blue
        'rgba(34, 197, 94, 0.8)',  // Green
        'rgba(16, 185, 129, 0.8)', // Teal
        'rgba(6, 182, 212, 0.8)',  // Cyan
        'rgba(139, 92, 246, 0.8)', // Purple
        'rgba(168, 85, 247, 0.8)', // Violet
        'rgba(236, 72, 153, 0.8)', // Pink
        'rgba(249, 115, 22, 0.8)', // Orange
        'rgba(234, 179, 8, 0.8)',  // Yellow
        'rgba(244, 63, 94, 0.8)',  // Rose
        'rgba(14, 165, 233, 0.8)', // Sky
        'rgba(34, 197, 94, 0.8)',  // Lime
        'rgba(249, 115, 22, 0.8)', // Amber
        'rgba(239, 68, 68, 0.8)'   // Red
    ];

    const borderColors = colors.map(c => c.replace('0.8', '1'));

    studentPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Student List',
                data: labels.map((_, i) => i + 1), // Just for visual height
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 8,
                hoverBackgroundColor: colors.map(c => c.replace('0.8', '0.95')),
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    borderColor: '#4f46e5',
                    borderWidth: 2,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            return 'Roll Number: ' + names[index];
                        },
                        label: function(tooltipItem) {
                            const index = tooltipItem.dataIndex;
                            return 'Name: ' + names[index];
                        },
                        afterLabel: function(tooltipItem) {
                            const index = tooltipItem.dataIndex;
                            return 'Status: ' + studentData[index].marks;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false,
                    beginAtZero: true,
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 12,
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    });
}

function showNoDataMessage() {
    const message = document.getElementById('noDataMessage');
    if (message) {
        message.style.display = 'block';
    }
    
    // Hide charts
    const pieContainer = document.getElementById('pieChart');
    const barContainer = document.getElementById('barChart');
    const perfContainer = document.getElementById('studentPerformanceChart');
    if (pieContainer) pieContainer.style.display = 'none';
    if (barContainer) barContainer.style.display = 'none';
    if (perfContainer) perfContainer.style.display = 'none';
}

function hideNoDataMessage() {
    const message = document.getElementById('noDataMessage');
    if (message) {
        message.style.display = 'none';
    }
    
    // Show charts
    const pieContainer = document.getElementById('pieChart');
    const barContainer = document.getElementById('barChart');
    const perfContainer = document.getElementById('studentPerformanceChart');
    if (pieContainer) pieContainer.style.display = 'block';
    if (barContainer) barContainer.style.display = 'block';
    if (perfContainer) perfContainer.style.display = 'block';
}
