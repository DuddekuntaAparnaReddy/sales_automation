// ─── Campaign Management JS ───────────────────────────────────────────────────
let editingCampaignId = null;
let pendingDeleteId   = null;

// ── Stats ─────────────────────────────────────────────────────────────────────
async function loadCampaignStats() {
    try {
        const r = await fetch("http://127.0.0.1:8000/api/campaigns/stats");
        const d = await r.json();
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set("camp-stat-total",     d.total_campaigns    ?? 0);
        set("camp-stat-active",    d.active_campaigns   ?? 0);
        set("camp-stat-completed", d.completed_campaigns?? 0);
        set("camp-stat-emails",    d.emails_sent        ?? 0);
    } catch (e) { console.error("[Campaign Stats]", e); }
}

// ── Load & Render ─────────────────────────────────────────────────────────────
async function loadCampaigns() {
    const search = document.getElementById("camp_search")?.value || "";
    const type   = document.getElementById("camp_filter_type")?.value || "";
    const status = document.getElementById("camp_filter_status")?.value || "";

    const url = `http://127.0.0.1:8000/campaigns?search=${encodeURIComponent(search)}&type=${encodeURIComponent(type)}&status=${encodeURIComponent(status)}`;
    try {
        const r = await fetch(url);
        const campaigns = await r.json();
        renderCampaignTable(campaigns);
        loadCampaignStats();
    } catch (e) { console.error("[loadCampaigns]", e); }
}

function renderCampaignTable(campaigns) {
    const tbody = document.getElementById("campaigns-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!campaigns || campaigns.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:2rem;">No campaigns found. Create your first campaign above.</td></tr>`;
        return;
    }

    campaigns.forEach(c => {
        const statusClass = c.status === "Active"    ? "badge-success"
                          : c.status === "Completed" ? "badge-info"
                          : "badge-warning";

        // Escape for onclick
        const eName    = (c.campaign_name   || "").replace(/'/g, "\\'");
        const eType    = (c.campaign_type   || "").replace(/'/g, "\\'");
        const eProduct = (c.product_name    || "").replace(/'/g, "\\'");
        const eOffer   = (c.offer_details   || "").replace(/'/g, "\\'").replace(/\n/g, "\\n");
        const eAud     = (c.target_audience || "").replace(/'/g, "\\'");
        const eStatus  = (c.status          || "Active").replace(/'/g, "\\'");

        tbody.innerHTML += `
        <tr>
            <td><strong>${c.campaign_name}</strong><br>
                <span style="font-size:0.78rem;color:var(--text-muted);">${c.campaign_type || "—"}</span>
            </td>
            <td>${c.product_name || "—"}</td>
            <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${c.offer_details || ''}">${c.offer_details || "—"}</td>
            <td>${c.target_audience || "—"}</td>
            <td><span class="badge ${statusClass}">${c.status || "Active"}</span></td>
            <td>${c.start_date ? c.start_date : "—"}</td>
            <td style="white-space:nowrap;">
                <button class="btn-action" style="background:#3b82f6;padding:3px 8px;font-size:11px;margin-right:4px;"
                    onclick="previewAIContent(${c.campaign_id})">Preview AI</button>
                <button class="btn-action" style="background:#eab308;padding:3px 8px;font-size:11px;margin-right:4px;"
                    onclick="editCampaign(${c.campaign_id},'${eName}','${eType}','${eProduct}','${eOffer}','${eAud}','${c.start_date||''}','${c.end_date||''}','${eStatus}')">Edit</button>
                <button class="btn-action" style="background:#ef4444;padding:3px 8px;font-size:11px;"
                    onclick="showDeleteCampaignConfirm(${c.campaign_id},'${eName}')">Delete</button>
            </td>
        </tr>`;
    });
}

// ── Form Toggle ───────────────────────────────────────────────────────────────
function showCampaignForm() {
    const form = document.getElementById("campaign-form-panel");
    if (!form) return;
    const isHidden = form.style.display === "none" || !form.style.display;
    form.style.display = isHidden ? "block" : "none";
    if (isHidden) {
        resetCampaignForm();
        form.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function resetCampaignForm() {
    editingCampaignId = null;
    ["camp_name","camp_type","camp_product","camp_offer","camp_audience",
     "camp_start","camp_end","camp_status"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = el.tagName === "SELECT" ? el.options[0]?.value || "" : "";
    });
    document.getElementById("camp-form-title").textContent  = "Create New Campaign";
    document.getElementById("camp-save-btn").textContent    = "🚀 Create Campaign & Generate AI Content";
    hideCampaignAIPreview();
}

// ── Edit ─────────────────────────────────────────────────────────────────────
function editCampaign(id, name, type, product, offer, audience, start, end, status) {
    editingCampaignId = id;
    const form = document.getElementById("campaign-form-panel");
    if (form) {
        form.style.display = "block";
        form.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val || ""; };
    set("camp_name",     name);
    set("camp_type",     type);
    set("camp_product",  product);
    set("camp_offer",    offer.replace(/\\n/g, "\n"));
    set("camp_audience", audience);
    set("camp_start",    start);
    set("camp_end",      end);
    set("camp_status",   status);
    document.getElementById("camp-form-title").textContent = "Edit Campaign";
    document.getElementById("camp-save-btn").textContent   = "💾 Save Changes";
}

// ── Save (Create / Update) ────────────────────────────────────────────────────
async function saveCampaign() {
    const name     = document.getElementById("camp_name")?.value?.trim();
    const type     = document.getElementById("camp_type")?.value;
    const product  = document.getElementById("camp_product")?.value?.trim();
    const offer    = document.getElementById("camp_offer")?.value?.trim();
    const audience = document.getElementById("camp_audience")?.value?.trim();
    const start    = document.getElementById("camp_start")?.value;
    const end      = document.getElementById("camp_end")?.value;
    const status   = document.getElementById("camp_status")?.value || "Active";

    if (!name) { alert("Campaign Name is required."); return; }

    const user = JSON.parse(localStorage.getItem("user") || "{}");
    const created_by = user.user_id || null;

    const payload = { campaign_name: name, campaign_type: type, product_name: product,
                      offer_details: offer, target_audience: audience,
                      start_date: start || null, end_date: end || null,
                      status, created_by };

    const url    = editingCampaignId ? `http://127.0.0.1:8000/campaign/${editingCampaignId}` : "http://127.0.0.1:8000/campaign";
    const method = editingCampaignId ? "PUT" : "POST";

    const saveBtn = document.getElementById("camp-save-btn");
    if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = "⏳ Processing..."; }

    try {
        const r = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await r.json();

        if (!r.ok) {
            alert(data.error || "An error occurred. Please try again.");
            return;
        }

        // Show AI preview if newly created
        if (!editingCampaignId && data.ai_content) {
            showCampaignAIPreviewPanel(data.ai_content);
        }

        document.getElementById("campaign-form-panel").style.display = "none";
        loadCampaigns();

        // Show success toast
        showCampaignToast(editingCampaignId ? "Campaign updated successfully!" : "Campaign created & emails sent!");
        editingCampaignId = null;
    } catch (e) {
        alert("Backend Connection Error. Make sure the server is running.");
    } finally {
        if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = editingCampaignId ? "💾 Save Changes" : "🚀 Create Campaign & Generate AI Content"; }
    }
}

// ── AI Content Preview ────────────────────────────────────────────────────────
async function previewAIContent(campaignId) {
    try {
        const r = await fetch(`http://127.0.0.1:8000/campaign/${campaignId}`);
        const c = await r.json();
        if (c.ai_title || c.ai_subject || c.ai_body) {
            showCampaignAIPreviewPanel({ title: c.ai_title, subject: c.ai_subject, body: c.ai_body, cta: c.ai_cta });
        } else {
            alert("No AI content stored for this campaign yet.");
        }
    } catch (e) { alert("Could not fetch campaign details."); }
}

function showCampaignAIPreviewPanel(aiContent) {
    const panel = document.getElementById("ai-preview-panel");
    if (!panel) return;
    panel.style.display = "block";
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val || "—"; };
    set("ai-prev-title",   aiContent.title);
    set("ai-prev-subject", aiContent.subject);
    set("ai-prev-body",    typeof aiContent.body === "object" ? JSON.stringify(aiContent.body) : (aiContent.body || ""));
    set("ai-prev-cta",     aiContent.cta);
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function hideCampaignAIPreview() {
    const panel = document.getElementById("ai-preview-panel");
    if (panel) panel.style.display = "none";
}

// ── Delete with Modal ─────────────────────────────────────────────────────────
function showDeleteCampaignConfirm(id, name) {
    pendingDeleteId = id;
    const modal = document.getElementById("camp-delete-modal");
    const msg   = document.getElementById("camp-delete-msg");
    if (msg)   msg.textContent = `Are you sure you want to delete the campaign "${name}"? This action cannot be undone.`;
    if (modal) {
        modal.style.display = "flex";
        if (window.lucide) lucide.createIcons();
    }
}

function closeDeleteCampaignModal() {
    const modal = document.getElementById("camp-delete-modal");
    if (modal) modal.style.display = "none";
    pendingDeleteId = null;
}

async function executeDeleteCampaign() {
    if (!pendingDeleteId) return;
    const id = pendingDeleteId;
    closeDeleteCampaignModal();
    try {
        const r = await fetch(`http://127.0.0.1:8000/campaign/${id}`, { method: "DELETE" });
        const d = await r.json();
        if (!r.ok) { alert(d.error || "Delete failed"); return; }
        showCampaignToast("Campaign deleted.");
        loadCampaigns();
    } catch (e) { alert("Backend Connection Error."); }
}

// ── Toast Notification ────────────────────────────────────────────────────────
function showCampaignToast(message) {
    let toast = document.getElementById("camp-toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "camp-toast";
        toast.style.cssText = `
            position:fixed;bottom:2rem;right:2rem;background:linear-gradient(135deg,#22c55e,#16a34a);
            color:white;padding:0.85rem 1.5rem;border-radius:0.75rem;font-weight:600;font-size:0.9rem;
            box-shadow:0 8px 24px rgba(34,197,94,0.3);z-index:99999;transition:opacity 0.4s;
        `;
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = "1";
    setTimeout(() => { toast.style.opacity = "0"; }, 3000);
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadCampaigns();
});