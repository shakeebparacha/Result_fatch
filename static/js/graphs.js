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
                const status = String(row.Status || '').toUpperCase();
                if (status === 'PASS') {
                    passCount++;
                } else if (status === 'FAIL') {
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

    // Check for subject group filter
    const filterElem = document.getElementById('subjectGroupFilter');
    if (filterElem && !filterElem.hasEventListener) {
        filterElem.addEventListener('change', loadGraphData);
        filterElem.hasEventListener = true;
    }

function renderStudentPerformanceChart(results) {
    const ctx = document.getElementById('studentPerformanceChart');
    if (!ctx) return;

    if (studentPerformanceChart) {
        studentPerformanceChart.destroy();
    }

    const filterVal = document.getElementById('subjectGroupFilter') ? document.getElementById('subjectGroupFilter').value : 'all';
    const scienceSubjectsList = ["PHYSICS", "CHEMISTRY", "MATH", "MATHEMATICS", "BIOLOGY", "COMPUTER", "STATISTICS"];

    // parse subject pass column to accumulate pass / fails for each subject
    // format expected: "English:PASS, URDU:FAIL"
    const subjectStats = {};

    results.forEach(row => {
        const subjectPassRaw = row.Subject_Pass || "";
        if (subjectPassRaw && subjectPassRaw !== "All Pass" && subjectPassRaw.includes(":")) {
            const subjects = subjectPassRaw.split(",");
            subjects.forEach(s => {
                const parts = s.split(":");
                if (parts.length >= 2) {
                    const subjName = parts[0].trim().toUpperCase();
                    const subjStatus = parts[1].trim().toUpperCase();

                    // Apply filter
                    const isScience = scienceSubjectsList.some(sci => subjName.includes(sci));
                    if (filterVal === 'science' && !isScience) return;
                    if (filterVal === 'arts' && isScience) return;

                    if (!subjectStats[subjName]) {
                        subjectStats[subjName] = { pass: 0, fail: 0 };
                    }
                    if (subjStatus.includes('PASS')) {
                        subjectStats[subjName].pass++;
                    } else {
                        subjectStats[subjName].fail++;
                    }
                }
            });
        }
    });

    let labels = Object.keys(subjectStats);
    
    // Sort labels by pass ratio 
    labels.sort((a, b) => {
        const totalA = subjectStats[a].pass + subjectStats[a].fail;
        const totalB = subjectStats[b].pass + subjectStats[b].fail;
        const ratioA = totalA > 0 ? subjectStats[a].pass / totalA : 0;
        const ratioB = totalB > 0 ? subjectStats[b].pass / totalB : 0;
        return ratioB - ratioA; // Descending order
    });

    const passData = labels.map(l => subjectStats[l].pass);
    const failData = labels.map(l => subjectStats[l].fail);

    studentPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Pass',
                    data: passData,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Fail',
                    data: failData,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: false,
                    ticks: { color: '#f8fafc' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    stacked: false,
                    beginAtZero: true,
                    ticks: { color: '#f8fafc', stepSize: 1 },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    borderColor: '#4f46e5',
                    borderWidth: 1
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
