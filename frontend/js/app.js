const API_BASE = 'http://localhost:3000';

// ===== State =====
const state = {
  currentRoute: 'dashboard',
  providers: [],
  config: null,
  terminalOpen: false,
  terminalHistory: [],
  cronJobs: []
};

// ===== DOM refs =====
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const content = document.getElementById('content');
const pageTitle = document.getElementById('page-title');
const terminalPanel = document.getElementById('terminal-panel');
const terminalOutput = document.getElementById('terminal-output');
const terminalInput = document.getElementById('terminal-input');

// ===== API Client =====
async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    let err = await res.text();
    try {
      const parsed = JSON.parse(err);
      err = parsed.detail || err;
    } catch (_) {}
    throw new Error(`API ${method} ${path}: ${res.status} ${err}`);
  }
  return res.json();
}

const api_get = (path) => api('GET', path);
const api_post = (path, body) => api('POST', path, body);
const api_del = (path) => api('DELETE', path);

const LLM_PROVIDER_IDS = ['google', 'custom_qwen', 'openai', 'claude', 'glm', 'qwen'];
const configuredLlms = () => state.providers.filter(p => LLM_PROVIDER_IDS.includes(p.id) && p.configured);

// ===== Terminal =====
function terminalLog(msg, type = 'info') {
  const div = document.createElement('div');
  div.className = `terminal-line ${type}`;
  div.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  terminalOutput.appendChild(div);
  terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

function terminalClear() {
  terminalOutput.innerHTML = '';
}

function toggleTerminal() {
  state.terminalOpen = !state.terminalOpen;
  terminalPanel.classList.toggle('open', state.terminalOpen);
  if (state.terminalOpen) terminalInput.focus();
}

document.getElementById('btn-terminal-toggle').addEventListener('click', toggleTerminal);
document.getElementById('btn-terminal-close').addEventListener('click', () => toggleTerminal());

terminalInput.addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    const cmd = terminalInput.value.trim();
    terminalInput.value = '';
    if (!cmd) return;
    terminalLog(`$ ${cmd}`, 'system');
    state.terminalHistory.push(cmd);

    if (cmd === 'clear') { terminalClear(); return; }
    if (cmd === 'help') {
      terminalLog('Available commands: help, clear, status, providers, logs');
      return;
    }
    if (cmd === 'status') {
      try {
        const h = await api_get('/api/health');
        terminalLog(`Status: ${h.status} | v${h.version}`, 'success');
      } catch (e) {
        terminalLog(`Error: ${e.message}`, 'error');
      }
      return;
    }
    if (cmd === 'providers') {
      try {
        const p = await api_get('/api/providers');
        terminalLog(`Available providers: ${p.providers.map(x => x.id).join(', ')}`, 'info');
      } catch (e) {
        terminalLog(`Error: ${e.message}`, 'error');
      }
      return;
    }
    if (cmd === 'logs') {
      try {
        const logs = await api_get('/api/logs');
        terminalLog(`Recent logs: ${logs.logs.length} files`, 'info');
      } catch (e) {
        terminalLog(`Error: ${e.message}`, 'error');
      }
      return;
    }
    terminalLog(`Unknown command: ${cmd}. Type 'help' for available commands.`, 'warn');
  }
});

// ===== Routing =====
const routes = {
  dashboard: { title: 'Dashboard', render: 'renderDashboard' },
  chat: { title: 'AI Chat', render: 'renderChat' },
  code: { title: 'Code Studio', render: 'renderCode' },
  course: { title: 'Course Creator', render: 'renderCourse' },
  video: { title: 'Video Studio', render: 'renderVideo' },
  settings: { title: 'Settings', render: 'renderSettings' },
  cron: { title: 'Scheduler', render: 'renderCron' },
  logs: { title: 'Logs', render: 'renderLogs' },
};

function navigate(route) {
  state.currentRoute = route;
  $$('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.route === route);
  });
  const page = routes[route];
  if (page) {
    pageTitle.textContent = page.title;
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    const fn = typeof page.render === 'function' ? page.render : window[page.render];
    if (typeof fn === 'function') fn();
  }
}

window.addEventListener('hashchange', () => {
  const route = location.hash.slice(1) || 'dashboard';
  if (routes[route]) navigate(route);
});

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', (e) => {
    e.preventDefault();
    const route = el.dataset.route;
    location.hash = route;
  });
});

document.getElementById('btn-run').addEventListener('click', () => {
  if (state.currentRoute === 'chat') document.getElementById('btn-chat-send')?.click();
  if (state.currentRoute === 'code') document.getElementById('btn-code-generate')?.click();
});

// ===== Dashboard =====
async function renderDashboard() {
  let health = { status: 'unknown', version: '3.0.0' };
  try {
    health = await api_get('/api/health');
    const providers = await api_get('/api/providers');
    state.providers = providers.providers;
    const configRes = await api_get('/api/config');
    state.config = configRes;
  } catch (e) {
    terminalLog(`Dashboard: ${e.message} (server may be offline)`, 'error');
  }

  const cfg = state.config || { api_keys: {}, preferences: {} };
  const hasKeys = state.providers.some(p => p.configured);
  const keyCount = state.providers.filter(p => p.configured).length;

  content.innerHTML = `
    <div class="grid-2 dashboard-stats">
      <div class="card">
        <div class="stat-value">${keyCount}</div>
        <div class="stat-label">API Keys Configured</div>
      </div>
      <div class="card">
        <div class="stat-value">${state.providers.length}</div>
        <div class="stat-label">Available Providers</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">System Status</div>
      <div class="flex-between mb-1">
        <span>Engine</span>
        <span class="badge badge-success">v${health.version || '3.0.0'}</span>
      </div>
      <div class="flex-between mb-1">
        <span>API Status</span>
        <span class="badge badge-success">${health.status || 'unknown'}</span>
      </div>
      <div class="flex-between">
        <span>Active LLM</span>
        <span class="badge">${cfg.effective_llm || cfg.preferences?.default_llm || 'qwen'}</span>
      </div>
    </div>

    <div class="card">
      <div class="card-header">Providers</div>
      <div class="provider-list">
        ${state.providers.map(p => `
          <div class="provider-tag">
            <span class="dot ${p.configured || cfg.api_keys[p.id] ? 'online' : 'offline'}"></span>
            ${p.name}
          </div>
        `).join('')}
        ${state.providers.length === 0 ? '<span class="text-muted text-sm">No providers loaded (server offline?)</span>' : ''}
      </div>
    </div>

    <div class="card">
      <div class="card-header">Quick Actions</div>
      <div class="flex gap-1">
        <button class="btn btn-primary" onclick="location.hash='course'">Create Course</button>
        <button class="btn btn-primary" onclick="location.hash='video'">Create Video</button>
        <button class="btn" onclick="location.hash='settings'">Configure API Keys</button>
      </div>
    </div>

    ${!hasKeys ? `
    <div class="card" style="border-color: var(--warning);">
      <div class="card-title" style="color: var(--warning);">⚠ API Keys Required</div>
      <div class="card-subtitle">Go to Settings to configure your API keys before using the creation pipelines.</div>
    </div>` : ''}
  `;
}

// ===== Chat =====
async function renderChat() {
  let history = { items: [] };
  try {
    history = await api_get('/api/chat/history');
  } catch (e) {
    terminalLog(`Chat history load error: ${e.message}`, 'error');
  }

  content.innerHTML = `
    <div class="grid-2" style="align-items: start;">
      <div class="card">
        <div class="card-header">AI Chat</div>
        <div class="form-group">
          <label class="form-label">Provider</label>
          <select id="chat-provider">
            <option value="">Auto (${configuredLlms()[0]?.name || 'configure a provider first'})</option>
            ${configuredLlms().map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Prompt</label>
          <textarea id="chat-prompt" rows="6" placeholder="Enter your prompt..."></textarea>
        </div>
      <button class="btn btn-primary" id="btn-chat-send" ${configuredLlms().length ? '' : 'disabled'}>Send</button>
      ${configuredLlms().length ? '' : '<div class="text-sm text-muted mt-1">Add a Google API key or Custom Qwen server in Settings first.</div>'}
        <div class="mt-2" id="chat-result" style="display:none;">
          <div class="card-header">Response <span id="chat-cost" class="text-muted text-xs"></span></div>
          <pre class="json" id="chat-response"></pre>
        </div>
      </div>

      <div class="card">
        <div class="flex-between mb-1">
          <div class="card-header" style="margin-bottom:0;">Chat History</div>
          <button class="btn btn-sm btn-danger" id="btn-chat-clear">Clear</button>
        </div>
        <div id="chat-history-list" class="history-list">
          ${history.items.length === 0 ? '<div class="text-muted text-sm">No saved chats yet.</div>' : history.items.map(item => `
            <button class="history-item" data-id="${item.id}">
              <span class="history-title">${escapeHtml(item.prompt.slice(0, 90))}</span>
              <span class="history-meta">${escapeHtml(item.provider)} · ${new Date(item.created_at).toLocaleString()}</span>
            </button>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  document.getElementById('btn-chat-send').addEventListener('click', async () => {
    const prompt = document.getElementById('chat-prompt').value.trim();
    const provider = document.getElementById('chat-provider').value;
    if (!prompt) return;
    const btn = document.getElementById('btn-chat-send');
    btn.disabled = true;
    btn.textContent = 'Sending...';
    terminalLog(`Chat: sending to ${provider || 'auto'}...`, 'info');

    try {
      const res = await api_post('/api/chat', { prompt, provider });
      document.getElementById('chat-result').style.display = 'block';
      document.getElementById('chat-response').textContent = res.result;
      document.getElementById('chat-cost').textContent = `| ${res.cost}`;
      terminalLog(`Chat response received (${res.provider})`, 'success');
      prependChatHistory({
        id: res.chat_id || String(Date.now()),
        created_at: new Date().toISOString(),
        provider: res.provider,
        cost: res.cost,
        prompt,
        response: res.result,
      });
    } catch (e) {
      terminalLog(`Chat error: ${e.message}`, 'error');
      document.getElementById('chat-result').style.display = 'block';
      document.getElementById('chat-response').textContent = `Error: ${e.message}`;
      prependChatHistory({
        id: String(Date.now()),
        created_at: new Date().toISOString(),
        provider: provider || 'auto',
        cost: 'failed',
        prompt,
        response: `Error: ${e.message}`,
      });
    } finally {
      btn.disabled = false;
      btn.textContent = 'Send';
    }
  });

  document.querySelectorAll('.history-item').forEach(button => {
    button.addEventListener('click', () => {
      const item = history.items.find(x => x.id === button.dataset.id);
      if (!item) return;
      document.getElementById('chat-result').style.display = 'block';
      document.getElementById('chat-cost').textContent = `| ${item.cost || ''}`;
      document.getElementById('chat-response').textContent = item.response;
      document.getElementById('chat-prompt').value = item.prompt;
    });
  });

  document.getElementById('btn-chat-clear').addEventListener('click', async () => {
    try {
      await api_del('/api/chat/history');
      terminalLog('Chat history cleared', 'success');
      renderChat();
    } catch (e) {
      terminalLog(`Clear history failed: ${e.message}`, 'error');
    }
  });
}

function prependChatHistory(item) {
  const list = document.getElementById('chat-history-list');
  if (!list) return;
  const empty = list.querySelector('.text-muted');
  if (empty) empty.remove();
  const button = document.createElement('button');
  button.className = 'history-item';
  button.dataset.id = item.id;
  button.innerHTML = `
    <span class="history-title">${escapeHtml(item.prompt.slice(0, 90))}</span>
    <span class="history-meta">${escapeHtml(item.provider)} · ${new Date(item.created_at).toLocaleString()}</span>
  `;
  button.addEventListener('click', () => {
    document.getElementById('chat-result').style.display = 'block';
    document.getElementById('chat-cost').textContent = `| ${item.cost || ''}`;
    document.getElementById('chat-response').textContent = item.response;
    document.getElementById('chat-prompt').value = item.prompt;
  });
  list.prepend(button);
}

// ===== Settings =====
async function renderSettings() {
  let config;
  try {
    config = await api_get('/api/config');
    state.config = config;
  } catch (e) {
    config = { api_keys: {}, preferences: {} };
  }

  content.innerHTML = `
    <div class="card">
      <div class="card-header">API Keys</div>
      ${Object.keys(config.api_keys).filter(k => k !== 'custom_qwen').map(k => `
        <div class="form-group">
          <div class="flex-between mb-1">
            <label class="form-label" style="margin-bottom:0;">${k.replace('_', ' ').toUpperCase()}</label>
            <span class="badge ${config.api_keys[k] ? 'badge-success' : ''}">${config.api_keys[k] ? 'Stored' : 'Not stored'}</span>
          </div>
          <div class="flex gap-1">
            <input type="password" id="key-${k}" placeholder="${k === 'google' ? 'AIza...' : 'API key'}" value="" />
            <button class="btn btn-sm btn-primary" onclick="saveApiKey('${k}')">Save</button>
            ${config.api_keys[k] ? `<button class="btn btn-sm btn-danger" onclick="removeApiKey('${k}')">Remove</button>` : ''}
          </div>
          ${config.api_keys[k] ? '<div class="text-xs text-muted mt-1">Stored securely in local config as a masked value here.</div>' : ''}
        </div>
      `).join('')}
    </div>

    <div class="card">
      <div class="card-header">Custom Qwen Server</div>
      ${renderCustomQwenSettings(config)}
    </div>

    <div class="card">
      <div class="card-header">Preferences</div>
      <div class="form-group">
        <label class="form-label">Default LLM Provider</label>
        <select id="pref-default-llm">
                  <option value="google" ${config.preferences?.default_llm === 'google' ? 'selected' : ''}>Google Gemini</option>
          <option value="custom_qwen" ${config.preferences?.default_llm === 'custom_qwen' ? 'selected' : ''}>Custom Qwen Server</option>
          <option value="qwen" ${config.preferences?.default_llm === 'qwen' ? 'selected' : ''}>Qwen 2.5 7B (Fast)</option>
          <option value="glm" ${config.preferences?.default_llm === 'glm' ? 'selected' : ''}>GLM-5.2 (Powerful)</option>
          <option value="openai" ${config.preferences?.default_llm === 'openai' ? 'selected' : ''}>OpenAI</option>
          <option value="claude" ${config.preferences?.default_llm === 'claude' ? 'selected' : ''}>Claude</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Default Video Engine</label>
        <select id="pref-default-video-engine">
          <option value="pruna" ${config.preferences?.default_video_engine === 'pruna' ? 'selected' : ''}>Pruna P-Video</option>
          <option value="google_video" ${config.preferences?.default_video_engine === 'google_video' ? 'selected' : ''}>Google GenAI Video</option>
        </select>
      </div>
      <button class="btn btn-primary" onclick="savePreferences()">Save Preferences</button>
    </div>
  `;
}

window.saveApiKey = async (provider) => {
  const key = document.getElementById(`key-${provider}`).value.trim();
  if (!key) return;
  try {
    await api_post('/api/config/api-key', { provider, key });
    const providers = await api_get('/api/providers');
    state.providers = providers.providers;
    terminalLog(`Saved API key for ${provider}`, 'success');
    renderSettings();
  } catch (e) {
    terminalLog(`Failed to save key: ${e.message}`, 'error');
  }
};

function renderCustomQwenSettings(config) {
  const custom = config.provider_configs?.custom_qwen || {};
  const stored = Boolean(custom.endpoint_url);
  return `
    <div class="flex-between mb-1">
      <span class="text-sm">Ollama-compatible /api/chat endpoint</span>
      <span class="badge ${stored ? 'badge-success' : ''}">${stored ? 'Stored' : 'Not stored'}</span>
    </div>
    <div class="form-group">
      <label class="form-label">Endpoint URL</label>
      <input type="text" id="custom-qwen-url" placeholder="http://162.35.163.67:11435/api/chat" value="${escapeHtml(custom.endpoint_url || '')}" />
    </div>
    <div class="grid-2">
      <div class="form-group">
        <label class="form-label">Username</label>
        <input type="text" id="custom-qwen-username" placeholder="qwen_coder" value="${escapeHtml(custom.username || '')}" />
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" id="custom-qwen-password" placeholder="${custom.password ? 'Stored password' : 'Password'}" value="" />
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Model</label>
      <input type="text" id="custom-qwen-model" placeholder="qwen2.5-coder" value="${escapeHtml(custom.model || 'qwen2.5-coder')}" />
    </div>
    <div class="flex gap-1">
      <button class="btn btn-sm btn-primary" onclick="saveCustomQwen()">Save Custom Qwen</button>
      ${stored ? '<button class="btn btn-sm btn-danger" onclick="removeCustomQwen()">Remove</button>' : ''}
    </div>
  `;
}

window.removeApiKey = async (provider) => {
  try {
    await api_del(`/api/config/api-key/${provider}`);
    const providers = await api_get('/api/providers');
    state.providers = providers.providers;
    terminalLog(`Removed API key for ${provider}`, 'success');
    renderSettings();
  } catch (e) {
    terminalLog(`Failed to remove key: ${e.message}`, 'error');
  }
};

window.saveCustomQwen = async () => {
  const endpoint_url = document.getElementById('custom-qwen-url').value.trim();
  const username = document.getElementById('custom-qwen-username').value.trim();
  const password = document.getElementById('custom-qwen-password').value;
  const model = document.getElementById('custom-qwen-model').value.trim() || 'qwen2.5-coder';
  if (!endpoint_url) {
    terminalLog('Custom Qwen endpoint URL is required', 'warn');
    return;
  }
  const config = { endpoint_url, username, model };
  if (password) config.password = password;
  try {
    await api_post('/api/config/provider', { provider: 'custom_qwen', config });
    const providers = await api_get('/api/providers');
    state.providers = providers.providers;
    terminalLog('Saved Custom Qwen server', 'success');
    renderSettings();
  } catch (e) {
    terminalLog(`Failed to save Custom Qwen: ${e.message}`, 'error');
  }
};

window.removeCustomQwen = async () => {
  try {
    await api_del('/api/config/provider/custom_qwen');
    const providers = await api_get('/api/providers');
    state.providers = providers.providers;
    terminalLog('Removed Custom Qwen server', 'success');
    renderSettings();
  } catch (e) {
    terminalLog(`Failed to remove Custom Qwen: ${e.message}`, 'error');
  }
};

// ===== Code Studio =====
async function renderCode() {
  let tree = { items: [] };
  try {
    tree = await api_get('/api/workspace/tree');
  } catch (e) {
    terminalLog(`Workspace load error: ${e.message}`, 'error');
  }

  const files = tree.items.filter(item => item.type === 'file').slice(0, 160);
  content.innerHTML = `
    <div class="grid-2" style="align-items: start;">
      <div class="card">
        <div class="card-header">Coding Agent</div>
        <div class="form-group">
          <label class="form-label">Provider</label>
          <select id="code-provider">
            <option value="">Auto (${configuredLlms()[0]?.name || 'configure a provider first'})</option>
            ${configuredLlms().map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Request</label>
          <textarea id="code-prompt" rows="8" placeholder="Example: Add a provider, fix a UI issue, or improve an API route."></textarea>
        </div>
        <label class="check-row">
          <input type="checkbox" id="code-apply" />
          <span>Apply file changes automatically</span>
        </label>
        <div class="flex gap-1 mt-2">
          <button class="btn btn-primary" id="btn-code-generate">Generate Changes</button>
          <button class="btn" id="btn-code-refresh">Refresh Files</button>
        </div>
      </div>

      <div class="card">
        <div class="card-header">Workspace Files</div>
        <div class="file-list">
          ${files.map(file => `<button class="file-row" data-path="${escapeHtml(file.path)}">${escapeHtml(file.path)}</button>`).join('')}
        </div>
      </div>
    </div>

    <div id="code-results" class="card" style="display:none;">
      <div class="card-header">Generated Plan</div>
      <div id="code-summary" class="card-subtitle"></div>
      <div id="code-applied" class="text-sm mb-1"></div>
      <pre class="json" id="code-plan"></pre>
    </div>
  `;

  document.getElementById('btn-code-refresh').addEventListener('click', renderCode);
  document.getElementById('btn-code-generate').addEventListener('click', generateCodeChanges);
  document.querySelectorAll('.file-row').forEach(button => {
    button.addEventListener('click', () => previewWorkspaceFile(button.dataset.path));
  });
}

async function generateCodeChanges() {
  const prompt = document.getElementById('code-prompt').value.trim();
  const provider = document.getElementById('code-provider').value;
  const apply = document.getElementById('code-apply').checked;
  if (!prompt) {
    terminalLog('Describe the coding change first', 'warn');
    return;
  }

  const btn = document.getElementById('btn-code-generate');
  if (!configuredLlms().length) {
    terminalLog('Add a Google API key or Custom Qwen server in Settings first', 'warn');
    return;
  }
  btn.disabled = true;
  btn.textContent = apply ? 'Generating and applying...' : 'Generating...';
  terminalLog(`Code Studio: sending request to ${provider || 'auto'}...`, 'info');

  try {
    const res = await api_post('/api/code/generate', { prompt, provider, apply });
    document.getElementById('code-results').style.display = 'block';
    document.getElementById('code-summary').textContent = `${res.plan.summary || 'Generated changes'} | ${res.provider}`;
    document.getElementById('code-applied').textContent = res.applied?.length
      ? `Applied ${res.applied.length} file(s): ${res.applied.map(f => f.path).join(', ')}`
      : 'Not applied. Review the JSON before enabling auto-apply.';
    document.getElementById('code-plan').textContent = JSON.stringify(res.plan, null, 2);
    terminalLog(`Code plan ready (${res.plan.files?.length || 0} file changes)`, 'success');
  } catch (e) {
    document.getElementById('code-results').style.display = 'block';
    document.getElementById('code-summary').textContent = 'Generation failed';
    document.getElementById('code-plan').textContent = e.message;
    terminalLog(`Code Studio error: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Changes';
  }
}

async function previewWorkspaceFile(path) {
  try {
    const file = await api_get(`/api/workspace/file?path=${encodeURIComponent(path)}`);
    document.getElementById('code-results').style.display = 'block';
    document.getElementById('code-summary').textContent = file.path;
    document.getElementById('code-applied').textContent = '';
    document.getElementById('code-plan').textContent = file.content;
  } catch (e) {
    terminalLog(`File preview failed: ${e.message}`, 'error');
  }
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

window.savePreferences = async () => {
  const default_llm = document.getElementById('pref-default-llm').value;
  const default_video_engine = document.getElementById('pref-default-video-engine').value;
  try {
    await api_post('/api/config/preferences', { default_llm, default_video_engine });
    terminalLog('Preferences saved', 'success');
  } catch (e) {
    terminalLog(`Failed to save preferences: ${e.message}`, 'error');
  }
};

// ===== Cron =====
async function renderCron() {
  let jobs = [];
  try {
    const res = await api_get('/api/cron/list');
    jobs = res.jobs;
    state.cronJobs = jobs;
  } catch (e) { terminalLog(`Cron load error: ${e.message}`, 'error'); }

  content.innerHTML = `
    <div class="card">
      <div class="card-header">Schedule New Job</div>
      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Label</label>
          <input type="text" id="cron-label" placeholder="Daily course generation" />
        </div>
        <div class="form-group">
          <label class="form-label">Cron Schedule</label>
          <input type="text" id="cron-schedule" placeholder="0 2 * * *" />
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Mode</label>
        <select id="cron-mode">
          <option value="course">Course Creation</option>
          <option value="video">Video Production</option>
        </select>
      </div>
      <button class="btn btn-primary" onclick="addCronJob()">Add Job</button>
    </div>

    <div class="card">
      <div class="card-header">Scheduled Jobs (${jobs.length})</div>
      ${jobs.length === 0 ? '<div class="text-muted">No jobs scheduled yet.</div>' : jobs.map(j => `
        <div class="cron-item">
          <div>
            <div class="cron-schedule">${j.schedule}</div>
            <div class="cron-command">${j.command || j.mode}</div>
            <div class="text-xs text-muted">${j.label || ''}</div>
          </div>
          <button class="btn btn-sm btn-danger" onclick="removeCron('${j.id}')">Delete</button>
        </div>
      `).join('')}
    </div>
  `;
}

window.addCronJob = async () => {
  const label = document.getElementById('cron-label').value.trim() || 'Untitled job';
  const schedule = document.getElementById('cron-schedule').value.trim();
  const mode = document.getElementById('cron-mode').value;
  if (!schedule) { terminalLog('Please enter a cron schedule', 'warn'); return; }

  const command = mode === 'course'
    ? 'python scripts/course_generator.py --blueprint=data/blueprints/daily.json'
    : 'python scripts/video_pipeline.py --style=cinematic --output=data/videos/';

  try {
    await api_post('/api/cron/add', { schedule, command, mode, label });
    terminalLog(`Cron job added: ${schedule} (${label})`, 'success');
    renderCron();
  } catch (e) {
    terminalLog(`Failed to add cron: ${e.message}`, 'error');
  }
};

window.removeCron = async (id) => {
  try {
    await api_del(`/api/cron/${id}`);
    terminalLog('Cron job removed', 'success');
    renderCron();
  } catch (e) {
    terminalLog(`Failed to remove cron: ${e.message}`, 'error');
  }
};

// ===== Logs =====
async function renderLogs() {
  content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const res = await api_get('/api/logs');
    content.innerHTML = `
      <div class="card">
        <div class="card-header">System Logs</div>
        ${res.logs.length === 0 ? '<div class="text-muted">No logs yet.</div>' : `
        <table class="shots-table">
          <thead><tr><th>File</th><th>Size</th><th>Modified</th></tr></thead>
          <tbody>
            ${res.logs.map(l => `
              <tr><td>${l.name}</td><td>${l.size} B</td><td>${new Date(l.modified * 1000).toLocaleString()}</td></tr>
            `).join('')}
          </tbody>
        </table>`}
      </div>`;
  } catch (e) {
    content.innerHTML = `<div class="card"><div class="card-header">Logs</div><div class="text-muted">Error loading logs: ${e.message}</div></div>`;
  }
}

// ===== Init =====
async function init() {
  try {
    const health = await api_get('/api/health');
    terminalLog(`Johnny Agents v${health.version} initialized`, 'success');
    const providers = await api_get('/api/providers');
    state.providers = providers.providers;
  } catch (e) {
    terminalLog(`Backend not reachable: ${e.message}. Start the server first.`, 'error');
  }

  const route = location.hash.slice(1) || 'dashboard';
  if (routes[route]) navigate(route);
}

// Expose for sub-modules
window.state = state;
window.api_post = api_post;
window.api_get = api_get;
window.terminalLog = terminalLog;

document.addEventListener('DOMContentLoaded', init);
