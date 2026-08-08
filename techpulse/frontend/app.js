// Config
const API_BASE = 'http://127.0.0.1:8001/api';

// State Variables
let isPolling = false;
let activeCallSid = null;
let pollInterval = null;

// DOM Elements
const agentStatusDot = document.getElementById('agent-status-dot');
const agentStatusText = document.getElementById('agent-status-text');
const voiceAgentText = document.getElementById('voice-agent-text');
const connectionBadge = document.getElementById('connection-badge');
const targetPhoneInput = document.getElementById('target-phone');
const startCallBtn = document.getElementById('start-call-btn');
const testCallBtn = document.getElementById('test-call-btn');
const callBtnSpinner = document.getElementById('call-btn-spinner');
const errorMsg = document.getElementById('error-message');
const successMsg = document.getElementById('success-message');

const progressBar = document.getElementById('active-call-progress');
const stepConnecting = document.getElementById('step-connecting');
const stepCalling = document.getElementById('step-calling');
const stepConnected = document.getElementById('step-connected');
const stepCompleted = document.getElementById('step-completed');
const activeCallDetails = document.getElementById('active-call-details');
const activeCallSidText = document.getElementById('active-call-sid');
const activeCallDurationText = document.getElementById('active-call-duration');

const newsList = document.getElementById('news-list');
const activityTbody = document.getElementById('activity-tbody');

// Helper: Show/Hide Message Boxes
function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.style.display = 'block';
    successMsg.style.display = 'none';
}

function showSuccess(msg) {
    successMsg.textContent = msg;
    successMsg.style.display = 'block';
    errorMsg.style.display = 'none';
}

function clearMessages() {
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
}

// Format date nicely
function formatDate(isoString) {
    if (!isoString) return '-';
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + date.toLocaleDateString();
    } catch (e) {
        return isoString;
    }
}

// 1. Fetch Configuration Status
async function checkConfigStatus() {
    try {
        const res = await fetch(`${API_BASE}/config/status`);
        if (!res.ok) throw new Error('API server status check failed.');
        const status = await res.json();
        
        const isLive = status.elevenlabs_configured && status.twilio_configured;
        
        // Update connection badges
        connectionBadge.className = 'status-badge'; // reset
        if (isLive) {
            connectionBadge.classList.add('live-mode');
            connectionBadge.textContent = 'Live Integration';
            agentStatusText.textContent = 'Ready (Live)';
            agentStatusDot.className = 'status-dot status-ready';
        } else {
            connectionBadge.classList.add('mock-mode');
            connectionBadge.textContent = 'Simulated Mode';
            agentStatusText.textContent = 'Ready (Mock Fallback)';
            agentStatusDot.className = 'status-dot status-warning';
        }
        
        // Pre-fill target phone input if configured
        if (status.details.TARGET_PHONE_NUMBER === 'Configured') {
            // Note: Since we don't expose actual value, we ask the backend config status or use default.
            // In a real app we might fetch it or just keep input empty. We'll check if target_phone_configured
            if (status.target_phone_configured) {
                // Fetch status from API doesn't return value for security, but we will handle this.
            }
        }
        
        // Enable Controls
        startCallBtn.removeAttribute('disabled');
        if (status.target_phone_configured) {
            testCallBtn.removeAttribute('disabled');
        } else {
            testCallBtn.setAttribute('title', 'Configure TARGET_PHONE_NUMBER in .env to run quick test');
        }
        
    } catch (err) {
        console.error('Error fetching config status:', err);
        agentStatusText.textContent = 'Server Offline';
        agentStatusDot.className = 'status-dot status-error';
        connectionBadge.className = 'status-badge';
        connectionBadge.textContent = 'Disconnected';
        showError('Cannot connect to FastAPI backend server. Please verify it is running on http://127.0.0.1:8000.');
    }
}

// 2. Fetch News Topics
async function fetchNews() {
    if (!newsList) return;
    try {
        const res = await fetch(`${API_BASE}/news`);
        if (!res.ok) throw new Error('Failed to fetch news.');
        const news = await res.json();
        
        newsList.innerHTML = '';
        
        for (const [key, details] of Object.entries(news)) {
            const categoryLabel = key === 'ai' ? 'Artificial Intelligence' : key.toUpperCase();
            
            const card = document.createElement('div');
            card.className = 'news-card';
            card.innerHTML = `
                <div class="news-card-header">
                    <span class="news-card-title">${details.topic}</span>
                    <span class="news-category-badge">${categoryLabel}</span>
                </div>
                <div class="news-card-body">${details.what_happened}</div>
                <div class="news-card-impact"><strong>Impact:</strong> ${details.why_it_matters}</div>
            `;
            newsList.appendChild(card);
        }
    } catch (err) {
        console.error('Error loading news:', err);
        newsList.innerHTML = '<div class="loading-placeholder">Failed to load news topics.</div>';
    }
}

// 3. Fetch Recent Calls
async function fetchCalls() {
    try {
        const res = await fetch(`${API_BASE}/calls`);
        if (!res.ok) throw new Error('Failed to fetch calls.');
        const calls = await res.json();
        
        activityTbody.innerHTML = '';
        
        if (calls.length === 0) {
            activityTbody.innerHTML = `
                <tr>
                    <td colspan="5" class="table-loading">No calls recorded yet.</td>
                </tr>
            `;
            return;
        }
        
        calls.forEach(call => {
            const tr = document.createElement('tr');
            
            // Format status badge
            let statusClass = '';
            if (call.status === 'completed') statusClass = 'status-ready';
            else if (call.status === 'in-progress' || call.status === 'ringing') statusClass = 'status-warning';
            else if (call.status === 'failed' || call.status === 'busy' || call.status === 'no-answer') statusClass = 'status-error';
            
            const statusBadgeMarkup = statusClass 
                ? `<span class="status-dot ${statusClass}"></span> ${call.status}` 
                : call.status;

            tr.innerHTML = `
                <td>${formatDate(call.date_created)}</td>
                <td><code>${call.to}</code></td>
                <td>${statusBadgeMarkup}</td>
                <td>${call.duration}s</td>
                <td><span class="status-badge ${call.is_mock ? 'mock-mode' : 'live-mode'}">${call.is_mock ? 'Mock' : 'Live'}</span></td>
            `;
            activityTbody.appendChild(tr);
        });
        
        // If we are tracking an active call, update the UI tracker from this list
        if (activeCallSid) {
            const activeCall = calls.find(c => c.sid === activeCallSid);
            if (activeCall) {
                updateCallProgressTracker(activeCall);
            }
        }
    } catch (err) {
        console.error('Error loading call history:', err);
    }
}

// 4. Update Call Progress Tracker UI
function updateCallProgressTracker(call) {
    activeCallSidText.textContent = call.sid;
    activeCallDurationText.textContent = `${call.duration}s`;
    activeCallDetails.style.display = 'block';
    
    // Clear all steps classes first
    const steps = [stepConnecting, stepCalling, stepConnected, stepCompleted];
    steps.forEach(step => {
        step.classList.remove('active', 'completed-step');
    });
    
    const status = call.status.toLowerCase();
    
    if (status === 'queued') {
        progressBar.style.width = '12.5%';
        stepConnecting.classList.add('active');
    } else if (status === 'ringing') {
        progressBar.style.width = '37.5%';
        stepConnecting.classList.add('completed-step');
        stepCalling.classList.add('active');
    } else if (status === 'in-progress') {
        progressBar.style.width = '62.5%';
        stepConnecting.classList.add('completed-step');
        stepCalling.classList.add('completed-step');
        stepConnected.classList.add('active');
    } else if (status === 'completed') {
        progressBar.style.width = '100%';
        stepConnecting.classList.add('completed-step');
        stepCalling.classList.add('completed-step');
        stepConnected.classList.add('completed-step');
        stepCompleted.classList.add('active');
        stopPollingCall();
    } else if (['failed', 'busy', 'no-answer', 'canceled'].includes(status)) {
        progressBar.style.width = '100%';
        progressBar.style.backgroundColor = 'var(--color-error)';
        
        // Mark current steps as failed
        showError(`Call ended with status: ${call.status.toUpperCase()}`);
        stopPollingCall();
    }
}

// Polling controls
function startPollingCall(callSid) {
    activeCallSid = callSid;
    isPolling = true;
    
    // Reset progress bar colors
    progressBar.style.backgroundColor = 'var(--color-accent)';
    
    // Quick initial update
    fetchCalls();
    
    // Start interval
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(fetchCalls, 1500);
}

function stopPollingCall() {
    isPolling = false;
    activeCallSid = null;
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    // Final table refresh
    setTimeout(fetchCalls, 1000);
}

// 5. Trigger Call
async function triggerCall(phoneNumber = null) {
    clearMessages();
    startCallBtn.disabled = true;
    testCallBtn.disabled = true;
    callBtnSpinner.style.display = 'inline-block';
    
    try {
        let endpoint = `${API_BASE}/call`;
        let payload = {};
        
        if (phoneNumber) {
            // Outbound Call targeting custom number
            payload = { phone_number: phoneNumber };
        } else {
            // Outbound Call targeting default system number
            endpoint = `${API_BASE}/call/test`;
        }
        
        const options = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        };
        if (phoneNumber) options.body = JSON.stringify(payload);
        
        const res = await fetch(endpoint, options);
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Failed to trigger outbound call.');
        }
        
        showSuccess(data.message);
        
        // Track the initiated call
        if (data.call && data.call.sid) {
            startPollingCall(data.call.sid);
        }
    } catch (err) {
        console.error('Call triggering failed:', err);
        showError(err.message);
        callBtnSpinner.style.display = 'none';
        startCallBtn.disabled = false;
        testCallBtn.disabled = false;
    } finally {
        callBtnSpinner.style.display = 'none';
        startCallBtn.disabled = false;
        testCallBtn.disabled = false;
    }
}

// Event Listeners
startCallBtn.addEventListener('click', () => {
    const rawNumber = targetPhoneInput.value.trim();
    if (!rawNumber) {
        showError('Please enter a target phone number.');
        return;
    }
    // Basic formatting clean up (ensure it starts with +)
    let phoneNum = rawNumber;
    if (!phoneNum.startsWith('+')) {
        phoneNum = '+' + phoneNum;
    }
    triggerCall(phoneNum);
});

testCallBtn.addEventListener('click', () => {
    triggerCall(null);
});

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    checkConfigStatus();
    fetchNews();
    fetchCalls();
    
    // Auto-refresh logs and configuration status every 10 seconds
    setInterval(() => {
        if (!isPolling) {
            fetchCalls();
            checkConfigStatus();
        }
    }, 10000);
});
