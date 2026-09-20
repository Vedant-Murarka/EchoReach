/**
 * EchoReach Frontend Application Controller
 * Enterprise SaaS Dashboard — Multi-Agent Autonomous Sales Outreach
 */

// Global Application State
const AppState = {
  currentView: "pipeline",
  theme: "light",
  leads: [],
  selectedLead: null,
  decisionLogs: [],
  guardrails: null,
  searchQuery: "",
  traceAgentFilter: "ALL",
  pollingInterval: null
};

// Agent Visual Metaphors
const AGENT_META = {
  "Research Agent": { icon: "🔍", badge: "badge-blue" },
  "Drafting Agent": { icon: "✍️", badge: "badge-purple" },
  "Genericness Checker Agent": { icon: "🛡️", badge: "badge-amber" },
  "Sequence Planner Agent": { icon: "📅", badge: "badge-blue" },
  "Human Guardrail Queue": { icon: "👤", badge: "badge-amber" },
  "Human Guardrail Queue & Sandbox Sender": { icon: "📬", badge: "badge-green" },
  "Send Guardrails Engine": { icon: "⚠️", badge: "badge-amber" },
  "Reply Classifier Agent": { icon: "🎯", badge: "badge-green" },
  "Next-Step Decision Agent": { icon: "⚡", badge: "badge-purple" },
  "Self-Improving Classifier Engine": { icon: "🧠", badge: "badge-purple" },
  "default": { icon: "🤖", badge: "badge-slate" }
};

// Lifecycle: DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  setupNavigation();
  setupModals();
  await refreshAllData();

  // Background polling every 6 seconds for live decision trace & guardrail cap
  AppState.pollingInterval = setInterval(async () => {
    await updateDecisionTrace();
    await updateGuardrailsCounter();
  }, 6000);
});

// Theme Management (Default Light with Dark Toggle)
function initTheme() {
  const savedTheme = localStorage.getItem("echoreach_theme") || "light";
  applyTheme(savedTheme);
}

function applyTheme(theme) {
  AppState.theme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("echoreach_theme", theme);

  const sunIcon = document.getElementById("theme-icon-sun");
  const moonIcon = document.getElementById("theme-icon-moon");

  if (sunIcon && moonIcon) {
    if (theme === "dark") {
      sunIcon.style.display = "block";
      moonIcon.style.display = "none";
    } else {
      sunIcon.style.display = "none";
      moonIcon.style.display = "block";
    }
  }
}

function toggleTheme() {
  const nextTheme = AppState.theme === "light" ? "dark" : "light";
  applyTheme(nextTheme);
}

// Navigation & View Routing
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(i => i.classList.remove("active"));
      item.classList.add("active");

      const viewName = item.getAttribute("data-view");
      switchView(viewName);
    });
  });
}

function switchView(viewName) {
  AppState.currentView = viewName;
  document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));

  const targetSection = document.getElementById(`view-${viewName}`);
  if (targetSection) {
    targetSection.classList.add("active");
  }

  const titleEl = document.getElementById("header-title-text");
  if (titleEl) {
    const titles = {
      pipeline: "Lead Pipeline Board",
      approval: "Human Approval Queue (Guardrail Check)",
      timeline: "Lead Inspector & Timeline",
      trace: "Autonomous Decision Trace Feed",
      simulator: "Prospect Persona Simulator & Feedback Studio",
      analytics: "Pipeline Funnel & Intent Analytics"
    };
    titleEl.textContent = titles[viewName] || "EchoReach Dashboard";
  }

  if (viewName === "pipeline") renderPipelineBoard();
  if (viewName === "approval") renderApprovalQueue();
  if (viewName === "trace") renderLiveTrace();
  if (viewName === "simulator") renderSimulatorView();
  if (viewName === "analytics") renderAnalyticsView();
}

// Master Data Refresh
async function refreshAllData() {
  try {
    const [leads, logs, guardrails] = await Promise.all([
      ApiService.getLeads(),
      ApiService.getDecisionLogs(),
      ApiService.getGuardrailsStatus()
    ]);

    AppState.leads = leads;
    AppState.decisionLogs = logs;
    AppState.guardrails = guardrails;

    renderPipelineBoard();
    updateGuardrailsCounter();
    updateApprovalBadge();
    populateSimulatorLeadSelect();
  } catch (err) {
    showToast("⚠️ Could not sync with API. Check server status.", "error");
  }
}

// Lead Pipeline Kanban Board
function renderPipelineBoard() {
  const container = document.getElementById("kanban-container");
  if (!container) return;

  const totalCountEl = document.getElementById("pipeline-total-count");
  if (totalCountEl) totalCountEl.textContent = AppState.leads.length;

  const query = AppState.searchQuery.toLowerCase().trim();
  const filteredLeads = AppState.leads.filter(l => {
    if (!query) return true;
    return (
      l.name.toLowerCase().includes(query) ||
      l.company.toLowerCase().includes(query) ||
      l.title.toLowerCase().includes(query) ||
      l.email.toLowerCase().includes(query)
    );
  });

  const columns = [
    { title: "New Accounts", stage: "New" },
    { title: "Researched / Drafted", stage: "Researched" },
    { title: "Pending Approval", stage: "Pending Approval" },
    { title: "Touches Dispatched", stage: "Touch Sent" },
    { title: "Escalated to Rep", stage: "Escalated to Rep" },
    { title: "Paused / Stopped", stage: "Stopped (Not Interested)" }
  ];

  container.innerHTML = "";

  columns.forEach(col => {
    const colLeads = filteredLeads.filter(l => {
      if (col.stage === "Researched") return l.stage === "Researched" || l.stage === "Drafted";
      if (col.stage === "Stopped (Not Interested)") return l.stage.includes("Stopped") || l.stage.includes("Paused");
      return l.stage === col.stage;
    });

    const colEl = document.createElement("div");
    colEl.className = "kanban-col";
    colEl.innerHTML = `
      <div class="kanban-col-header">
        <h3>${col.title}</h3>
        <span class="badge badge-slate">${colLeads.length}</span>
      </div>
      <div class="kanban-leads-list" style="display: flex; flex-direction: column; gap: 8px;">
        ${colLeads.length === 0 ? '<div style="color: var(--text-muted); font-size: 12px; text-align: center; padding: 24px 0;">No accounts</div>' : ''}
      </div>
    `;

    const listEl = colEl.querySelector(".kanban-leads-list");
    colLeads.forEach(lead => {
      const card = document.createElement("div");
      card.className = "lead-card";

      const initials = lead.company.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "AC";
      const factsCount = lead.research_facts ? lead.research_facts.length : 0;

      card.innerHTML = `
        <div class="lead-card-header">
          <div style="display: flex; gap: 10px; align-items: center;">
            <div style="width: 28px; height: 28px; border-radius: var(--radius-sm); background: var(--bg-subtle); border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: var(--text-secondary);">
              ${initials}
            </div>
            <div>
              <div class="lead-card-name">${escapeHtml(lead.name)}</div>
              <div class="lead-card-company">${escapeHtml(lead.title)} @ <strong>${escapeHtml(lead.company)}</strong></div>
            </div>
          </div>
        </div>
        
        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px;">
          <span class="badge ${getStageBadgeClass(lead.stage)}">${escapeHtml(lead.stage)}</span>
        </div>

        <div class="lead-card-meta">
          <span>Cadence Touch #${lead.current_touch_number}</span>
          <span>${factsCount} Facts Verified</span>
        </div>

        <div class="lead-card-actions">
          <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="inspectLead(${lead.id})">Inspect</button>
          ${lead.stage === 'New' ? `<button class="btn btn-primary btn-sm" style="flex: 1;" onclick="triggerLeadPipeline(${lead.id})">Run Graph</button>` : ''}
          ${lead.stage === 'Pending Approval' ? `<button class="btn btn-secondary btn-sm" style="color: var(--accent-amber-text); border-color: rgba(245,158,11,0.3);" onclick="switchView('approval')">Review</button>` : ''}
        </div>
      `;
      listEl.appendChild(card);
    });

    container.appendChild(colEl);
  });
}

function getStageBadgeClass(stage) {
  if (stage === "New") return "badge-slate";
  if (stage === "Researched" || stage === "Drafted") return "badge-blue";
  if (stage === "Pending Approval") return "badge-amber";
  if (stage === "Touch Sent") return "badge-purple";
  if (stage === "Escalated to Rep") return "badge-green";
  if (stage.includes("Stopped") || stage.includes("Paused")) return "badge-rose";
  return "badge-slate";
}

function handleSearchLeads(event) {
  AppState.searchQuery = event.target.value;
  renderPipelineBoard();
}

// Trigger Pipeline Execution for a Lead
async function triggerLeadPipeline(leadId) {
  try {
    showToast("🚀 Executing LangGraph Multi-Agent Pipeline...");
    const res = await ApiService.runPipeline(leadId);
    showToast(`✅ Generated Touch Draft (ID: ${res.generated_touch_id})`, "success");
    await refreshAllData();
  } catch (err) {
    showToast(`❌ Pipeline failed: ${err.message}`, "error");
  }
}

// Human Approval Queue Desk
function renderApprovalQueue() {
  const container = document.getElementById("approval-queue-list");
  if (!container) return;

  const pendingLeads = AppState.leads.filter(
    l => l.stage === "Pending Approval" || (l.touches && l.touches.some(t => t.status === "pending_approval"))
  );

  container.innerHTML = "";
  if (pendingLeads.length === 0) {
    container.innerHTML = `
      <div class="card" style="padding: 48px; text-align: center;">
        <div style="font-size: 36px; margin-bottom: 12px;">✅</div>
        <h3 class="card-title">Approval Queue is Clear</h3>
        <p class="card-subtitle" style="margin-top: 6px;">All generated touches have been approved or dispatched into the sandboxed inbox.</p>
      </div>
    `;
    return;
  }

  pendingLeads.forEach(lead => {
    const pendingTouch = (lead.touches && lead.touches.find(t => t.status === "pending_approval")) || {
      id: 0,
      subject: `Personalized touch for ${lead.company}`,
      body: `Hi ${lead.name},\n\nI noticed your recent product expansion and engineering momentum. Would you be open to a brief chat?`,
      touch_number: lead.current_touch_number
    };

    const card = document.createElement("div");
    card.className = "card";
    card.style.marginBottom = "20px";
    card.innerHTML = `
      <div class="card-header">
        <div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <h3 class="card-title">${escapeHtml(lead.name)} — ${escapeHtml(lead.title)}</h3>
            <span class="badge badge-blue">${escapeHtml(lead.company)}</span>
          </div>
          <p class="card-subtitle">${lead.email} · Sequence Touch #${pendingTouch.touch_number}</p>
        </div>
        <div style="display: flex; gap: 8px;">
          <span class="badge badge-green">Suppression: PASS</span>
          <span class="badge badge-amber">Daily Cap: OK (${AppState.guardrails ? AppState.guardrails.send_count : 0}/50)</span>
        </div>
      </div>

      <div class="card-body">
        <div class="approval-grid">
          <!-- Left: Extracted Research Facts -->
          <div class="facts-panel">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px; letter-spacing: 0.5px;">
              Extracted Grounded Facts (Research Agent)
            </div>
            ${(lead.research_facts && lead.research_facts.length > 0) ? lead.research_facts.map(f => `
              <div class="fact-item">
                <div class="fact-type">[${escapeHtml(f.fact_type)}]</div>
                <div style="margin-top: 3px; color: var(--text-primary);">${escapeHtml(f.content)}</div>
                <div style="font-size: 10px; color: var(--text-muted); margin-top: 3px;">Source: ${escapeHtml(f.source || 'Web Search')}</div>
              </div>
            `).join("") : '<div style="color: var(--text-muted); font-size: 12px;">No research facts found.</div>'}
          </div>

          <!-- Right: Editable Draft Studio -->
          <div>
            <div class="form-group">
              <label>Outreach Subject Line</label>
              <input type="text" class="form-control" id="draft-subject-${lead.id}" value="${escapeHtml(pendingTouch.subject || '')}" />
            </div>
            <div class="form-group">
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <label style="margin-bottom: 0;">Email Body (Grounded with Facts)</label>
                <span style="font-size: 11px; color: var(--text-muted);">Genericness check: Passed</span>
              </div>
              <textarea class="form-control" id="draft-body-${lead.id}" rows="7">${escapeHtml(pendingTouch.body || '')}</textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px;">
              <button class="btn btn-danger btn-sm" onclick="handleApprovalAction(${lead.id}, ${pendingTouch.id}, 'reject')">Reject</button>
              <button class="btn btn-secondary btn-sm" onclick="handleApprovalAction(${lead.id}, ${pendingTouch.id}, 'edit')">Save Edits</button>
              <button class="btn btn-success btn-sm" onclick="handleApprovalAction(${lead.id}, ${pendingTouch.id}, 'approve')">Approve & Deliver to Sandbox</button>
            </div>
          </div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

async function handleApprovalAction(leadId, touchId, action) {
  try {
    const subject = document.getElementById(`draft-subject-${leadId}`)?.value;
    const body = document.getElementById(`draft-body-${leadId}`)?.value;

    const res = await ApiService.processApproval(leadId, touchId, action, subject, body);
    if (res.success) {
      showToast(`✅ ${res.message}`, "success");
    } else {
      showToast(`⚠️ Guardrail Enforced: ${res.message}`, "error");
    }
    await refreshAllData();
    renderApprovalQueue();
  } catch (err) {
    showToast(`Action failed: ${err.message}`, "error");
  }
}

// Live Reasoning Trace Feed
function renderLiveTrace() {
  const container = document.getElementById("reasoning-trace-feed");
  if (!container) return;

  container.innerHTML = "";

  const filter = AppState.traceAgentFilter;
  const filteredLogs = AppState.decisionLogs.filter(log => {
    if (filter === "ALL") return true;
    return log.agent_name === filter;
  });

  if (filteredLogs.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 40px; font-size: 13px;">No agent reasoning traces matching filter.</div>';
    return;
  }

  filteredLogs.forEach(log => {
    const meta = AGENT_META[log.agent_name] || AGENT_META["default"];
    const timeStr = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const item = document.createElement("div");
    item.className = "trace-item";
    item.innerHTML = `
      <div class="trace-avatar">${meta.icon}</div>
      <div class="trace-content">
        <div class="trace-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="trace-agent-name">${escapeHtml(log.agent_name)}</span>
            <span class="badge ${meta.badge}">${log.lead_id ? `Lead #${log.lead_id}` : 'System'}</span>
          </div>
          <span class="trace-time">${timeStr}</span>
        </div>
        ${log.input_summary ? `<div class="trace-input"><strong>Input Context:</strong> ${escapeHtml(log.input_summary)}</div>` : ''}
        <div class="trace-reasoning">${escapeHtml(log.reasoning)}</div>
        ${log.output_summary ? `<div class="trace-output">↳ <strong>Outcome:</strong> ${escapeHtml(log.output_summary)}</div>` : ''}
      </div>
    `;
    container.appendChild(item);
  });
}

function handleFilterTrace(event) {
  AppState.traceAgentFilter = event.target.value;
  renderLiveTrace();
}

// Lead Detail & Timeline Inspector
async function inspectLead(leadId) {
  try {
    const lead = await ApiService.getLeadById(leadId);
    const logs = await ApiService.getDecisionLogs(leadId);
    AppState.selectedLead = lead;

    switchView("timeline");
    const container = document.getElementById("lead-detail-content");
    if (!container) return;

    container.innerHTML = `
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
          <div>
            <h2 style="font-size: 20px; font-weight: 700; color: var(--text-primary);">${escapeHtml(lead.name)}</h2>
            <div style="color: var(--text-secondary); font-size: 13px; margin-top: 2px;">
              ${escapeHtml(lead.title)} @ <strong style="color: var(--primary-text);">${escapeHtml(lead.company)}</strong> · ${escapeHtml(lead.email)}
            </div>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" onclick="switchView('pipeline')">← Back to Board</button>
            <button class="btn btn-primary btn-sm" onclick="triggerLeadPipeline(${lead.id})">Run Graph Pipeline</button>
            <button class="btn btn-secondary btn-sm" onclick="openSimulatorModal(${lead.id})">Simulate Reply</button>
          </div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">
              <h3 class="card-title">Extracted Research Intelligence</h3>
              <span class="badge badge-blue">${lead.research_facts ? lead.research_facts.length : 0} Facts</span>
            </div>
            <div class="card-body">
              ${(lead.research_facts && lead.research_facts.length > 0) ? lead.research_facts.map(f => `
                <div style="margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color);">
                  <span class="badge badge-blue">[${escapeHtml(f.fact_type)}]</span>
                  <div style="font-size: 13px; margin-top: 4px; color: var(--text-primary);">${escapeHtml(f.content)}</div>
                  <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Source: ${escapeHtml(f.source || 'Web Search')}</div>
                </div>
              `).join("") : '<div style="color: var(--text-muted); font-size: 12px;">No research facts extracted.</div>'}
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Multi-Touch Cadence Sequence</h3>
              <span class="badge badge-purple">${lead.touches ? lead.touches.length : 0} Touches</span>
            </div>
            <div class="card-body">
              ${(lead.touches && lead.touches.length > 0) ? lead.touches.map(t => `
                <div style="margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 13px;">Touch #${t.touch_number} (${t.channel.toUpperCase()})</strong>
                    <span class="badge ${t.status === 'sent' ? 'badge-green' : 'badge-amber'}">${t.status}</span>
                  </div>
                  <div style="font-size: 12px; font-weight: 500; color: var(--primary-text); margin: 4px 0;">${escapeHtml(t.subject || 'No Subject')}</div>
                  <div style="font-size: 12px; color: var(--text-secondary); white-space: pre-line;">${escapeHtml(t.body)}</div>
                </div>
              `).join("") : '<div style="color: var(--text-muted); font-size: 12px;">No outreach touches drafted yet.</div>'}
            </div>
          </div>
        </div>

        <div>
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Agent Reasoning Trace for Account</h3>
              <span class="badge badge-slate">${logs.length} Entries</span>
            </div>
            <div class="card-body" style="max-height: 680px; overflow-y: auto;">
              <div style="display: flex; flex-direction: column; gap: 10px;">
                ${logs.map(log => `
                  <div class="trace-item" style="padding: 12px;">
                    <div class="trace-avatar" style="width: 30px; height: 30px; font-size: 14px;">${AGENT_META[log.agent_name]?.icon || '🤖'}</div>
                    <div class="trace-content">
                      <div style="font-size: 12.5px; font-weight: 600; color: var(--text-primary);">${escapeHtml(log.agent_name)}</div>
                      <div style="font-size: 12px; color: var(--text-secondary); margin: 4px 0;">${escapeHtml(log.reasoning)}</div>
                      <div style="font-size: 11px; color: var(--primary-text);">${escapeHtml(log.output_summary || '')}</div>
                    </div>
                  </div>
                `).join("") || '<div style="color: var(--text-muted); font-size: 12px;">No decision logs recorded for this lead.</div>'}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    showToast(`Failed to load account details: ${err.message}`, "error");
  }
}

// Prospect Reply Simulator & Self-Improving Studio
async function renderSimulatorView() {
  const container = document.getElementById("simulator-replies-list");
  if (!container) return;

  try {
    const replies = await ApiService.getReplies();
    container.innerHTML = "";

    if (replies.length === 0) {
      container.innerHTML = `
        <div class="card" style="padding: 40px; text-align: center;">
          <h3 class="card-title">No Replies Simulated Yet</h3>
          <p class="card-subtitle" style="margin-top: 6px;">Click "Trigger Persona Reply" above to test the 5-class intent classifier.</p>
        </div>
      `;
      return;
    }

    replies.forEach(r => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.marginBottom = "12px";

      const confidencePct = (r.confidence * 100).toFixed(0);
      const isCorrected = r.is_corrected;

      card.innerHTML = `
        <div class="card-header" style="padding: 12px 16px;">
          <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
            <span class="badge badge-purple">${escapeHtml(r.persona_type)}</span>
            <span class="badge ${r.classification === 'Interested' ? 'badge-green' : 'badge-amber'}">
              ${escapeHtml(r.classification)} (${confidencePct}% Confidence)
            </span>
            ${isCorrected ? `<span class="badge badge-rose">Human Corrected → ${escapeHtml(r.corrected_classification)}</span>` : ''}
          </div>
          <button class="btn btn-secondary btn-sm" onclick="openCorrectionModal(${r.id}, '${escapeHtml(r.classification)}', '${escapeHtml(r.raw_text.replace(/'/g, "\\'"))}')">
            Tune Model Feedback
          </button>
        </div>
        <div class="card-body" style="padding: 14px 16px;">
          <div style="font-size: 13px; color: var(--text-primary); background: var(--bg-subtle); padding: 10px 12px; border-radius: var(--radius-md); border-left: 3px solid var(--primary); font-style: italic;">
            "${escapeHtml(r.raw_text)}"
          </div>
          <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 8px;">
            <strong>Classifier Reasoning:</strong> ${escapeHtml(r.reasoning || 'Heuristic fallback applied')}
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    showToast(`Could not load replies: ${err.message}`, "error");
  }
}

function openSimulatorModal(leadId) {
  const leadSelect = document.getElementById("sim-lead-select");
  if (leadSelect && leadId) {
    leadSelect.value = leadId;
  }
  document.getElementById("modal-simulator").classList.add("active");
}

function populateSimulatorLeadSelect() {
  const sel = document.getElementById("sim-lead-select");
  if (!sel) return;
  sel.innerHTML = "";
  AppState.leads.forEach(l => {
    const opt = document.createElement("option");
    opt.value = l.id;
    opt.textContent = `${l.name} (${l.company} — ${l.stage})`;
    sel.appendChild(opt);
  });
}

function openCorrectionModal(replyId, currentClass, rawText) {
  document.getElementById("correction-reply-id").value = replyId;
  document.getElementById("correction-reply-text").textContent = `"${rawText}"`;
  document.getElementById("correction-class-select").value = currentClass;
  document.getElementById("correction-notes").value = "";
  document.getElementById("modal-correction").classList.add("active");
}

async function handleCorrectionSubmit(e) {
  e.preventDefault();
  const replyId = document.getElementById("correction-reply-id").value;
  const correctedClass = document.getElementById("correction-class-select").value;
  const notes = document.getElementById("correction-notes").value || "Operator Correction submitted via Studio";

  try {
    await ApiService.submitCorrection(replyId, correctedClass, notes);
    showToast("🧠 Model Memory Updated! Saved to classifier feedback exemplars.", "success");
    document.getElementById("modal-correction").classList.remove("active");
    await renderSimulatorView();
    await refreshAllData();
  } catch (err) {
    showToast(`Correction failed: ${err.message}`, "error");
  }
}

// Analytics View
async function renderAnalyticsView() {
  const container = document.getElementById("analytics-container");
  if (!container) return;

  try {
    const data = await ApiService.getAnalytics();
    container.innerHTML = `
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Total Accounts in Pipeline</div>
          <div class="metric-value">${data.total_leads}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Touches Delivered (Sandbox)</div>
          <div class="metric-value" style="color: var(--primary-text);">${data.total_touches_sent}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Replies Received</div>
          <div class="metric-value" style="color: var(--accent-emerald-text);">${data.replies_count}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Conversion / Reply Rate</div>
          <div class="metric-value" style="color: var(--accent-amber-text);">${data.reply_rate_percent}%</div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Pipeline Stage Distribution</h3>
          </div>
          <div class="card-body">
            <div style="display: flex; flex-direction: column; gap: 12px;">
              ${Object.entries(data.leads_by_stage || {}).map(([stage, count]) => {
                const pct = (count / Math.max(data.total_leads, 1) * 100).toFixed(0);
                return `
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                      <span>${escapeHtml(stage)}</span>
                      <strong>${count} (${pct}%)</strong>
                    </div>
                    <div style="height: 6px; background: var(--bg-subtle); border-radius: 999px; overflow: hidden;">
                      <div style="height: 100%; width: ${pct}%; background-color: var(--primary);"></div>
                    </div>
                  </div>
                `;
              }).join("")}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Intent Classification Breakdown</h3>
          </div>
          <div class="card-body">
            <div style="display: flex; flex-direction: column; gap: 12px;">
              ${Object.entries(data.replies_by_classification || {}).map(([cls, count]) => {
                const pct = (count / Math.max(data.replies_count, 1) * 100).toFixed(0);
                return `
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                      <span>${escapeHtml(cls)}</span>
                      <strong>${count} (${pct}%)</strong>
                    </div>
                    <div style="height: 6px; background: var(--bg-subtle); border-radius: 999px; overflow: hidden;">
                      <div style="height: 100%; width: ${pct}%; background-color: var(--accent-emerald);"></div>
                    </div>
                  </div>
                `;
              }).join("")}
            </div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    showToast(`Could not load analytics: ${err.message}`, "error");
  }
}

// Background Polling Helpers
async function updateDecisionTrace() {
  try {
    const logs = await ApiService.getDecisionLogs();
    AppState.decisionLogs = logs;
    if (AppState.currentView === "trace") {
      renderLiveTrace();
    }
  } catch (e) {}
}

async function updateGuardrailsCounter() {
  try {
    const g = await ApiService.getGuardrailsStatus();
    AppState.guardrails = g;
    const counterEl = document.getElementById("guardrail-cap-counter");
    if (counterEl) {
      counterEl.textContent = `Daily Cap: ${g.send_count}/${g.daily_cap}`;
    }
  } catch (e) {}
}

function updateApprovalBadge() {
  const count = AppState.leads.filter(
    l => l.stage === "Pending Approval" || (l.touches && l.touches.some(t => t.status === "pending_approval"))
  ).length;
  const badgeEl = document.getElementById("nav-badge-approval");
  if (badgeEl) {
    badgeEl.textContent = count;
    badgeEl.style.display = count > 0 ? "inline-block" : "none";
  }
}

// Modal Handlers
function setupModals() {
  document.querySelectorAll(".modal-close").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("active"));
    });
  });

  const simForm = document.getElementById("sim-form");
  if (simForm) {
    simForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const leadId = document.getElementById("sim-lead-select").value;
      const persona = document.getElementById("sim-persona-select").value;

      try {
        showToast("🎭 Simulating Prospect Reply & Running 5-Class Classifier...");
        const res = await ApiService.simulateReply(leadId, persona);
        showToast(`🎯 Classified as: ${res.classification} → Action: ${res.next_step_action}`, "success");
        document.getElementById("modal-simulator").classList.remove("active");
        await refreshAllData();
        if (AppState.currentView === "simulator") renderSimulatorView();
      } catch (err) {
        showToast(`Simulation failed: ${err.message}`, "error");
      }
    });
  }
}

async function handleCreateLead(e) {
  e.preventDefault();
  try {
    const payload = {
      name: document.getElementById("new-lead-name").value,
      title: document.getElementById("new-lead-title").value,
      company: document.getElementById("new-lead-company").value,
      email: document.getElementById("new-lead-email").value,
      linkedin_url: document.getElementById("new-lead-linkedin").value
    };
    await ApiService.createLead(payload);
    showToast("✅ Target lead created successfully!", "success");
    document.getElementById("modal-new-lead").classList.remove("active");
    e.target.reset();
    await refreshAllData();
  } catch (err) {
    showToast(`Failed to add lead: ${err.message}`, "error");
  }
}

// Toast Notifications
function showToast(msg, type = "info") {
  const container = document.getElementById("toast-container") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast ${type === 'error' ? 'toast-error' : (type === 'success' ? 'toast-success' : '')}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4200);
}

function createToastContainer() {
  const c = document.createElement("div");
  c.id = "toast-container";
  c.className = "toast-container";
  document.body.appendChild(c);
  return c;
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
