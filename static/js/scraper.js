/* ==================== SCRAPER PAGE ==================== */

let lastScrapeStatus = null;

document.addEventListener('DOMContentLoaded', function() {
    const scraperForm = document.getElementById('scraperForm');
    if (scraperForm) {
        scraperForm.addEventListener('submit', handleScraperSubmit);
    }

    const downloadBtn = document.getElementById('downloadScrapeReportBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            if (!lastScrapeStatus) {
                logToTerminal('> No completed scrape status found yet.', 'terminal-warning');
                return;
            }
            downloadScrapeReport(lastScrapeStatus);
        });
    }

    // Check if scraping is already running
    checkInitialStatus();
});

function checkInitialStatus() {
    const jobId = localStorage.getItem('scrapeJobId');
    const statusUrl = jobId ? `/api/scrape-status?job_id=${encodeURIComponent(jobId)}` : '/api/scrape-status';
    fetch(statusUrl)
        .then(res => res.json())
        .then(status => {
            if (status.is_running) {
                const terminal = document.getElementById('terminal');
                const terminalContent = document.getElementById('terminalContent');
                terminal.classList.add('active');
                terminalContent.innerHTML = '<div class="terminal-line terminal-info">> Resuming active session monitoring...</div>';
                logToTerminal(`> Scraping task is already in progress.`, 'terminal-success');
                startPollingStatus();
                return;
            }

            if (status.total > 0 && !status.is_running) {
                lastScrapeStatus = status;
                enableReportButton();
            }
        })
        .catch(err => console.log('Error checking status:', err));
}

function handleScraperSubmit(e) {
    e.preventDefault();

    const rollNumbers = document.getElementById('rollNumbers').value.trim();
    const courseType = document.getElementById('courseType').value;
    const examYear = document.getElementById('examYear').value;
    const examType = document.getElementById('examType').value;

    if (!rollNumbers) {
        alert('Please enter at least one roll number');
        return;
    }

    localStorage.setItem('scrapeRollNumbers', rollNumbers);

    const submitBtn = document.getElementById('submitBtn');
    const terminal = document.getElementById('terminal');
    const terminalContent = document.getElementById('terminalContent');

    // Show terminal
    terminal.classList.add('active');
    submitBtn.classList.add('loading');

    // Clear previous output
    terminalContent.innerHTML = '<div class="terminal-line terminal-info">> Initializing scraper...</div>';
    logToTerminal('> Connecting to Python backend...', 'terminal-info');

    // Send request
    fetch('/api/scrape', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            rollNumbers: rollNumbers,
            courseType: courseType,
            examYear: examYear,
            examTypeVal: examType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (data.job_id) {
                localStorage.setItem('scrapeJobId', data.job_id);
            }
            logToTerminal(`> Roll Numbers: ${rollNumbers}`, 'terminal-info');
            logToTerminal(`> ${data.message}`, 'terminal-success');
            startPollingStatus();
        } else {
            logToTerminal(`> Error: ${data.message}`, 'terminal-warning');
        }
    })
    .catch(error => {
        logToTerminal(`> Error: Failed to connect to backend!`, 'terminal-warning');
        logToTerminal(`> Is app.py running?`, 'terminal-warning');
    })
    .finally(() => {
        submitBtn.classList.remove('loading');
    });
}

function startPollingStatus() {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true; // Prevent multiple requests
    
    let lastMessage = "";
    let reportDownloaded = false;
    
    const intervalId = setInterval(() => {
        const jobId = localStorage.getItem('scrapeJobId');
        const statusUrl = jobId ? `/api/scrape-status?job_id=${encodeURIComponent(jobId)}` : '/api/scrape-status';
        fetch(statusUrl)
            .then(res => res.json())
            .then(status => {
                if (status.message && status.message !== lastMessage) {
                    logToTerminal(`> ${status.message}`, 'terminal-info');
                    lastMessage = status.message;
                }
                
                if (!status.is_running && status.total > 0) {
                    clearInterval(intervalId);
                    submitBtn.disabled = false;
                    lastScrapeStatus = status;
                    enableReportButton();
                    logToTerminal(`> Done! Successfully processed ${status.success} out of ${status.total} students.`, 'terminal-success');
                    logToTerminal(`> Please check the '/results' page to view and visualize the newly added data.`, 'terminal-warning');
                    if (status.duplicate_rolls && status.duplicate_rolls.length > 0) {
                        logToTerminal(`> Duplicate roll numbers removed: ${status.duplicate_rolls.join(', ')}`, 'terminal-warning');
                    }
                    if (status.invalid_rolls && status.invalid_rolls.length > 0) {
                        logToTerminal(`> Invalid roll numbers removed: ${status.invalid_rolls.join(', ')}`, 'terminal-warning');
                    }
                    if (!reportDownloaded) {
                        reportDownloaded = true;
                        // Expected to not auto-download: downloadScrapeReport(status);
                    }
                }
            })
            .catch(err => {
                clearInterval(intervalId);
                submitBtn.disabled = false;
                logToTerminal(`> Status check failed or server disconnected.`, 'terminal-warning');
            });
    }, 2000); // Check every 2 seconds
}

function enableReportButton() {
    const downloadBtn = document.getElementById('downloadScrapeReportBtn');
    if (!downloadBtn) {
        return;
    }
    downloadBtn.disabled = false;
}

function downloadScrapeReport(status) {
    const rollNumbers = localStorage.getItem('scrapeRollNumbers') || status.roll_numbers_input || '';
    if (!rollNumbers) {
        logToTerminal('> PDF report skipped (roll numbers not available).', 'terminal-warning');
        return;
    }

    logToTerminal('> Generating scrape summary PDF...', 'terminal-info');

    fetch('/api/download-scrape-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            roll_numbers: rollNumbers,
            failed_rolls: status.failed_rolls || [],
            duplicate_rolls: status.duplicate_rolls || [],
            invalid_rolls: status.invalid_rolls || []
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to generate scrape report');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Scrape_Report_${new Date().toISOString().replace(/[:.]/g, '-')}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            logToTerminal('> Scrape report downloaded.', 'terminal-success');
        })
        .catch(error => {
            logToTerminal(`> Error generating scrape report: ${error.message}`, 'terminal-warning');
        });
}

function logToTerminal(message, className = 'terminal-info') {
    const terminalContent = document.getElementById('terminalContent');
    const line = document.createElement('div');
    line.className = `terminal-line ${className}`;
    line.textContent = message;
    terminalContent.appendChild(line);
    terminalContent.scrollTop = terminalContent.scrollHeight;
}
