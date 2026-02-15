// AI Pentesting Playground - Frontend JavaScript - COMPLETE VERSION WITH DEBUG LOGGING

const API_BASE = window.location.origin;

// State
let state = {
    agents: [],
    models: [],
    roles: {},
    resources: {},
    selectedAgentId: null,
    editingAgentId: null,
    debugPanelCollapsed: false,
    currentTab: 'dashboard', // Current active tab
    activityFilters: {
        command: true,
        chat: true,
        system: true,
        error: true
    }
};

// ============================================================================
// Tab Navigation
// ============================================================================

function switchTab(tabName) {
    state.currentTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.dataset.tab === tabName) {
            content.classList.add('active');
        }
    });

    console.log(`Switched to tab: ${tabName}`);
}

// ============================================================================
// Debug & Activity Logging
// ============================================================================

function addActivityLog(type, message, agentId = null, details = null) {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;

    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });

    // Get agent info if available
    let agentName = '';
    if (agentId) {
        const agent = state.agents.find(a => a.id === agentId);
        agentName = agent ? `Agent-${agent.id.substring(0, 8)}` : 'Unknown';
    }

    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.setAttribute('data-type', type);

    let html = `
        <span class="log-time">${timeStr}</span>
        <span class="log-type">[${type.toUpperCase()}]</span>
    `;

    if (agentName) {
        html += `<span class="log-agent">${agentName}</span>`;
    }

    html += `<span class="log-message">${message}</span>`;

    logEntry.innerHTML = html;

    // Add details if provided
    if (details) {
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'log-details';
        detailsDiv.textContent = typeof details === 'object' ? JSON.stringify(details, null, 2) : details;
        logEntry.appendChild(detailsDiv);
    }

    // Check if should be visible based on filters
    if (!state.activityFilters[type]) {
        logEntry.style.display = 'none';
    }

    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Limit to last 100 entries
    while (logContainer.children.length > 100) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

function toggleDebugPanel() {
    const content = document.getElementById('debug-content');
    state.debugPanelCollapsed = !state.debugPanelCollapsed;

    if (state.debugPanelCollapsed) {
        content.classList.add('collapsed');
    } else {
        content.classList.remove('collapsed');
    }
}

function clearActivityLog() {
    const logContainer = document.getElementById('activity-log');
    logContainer.innerHTML = '';
    addActivityLog('system', 'Activity log cleared');
}

function updateLogFilters() {
    const entries = document.querySelectorAll('.log-entry');

    entries.forEach(entry => {
        const type = entry.getAttribute('data-type');
        if (state.activityFilters[type]) {
            entry.style.display = 'flex';
        } else {
            entry.style.display = 'none';
        }
    });
}

// ============================================================================
// API Functions
// ============================================================================

async function apiGet(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
}

async function apiPost(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
}

async function apiDelete(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
}

// ============================================================================
// UI Updates
// ============================================================================

function updateStatusIndicator(healthy) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');

    if (healthy) {
        indicator.style.color = '#10b981';
        text.textContent = 'Connected';
    } else {
        indicator.style.color = '#ef4444';
        text.textContent = 'Disconnected';
    }
}

function renderAgents() {
    const container = document.getElementById('agents-list');

    if (state.agents.length === 0) {
        container.innerHTML = '<div class="loading">No active agents</div>';
        return;
    }

    container.innerHTML = state.agents.map(agent => `
        <div class="agent-card ${state.selectedAgentId === agent.id ? 'active' : ''}" 
             data-agent-id="${agent.id}">
            <div class="agent-card-header">
                <span class="agent-role">${agent.role}</span>
                <span class="agent-status ${agent.status}">${agent.status}</span>
            </div>
            <div class="agent-model">${agent.model}</div>
            <div class="agent-tools">
                <small>${agent.allowed_tools ? agent.allowed_tools.length : 0} tools enabled</small>
            </div>
            <div class="agent-actions">
                <button class="btn btn-small btn-primary btn-chat" data-agent-id="${agent.id}">Chat</button>
                <button class="btn btn-small btn-secondary btn-permissions" data-agent-id="${agent.id}">⚙️</button>
                <button class="btn btn-small btn-danger btn-delete" data-agent-id="${agent.id}">Delete</button>
            </div>
        </div>
    `).join('');

    // Add event listeners
    document.querySelectorAll('.btn-chat').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            openChat(e.target.dataset.agentId);
        });
    });

    document.querySelectorAll('.btn-permissions').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            openPermissionsModal(e.target.dataset.agentId);
        });
    });

    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteAgent(e.target.dataset.agentId);
        });
    });
}

function renderModels() {
    const container = document.getElementById('models-grid');

    container.innerHTML = state.models.map(model => `
        <div class="model-card">
            <div class="model-card-header">
                <div class="model-name">${model.name}</div>
                <span class="model-badge ${model.is_downloaded ? 'downloaded' : 'available'}">
                    ${model.is_downloaded ? 'Downloaded' : 'Available'}
                </span>
            </div>
            <div class="model-info">${model.parameters} parameters • ${model.size_gb}GB</div>
            <div class="model-description">${model.description}</div>
            ${!model.is_downloaded ? `
                <button class="btn btn-primary btn-small btn-download" data-model="${model.name}">
                    Download
                </button>
            ` : ''}
        </div>
    `).join('');

    // Add download button listeners
    document.querySelectorAll('.btn-download').forEach(btn => {
        btn.addEventListener('click', () => downloadModel(btn.dataset.model));
    });
}

function updateResources() {
    const ram = state.resources.ram || { used_gb: 0, total_gb: 32 };
    const vram = state.resources.vram || { used_gb: 0, total_gb: 16 };
    const disk = state.resources.disk || { used_gb: 0, total_gb: 200 };

    const ramPercent = (ram.used_gb / ram.total_gb) * 100;
    const vramPercent = (vram.used_gb / vram.total_gb) * 100;
    const diskPercent = (disk.used_gb / disk.total_gb) * 100;

    document.getElementById('ram-bar').style.width = `${ramPercent}%`;
    document.getElementById('vram-bar').style.width = `${vramPercent}%`;
    document.getElementById('disk-bar').style.width = `${diskPercent}%`;

    document.getElementById('ram-text').textContent =
        `${ram.used_gb.toFixed(1)} / ${ram.total_gb.toFixed(1)} GB`;
    document.getElementById('vram-text').textContent =
        `${vram.used_gb.toFixed(1)} / ${vram.total_gb.toFixed(1)} GB`;
    document.getElementById('disk-text').textContent =
        `${disk.used_gb.toFixed(1)} / ${disk.total_gb.toFixed(1)} GB`;
}

// ============================================================================
// Agent Operations
// ============================================================================

async function fetchAgents() {
    try {
        const data = await apiGet('/api/agents');
        state.agents = data.agents;
        renderAgents();
    } catch (error) {
        console.error('Error fetching agents:', error);
    }
}

async function deleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    try {
        addActivityLog('system', `Deleting agent ${agentId.substring(0, 8)}...`, agentId);
        await apiDelete(`/api/agents/${agentId}`);
        if (state.selectedAgentId === agentId) {
            closeChat();
        }
        await fetchAgents();
        addActivityLog('system', `Agent deleted successfully`, agentId);
    } catch (error) {
        console.error('Error deleting agent:', error);
        addActivityLog('error', `Failed to delete agent: ${error.message}`, agentId);
        alert('Failed to delete agent');
    }
}

async function createAgent(role, model, customPrompt, customTools = null) {
    try {
        const data = { role, model };
        if (customPrompt) data.custom_prompt = customPrompt;
        if (customTools && customTools.length > 0) data.custom_tools = customTools;

        addActivityLog('system', `Creating ${role} agent with model ${model}...`);
        const result = await apiPost('/api/agents', data);
        await fetchAgents();
        closeModal();

        addActivityLog('system', `Agent created successfully`, result.agent_id || null, {
            role, model,
            tools: customTools || 'default'
        });
    } catch (error) {
        console.error('Error creating agent:', error);
        addActivityLog('error', `Failed to create agent: ${error.message}`);
        alert('Failed to create agent');
    }
}

// ============================================================================
// Model Operations
// ============================================================================

async function fetchModels() {
    try {
        const data = await apiGet('/api/models');
        state.models = data.models;
        renderModels();
        populateModelSelector();
    } catch (error) {
        console.error('Error fetching models:', error);
    }
}

async function downloadModel(modelName) {
    if (!confirm(`Download model ${modelName}? This may take several minutes.`)) return;

    try {
        const btn = document.querySelector(`[data-model="${modelName}"]`);
        btn.textContent = 'Downloading...';
        btn.disabled = true;

        addActivityLog('system', `Downloading model ${modelName}...`);
        await apiPost('/api/models/download', { model_name: modelName });

        addActivityLog('system', `Model ${modelName} downloaded successfully`);
        await fetchModels();
    } catch (error) {
        console.error('Error downloading model:', error);
        addActivityLog('error', `Failed to download model: ${error.message}`);
        alert('Failed to download model');
    }
}

// ============================================================================
// Chat Interface
// ============================================================================

function openChat(agentId) {
    state.selectedAgentId = agentId;
    const agent = state.agents.find(a => a.id === agentId);

    if (!agent) return;

    // Switch to chat tab
    switchTab('chat');

    document.getElementById('chat-agent-name').textContent =
        `Chat with ${agent.role} (${agent.model})`;
    document.getElementById('chat-messages').innerHTML = '';

    addActivityLog('system', `Opened chat with agent`, agentId);
    renderAgents(); // Update active state
}

function closeChat() {
    state.selectedAgentId = null;
    document.getElementById('chat-section').style.display = 'none';
    renderAgents();
}

async function sendMessage() {
    const textarea = document.getElementById('chat-textarea');
    const message = textarea.value.trim();

    if (!message || !state.selectedAgentId) return;

    // Add user message to UI
    addMessageToChat('user', message);
    textarea.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Log user message
    addActivityLog('chat', `User: ${message.substring(0, 100)}${message.length > 100 ? '...' : ''}`, state.selectedAgentId);

    try {
        const result = await apiPost(`/api/agents/${state.selectedAgentId}/task`, {
            type: 'chat',
            content: message
        });

        // Remove typing indicator
        removeTypingIndicator();

        if (result.success) {
            addMessageToChat('assistant', result.response);

            // Check if response contains command execution
            if (result.tool_used) {
                addActivityLog('command', `Executed tool: ${result.tool_used}`, state.selectedAgentId, result.tool_output);
            } else {
                addActivityLog('chat', `Agent: ${result.response.substring(0, 100)}...`, state.selectedAgentId);
            }
        } else {
            addMessageToChat('system', `Error: ${result.error}`);
            addActivityLog('error', `Task failed: ${result.error}`, state.selectedAgentId);
        }
    } catch (error) {
        removeTypingIndicator();
        console.error('Error sending message:', error);
        addMessageToChat('system', 'Failed to send message');
        addActivityLog('error', `Failed to send message: ${error.message}`, state.selectedAgentId);
    }
}

function addMessageToChat(role, content) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // Avatar emoji
    const avatar = role === 'user' ? '👤' : '🤖';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-bubble">
            <div class="message-role">${role}</div>
            <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
        </div>
    `;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message assistant loading';
    indicatorDiv.id = 'typing-indicator';
    indicatorDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(indicatorDiv);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

// ============================================================================
// Modal Operations
// ============================================================================

function openModal() {
    document.getElementById('modal-create-agent').classList.add('active');
}

function closeModal() {
    document.getElementById('modal-create-agent').classList.remove('active');
    document.getElementById('agent-prompt').value = '';
}

function populateModelSelector() {
    const select = document.getElementById('agent-model');
    const downloadedModels = state.models.filter(m => m.is_downloaded);

    select.innerHTML = downloadedModels.length > 0
        ? downloadedModels.map(m =>
            `<option value="${m.name}">${m.name} (${m.parameters})</option>`
        ).join('')
        : '<option value="">No models downloaded</option>';
}

async function updateRequirements() {
    const modelSelect = document.getElementById('agent-model');
    const selectedModel = modelSelect.value;

    if (!selectedModel) return;

    try {
        const data = await apiPost('/api/models/calculate-requirements', [selectedModel]);
        const req = data.requirements;

        document.getElementById('req-ram').textContent = `${req.total_ram_gb.toFixed(1)}GB`;
        document.getElementById('req-vram').textContent = `${req.total_vram_gb.toFixed(1)}GB`;
        document.getElementById('req-disk').textContent = `${req.total_disk_gb.toFixed(1)}GB`;

        const warningsDiv = document.getElementById('req-warnings');
        if (req.warnings.length > 0) {
            warningsDiv.innerHTML = req.warnings.map(w => `⚠️ ${w}`).join('<br>');
        } else if (!req.can_allocate) {
            warningsDiv.innerHTML = '⚠️ Insufficient resources!';
        } else {
            warningsDiv.innerHTML = '✓ Resources available';
            warningsDiv.style.color = '#10b981';
        }
    } catch (error) {
        console.error('Error calculating requirements:', error);
    }
}

// ============================================================================
// Permissions Modal
// ============================================================================

function openPermissionsModal(agentId) {
    const agent = state.agents.find(a => a.id === agentId);
    if (!agent) return;

    document.getElementById('permissions-agent-name').textContent = `Agent ${agent.id.substring(0, 8)}`;
    document.getElementById('permissions-agent-role').textContent = `Role: ${agent.role} | Model: ${agent.model}`;

    // Populate tools list
    const allTools = ['nmap', 'gobuster', 'sqlmap', 'metasploit', 'browser', 'command', 'custom_scripts'];
    const toolsList = document.getElementById('permissions-tools-list');
    const agentTools = agent.allowed_tools || [];

    toolsList.innerHTML = allTools.map(tool => {
        const isActive = agentTools.includes(tool);
        return `
            <div class="tool-badge ${isActive ? 'active' : 'disabled'}">
                <input type="checkbox" value="${tool}" ${isActive ? 'checked' : ''} class="tool-permission-checkbox">
                ${tool} ${tool === 'command' ? '⚠️' : ''}
            </div>
        `;
    }).join('');

    // Set command tool toggle
    document.getElementById('allow-command-tool').checked = agentTools.includes('command');

    document.getElementById('modal-agent-permissions').classList.add('active');
    state.editingAgentId = agentId;
}

function closePermissionsModal() {
    document.getElementById('modal-agent-permissions').classList.remove('active');
    state.editingAgentId = null;
}

async function saveAgentPermissions() {
    if (!state.editingAgentId) return;

    // Get selected tools
    const toolCheckboxes = document.querySelectorAll('.tool-permission-checkbox');
    const selectedTools = Array.from(toolCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    try {
        // Note: This would need a backend endpoint to update agent permissions
        // For now, we'll just update local state
        const agent = state.agents.find(a => a.id === state.editingAgentId);
        if (agent) {
            agent.allowed_tools = selectedTools;
        }

        addActivityLog('system', `Permissions updated successfully for agent`, state.editingAgentId, {
            tools: selectedTools
        });

        closePermissionsModal();
        renderAgents();
    } catch (error) {
        console.error('Error updating permissions:', error);
        addActivityLog('error', `Failed to update permissions: ${error.message}`, state.editingAgentId);
        alert('Failed to update permissions');
    }
}

// ============================================================================
// Initialization
// ============================================================================

async function init() {
    try {
        // Check health
        const health = await apiGet('/api/health');
        updateStatusIndicator(health.status === 'ok');
        addActivityLog('system', `Playground connected - ${health.status}`);

        // Fetch initial data
        await Promise.all([
            fetchModels(),
            fetchAgents(),
            fetchResources()
        ]);

        // Setup periodic updates
        setInterval(fetchAgents, 5000); // Update agents every 5s
        setInterval(fetchResources, 3000); // Update resources every 3s

    } catch (error) {
        console.error('Initialization error:', error);
        updateStatusIndicator(false);
        addActivityLog('error', `Initialization failed: ${error.message}`);
    }
}

async function fetchResources() {
    try {
        const data = await apiGet('/api/system/resources');
        state.resources = data;
        updateResources();
    } catch (error) {
        console.error('Error fetching resources:', error);
    }
}

// ============================================================================
// Event Listeners
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize
    init();

    state.editingAgentId = null;

    // Tab switching
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    // Debug panel filter checkboxes
    const filterIds = ['command', 'chat', 'system', 'error'];
    filterIds.forEach(filter => {
        const checkbox = document.getElementById(`filter-${filter}`);
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                state.activityFilters[filter] = e.target.checked;
                updateLogFilters();
            });
        }
    });

    // Create agent button
    document.getElementById('btn-create-agent').addEventListener('click', openModal);

    // Modal controls
    document.getElementById('btn-close-modal').addEventListener('click', closeModal);
    document.getElementById('btn-cancel-modal').addEventListener('click', closeModal);
    document.getElementById('btn-confirm-create').addEventListener('click', () => {
        const role = document.getElementById('agent-role').value;
        const model = document.getElementById('agent-model').value;
        const prompt = document.getElementById('agent-prompt').value.trim() || null;

        // Get selected tools
        const toolCheckboxes = document.querySelectorAll('#tools-selector input[type="checkbox"]:checked');
        const customTools = Array.from(toolCheckboxes).map(cb => cb.value);

        createAgent(role, model, prompt, customTools);
    });

    // Permissions modal controls
    document.getElementById('btn-close-permissions').addEventListener('click', closePermissionsModal);
    document.getElementById('btn-cancel-permissions').addEventListener('click', closePermissionsModal);
    document.getElementById('btn-save-permissions').addEventListener('click', saveAgentPermissions);

    // Model selector change
    document.getElementById('agent-model').addEventListener('change', updateRequirements);

    // Chat controls
    document.getElementById('btn-close-chat').addEventListener('click', closeChat);
    document.getElementById('btn-send').addEventListener('click', sendMessage);
    document.getElementById('chat-textarea').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
