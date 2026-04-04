/* ==================== SCRAPER PAGE ==================== */

document.addEventListener('DOMContentLoaded', function() {
    const scraperForm = document.getElementById('scraperForm');
    if (scraperForm) {
        scraperForm.addEventListener('submit', handleScraperSubmit);
        // Check if scraping is already running
        checkInitialStatus();
    }
});

function checkInitialStatus() {
    fetch('/api/scrape-status')
        .then(res => res.json())
        .then(status => {
            if (status.is_running) {
                const terminal = document.getElementById('terminal');
                const terminalContent = document.getElementById('terminalContent');
                terminal.classList.add('active');
                terminalContent.innerHTML = '<div class="terminal-line terminal-info">> Resuming active session monitoring...</div>';
                logToTerminal(`> Scraping task is already in progress.`, 'terminal-success');
                startPollingStatus();
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
    
    const intervalId = setInterval(() => {
        fetch('/api/scrape-status')
            .then(res => res.json())
            .then(status => {
                if (status.message && status.message !== lastMessage) {
                    logToTerminal(`> ${status.message}`, 'terminal-info');
                    lastMessage = status.message;
                }
                
                if (!status.is_running && status.total > 0) {
                    clearInterval(intervalId);
                    submitBtn.disabled = false;
                    logToTerminal(`> Done! Successfully processed ${status.success} out of ${status.total} students.`, 'terminal-success');
                    logToTerminal(`> Please check the '/results' page to view and visualize the newly added data.`, 'terminal-warning');
                }
            })
            .catch(err => {
                clearInterval(intervalId);
                submitBtn.disabled = false;
                logToTerminal(`> Status check failed or server disconnected.`, 'terminal-warning');
            });
    }, 2000); // Check every 2 seconds
}

function logToTerminal(message, className = 'terminal-info') {
    const terminalContent = document.getElementById('terminalContent');
    const line = document.createElement('div');
    line.className = `terminal-line ${className}`;
    line.textContent = message;
    terminalContent.appendChild(line);
    terminalContent.scrollTop = terminalContent.scrollHeight;
}
