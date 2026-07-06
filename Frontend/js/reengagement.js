// Re-engagement campaigns admin dashboard logic

async function loadInactiveUsers() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/reengagement/inactive");
        const data = await response.json();

        const list = document.getElementById("reengagement-list");
        if (!list) return;
        list.innerHTML = "";

        if (data.length === 0) {
            list.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); font-style: italic;">No inactive users identified.</td></tr>`;
            return;
        }

        data.forEach(user => {
            const badgeClass = user.risk_level === "High Risk" ? "badge-danger" : "badge-warning";
            list.innerHTML += `
            <tr>
                <td>
                    <div style="font-weight: 600;">${user.full_name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${user.email}</div>
                </td>
                <td>${user.last_active}</td>
                <td><span style="font-weight: 500;">${user.previous_interests}</span></td>
                <td><span class="badge ${badgeClass}">${user.risk_level}</span></td>
                <td>
                    <button class="btn-action" style="padding: 6px 12px; font-size: 12px;" onclick="triggerReengagementCampaign(${user.user_id}, this)">
                        Trigger Re-engage
                    </button>
                </td>
            </tr>
            `;
        });
    } catch (error) {
        console.error("Error loading inactive users:", error);
    }
}

async function loadReengagementStats() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/reengagement/stats");
        const data = await response.json();

        document.getElementById("reengage-stat-inactive").innerText = data.total_inactive || 0;
        document.getElementById("reengage-stat-sent").innerText = data.emails_sent || 0;
        document.getElementById("reengage-stat-reengaged").innerText = data.reengaged_users || 0;
        document.getElementById("reengage-stat-conversion").innerText = (data.conversion_rate || 0) + "%";
    } catch (error) {
        console.error("Error loading reengagement stats:", error);
    }
}

async function loadReengagementHistory() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/reengagement/history");
        const data = await response.json();

        const list = document.getElementById("reengagement-history-list");
        if (!list) return;
        list.innerHTML = "";

        if (data.length === 0) {
            list.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); font-style: italic;">No campaign logs found.</td></tr>`;
            return;
        }

        data.forEach(c => {
            const dateStr = c.sent_at ? new Date(c.sent_at).toLocaleString() : "N/A";
            const statusBadge = c.status === "Sent" ? "badge-success" : "badge-danger";
            const reengagedBadge = c.reengaged ? "badge-success" : "badge-warning";
            const reengagedText = c.reengaged ? "Yes" : "No";

            list.innerHTML += `
            <tr>
                <td style="font-size: 0.85rem; color: var(--text-secondary);">${dateStr}</td>
                <td>
                    <div style="font-weight: 500;">${c.customer_name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${c.customer_email}</div>
                </td>
                <td title="${c.body}">${c.subject}</td>
                <td><span class="badge ${statusBadge}">${c.status}</span></td>
                <td><span class="badge ${reengagedBadge}">${reengagedText}</span></td>
            </tr>
            `;
        });
    } catch (error) {
        console.error("Error loading campaign history:", error);
    }
}

async function triggerReengagementCampaign(userId, btn) {
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Sending...";
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/api/reengagement/trigger", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ user_id: userId })
        });

        const data = await response.json();

        if (response.ok) {
            alert(data.message || "Re-engagement email sent successfully!");
            // Refresh dashboard
            loadInactiveUsers();
            loadReengagementStats();
            loadReengagementHistory();
        } else {
            alert("Error: " + (data.error || "Failed to trigger campaign"));
            if (btn) {
                btn.disabled = false;
                btn.innerText = "Trigger Re-engage";
            }
        }
    } catch (error) {
        console.error("Error triggering campaign:", error);
        alert("Server Connection Error");
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Trigger Re-engage";
        }
    }
}

// Hook onload and refresh on showSection
document.addEventListener("DOMContentLoaded", () => {
    // Intercept showSection to load data when reengagement tab becomes active
    const originalShowSection = window.showSection;
    if (typeof originalShowSection === "function") {
        window.showSection = function(section, element) {
            originalShowSection(section, element);
            if (section === "reengagement") {
                loadInactiveUsers();
                loadReengagementStats();
                loadReengagementHistory();
            }
        };
    }
    
    // Auto-run if section is already active (for direct loading of tab)
    const reengageSection = document.getElementById("reengagement-section");
    if (reengageSection && reengageSection.style.display !== "none") {
        loadInactiveUsers();
        loadReengagementStats();
        loadReengagementHistory();
    }
});