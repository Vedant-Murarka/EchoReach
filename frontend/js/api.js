/**
 * EchoReach API Client
 * Interfaces with FastAPI endpoints for Leads, Approval Queue, Decision Logs, and Simulator
 */
const API_BASE_URL = window.location.origin.includes("http") ? "" : "http://127.0.0.1:8000";

const ApiService = {
  async getLeads(stage = null) {
    const url = stage ? `${API_BASE_URL}/leads?stage=${encodeURIComponent(stage)}` : `${API_BASE_URL}/leads`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch leads");
    return res.json();
  },

  async getLeadById(leadId) {
    const res = await fetch(`${API_BASE_URL}/leads/${leadId}`);
    if (!res.ok) throw new Error("Failed to fetch lead details");
    return res.json();
  },

  async createLead(leadData) {
    const res = await fetch(`${API_BASE_URL}/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(leadData)
    });
    if (!res.ok) throw new Error("Failed to create lead");
    return res.json();
  },

  async runPipeline(leadId, touchNumber = 1) {
    const res = await fetch(`${API_BASE_URL}/leads/${leadId}/run-pipeline?touch_number=${touchNumber}`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Pipeline run failed");
    return res.json();
  },

  async processApproval(leadId, touchId, action, editedSubject = null, editedBody = null) {
    const res = await fetch(`${API_BASE_URL}/leads/${leadId}/approve?touch_id=${touchId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        edited_subject: editedSubject,
        edited_body: editedBody
      })
    });
    if (!res.ok) throw new Error("Approval processing failed");
    return res.json();
  },

  async simulateReply(leadId, personaType) {
    const res = await fetch(`${API_BASE_URL}/leads/${leadId}/simulate-reply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ persona_type: personaType })
    });
    if (!res.ok) throw new Error("Reply simulation failed");
    return res.json();
  },

  async submitCorrection(replyId, correctedClass, notes = "Operator Correction") {
    const res = await fetch(`${API_BASE_URL}/replies/${replyId}/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        corrected_classification: correctedClass,
        notes
      })
    });
    if (!res.ok) throw new Error("Correction submission failed");
    return res.json();
  },

  async getReplies() {
    const res = await fetch(`${API_BASE_URL}/replies`);
    if (!res.ok) throw new Error("Failed to fetch replies");
    return res.json();
  },

  async getDecisionLogs(leadId = null) {
    const url = leadId ? `${API_BASE_URL}/leads/${leadId}/decision-log` : `${API_BASE_URL}/decision-log`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch decision logs");
    return res.json();
  },

  async getGuardrailsStatus() {
    const res = await fetch(`${API_BASE_URL}/guardrails/status`);
    if (!res.ok) throw new Error("Failed to fetch guardrails status");
    return res.json();
  },

  async getAnalytics() {
    const res = await fetch(`${API_BASE_URL}/analytics`);
    if (!res.ok) throw new Error("Failed to fetch analytics");
    return res.json();
  }
};
