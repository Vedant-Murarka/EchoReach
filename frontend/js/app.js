/**
 * EchoReach Frontend Application Controller
 * Handles UI state, live polling, modal workflows, and view rendering.
 */

// Global App State
const AppState = {
  currentView: "pipeline",
  leads: [],
  selectedLead: null,
  decisionLogs: [],
  guardrails: null,
  pollingInterval: null
};

// Agent Avatars Map
const AGENT_AVATARS = {
  "Research Agent": "🔍",
  "Drafting Agent": "✍️",
  "Genericness Checker Agent": "🛡️",
  "Human Guardrail Queue": "👤",
  "Human Guardrail Queue & Sandbox Sender": "📬",
  "Send Guardrails Engine": "⚠️",
  "Reply Classifier Agent": "🎯",
  "Next-Step Decision Agent": "⚡",
  "Self-Improving Classifier Engine": "🧠",
  "default": "🤖"
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  setupNavigation();
  setupModals();
  await refreshAllData();

  // Start background live polling every 5s for reasoning trace & guardrails
  AppState.pollingInterval = setInterval(async () => {
    await updateDecisionTrace();
    await updateGuardrailsCounter();
  }, 5000);
});

// Setup Tab Navigation
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
      approval: "Human Approval Queue (Guardrails)",
      timeline: "Lead Inspector & Timeline",
      trace: "Live Reasoning Trace Feed",
      simulator: "Prospect Reply Simulator & Self-Learning",
      analytics: "Pipeline Funnel & Analytics"
    };
    titleEl.textContent = titles[viewName] || "EchoReach Dashboard";
  }

  // View-specific refreshes
  if (viewName === "approval") renderApprovalQueue();
  if (viewName === "trace") renderLiveTrace();
  if (viewName === "simulator") renderSimulatorView();
  if (viewName === "analytics") renderAnalyticsView();
}

// Refresh Data from Backend
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
  } catch (err) {
    showToast("⚠️ API Connection Offline. Ensure backend is running.", "error");
  }
}

// Render Pipeline Board (Kanban Columns)
function renderPipelineBoard() {
  const container = document.getElementById("kanban-container");
  if (!container) return;

  const columns = [
    { title: "New Leads", stage: "New" },
    { title: "Researched / Drafted", stage: "Researched" },
    { title: "Pending Approval", stage: "Pending Approval" },
    { title: "Touch Sent", stage: "Touch Sent" },
    { title: "Escalated to Rep", stage: "Escalated to Rep" },
    { title: "Paused / Stopped", stage: "Stopped (Not Interested)" }
  ];

  container.innerHTML = "";

  columns.forEach(col => {
    const colLeads = AppState.leads.filter(l => {
      if (col.stage === "Researched") return l.stage === "Researched" || l.stage === "Drafted";
      if (col.stage === "Stopped (Not Interested)") return l.stage.includes("Stopped") || l.stage.includes("Paused");
      return l.stage === col.stage;
    });

    const colEl = document.createElement("div");
    colEl.className = "kanban-col glass";
    colEl.innerHTML = `
      <div class="kanban-col-header">
        <h3>${col.title}</h3>
        <span class="badge badge-blue">${colLeads.length}</span>
      </div>
      <div class="kanban-leads-list" style="display: flex; flex-direction: column; gap: 10px;">
        ${colLeads.length === 0 ? '<div style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 20px 0;">No leads</div>' : ''}
      </div>
    `;

    const listEl = colEl.querySelector(".kanban-leads-list");
    colLeads.forEach(lead => {
      const card = document.createElement("div");
      card.className = "lead-card";
      card.innerHTML = `
        <div class="lead-card-header">
          <div>
            <div class="lead-card-name">${lead.name}</div>
            <div class="lead-card-company">${lead.title} @ ${lead.company}</div>
          </div>
          <span class="badge ${getStageBadgeClass(lead.stage)}">${lead.stage}</span>
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 6px; display: flex; justify-content: space-between;">
          <span>Touch #${lead.current_touch_number}</span>
          <span>${lead.research_facts ? lead.research_facts.length : 0} Facts</span>
        </div>
        <div style="margin-top: 10px; display: flex; gap: 6px;">
          <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="inspectLead(${lead.id})">Inspect</button>
          ${lead.stage === 'New' ? `<button class="btn btn-primary" style="padding: 4px 8px; font-size: 11px;" onclick="triggerLeadPipeline(${lead.id})">Run Graph</button>` : ''}
        </div>
      `;
      listEl.appendChild(card);
    });

    container.appendChild(colEl);
  });
}

function getStageBadgeClass(stage) {
  if (stage === "New") return "badge-blue";
  if (stage === "Pending Approval") return "badge-amber";
  if (stage === "Touch Sent") return "badge-purple";
  if (stage === "Escalated to Rep") return "badge-green";
  if (stage.includes("Stopped")) return "badge-rose";
  return "badge-blue";
}

// Trigger Pipeline execution for a Lead
async function triggerLeadPipeline(leadId) {
  try {
    showToast("🚀 Executing LangGraph Multi-Agent Pipeline...");
    const res = await ApiService.runPipeline(leadId);
    showToast(`✅ Generated Touch Draft (ID: ${res.generated_touch_id})`);
    await refreshAllData();
  } catch (err) {
    showToast(`❌ Pipeline failed: ${err.message}`, "error");
  }
}

// Render Human Approval Queue View
function renderApprovalQueue() {
  const container = document.getElementById("approval-queue-list");
  if (!container) return;

  const pendingLeads = AppState.leads.filter(l => l.stage === "Pending Approval" || (l.touches && l.touches.some(t => t.status === "pending_approval")));

  container.innerHTML = "";
  if (pendingLeads.length === 0) {
    container.innerHTML = `
      <div class="glass-card" style="padding: 40px; text-align: center; color: var(--text-secondary);">
        <div style="font-size: 32px; margin-bottom: 12px;">🎉</div>
        <h3>Approval Queue is Clear!</h3>
        <p style="font-size: 13px; color: var(--text-muted); margin-top: 6px;">All generated touches have been reviewed or sent to sandbox inbox.</p>
      </div>
    `;
    return;
  }

  pendingLeads.forEach(lead => {
    const pendingTouch = (lead.touches && lead.touches.find(t => t.status === "pending_approval")) || {
      id: 0,
      subject: `Personalized touch for ${lead.company}`,
      body: `Hi ${lead.name},\n\nI noticed your recent expansion and hiring growth. Would you be open to a quick demo?`,
      touch_number: lead.current_touch_number
    };

    const card = document.createElement("div");
    card.className = "glass-card";
    card.style.padding = "24px";
    card.style.marginBottom = "20px";
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
        <div>
          <h3 style="font-size: 18px; font-weight: 600;">${lead.name} — ${lead.title} @ <span style="color: var(--accent-blue);">${lead.company}</span></h3>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Email: ${lead.email} | Touch #${pendingTouch.touch_number} (Cadence)</div>
        </div>
        <div style="display: flex; gap: 8px;">
          <span class="badge badge-green">Suppression Check: PASS</span>
          <span class="badge badge-amber">Daily Cap: OK (${AppState.guardrails ? AppState.guardrails.send_count : 0}/50)</span>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px;">
        <!-- Extracted Research Facts -->
        <div style="background: rgba(0,0,0,0.25); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px;">Inline Research Facts Extracted:</div>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${(lead.research_facts || []).map(f => `
              <div style="font-size: 12px; background: rgba(59, 130, 246, 0.08); padding: 8px; border-radius: 6px; border-left: 3px solid var(--accent-blue);">
                <span style="font-weight: 600; color: var(--accent-blue); text-transform: uppercase; font-size: 10px;">[${f.fact_type}]</span>
                <div style="margin-top: 3px; color: #e5e7eb;">${f.content}</div>
              </div>
            `).join("") || '<div style="color: var(--text-muted); font-size: 12px;">No research facts found</div>'}
          </div>
        </div>

        <!-- Generated Draft with Review Actions -->
        <div>
          <div class="form-group">
            <label>Subject Line</label>
            <input type="text" class="form-control" id="draft-subject-${lead.id}" value="${pendingTouch.subject || ''}" />
          </div>
          <div class="form-group">
            <label>Email Body (Incorporating $\\ge 2$ Facts)</label>
            <textarea class="form-control" id="draft-body-${lead.id}" rows="6">${pendingTouch.body || ''}</textarea>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px;">
            <button class="btn btn-danger" onclick="handleApprovalAction(${lead.id}, ${pendingTouch.id}, 'reject')">Reject</button>
            <button class="btn btn-secondary" onclick="handleApprovalAction(${lead.id}, ${pendingTouch.id}, 'edit')">Save Edits</button>
            <button class="btn btn-success" onclick="handleApprovalAction(${lead.id}, ${pendingTouch.id}, 'approve')">Approve & Deliver to Sandbox</button>
          </div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// Process Approval
async function handleApprovalAction(leadId, touchId, action) {
  try {
    const subject = document.getElementById(`draft-subject-${leadId}`)?.value;
    const body = document.getElementById(`draft-body-${leadId}`)?.value;

    const res = await ApiService.processApproval(leadId, touchId, action, subject, body);
    if (res.success) {
      showToast(`✅ ${res.message}`);
    } else {
      showToast(`⚠️ Guardrail Blocked: ${res.message}`, "error");
    }
    await refreshAllData();
    renderApprovalQueue();
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
}

// Render Live Reasoning Trace Feed
function renderLiveTrace() {
  const container = document.getElementById("reasoning-trace-feed");
  if (!container) return;

  container.innerHTML = "";
  if (AppState.decisionLogs.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 40px;">No decision logs recorded yet.</div>';
    return;
  }

  // Render chronologically
  AppState.decisionLogs.forEach(log => {
    const avatar = AGENT_AVATARS[log.agent_name] || AGENT_AVATARS["default"];
    const timeFormatted = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const item = document.createElement("div");
    item.className = "trace-item";
    item.innerHTML = `
      <div class="trace-avatar">${avatar}</div>
      <div class="trace-content">
        <div class="trace-header">
          <span class="trace-agent-name">${log.agent_name}</span>
          <span class="trace-time">${timeFormatted}</span>
        </div>
        ${log.input_summary ? `<div class="trace-input"><strong>Input:</strong> ${escapeHtml(log.input_summary)}</div>` : ''}
        <div class="trace-reasoning">${escapeHtml(log.reasoning)}</div>
        ${log.output_summary ? `<div class="trace-output">↳ <strong>Outcome:</strong> ${escapeHtml(log.output_summary)}</div>` : ''}
      </div>
    `;
    container.appendChild(item);
  });
}

// Lead Detail Inspector
async function inspectLead(leadId) {
  try {
    const lead = await ApiService.getLeadById(leadId);
    const logs = await ApiService.getDecisionLogs(leadId);
    AppState.selectedLead = lead;

    switchView("timeline");
    const container = document.getElementById("lead-detail-content");
    if (!container) return;

    container.innerHTML = `
      <div class="glass-card" style="padding: 24px; margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <h2 style="font-size: 22px; font-weight: 700;">${lead.name}</h2>
            <div style="color: var(--text-secondary); font-size: 14px; margin-top: 2px;">${lead.title} @ <strong style="color: #fff;">${lead.company}</strong></div>
            <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Email: ${lead.email} | LinkedIn: <a href="${lead.linkedin_url || '#'}" target="_blank" style="color: var(--accent-blue);">Profile</a></div>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-primary" onclick="triggerLeadPipeline(${lead.id})">Run Graph Pipeline</button>
            <button class="btn btn-secondary" onclick="openSimulatorModal(${lead.id})">Simulate Reply</button>
          </div>
        </div>
      </div>

      <!-- Two Column Detail -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
        <!-- Research Facts & Touch History -->
        <div>
          <h3 style="font-size: 16px; margin-bottom: 12px;">📊 Research Facts Extracted</h3>
          <div class="glass-card" style="padding: 16px; margin-bottom: 20px;">
            ${(lead.research_facts || []).map(f => `
              <div style="margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color);">
                <span class="badge badge-blue">[${f.fact_type}]</span>
                <div style="font-size: 13px; margin-top: 4px;">${f.content}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Source: ${f.source || 'Web'}</div>
              </div>
            `).join("") || '<div style="color: var(--text-muted);">No facts extracted.</div>'}
          </div>

          <h3 style="font-size: 16px; margin-bottom: 12px;">✉️ Multi-Touch Timeline</h3>
          <div class="glass-card" style="padding: 16px;">
            ${(lead.touches || []).map(t => `
              <div style="margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color);">
                <div style="display: flex; justify-content: space-between;">
                  <strong style="font-size: 14px;">Touch #${t.touch_number} (${t.channel.toUpperCase()})</strong>
                  <span class="badge ${t.status === 'sent' ? 'badge-green' : 'badge-amber'}">${t.status}</span>
                </div>
                <div style="font-size: 12px; color: #93c5fd; margin: 4px 0;">${t.subject || 'No Subject'}</div>
                <div style="font-size: 12px; color: var(--text-secondary); white-space: pre-line;">${t.body}</div>
              </div>
            `).join("") || '<div style="color: var(--text-muted);">No touches sent yet.</div>'}
          </div>
        </div>

        <!-- Decision Logs for this Lead -->
        <div>
          <h3 style="font-size: 16px; margin-bottom: 12px;">🧠 Agent Reasoning Trace for Lead</h3>
          <div style="display: flex; flex-direction: column; gap: 12px; max-height: 600px; overflow-y: auto;">
            ${logs.map(log => `
              <div class="trace-item" style="padding: 12px;">
                <div class="trace-avatar" style="width: 32px; height: 32px; font-size: 14px;">${AGENT_AVATARS[log.agent_name] || '🤖'}</div>
                <div class="trace-content">
                  <div style="font-size: 13px; font-weight: 600;">${log.agent_name}</div>
                  <div style="font-size: 12px; color: #e5e7eb; margin: 4px 0;">${escapeHtml(log.reasoning)}</div>
                  <div style="font-size: 11px; color: var(--accent-cyan);">${escapeHtml(log.output_summary || '')}</div>
                </div>
              </div>
            `).join("") || '<div style="color: var(--text-muted);">No decision logs yet.</div>'}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    showToast(`Failed to load lead: ${err.message}`, "error");
  }
}

// Prospect Reply Simulator Modal & Trigger
function openSimulatorModal(leadId) {
  const leadSelect = document.getElementById("sim-lead-select");
  if (leadSelect) {
    leadSelect.value = leadId;
  }
  document.getElementById("modal-simulator").classList.add("active");
}

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
        showToast(`🎯 Classified as: ${res.classification} -> Action: ${res.next_step_action}`);
        document.getElementById("modal-simulator").classList.remove("active");
        await refreshAllData();
      } catch (err) {
        showToast(`Simulation failed: ${err.message}`, "error");
      }
    });
  }
}

// Simulator & Self-Improving Studio View
async function renderSimulatorView() {
  const container = document.getElementById("simulator-replies-list");
  if (!container) return;

  const replies = await ApiService.getReplies();
  container.innerHTML = "";

  if (replies.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 40px;">No replies recorded yet. Trigger a reply above!</div>';
    return;
  }

  replies.forEach(r => {
    const card = document.createElement("div");
    card.className = "glass-card";
    card.style.padding = "16px";
    card.style.marginBottom = "14px";
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
        <div>
          <span class="badge badge-purple">${r.persona_type}</span>
          <span class="badge ${r.classification === 'Interested' ? 'badge-green' : 'badge-amber'}" style="margin-left: 6px;">${r.classification} (${(r.confidence*100).toFixed(0)}% Conf)</span>
          ${r.is_corrected ? `<span class="badge badge-rose" style="margin-left: 6px;">Corrected -> ${r.corrected_classification}</span>` : ''}
        </div>
        <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="openCorrectionModal(${r.id}, '${r.classification}')">✏️ Correct Class (Self-Improve)</button>
      </div>
      <div style="font-size: 13px; color: #f3f4f6; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; margin: 8px 0; font-style: italic;">
        "${escapeHtml(r.raw_text)}"
      </div>
      <div style="font-size: 11px; color: var(--text-muted);">Reasoning: ${escapeHtml(r.reasoning || '')}</div>
    `;
    container.appendChild(card);
  });
}

function openCorrectionModal(replyId, currentClass) {
  const newClass = prompt(`Submit Human Operator Correction for Reply #${replyId}.\nCurrent: ${currentClass}\n\nEnter new class (Interested, Objection, Out-of-Office, Not Interested, No Reply):`);
  if (!newClass) return;

  ApiService.submitCorrection(replyId, newClass.trim(), "Operator correction submitted via Studio")
    .then(res => {
      showToast("🧠 Correction saved! Injected into few-shot memory for next calls.");
      renderSimulatorView();
      refreshAllData();
    })
    .catch(err => showToast(`Error: ${err.message}`, "error"));
}

// Analytics View
async function renderAnalyticsView() {
  const container = document.getElementById("analytics-container");
  if (!container) return;

  const data = await ApiService.getAnalytics();
  container.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
      <div class="glass-card" style="padding: 20px;">
        <div style="font-size: 12px; color: var(--text-muted); text-transform: uppercase;">Total Leads in Pipeline</div>
        <div style="font-size: 32px; font-weight: 700; color: var(--accent-blue); margin-top: 4px;">${data.total_leads}</div>
      </div>
      <div class="glass-card" style="padding: 20px;">
        <div style="font-size: 12px; color: var(--text-muted); text-transform: uppercase;">Touches Delivered (Sandbox)</div>
        <div style="font-size: 32px; font-weight: 700; color: var(--accent-indigo); margin-top: 4px;">${data.total_touches_sent}</div>
      </div>
      <div class="glass-card" style="padding: 20px;">
        <div style="font-size: 12px; color: var(--text-muted); text-transform: uppercase;">Total Replies Received</div>
        <div style="font-size: 32px; font-weight: 700; color: var(--accent-emerald); margin-top: 4px;">${data.replies_count}</div>
      </div>
      <div class="glass-card" style="padding: 20px;">
        <div style="font-size: 12px; color: var(--text-muted); text-transform: uppercase;">Reply Rate</div>
        <div style="font-size: 32px; font-weight: 700; color: var(--accent-amber); margin-top: 4px;">${data.reply_rate_percent}%</div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div class="glass-card" style="padding: 20px;">
        <h3 style="font-size: 16px; margin-bottom: 14px;">📈 Pipeline Funnel by Stage</h3>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          ${Object.entries(data.leads_by_stage || {}).map(([stage, count]) => `
            <div>
              <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                <span>${stage}</span>
                <strong>${count}</strong>
              </div>
              <div style="height: 8px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden;">
                <div style="height: 100%; width: ${(count / Math.max(data.total_leads, 1) * 100)}%; background: linear-gradient(90deg, var(--accent-blue), var(--accent-indigo));"></div>
              </div>
            </div>
          `).join("")}
        </div>
      </div>

      <div class="glass-card" style="padding: 20px;">
        <h3 style="font-size: 16px; margin-bottom: 14px;">🎯 Reply Intent Classification Breakdown</h3>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          ${Object.entries(data.replies_by_classification || {}).map(([cls, count]) => `
            <div>
              <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                <span>${cls}</span>
                <strong>${count}</strong>
              </div>
              <div style="height: 8px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden;">
                <div style="height: 100%; width: ${(count / Math.max(data.replies_count, 1) * 100)}%; background: linear-gradient(90deg, var(--accent-emerald), var(--accent-cyan));"></div>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}

// Background updates
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
  const count = AppState.leads.filter(l => l.stage === "Pending Approval").length;
  const badgeEl = document.getElementById("nav-badge-approval");
  if (badgeEl) {
    badgeEl.textContent = count;
    badgeEl.style.display = count > 0 ? "inline-block" : "none";
  }
}

// Utility Helpers
function showToast(msg, type = "info") {
  const container = document.getElementById("toast-container") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = "toast";
  if (type === "error") toast.style.borderColor = "var(--accent-rose)";
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
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
