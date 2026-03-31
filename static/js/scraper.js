/* ==================== SCRAPER PAGE ==================== */

document.addEventListener('DOMContentLoaded', function() {
    const scraperForm = document.getElementById('scraperForm');
    if (scraperForm) {
        scraperForm.addEventListener('submit', handleScraperSubmit);
    }
});

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
        } else {
            logToTerminal(`> Error: ${data.message}`, 'terminal-warning');
        }
        submitBtn.classList.remove('loading');
    })
    .catch(error => {
        logToTerminal(`> Error: Failed to connect to backend!`, 'terminal-warning');
        logToTerminal(`> Is app.py running?`, 'terminal-warning');
        submitBtn.classList.remove('loading');
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
