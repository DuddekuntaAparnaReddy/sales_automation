// Lead Pipeline Management Logic

let allLeadsCache = [];

async function loadLeads() {
    const searchVal = document.getElementById("lead-search") ? document.getElementById("lead-search").value.trim() : "";
    const categoryVal = document.getElementById("lead-filter-category") ? document.getElementById("lead-filter-category").value : "";
    const sortVal = document.getElementById("lead-sort") ? document.getElementById("lead-sort").value : "date_desc";

    const queryParams = new URLSearchParams();
    if (searchVal) queryParams.append("search", searchVal);
    if (categoryVal) queryParams.append("category", categoryVal);
    if (sortVal) queryParams.append("sort", sortVal);

    try {
        const response = await fetch(`http://127.0.0.1:8000/leads?${queryParams.toString()}`);
        const data = await response.json();
        
        allLeadsCache = data;

        const leadsList = document.getElementById("leads-list");
        if (!leadsList) return;
        leadsList.innerHTML = "";

        data.forEach(lead => {
            // lead format: [lead_id, name, email, phone, company, lead_status, user_id, product_interest, budget, purchase_timeline, customer_intent, lead_score, lead_type, created_at]
            const leadId = lead[0];
            const name = lead[1];
            const email = lead[2];
            const product = lead[7] || "Not Specified";
            const score = lead[11] || 0;
            const category = lead[12] || "Cold Lead";

            let badgeColorStyle = "background: rgba(239, 68, 68, 0.2); color: #ef4444;"; // Red for Hot
            if (category === "Warm Lead") {
                badgeColorStyle = "background: rgba(234, 179, 8, 0.2); color: #eab308;"; // Yellow/Orange
            } else if (category === "Cold Lead") {
                badgeColorStyle = "background: rgba(59, 130, 246, 0.2); color: #3b82f6;"; // Blue
            }

            leadsList.innerHTML += `
            <tr>
                <td>${name}</td>
                <td>${email}</td>
                <td>${product}</td>
                <td style="font-weight: 700; color: var(--primary);">${score}</td>
                <td>
                    <span class="badge" style="${badgeColorStyle}">
                        ${category}
                    </span>
                </td>
                <td>
                    <button class="btn-action" style="padding: 4px 8px; font-size: 12px;" onclick="viewLeadDetails(${leadId})">
                        View Details
                    </button>
                </td>
            </tr>
            `;
        });
    } catch(error) {
        console.error("Error loading leads:", error);
    }
}

function viewLeadDetails(leadId) {
    const lead = allLeadsCache.find(l => l[0] === leadId);
    if (!lead) return;

    const name = lead[1];
    const email = lead[2];
    const phone = lead[3] || "N/A";
    const company = lead[4] || "N/A";
    const status = lead[5] || "New";
    const userId = lead[6] || "N/A";
    const product = lead[7] || "N/A";
    const budget = lead[8] !== null ? `₹${lead[8].toLocaleString()}` : "N/A";
    const timeline = lead[9] || "N/A";
    const intent = lead[10] || "N/A";
    const score = lead[11] || 0;
    const category = lead[12] || "Cold Lead";
    const date = lead[13] ? new Date(lead[13]).toLocaleString() : "N/A";

    const modalContent = document.getElementById("lead-modal-content");
    if (!modalContent) return;

    modalContent.innerHTML = `
        <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; grid-column: span 2; font-weight: 600; color: var(--text-muted); font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;">
            Customer Information
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Full Name</strong>
            <span style="font-size: 0.95rem; font-weight: 500;">${name}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Email Address</strong>
            <span style="font-size: 0.95rem; font-weight: 500;">${email}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Phone Number</strong>
            <span style="font-size: 0.95rem; font-weight: 500;">${phone}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Company Name</strong>
            <span style="font-size: 0.95rem; font-weight: 500;">${company}</span>
        </div>

        <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; grid-column: span 2; margin-top: 1rem; font-weight: 600; color: var(--text-muted); font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;">
            AI Extraction & Qualification Info
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Product Interest</strong>
            <span style="font-size: 0.95rem; font-weight: 500; color: var(--success);">${product}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Stated Budget</strong>
            <span style="font-size: 0.95rem; font-weight: 500; color: var(--warning);">${budget}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Purchase Timeline</strong>
            <span style="font-size: 0.95rem; font-weight: 500;">${timeline}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Customer Intent</strong>
            <span style="font-size: 0.95rem; font-weight: 500;">${intent}</span>
        </div>

        <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; grid-column: span 2; margin-top: 1rem; font-weight: 600; color: var(--text-muted); font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;">
            Lead Score & Metrics
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Lead Score</strong>
            <span style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${score} / 100</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Classification</strong>
            <span style="font-size: 1.2rem; font-weight: 700; color: ${category === 'Hot Lead' ? '#ef4444' : category === 'Warm Lead' ? '#eab308' : '#3b82f6'};">${category}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Registered Date</strong>
            <span style="font-size: 0.9rem;">${date}</span>
        </div>
        <div>
            <strong style="color: var(--text-muted); font-size: 0.8rem; display:block;">Linked User ID</strong>
            <span style="font-size: 0.9rem;">${userId}</span>
        </div>
    `;

    document.getElementById("lead-details-modal").style.display = "flex";
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function closeLeadDetailsModal() {
    document.getElementById("lead-details-modal").style.display = "none";
}

// Bind events on load
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("lead-search");
    const categoryFilter = document.getElementById("lead-filter-category");
    const sortSelect = document.getElementById("lead-sort");

    if (searchInput) {
        searchInput.addEventListener("input", loadLeads);
    }

    if (categoryFilter) {
        categoryFilter.addEventListener("change", loadLeads);
    }

    if (sortSelect) {
        sortSelect.addEventListener("change", loadLeads);
    }

    loadLeads();
});