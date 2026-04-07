// API Base URL (proxied through nginx)
const API_BASE = '/api';

// DOM Elements
const jobForm = document.getElementById('jobForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');
const statusSection = document.getElementById('statusSection');
const jobIdDisplay = document.getElementById('jobIdDisplay');
const statusBadge = document.getElementById('statusBadge');
const progressMessage = document.getElementById('progressMessage');
const resultsSection = document.getElementById('resultsSection');
const resultsSummary = document.getElementById('resultsSummary');
const rawResults = document.getElementById('rawResults');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');

// Polling state
let pollingInterval = null;

// Form submission handler
jobForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Reset UI
    hideAllSections();
    setLoading(true);
    
    // Get form data
    const inputData = document.getElementById('inputData').value;
    const numChunks = parseInt(document.getElementById('numChunks').value, 10);
    
    try {
        // Submit job to API
        const response = await fetch(`${API_BASE}/jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input_data: inputData,
                num_chunks: numChunks,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to submit job');
        }
        
        const data = await response.json();
        
        // Show status section and start polling
        showStatusSection(data.job_id);
        startPolling(data.job_id);
        
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});

// Start polling for job status
function startPolling(jobId) {
    // Clear any existing polling
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Poll immediately, then every 1 second
    pollJobStatus(jobId);
    pollingInterval = setInterval(() => pollJobStatus(jobId), 1000);
}

// Poll job status from API
async function pollJobStatus(jobId) {
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch job status');
        }
        
        const data = await response.json();
        updateStatusUI(data);
        
        // Stop polling if job is complete or failed
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
            clearInterval(pollingInterval);
            pollingInterval = null;
            
            if (data.status === 'SUCCESS') {
                showResults(data.result);
            } else if (data.status === 'FAILURE') {
                showError(data.error || 'Job failed');
            }
        }
        
    } catch (error) {
        console.error('Polling error:', error);
        // Don't stop polling on transient errors
    }
}

// Update status UI
function updateStatusUI(data) {
    statusBadge.textContent = data.status;
    statusBadge.className = 'badge ' + data.status.toLowerCase();
    
    if (data.progress) {
        progressMessage.textContent = data.progress;
    }
}

// Show status section
function showStatusSection(jobId) {
    statusSection.style.display = 'block';
    jobIdDisplay.textContent = jobId;
    statusBadge.textContent = 'PENDING';
    statusBadge.className = 'badge pending';
    progressMessage.textContent = 'Job submitted, waiting for worker...';
}

// Show results
function showResults(result) {
    resultsSection.style.display = 'block';
    
    // Build summary cards
    resultsSummary.innerHTML = `
        <div class="result-item">
            <span class="value">${result.total_chunks}</span>
            <span class="label">Chunks Processed</span>
        </div>
        <div class="result-item">
            <span class="value">${result.total_chars_processed}</span>
            <span class="label">Characters Processed</span>
        </div>
        <div class="result-item">
            <span class="value">${result.total_processing_time}s</span>
            <span class="label">Total Processing Time</span>
        </div>
    `;
    
    // Show raw JSON
    rawResults.textContent = JSON.stringify(result, null, 2);
}

// Show error
function showError(message) {
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
}

// Hide all result sections
function hideAllSections() {
    statusSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    progressMessage.textContent = '';
}

// Set loading state
function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    btnText.style.display = isLoading ? 'none' : 'inline';
    btnLoading.style.display = isLoading ? 'inline' : 'none';
}
