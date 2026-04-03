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

    // Prepare data - extract numeric marks and sort by them
    const studentData = results
        .filter(row => row.Roll_Number && row.Name)
        .map(row => {
            const marksStr = row.Total_Marks ? String(row.Total_Marks) : '';
            // Try to extract numbers from string like "PASS 518", otherwise 0
            const numericMatch = marksStr.match(/\d+/);
            const numericMarks = numericMatch ? parseInt(numericMatch[0]) : 0;
            
            return {
                rollNumber: parseInt(row.Roll_Number) || 0,
                name: row.Name || 'Unknown',
                rawMarks: marksStr,
                numericMarks: numericMarks
            };
        })
        .filter(s => s.numericMarks > 0); // Only plot students with valid numeric marks

    // Create scatter data points
    const scatterData = studentData.map(s => ({
        x: s.rollNumber,
        y: s.numericMarks,
        name: s.name,
        rawMarks: s.rawMarks
    }));

    studentPerformanceChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Student Marks',
                data: scatterData,
                backgroundColor: 'rgba(99, 102, 241, 0.8)', // Indigo
                borderColor: 'rgba(79, 70, 229, 1)',
                pointRadius: 6,
                pointHoverRadius: 8,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
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
                        label: function(context) {
                            const point = context.raw;
                            return [
                                'Name: ' + point.name,
                                'Roll No: ' + point.x,
                                'Status/Marks: ' + point.rawMarks
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Roll Number',
                        color: '#f8fafc'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: { family: "'Poppins', sans-serif" }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Total Marks',
                        color: '#f8fafc'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: { family: "'Poppins', sans-serif" }
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
