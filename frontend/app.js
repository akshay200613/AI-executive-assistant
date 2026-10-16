/**
 * AI Executive Assistant — Client-side Application Logic
 * Supports real-time streaming simulation, multi-step compound task breakdown,
 * dynamic Render backend configuration, telemetry modal, and session history.
 */

(function () {
  'use strict';

  // --- Configuration & State ---
  const DEFAULT_BACKEND = 'https://ai-executive-assistant-api.onrender.com';
  const LOCAL_BACKEND = 'http://localhost:8000';

  let currentBackendUrl = localStorage.getItem('aea_backend_url') || DEFAULT_BACKEND;
  let sessionId = localStorage.getItem('aea_session_id') || generateUUID();
  localStorage.setItem('aea_session_id', sessionId);

  let queryHistory = JSON.parse(localStorage.getItem('aea_query_history') || '[]');
  let isGenerating = false;

  // --- DOM Elements ---
  const chatViewport = document.getElementById('chat-viewport');
  const messagesContainer = document.getElementById('messages-container');
  const welcomeHero = document.getElementById('welcome-hero');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const newChatBtn = document.getElementById('new-chat-btn');
  const sessionIdDisplay = document.getElementById('session-id-display');
  const sessionCard = document.getElementById('session-card');
  const sessionCopyBadge = document.getElementById('session-copy-badge');
  const historyList = document.getElementById('history-list');

  // Topbar & Sidebar Status
  const apiStatusDot = document.getElementById('api-status-dot');
  const apiStatusText = document.getElementById('api-status-text');
  const backendPingText = document.getElementById('backend-ping-text');
  const backendLabelBtn = document.getElementById('backend-label-btn');

  // Sidebar Mobile Controls
  const sidebar = document.getElementById('sidebar');
  const mobileToggleBtn = document.getElementById('mobile-toggle-btn');
  const sidebarCloseBtn = document.getElementById('sidebar-close-btn');

  // Config Modal Elements
  const configModal = document.getElementById('config-modal');
  const openConfigBtn = document.getElementById('open-config-btn');
  const topConfigBtn = document.getElementById('top-config-btn');
  const configModalClose = document.getElementById('config-modal-close');
  const cancelConfigBtn = document.getElementById('cancel-config-btn');
  const saveConfigBtn = document.getElementById('save-config-btn');
  const backendUrlInput = document.getElementById('backend-url-input');
  const testConnectionBtn = document.getElementById('test-connection-btn');
  const connectionStatusBox = document.getElementById('connection-status-box');
  const presetBtns = document.querySelectorAll('.preset-btn');

  // Stats Modal Elements
  const statsModal = document.getElementById('stats-modal');
  const statsModalBtn = document.getElementById('stats-modal-btn');
  const statsModalClose = document.getElementById('stats-modal-close');
  const closeStatsBtn = document.getElementById('close-stats-btn');
  const refreshStatsBtn = document.getElementById('refresh-stats-btn');
  const statTotalReqs = document.getElementById('stat-total-reqs');
  const statAvgLatency = document.getElementById('stat-avg-latency');
  const statErrorRate = document.getElementById('stat-error-rate');
  const statTotalTasks = document.getElementById('stat-total-tasks');
  const distributionBars = document.getElementById('distribution-bars');

  // Toast
  const toast = document.getElementById('toast');

  // --- Helpers ---
  function generateUUID() {
    if (window.crypto && window.crypto.randomUUID) {
      return window.crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function showToast(message, duration = 2500) {
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  }

  function updateSessionDisplay() {
    sessionIdDisplay.textContent = sessionId.slice(0, 8) + '...';
  }

  function updateBackendLabel() {
    try {
      const parsed = new URL(currentBackendUrl);
      backendLabelBtn.textContent = `API: ${parsed.hostname}`;
      backendPingText.textContent = `Target: ${parsed.hostname}`;
    } catch {
      backendLabelBtn.textContent = 'API: Config';
    }
  }

  // --- Backend Connectivity & Health Check ---
  async function checkHealth(urlToCheck = currentBackendUrl) {
    try {
      const cleanUrl = urlToCheck.replace(/\/+$/, '');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const resp = await fetch(`${cleanUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (resp.ok) {
        const data = await resp.json();
        return { ok: true, data };
      }
      return { ok: false, error: `HTTP ${resp.status}` };
    } catch (err) {
      return { ok: false, error: err.message || 'Network unreachable' };
    }
  }

  async function refreshHealthStatus() {
    apiStatusDot.className = 'pulse-dot';
    apiStatusText.textContent = 'Backend: Pinging...';

    const result = await checkHealth();
    if (result.ok) {
      apiStatusDot.classList.add('online');
      apiStatusText.textContent = 'Backend: Online';
      backendPingText.textContent = 'API Connected';
      backendPingText.style.color = 'var(--accent-emerald)';
    } else {
      apiStatusDot.classList.add('offline');
      apiStatusText.textContent = 'Backend: Offline';
      backendPingText.textContent = 'API Offline (Check URL)';
      backendPingText.style.color = 'var(--accent-rose)';
    }
  }

  // --- Sidebar & Mobile Drawer ---
  function openSidebar() {
    sidebar.classList.add('open');
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
  }

  // --- Session History in Sidebar ---
  function renderHistory() {
    historyList.innerHTML = '';
    if (!queryHistory || queryHistory.length === 0) {
      historyList.innerHTML = '<div class="history-empty">No queries in this session yet</div>';
      return;
    }

    queryHistory.slice(-8).reverse().forEach(q => {
      const item = document.createElement('div');
      item.className = 'history-item';
      item.textContent = `💬 ${q}`;
      item.title = q;
      item.addEventListener('click', () => {
        chatInput.value = q;
        chatInput.focus();
        adjustTextareaHeight();
        closeSidebar();
      });
      historyList.appendChild(item);
    });
  }

  function addQueryToHistory(text) {
    if (!queryHistory.includes(text)) {
      queryHistory.push(text);
      if (queryHistory.length > 20) queryHistory.shift();
      localStorage.setItem('aea_query_history', JSON.stringify(queryHistory));
      renderHistory();
    }
  }

  // --- Modals Logic ---
  function openConfigModal() {
    backendUrlInput.value = currentBackendUrl;
    connectionStatusBox.className = 'connection-status-box';
    connectionStatusBox.innerHTML = '<span class="status-msg">Click "Test" to check backend reachability</span>';
    configModal.classList.add('open');
  }

  function closeConfigModal() {
    configModal.classList.remove('open');
  }

  async function openStatsModal() {
    statsModal.classList.add('open');
    await fetchAndRenderStats();
  }

  function closeStatsModal() {
    statsModal.classList.remove('open');
  }

  async function fetchAndRenderStats() {
    statTotalReqs.textContent = '...';
    statAvgLatency.textContent = '...';
    statErrorRate.textContent = '...';
    statTotalTasks.textContent = '...';
    distributionBars.innerHTML = '<div class="empty-stats">Loading live metrics from backend...</div>';

    try {
      const cleanUrl = currentBackendUrl.replace(/\/+$/, '');
      const resp = await fetch(`${cleanUrl}/stats`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const apiStats = data.api || {};
      const agentStats = data.agent || {};

      statTotalReqs.textContent = apiStats.total_requests || 0;
      statAvgLatency.textContent = `${apiStats.avg_latency_ms || 0} ms`;
      statErrorRate.textContent = `${Math.round((apiStats.error_rate || 0) * 100)}%`;
      statTotalTasks.textContent = agentStats.total_tasks || 0;

      const dist = agentStats.task_distribution || {};
      const distKeys = Object.keys(dist);

      if (distKeys.length === 0) {
        distributionBars.innerHTML = '<div class="empty-stats">No task distribution recorded yet.</div>';
      } else {
        const maxVal = Math.max(...Object.values(dist), 1);
        distributionBars.innerHTML = '';
        distKeys.forEach(key => {
          const count = dist[key];
          const pct = Math.round((count / maxVal) * 100);
          const barItem = document.createElement('div');
          barItem.className = 'dist-bar-item';
          barItem.innerHTML = `
            <div class="dist-bar-meta">
              <span><strong>${key.replace(/_/g, ' ')}</strong></span>
              <span>${count} task${count > 1 ? 's' : ''}</span>
            </div>
            <div class="dist-bar-bg">
              <div class="dist-bar-fill" style="width: ${pct}%"></div>
            </div>
          `;
          distributionBars.appendChild(barItem);
        });
      }
    } catch (err) {
      distributionBars.innerHTML = `<div class="empty-stats" style="color:var(--accent-rose)">Failed to fetch stats: ${err.message}. Make sure the backend is running.</div>`;
    }
  }

  // --- Message UI Creators ---
  function appendUserMessage(text) {
    if (welcomeHero) welcomeHero.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `
      <div class="avatar user-avatar">👤</div>
      <div class="message-bubble-wrapper">
        <div class="message-bubble">${escapeHtml(text)}</div>
      </div>
    `;
    messagesContainer.appendChild(row);
    scrollToBottom();
  }

  function appendThinkingMessage() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.id = 'thinking-indicator';
    row.innerHTML = `
      <div class="avatar bot-avatar">🧠</div>
      <div class="message-bubble-wrapper">
        <div class="thinking-bubble">
          <span>Executive agent decomposing & executing</span>
          <div class="thinking-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
    scrollToBottom();
    return row;
  }

  function removeThinkingMessage() {
    const el = document.getElementById('thinking-indicator');
    if (el) el.remove();
  }

  function appendAssistantMessage(data) {
    removeThinkingMessage();

    const row = document.createElement('div');
    row.className = 'message-row assistant';

    const bubbleWrapper = document.createElement('div');
    bubbleWrapper.className = 'message-bubble-wrapper';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubbleWrapper.appendChild(bubble);

    // Build Execution Plan / Steps if compound
    if (data.steps && data.steps.length > 0) {
      const breakdownCard = document.createElement('div');
      breakdownCard.className = 'task-breakdown-card';

      const toggleBtn = document.createElement('button');
      toggleBtn.className = 'breakdown-toggle-btn open';
      toggleBtn.innerHTML = `
        <span class="toggle-title">
          <span>⚡</span>
          <span>Task Breakdown (${data.steps.length} Step${data.steps.length > 1 ? 's' : ''})</span>
        </span>
        <span class="toggle-icon">▼</span>
      `;

      const contentBox = document.createElement('div');
      contentBox.className = 'breakdown-content';

      data.steps.forEach((step, idx) => {
        const stepCard = document.createElement('div');
        stepCard.className = 'step-card';
        const formattedIntent = step.intent ? step.intent.replace(/_/g, ' ').toUpperCase() : 'STEP';
        const confPercent = step.confidence ? Math.round(step.confidence * 100) : 100;

        stepCard.innerHTML = `
          <div class="step-header">
            <span class="step-name">Step ${idx + 1}: ${formattedIntent}</span>
            <span class="step-confidence">${confPercent}% Confidence</span>
          </div>
          <div class="step-output-box">${escapeHtml(JSON.stringify(step.tool_output, null, 2))}</div>
        `;
        contentBox.appendChild(stepCard);
      });

      toggleBtn.addEventListener('click', () => {
        toggleBtn.classList.toggle('open');
      });

      breakdownCard.appendChild(toggleBtn);
      breakdownCard.appendChild(contentBox);
      bubbleWrapper.appendChild(breakdownCard);
    }

    // Meta Badge
    const metaBar = document.createElement('div');
    metaBar.className = 'message-meta';
    metaBar.innerHTML = `
      <span class="meta-badge">🎯 Intent: <strong>${data.intent || 'generic'}</strong></span>
      <span class="meta-badge">🛠️ Tool: <strong>${data.tool_used || 'planner'}</strong></span>
      <span class="meta-badge">⚡ ${data.latency_ms || 0} ms</span>
    `;
    bubbleWrapper.appendChild(metaBar);

    row.innerHTML = '<div class="avatar bot-avatar">🧠</div>';
    row.appendChild(bubbleWrapper);
    messagesContainer.appendChild(row);

    // Stream text response smoothly
    streamText(bubble, data.response || '');
  }

  function streamText(targetElement, fullText) {
    const words = fullText.split(' ');
    let currentIndex = 0;
    targetElement.innerHTML = '<span class="typing-cursor"></span>';

    const interval = setInterval(() => {
      if (currentIndex < words.length) {
        const partial = words.slice(0, currentIndex + 1).join(' ');
        targetElement.innerHTML = formatMarkdown(partial) + '<span class="typing-cursor"></span>';
        currentIndex++;
        scrollToBottom();
      } else {
        clearInterval(interval);
        targetElement.innerHTML = formatMarkdown(fullText);
        scrollToBottom();
      }
    }, 30);
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let escaped = escapeHtml(text);
    // Code blocks
    escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Inline code
    escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Bullet lists
    escaped = escaped.replace(/^\s*-\s+(.*)$/gm, '<li>$1</li>');
    escaped = escaped.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
    // Paragraphs
    escaped = escaped.split('\n\n').map(p => p.startsWith('<ul>') || p.startsWith('<pre>') ? p : `<p>${p}</p>`).join('');
    return escaped;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function scrollToBottom() {
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function adjustTextareaHeight() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + 'px';
  }

  // --- Send Message Flow ---
  async function handleSend() {
    const text = chatInput.value.trim();
    if (!text || isGenerating) return;

    isGenerating = true;
    sendBtn.disabled = true;
    chatInput.value = '';
    adjustTextareaHeight();

    appendUserMessage(text);
    addQueryToHistory(text);
    appendThinkingMessage();

    try {
      const cleanUrl = currentBackendUrl.replace(/\/+$/, '');
      const resp = await fetch(`${cleanUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Server returned HTTP ${resp.status}`);
      }

      const data = await resp.json();
      appendAssistantMessage(data);
    } catch (err) {
      removeThinkingMessage();
      appendAssistantMessage({
        response: `⚠️ **Communication Error**: Unable to reach backend at \`${currentBackendUrl}\`.\n\n**Details**: ${err.message}\n\nPlease click the **API Config** button in the header to ensure your Render backend URL is correct and online.`,
        intent: 'error',
        tool_used: 'none',
        latency_ms: 0,
        steps: [],
      });
      refreshHealthStatus();
    } finally {
      isGenerating = false;
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  // --- Reset / New Session ---
  function resetSession() {
    sessionId = generateUUID();
    localStorage.setItem('aea_session_id', sessionId);
    updateSessionDisplay();
    messagesContainer.innerHTML = '';
    if (welcomeHero) welcomeHero.style.display = 'block';
    showToast('New session created!');
    closeSidebar();
  }

  // --- Event Listeners Initialization ---
  function initEvents() {
    // Input Keydown
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
    chatInput.addEventListener('input', adjustTextareaHeight);
    sendBtn.addEventListener('click', handleSend);

    // New Chat
    newChatBtn.addEventListener('click', resetSession);

    // Copy Session ID
    sessionCard.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(sessionId);
        sessionCopyBadge.textContent = 'Copied!';
        setTimeout(() => { sessionCopyBadge.textContent = 'Copy'; }, 1800);
        showToast('Session ID copied to clipboard');
      } catch {
        showToast('Failed to copy session ID');
      }
    });

    // Mobile Drawer
    mobileToggleBtn.addEventListener('click', openSidebar);
    sidebarCloseBtn.addEventListener('click', closeSidebar);

    // Suggested Prompt Chips & Cards
    document.addEventListener('click', (e) => {
      const target = e.target.closest('[data-prompt]');
      if (target) {
        const prompt = target.getAttribute('data-prompt');
        if (prompt) {
          chatInput.value = prompt;
          chatInput.focus();
          adjustTextareaHeight();
          closeSidebar();
        }
      }
    });

    // Config Modal Triggers
    openConfigBtn.addEventListener('click', openConfigModal);
    topConfigBtn.addEventListener('click', openConfigModal);
    configModalClose.addEventListener('click', closeConfigModal);
    cancelConfigBtn.addEventListener('click', closeConfigModal);

    // Preset Buttons
    presetBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const url = btn.getAttribute('data-url');
        if (url) backendUrlInput.value = url;
      });
    });

    // Test Backend Connection
    testConnectionBtn.addEventListener('click', async () => {
      const url = backendUrlInput.value.trim();
      connectionStatusBox.className = 'connection-status-box';
      connectionStatusBox.innerHTML = '<span class="status-msg">Testing connection to /health...</span>';

      const res = await checkHealth(url);
      if (res.ok) {
        connectionStatusBox.className = 'connection-status-box success';
        connectionStatusBox.innerHTML = `<span>✅ <strong>Success!</strong> Backend reached (/health responded ok).</span>`;
      } else {
        connectionStatusBox.className = 'connection-status-box error';
        connectionStatusBox.innerHTML = `<span>❌ <strong>Failed:</strong> ${res.error}. Verify CORS or service URL.</span>`;
      }
    });

    // Save Config
    saveConfigBtn.addEventListener('click', () => {
      const url = backendUrlInput.value.trim().replace(/\/+$/, '');
      if (url) {
        currentBackendUrl = url;
        localStorage.setItem('aea_backend_url', currentBackendUrl);
        updateBackendLabel();
        closeConfigModal();
        showToast('Backend URL updated!');
        refreshHealthStatus();
      }
    });

    // Stats Modal Triggers
    statsModalBtn.addEventListener('click', openStatsModal);
    statsModalClose.addEventListener('click', closeStatsModal);
    closeStatsBtn.addEventListener('click', closeStatsModal);
    refreshStatsBtn.addEventListener('click', fetchAndRenderStats);

    // Backdrop Click Closes Modals
    window.addEventListener('click', (e) => {
      if (e.target === configModal) closeConfigModal();
      if (e.target === statsModal) closeStatsModal();
    });
  }

  // --- Bootstrap ---
  function init() {
    updateSessionDisplay();
    updateBackendLabel();
    renderHistory();
    initEvents();
    refreshHealthStatus();
    // Periodic health polling every 30s
    setInterval(refreshHealthStatus, 30000);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
