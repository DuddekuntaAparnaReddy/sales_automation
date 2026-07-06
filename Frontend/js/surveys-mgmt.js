// ─── Survey Management Frontend JS ──────────────────────────────────────────
let editingSurveyId    = null;
let pendingDeleteSurveyId = null;
let currentActiveSurveyQuestions = [];

// ── Tab Navigation ────────────────────────────────────────────────────────────
function showSurveySubTab(tabName) {
    document.querySelectorAll('.survey-tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.survey-tab-btn').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(`survey-tab-${tabName}`).style.display = 'block';
    event?.target?.classList?.add('active');
    
    if (tabName === 'list') {
        loadSurveys();
    } else if (tabName === 'feedback') {
        loadFeedbackResponses(); // Fallback general ratings
    }
}

// ── Stats ─────────────────────────────────────────────────────────────────────
async function loadSurveyStats() {
    try {
        const r = await fetch("http://127.0.0.1:8000/api/surveys/stats");
        const d = await r.json();
        const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setVal("survey-stat-total", d.total_surveys ?? 0);
        setVal("survey-stat-active", d.active_surveys ?? 0);
        setVal("survey-stat-responses", d.total_responses ?? 0);
        setVal("survey-stat-rate", `${d.response_rate ?? 0}%`);
    } catch (e) { console.error("[Survey Stats]", e); }
}

// ── Load & Render ─────────────────────────────────────────────────────────────
async function loadSurveys() {
    const search   = document.getElementById("survey_search")?.value || "";
    const category = document.getElementById("survey_filter_category")?.value || "";
    const status   = document.getElementById("survey_filter_status")?.value || "";

    const url = `http://127.0.0.1:8000/api/surveys?search=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}&status=${encodeURIComponent(status)}`;
    try {
        const r = await fetch(url);
        const surveys = await r.json();
        renderSurveyTable(surveys);
        loadSurveyStats();
    } catch (e) { console.error("[loadSurveys]", e); }
}

function renderSurveyTable(surveys) {
    const tbody = document.getElementById("surveys-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!surveys || surveys.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:2rem;">No surveys found. Click Create Survey above.</td></tr>`;
        return;
    }

    surveys.forEach(s => {
        const statusClass = s.status === "Active" ? "badge-success" : "badge-danger";

        // Escape for onclick
        const eTitle = (s.title || "").replace(/'/g, "\\'");
        const eDesc  = (s.description || "").replace(/'/g, "\\'").replace(/\n/g, "\\n");
        const eCat   = (s.category || "").replace(/'/g, "\\'");

        tbody.innerHTML += `
        <tr>
            <td><strong>${s.title}</strong></td>
            <td>${s.category || "—"}</td>
            <td>${s.expiry_date ? s.expiry_date : "No Expiry"}</td>
            <td><span class="badge ${statusClass}">${s.status}</span></td>
            <td><strong style="color:var(--primary);">${s.total_responses}</strong> responses</td>
            <td style="white-space:nowrap;">
                <button class="btn-action" style="background:#8b5cf6;padding:3px 8px;font-size:11px;margin-right:4px;"
                    onclick="viewSurveyResponsesAndInsights(${s.id},'${eTitle}')">Responses & AI</button>
                <button class="btn-action" style="background:#eab308;padding:3px 8px;font-size:11px;margin-right:4px;"
                    onclick="triggerEditSurvey(${s.id})">Edit</button>
                <button class="btn-action" style="background:#ef4444;padding:3px 8px;font-size:11px;"
                    onclick="showDeleteSurveyConfirm(${s.id},'${eTitle}')">Delete</button>
            </td>
        </tr>`;
    });
}

// ── Dynamic Question Builder ──────────────────────────────────────────────────
let surveyQuestions = [];

function addQuestionField(questionText = "", questionType = "text") {
    const container = document.getElementById("questions-builder-container");
    if (!container) return;

    const qIndex = surveyQuestions.length;
    surveyQuestions.push({ question_text: questionText, question_type: questionType });

    const qDiv = document.createElement("div");
    qDiv.id = `q-builder-row-${qIndex}`;
    qDiv.style.cssText = "display:flex;gap:0.75rem;margin-bottom:0.75rem;align-items:center;background:var(--surface-secondary);padding:0.75rem;border-radius:0.5rem;border:1px solid var(--border-color);";
    qDiv.innerHTML = `
        <div style="flex:1;">
            <input type="text" class="form-control q-text-input" style="margin:0;" placeholder="Question text (e.g. How satisfied are you?)" value="${questionText}" oninput="updateQuestionText(${qIndex}, this.value)">
        </div>
        <div style="width:150px;">
            <select class="form-control q-type-select" style="margin:0;" onchange="updateQuestionType(${qIndex}, this.value)">
                <option value="text" ${questionType === 'text' ? 'selected' : ''}>Text (Open)</option>
                <option value="rating" ${questionType === 'rating' ? 'selected' : ''}>Rating (1-5)</option>
                <option value="choice" ${questionType === 'choice' ? 'selected' : ''}>Choice (Yes/No)</option>
            </select>
        </div>
        <button type="button" class="btn-action" style="background:var(--danger);padding:0.5rem;border-radius:0.375rem;" onclick="removeQuestionField(${qIndex})">
            &times;
        </button>
    `;
    container.appendChild(qDiv);
}

function updateQuestionText(index, value) {
    if (surveyQuestions[index]) {
        surveyQuestions[index].question_text = value;
    }
}

function updateQuestionType(index, value) {
    if (surveyQuestions[index]) {
        surveyQuestions[index].question_type = value;
    }
}

function removeQuestionField(index) {
    const row = document.getElementById(`q-builder-row-${index}`);
    if (row) {
        row.remove();
    }
    surveyQuestions[index] = null; // mark as removed
}

// ── Show Survey Form Panel ────────────────────────────────────────────────────
function showSurveyForm() {
    const form = document.getElementById("survey-form-panel");
    if (!form) return;
    const isHidden = form.style.display === "none" || !form.style.display;
    form.style.display = isHidden ? "block" : "none";
    if (isHidden) {
        resetSurveyForm();
        form.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function resetSurveyForm() {
    editingSurveyId = null;
    document.getElementById("survey_title").value = "";
    document.getElementById("survey_description").value = "";
    document.getElementById("survey_category").value = "Product Feedback";
    document.getElementById("survey_expiry").value = "";
    
    const container = document.getElementById("questions-builder-container");
    if (container) container.innerHTML = "";
    surveyQuestions = [];

    document.getElementById("survey-form-title").textContent = "Create New Survey";
    document.getElementById("survey-save-btn").textContent   = "🚀 Create Survey";
    
    // Add two default questions to guide the admin
    addQuestionField("How would you rate your overall experience?", "rating");
    addQuestionField("Would you recommend our product to others?", "choice");
    addQuestionField("What improvements would you like to see?", "text");
}

// ── Save Survey ───────────────────────────────────────────────────────────────
async function saveSurvey() {
    const title       = document.getElementById("survey_title").value.trim();
    const description = document.getElementById("survey_description").value.trim();
    const category    = document.getElementById("survey_category").value;
    const expiry_date = document.getElementById("survey_expiry").value || null;

    if (!title) { alert("Survey Title is required."); return; }

    // Filter out deleted/empty questions
    const cleanQuestions = surveyQuestions.filter(q => q && q.question_text.trim());
    if (cleanQuestions.length === 0) {
        alert("Please add at least one question.");
        return;
    }

    const session = JSON.parse(localStorage.getItem("session") || "{}");
    const created_by = session.user_id || 1;

    const payload = {
        title,
        description,
        category,
        expiry_date,
        created_by,
        questions: cleanQuestions
    };

    const url    = editingSurveyId ? `http://127.0.0.1:8000/api/surveys/${editingSurveyId}` : "http://127.0.0.1:8000/api/surveys";
    const method = editingSurveyId ? "PUT" : "POST";

    const saveBtn = document.getElementById("survey-save-btn");
    if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = "Processing..."; }

    try {
        const r = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const d = await r.json();
        
        if (!r.ok) { alert(d.error || "Save failed."); return; }

        showSurveyToast(editingSurveyId ? "Survey updated successfully!" : "Survey created successfully!");
        document.getElementById("survey-form-panel").style.display = "none";
        loadSurveys();
    } catch (e) {
        alert("Error connecting to backend");
    } finally {
        if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = editingSurveyId ? "💾 Save Changes" : "🚀 Create Survey"; }
    }
}

// ── Edit Trigger ──────────────────────────────────────────────────────────────
async function triggerEditSurvey(surveyId) {
    editingSurveyId = surveyId;
    const form = document.getElementById("survey-form-panel");
    if (form) {
        form.style.display = "block";
        form.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    document.getElementById("survey-form-title").textContent = "Edit Survey";
    document.getElementById("survey-save-btn").textContent   = "💾 Save Changes";

    try {
        const r = await fetch(`http://127.0.0.1:8000/api/surveys/${surveyId}`);
        const s = await r.json();
        
        document.getElementById("survey_title").value       = s.title || "";
        document.getElementById("survey_description").value = s.description || "";
        document.getElementById("survey_category").value    = s.category || "Product Feedback";
        document.getElementById("survey_expiry").value      = s.expiry_date || "";

        const container = document.getElementById("questions-builder-container");
        if (container) container.innerHTML = "";
        surveyQuestions = [];

        if (s.questions && s.questions.length > 0) {
            s.questions.forEach(q => {
                addQuestionField(q.question_text, q.question_type);
            });
        }
    } catch (e) { alert("Error loading survey details."); }
}

// ── Delete ────────────────────────────────────────────────────────────────────
function showDeleteSurveyConfirm(id, title) {
    pendingDeleteSurveyId = id;
    const modal = document.getElementById("survey-delete-modal");
    const msg   = document.getElementById("survey-delete-msg");
    if (msg) msg.textContent = `Are you sure you want to delete the survey "${title}"? All submitted responses will be permanently deleted.`;
    if (modal) modal.style.display = "flex";
}

function closeDeleteSurveyModal() {
    const modal = document.getElementById("survey-delete-modal");
    if (modal) modal.style.display = "none";
    pendingDeleteSurveyId = null;
}

async function executeDeleteSurvey() {
    if (!pendingDeleteSurveyId) return;
    const id = pendingDeleteSurveyId;
    closeDeleteSurveyModal();
    try {
        const r = await fetch(`http://127.0.0.1:8000/api/surveys/${id}`, { method: "DELETE" });
        const d = await r.json();
        if (!r.ok) { alert(d.error || "Delete failed"); return; }
        showSurveyToast("Survey deleted successfully.");
        loadSurveys();
    } catch (e) { alert("Backend Connection Error."); }
}

// ── Responses & AI Insights Modal ──────────────────────────────────────────────
let activeSurveyId = null;
let currentResponsesRaw = [];

async function viewSurveyResponsesAndInsights(surveyId, surveyTitle) {
    activeSurveyId = surveyId;
    const modal = document.getElementById("survey-responses-modal");
    const titleEl = document.getElementById("survey-modal-title");
    if (titleEl) titleEl.textContent = surveyTitle;
    if (modal) modal.style.display = "flex";

    // Select subtab "responses" by default inside modal
    toggleModalSubTab("responses");
    loadModalResponses(surveyId);
    loadModalAIInsights(surveyId);
}

function toggleModalSubTab(tabName) {
    document.querySelectorAll(".modal-tab-content").forEach(el => el.style.display = "none");
    document.querySelectorAll(".modal-tab-btn").forEach(btn => btn.classList.remove("active"));

    document.getElementById(`modal-tab-${tabName}`).style.display = "block";
    document.getElementById(`modal-btn-${tabName}`).classList.add("active");
}

async function loadModalResponses(surveyId) {
    const container = document.getElementById("modal-responses-container");
    if (!container) return;
    container.innerHTML = "<p style='color:var(--text-muted);text-align:center;padding:2rem;'>Loading submissions...</p>";

    try {
        const r = await fetch(`http://127.0.0.1:8000/api/surveys/${surveyId}/responses`);
        const responses = await r.json();
        currentResponsesRaw = responses;

        container.innerHTML = "";
        if (!responses || responses.length === 0) {
            container.innerHTML = "<p style='color:var(--text-muted);text-align:center;padding:2rem;'>No responses submitted yet.</p>";
            return;
        }

        responses.forEach((resp, index) => {
            const dateStr = resp.submitted_at ? new Date(resp.submitted_at).toLocaleString() : "N/A";
            let answersHtml = "";
            for (const q in resp.response_data) {
                answersHtml += `
                    <div style="margin-bottom:0.5rem;font-size:0.9rem;">
                        <span style="color:var(--text-muted);font-weight:500;">Q: ${q}</span><br>
                        <span style="color:white;font-weight:600;">A: ${resp.response_data[q]}</span>
                    </div>
                `;
            }

            container.innerHTML += `
                <div style="background:var(--surface-secondary);border:1px solid var(--border-color);border-radius:0.75rem;padding:1.25rem;margin-bottom:1rem;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.75rem;border-bottom:1px solid var(--border-color);padding-bottom:0.5rem;font-size:0.8rem;color:var(--text-muted);">
                        <span><strong style="color:var(--primary);">${resp.user_name}</strong> (${resp.user_email})</span>
                        <span>${dateStr}</span>
                    </div>
                    ${answersHtml}
                </div>
            `;
        });
    } catch (e) { container.innerHTML = "<p style='color:red;'>Failed to load responses.</p>"; }
}

async function loadModalAIInsights(surveyId) {
    const setInsight = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setInsight("ai-survey-sentiment", "Loading...");
    const listInterests = document.getElementById("ai-survey-interests");
    const listIssues     = document.getElementById("ai-survey-issues");
    const listRecs       = document.getElementById("ai-survey-recs");
    
    if (listInterests) listInterests.innerHTML = "<li>Loading...</li>";
    if (listIssues) listIssues.innerHTML = "<li>Loading...</li>";
    if (listRecs) listRecs.innerHTML = "<li>Loading...</li>";

    try {
        const r = await fetch(`http://127.0.0.1:8000/api/surveys/${surveyId}/insights`);
        const insight = await r.json();

        setInsight("ai-survey-sentiment", insight.sentiment || "Mixed");
        
        if (listInterests) {
            listInterests.innerHTML = "";
            (insight.top_interests || []).forEach(item => {
                listInterests.innerHTML += `<li><i data-lucide="tag" style="width:12px;margin-right:5px;display:inline;"></i>${item}</li>`;
            });
        }
        if (listIssues) {
            listIssues.innerHTML = "";
            (insight.common_issues || []).forEach(item => {
                listIssues.innerHTML += `<li><i data-lucide="alert-triangle" style="width:12px;margin-right:5px;display:inline;color:var(--danger);"></i>${item}</li>`;
            });
        }
        if (listRecs) {
            listRecs.innerHTML = "";
            (insight.recommendations || []).forEach(item => {
                listRecs.innerHTML += `<li><i data-lucide="check-circle" style="width:12px;margin-right:5px;display:inline;color:var(--success);"></i>${item}</li>`;
            });
        }

        if (window.lucide) lucide.createIcons();
    } catch (e) { console.error(e); }
}

async function triggerAIInsightGen() {
    if (!activeSurveyId) return;
    const btn = document.getElementById("ai-insight-gen-btn");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Analyzing with Llama 3.1..."; }

    try {
        const r = await fetch(`http://127.0.0.1:8000/api/surveys/${activeSurveyId}/insights`, { method: "POST" });
        const d = await r.json();
        if (r.ok) {
            showSurveyToast("AI Insights updated!");
            loadModalAIInsights(activeSurveyId);
        } else {
            alert(d.error || "Generation failed.");
        }
    } catch (e) { alert("Error calling AI analysis endpoint."); }
    finally { if (btn) { btn.disabled = false; btn.textContent = "⚡ Trigger Llama 3.1 Analysis"; } }
}

function closeSurveyResponsesModal() {
    const modal = document.getElementById("survey-responses-modal");
    if (modal) modal.style.display = "none";
    activeSurveyId = null;
}

// ── Export Survey Data ────────────────────────────────────────────────────────
function exportSurveyResponses() {
    if (!currentResponsesRaw || currentResponsesRaw.length === 0) {
        alert("No responses available to export.");
        return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentResponsesRaw, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `survey_responses_${activeSurveyId || 'export'}.json`);
    dlAnchorElem.click();
}

// ── Toast Notification ────────────────────────────────────────────────────────
function showSurveyToast(message) {
    let toast = document.getElementById("survey-toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "survey-toast";
        toast.style.cssText = `
            position:fixed;bottom:2rem;right:2rem;background:linear-gradient(135deg,#8b5cf6,#6366f1);
            color:white;padding:0.85rem 1.5rem;border-radius:0.75rem;font-weight:600;font-size:0.9rem;
            box-shadow:0 8px 24px rgba(139,92,246,0.3);z-index:99999;transition:opacity 0.4s;
        `;
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = "1";
    setTimeout(() => { toast.style.opacity = "0"; }, 3000);
}

// ── Hook On Load ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadSurveys();
});
