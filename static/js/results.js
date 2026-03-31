/* ==================== RESULTS PAGE ==================== */

let allData = [];
let filteredData = [];
let currentSort = { column: 0, ascending: true };
let currentPage = 1;
let rowsPerPage = 10;

document.addEventListener('DOMContentLoaded', function() {
    initializeResultsPage();
});

function initializeResultsPage() {
    setupFileUpload();
    setupSearch();
    setupRowsPerPage();
    setupExport();
    loadResults();
}

/* ==================== FILE UPLOAD ==================== */

function setupFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    if (!uploadArea) return;

    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFileUpload(e.dataTransfer.files[0], uploadStatus);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0], uploadStatus);
        }
    });
}

function handleFileUpload(file, uploadStatus) {
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
        showUploadStatus('Only CSV files are allowed', 'error', uploadStatus);
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showUploadStatus('Uploading...', 'loading', uploadStatus);

    fetch('/api/upload-csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showUploadStatus(`✅ ${data.message}`, 'success', uploadStatus);
            loadResults();
        } else {
            showUploadStatus(`❌ ${data.message}`, 'error', uploadStatus);
        }
    })
    .catch(error => {
        showUploadStatus(`❌ Upload failed: ${error.message}`, 'error', uploadStatus);
    });
}

function showUploadStatus(message, type, uploadStatus) {
    uploadStatus.textContent = message;
    uploadStatus.className = type;
    uploadStatus.style.display = 'block';

    if (type !== 'loading') {
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    }
}

/* ==================== LOAD RESULTS ==================== */

function loadResults() {
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) loadingSpinner.style.display = 'flex';

    fetch('/api/results')
        .then(response => response.json())
        .then(data => {
            allData = data.data || [];
            filteredData = [...allData];
            currentPage = 1;
            renderTable();
            if (loadingSpinner) loadingSpinner.style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading results:', error);
            if (loadingSpinner) loadingSpinner.style.display = 'none';
        });
}

/* ==================== SEARCH ==================== */

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        
        filteredData = allData.filter(row => {
            const rollNum = (row.Roll_Number || '').toLowerCase();
            const name = (row.Name || '').toLowerCase();
            return rollNum.includes(searchTerm) || name.includes(searchTerm);
        });

        currentPage = 1;
        renderTable();
    });
}

/* ==================== SORT ==================== */

function sortTable(columnIndex) {
    const headers = ['Roll_Number', 'Name', 'Father_Name', 'Total_Marks'];
    const columnName = headers[columnIndex];

    if (currentSort.column === columnIndex) {
        currentSort.ascending = !currentSort.ascending;
    } else {
        currentSort.column = columnIndex;
        currentSort.ascending = true;
    }

    filteredData.sort((a, b) => {
        let aVal = a[columnName] || '';
        let bVal = b[columnName] || '';

        // Try numeric comparison
        if (!isNaN(aVal) && !isNaN(bVal)) {
            aVal = parseFloat(aVal);
            bVal = parseFloat(bVal);
        } else {
            aVal = String(aVal).toLowerCase();
            bVal = String(bVal).toLowerCase();
        }

        if (aVal < bVal) return currentSort.ascending ? -1 : 1;
        if (aVal > bVal) return currentSort.ascending ? 1 : -1;
        return 0;
    });

    currentPage = 1;
    renderTable();
}

/* ==================== PAGINATION ==================== */

function setupRowsPerPage() {
    const select = document.getElementById('rowsPerPage');
    if (!select) return;

    select.addEventListener('change', (e) => {
        rowsPerPage = parseInt(e.target.value);
        currentPage = 1;
        renderTable();
    });
}

function renderPagination() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    pagination.innerHTML = '';

    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    if (totalPages <= 1) return;

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '← Previous';
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
        }
    });
    pagination.appendChild(prevBtn);

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const btn = document.createElement('button');
        btn.textContent = '1';
        btn.addEventListener('click', () => {
            currentPage = 1;
            renderTable();
        });
        pagination.appendChild(btn);

        if (startPage > 2) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.style.padding = '0.5rem 0.25rem';
            pagination.appendChild(dots);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        if (i === currentPage) btn.classList.add('active');
        btn.addEventListener('click', () => {
            currentPage = i;
            renderTable();
        });
        pagination.appendChild(btn);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.style.padding = '0.5rem 0.25rem';
            pagination.appendChild(dots);
        }

        const btn = document.createElement('button');
        btn.textContent = totalPages;
        btn.addEventListener('click', () => {
            currentPage = totalPages;
            renderTable();
        });
        pagination.appendChild(btn);
    }

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next →';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderTable();
        }
    });
    pagination.appendChild(nextBtn);
}

/* ==================== RENDER TABLE ==================== */

function renderTable() {
    const tableBody = document.getElementById('tableBody');
    if (!tableBody) return;

    if (filteredData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="no-data">No results found. Try a different search or upload a CSV file.</td></tr>';
        renderPagination();
        return;
    }

    const startIdx = (currentPage - 1) * rowsPerPage;
    const endIdx = startIdx + rowsPerPage;
    const pageData = filteredData.slice(startIdx, endIdx);

    tableBody.innerHTML = pageData.map(row => `
        <tr>
            <td>${row.Roll_Number || '-'}</td>
            <td>${row.Name || '-'}</td>
            <td>${row.Father_Name || '-'}</td>
            <td>${row.Total_Marks || '-'}</td>
        </tr>
    `).join('');

    renderPagination();
}

/* ==================== EXPORT ==================== */

function setupExport() {
    const exportBtn = document.getElementById('exportBtn');
    if (!exportBtn) return;

    exportBtn.addEventListener('click', () => {
        if (filteredData.length === 0) {
            alert('No data to export');
            return;
        }

        const headers = ['Roll_Number', 'Name', 'Father_Name', 'Total_Marks'];
        let csv = headers.join(',') + '\n';

        filteredData.forEach(row => {
            csv += headers.map(h => {
                let val = row[h] || '';
                // Escape quotes and wrap in quotes if contains comma
                if (typeof val === 'string' && val.includes(',')) {
                    val = `"${val.replace(/"/g, '""')}"`;
                }
                return val;
            }).join(',') + '\n';
        });

        // Create blob and download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Student_Results_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    });
}
