/* ==================== RESULTS PAGE ==================== */

let allData = [];
let filteredData = [];
let currentSort = { column: 0, ascending: true };
let currentPage = 1;
let rowsPerPage = 10;
let allDynamicSubjects = [];
let visibleDynamicSubjects = [];

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

// Clear Data functionality
window.clearData = function() {
    if (confirm("Are you sure you want to clear all data? This cannot be undone.")) {
        fetch('/api/clear-data', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                allData = [];
                filteredData = [];
                renderTable();
                alert(data.message);
            } else {
                alert('Error clearing data: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error clearing data:', error);
            alert('An error occurred while clearing data.');
        });
    }
};

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

    const ext = file.name.toLowerCase().split('.').pop();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
        showUploadStatus('Only CSV and Excel files (.xls/.xlsx) are allowed', 'error', uploadStatus);
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

    fetch('/api/results?_t=' + new Date().getTime())
        .then(response => response.json())
        .then(data => {
            allData = data.data || [];
            filteredData = [...allData];
            currentPage = 1;
            extractSubjectStatuses();
            extractDynamicSubjects();
            renderTableHeader();
            renderTable();
            if (loadingSpinner) loadingSpinner.style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading results:', error);
            if (loadingSpinner) loadingSpinner.style.display = 'none';
        });
}

/* ==================== SEARCH & FILTER ==================== */

let selectedSubjects = [];

function extractSubjectStatuses() {
    const subjectsSet = new Set();

    allData.forEach(row => {
        const subjectStatuses = getRowSubjectStatuses(row);
        subjectStatuses.forEach(label => subjectsSet.add(label));
    });

    const subjectsArray = Array.from(subjectsSet).sort((a, b) => a.localeCompare(b));
    renderSubjectFilter(subjectsArray);
}

function getRowSubjectStatuses(row) {
    const subjectStatuses = [];
    const raw = (row.Subject_Pass || '').trim();

    if (!raw || raw === '-' || raw.toLowerCase() === 'all pass') {
        return subjectStatuses;
    }

    if (!raw.includes(':')) {
        return subjectStatuses;
    }

    const parts = raw.split(',');
    parts.forEach(part => {
        const cleaned = part.trim();
        if (!cleaned) {
            return;
        }

        const pieces = cleaned.split(':');
        if (pieces.length < 2) {
            return;
        }

        const subject = (pieces[0] || '').trim();
        const statusRaw = (pieces[pieces.length - 1] || '').trim();
        if (!subject || !statusRaw) {
            return;
        }

        const status = statusRaw.toUpperCase();
        subjectStatuses.push(`${subject}:${status}`);
    });

    return subjectStatuses;
}

function renderSubjectFilter(subjects) {
    const dropdown = document.getElementById('subjectFilterDropdown');
    const filterBtn = document.getElementById('subjectFilterBtn');
    if (!dropdown || !filterBtn) return;

    // Toggle dropdown
    filterBtn.onclick = function() {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    };

    dropdown.innerHTML = '';
    
    if (subjects.length === 0) {
        dropdown.innerHTML = '<div style="padding: 5px; color: #888; font-size: 13px;">No failed subjects found</div>';
        return;
    }

    subjects.forEach(subject => {
        const label = document.createElement('label');
        label.style.display = 'block';
        label.style.padding = '5px';
        label.style.cursor = 'pointer';
        label.style.whiteSpace = 'nowrap';
        label.style.color = '#333';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = subject;
        checkbox.style.marginRight = '8px';
        
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                selectedSubjects.push(subject);
            } else {
                selectedSubjects = selectedSubjects.filter(s => s !== subject);
            }
            applyFilters();
        });

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(subject));
        dropdown.appendChild(label);
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (!filterBtn.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    });
}

function applyFilters() {
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    filteredData = allData.filter(row => {
        const rollNum = (row.Roll_Number || '').toLowerCase();
        const name = (row.Name || '').toLowerCase();
        const matchesSearch = rollNum.includes(searchTerm) || name.includes(searchTerm);
        
        let matchesSubject = true;
        if (selectedSubjects.length > 0) {
            const rowSubjectStatuses = getRowSubjectStatuses(row);
            matchesSubject = rowSubjectStatuses.some(label => selectedSubjects.includes(label));
        }

        return matchesSearch && matchesSubject;
    });

    currentPage = 1;
    renderTable();
}

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', () => {
        applyFilters();
    });
}

function extractDynamicSubjects() {
    const subjectsSet = new Set();
    allData.forEach(row => {
        let subjectsRaw = (row.Subject_Pass || '').trim();
        if (subjectsRaw && subjectsRaw !== '-' && subjectsRaw.toLowerCase() !== 'all pass' && subjectsRaw.includes(':')) {
            const subjects = subjectsRaw.split(',');
            subjects.forEach(s => {
                const parts = s.split(':');
                if (parts.length > 0) {
                    const subjName = parts[0].trim();
                    if (subjName) {
                        subjectsSet.add(subjName);
                    }
                }
            });
        }
    });
    allDynamicSubjects = Array.from(subjectsSet).sort();
    // Default the new filter to off (hide all dynamic columns initially)
    visibleDynamicSubjects = [];
    renderColumnVisibilityFilter();
}

function renderColumnVisibilityFilter() {
    const dropdown = document.getElementById('columnVisibilityDropdown');
    const toggleBtn = document.getElementById('columnVisibilityBtn');
    if (!dropdown || !toggleBtn) return;

    toggleBtn.onclick = function() {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        document.getElementById('subjectFilterDropdown').style.display = 'none'; // Close other dropdown
    };

    dropdown.innerHTML = '';
    
    if (allDynamicSubjects.length === 0) {
        dropdown.innerHTML = '<div style="padding: 5px; color: #888; font-size: 13px;">No subjects available</div>';
        return;
    }

    allDynamicSubjects.forEach(subject => {
        const label = document.createElement('label');
        label.style.display = 'block';
        label.style.padding = '5px';
        label.style.cursor = 'pointer';
        label.style.whiteSpace = 'nowrap';
        label.style.color = '#333';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = subject;
        checkbox.style.marginRight = '8px';
        checkbox.checked = visibleDynamicSubjects.includes(subject);
        
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                if (!visibleDynamicSubjects.includes(subject)) {
                    visibleDynamicSubjects.push(subject);
                }
            } else {
                visibleDynamicSubjects = visibleDynamicSubjects.filter(s => s !== subject);
            }
            renderTableHeader();
            renderTable();
        });

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(subject));
        dropdown.appendChild(label);
    });
    
    // Close dropdown when clicking outside is already handled via document click? Wait, need to add document click handler for this one too.
    document.addEventListener('click', function(event) {
        if (!toggleBtn.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    });
}

/* ==================== SORT ==================== */

let dynamicSortStartIdx = 6; // Because we have 6 fixed columns (S.No., Roll Number, Name, Father Name, Marks, Status, Subject Pass)

function renderTableHeader() {
    const tableHeader = document.getElementById('tableHeader');
    if (!tableHeader) return;

    let html = `
        <tr>
            <th>S.No.</th>
            <th onclick="sortTable(0)">Roll Number <span class="sort-icon">⬍</span></th>
            <th onclick="sortTable(1)">Name <span class="sort-icon">⬍</span></th>
            <th onclick="sortTable(2)">Father Name <span class="sort-icon">⬍</span></th>
            <th onclick="sortTable(3)">Marks <span class="sort-icon">⬍</span></th>
            <th onclick="sortTable(4)">Status <span class="sort-icon">⬍</span></th>
            <th onclick="sortTable(5)">Subject Pass <span class="sort-icon">⬍</span></th>`;
            
    // Add dynamic subject headers
    visibleDynamicSubjects.forEach((subject, idx) => {
        html += `<th onclick="sortDynamicTable('${subject}', ${dynamicSortStartIdx + idx})">${subject} <span class="sort-icon">⬍</span></th>`;
    });

    html += `</tr>`;
    tableHeader.innerHTML = html;
}

function getSubjectMark(row, subjectName) {
    const displaySubjectPass = row.Subject_Pass || '-';
    if (displaySubjectPass && displaySubjectPass !== '-' && displaySubjectPass !== 'All Pass' && displaySubjectPass.includes(':')) {
        const subjects = displaySubjectPass.split(',');
        for (let s of subjects) {
            const parts = s.split(':');
            if (parts.length >= 2 && parts[0].trim() === subjectName) {
                return parseFloat(parts[1].trim()) || 0;
            }
        }
    }
    return 0; // Default if not found
}

function sortDynamicTable(subjectName, columnIndex) {
    if (currentSort.column === columnIndex) {
        currentSort.ascending = !currentSort.ascending;
    } else {
        currentSort.column = columnIndex;
        currentSort.ascending = true;
    }

    filteredData.sort((a, b) => {
        let aVal = getSubjectMark(a, subjectName);
        let bVal = getSubjectMark(b, subjectName);

        if (aVal < bVal) return currentSort.ascending ? -1 : 1;
        if (aVal > bVal) return currentSort.ascending ? 1 : -1;
        return 0;
    });

    currentPage = 1;
    renderTable();
}

function sortTable(columnIndex) {
    const headers = ['Roll_Number', 'Name', 'Father_Name', 'Total_Marks', 'Status', 'Subject_Pass'];
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
        const dropColSpan = 7 + visibleDynamicSubjects.length;
        tableBody.innerHTML = `<tr><td colspan="${dropColSpan}" class="no-data">No results found. Try a different search or upload a CSV file.</td></tr>`;
        renderPagination();
        return;
    }

    const startIdx = (currentPage - 1) * rowsPerPage;
    const endIdx = startIdx + rowsPerPage;
    const pageData = filteredData.slice(startIdx, endIdx);

    tableBody.innerHTML = pageData.map((row, index) => {
        const serialNumber = startIdx + index + 1;
        let displaySubjectPass = row.Subject_Pass || '-';
        if (displaySubjectPass && displaySubjectPass !== '-' && displaySubjectPass !== 'All Pass' && displaySubjectPass.includes(':')) {
            const failedSubjects = [];
            const subjects = displaySubjectPass.split(',');
            subjects.forEach(s => {
                const parts = s.split(':');
                if (parts.length >= 3) {
                    const status = parts[2].trim().toUpperCase();
                    if (status.includes('FAIL') || status.includes('LESS THAN')) {
                        failedSubjects.push(parts[0].trim());
                    }
                } else if (parts.length >= 2) {
                    const status = parts[1].trim().toUpperCase();
                    if (status.includes('FAIL') || status.includes('LESS THAN')) {
                        failedSubjects.push(parts[0].trim());
                    }
                }
            });
            if (failedSubjects.length > 0) {
                displaySubjectPass = failedSubjects.join(', ');
            } else {
                displaySubjectPass = 'Pass all Subject';
            }
        }
        
        let rowHtml = `
        <tr>
            <td>${serialNumber}</td>
            <td>${row.Roll_Number || '-'}</td>
            <td>${row.Name || '-'}</td>
            <td>${row.Father_Name || '-'}</td>
            <td><strong>${row.Total_Marks || '-'}</strong></td>
            <td><div class="status-badge ${row.Status === 'PASS' ? 'success' : 'danger'}">${row.Status || '-'}</div></td>
            <td>${displaySubjectPass}</td>`;

        visibleDynamicSubjects.forEach(subject => {
            let mark = '-';
            if (row.Subject_Pass && row.Subject_Pass !== '-' && row.Subject_Pass !== 'All Pass' && row.Subject_Pass.includes(':')) {
                const subjects = row.Subject_Pass.split(',');
                for (let s of subjects) {
                    const parts = s.split(':');
                    if (parts.length >= 2 && parts[0].trim() === subject) {
                        mark = parts[1].trim();
                        break;
                    }
                }
            }
            rowHtml += `<td>${mark}</td>`;
        });

        rowHtml += `</tr>`;
        return rowHtml;
    }).join('');

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

        const baseHeaders = ['S.No.', 'Roll_Number', 'Name', 'Father_Name', 'Total_Marks', 'Status', 'Subject_Pass'];
        const headers = [...baseHeaders, ...visibleDynamicSubjects];
        let csv = headers.join(',') + '\n';

        filteredData.forEach((row, index) => {
            const rowData = [
                index + 1,
                row.Roll_Number || '',
                row.Name || '',
                row.Father_Name || '',
                row.Total_Marks || '',
                row.Status || '',
                row.Subject_Pass || ''
            ];

            visibleDynamicSubjects.forEach(subject => {
                let mark = '';
                if (row.Subject_Pass && row.Subject_Pass !== '-' && row.Subject_Pass !== 'All Pass' && row.Subject_Pass.includes(':')) {
                    const subjects = row.Subject_Pass.split(',');
                    for (let s of subjects) {
                        const parts = s.split(':');
                        if (parts.length >= 2 && parts[0].trim() === subject) {
                            mark = parts[1].trim();
                            break;
                        }
                    }
                }
                rowData.push(mark);
            });
            
            csv += rowData.map(val => {
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

