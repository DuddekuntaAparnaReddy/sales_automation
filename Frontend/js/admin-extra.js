let editingEventId = null;

function showEventForm() {
    const form = document.getElementById("event-form");
    if (form.style.display === "none" || !form.style.display) {
        form.style.display = "block";
    } else {
        form.style.display = "none";
        editingEventId = null;
        document.getElementById("event_name").value = "";
        document.getElementById("event_type").value = "Product Launch";
        document.getElementById("event_date").value = "";
        document.getElementById("event_time").value = "";
        document.getElementById("location").value = "";
        document.getElementById("registration_deadline").value = "";
        document.getElementById("event_description").value = "";
        document.getElementById("invitation_status").value = "Active";
    }
}

async function saveEvent() {
    const event_name = document.getElementById("event_name").value;
    const event_type = document.getElementById("event_type").value;
    const event_date = document.getElementById("event_date").value;
    const time = document.getElementById("event_time").value;
    const location = document.getElementById("location").value;
    const registration_deadline = document.getElementById("registration_deadline").value;
    const description = document.getElementById("event_description").value;
    const invitation_status = document.getElementById("invitation_status").value;

    if (!event_name) {
        alert("Event Name is required");
        return;
    }

    const url = editingEventId 
        ? `http://127.0.0.1:8000/event/${editingEventId}`
        : "http://127.0.0.1:8000/event";
    const method = editingEventId ? "PUT" : "POST";

    // Set default created_by to logged-in user id or 1
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    const created_by = user.user_id || 1;

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                event_name,
                event_type,
                event_date,
                time,
                location,
                registration_deadline,
                description,
                invitation_status,
                created_by
            })
        });

        const data = await response.json();
        alert(data.message || data.error);

        // Reset
        editingEventId = null;
        document.getElementById("event_name").value = "";
        document.getElementById("event_type").value = "Product Launch";
        document.getElementById("event_date").value = "";
        document.getElementById("event_time").value = "";
        document.getElementById("location").value = "";
        document.getElementById("registration_deadline").value = "";
        document.getElementById("event_description").value = "";
        document.getElementById("invitation_status").value = "Active";
        document.getElementById("event-form").style.display = "none";

        loadEventsMgmt();
        // Reload global events page data if function is active
        if (typeof loadEvents === "function") loadEvents();

    } catch (error) {
        alert("Backend Connection Error");
    }
}

function editEvent(id, name, type, date, time, location, deadline, description, status) {
    const form = document.getElementById("event-form");
    form.style.display = "block";
    document.getElementById("event_name").value = name || "";
    document.getElementById("event_type").value = type || "Product Launch";
    document.getElementById("event_date").value = date || "";
    document.getElementById("event_time").value = time || "";
    document.getElementById("location").value = location || "";
    document.getElementById("registration_deadline").value = deadline || "";
    document.getElementById("event_description").value = description || "";
    document.getElementById("invitation_status").value = status || "Active";
    editingEventId = id;
    // Scroll the form into view so admin doesn't miss it
    form.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Step 1: Show the styled delete confirmation modal
function deleteEvent(id, name) {
    const modal = document.getElementById("delete-confirm-modal");
    const msgEl  = document.getElementById("delete-confirm-msg");
    const yesBtn = document.getElementById("delete-confirm-yes");

    if (msgEl) {
        msgEl.textContent = `Are you sure you want to delete "${name || 'this event'}"? All its registrations will also be removed.`;
    }
    yesBtn.dataset.deleteId = id;

    modal.style.display = "flex";
    if (window.lucide) lucide.createIcons();
}

// Step 2: User clicked "Yes, Delete"
async function executeDeleteEvent() {
    const yesBtn = document.getElementById("delete-confirm-yes");
    const id = yesBtn.dataset.deleteId;
    closeDeleteConfirmModal();

    try {
        const response = await fetch(`http://127.0.0.1:8000/event/${id}`, {
            method: "DELETE"
        });
        const data = await response.json();
        if (!response.ok) {
            alert(data.error || "Delete failed");
        }
        loadEventsMgmt();
        if (typeof loadEvents === "function") loadEvents();
    } catch (error) {
        alert("Backend Connection Error");
    }
}

function closeDeleteConfirmModal() {
    const modal = document.getElementById("delete-confirm-modal");
    if (modal) modal.style.display = "none";
}

async function loadEventsStats() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/events/stats");
        const data = await response.json();
        const totalEl = document.getElementById("events-stat-total");
        const upcomingEl = document.getElementById("events-stat-upcoming");
        const completedEl = document.getElementById("events-stat-completed");
        const regsEl = document.getElementById("events-stat-registrations");

        if (totalEl) totalEl.innerText = data.total_events || 0;
        if (upcomingEl) upcomingEl.innerText = data.upcoming_events || 0;
        if (completedEl) completedEl.innerText = data.completed_events || 0;
        if (regsEl) regsEl.innerText = data.total_registrations || 0;
    } catch (error) {
        console.log("Error loading event stats:", error);
    }
}

async function loadEventsMgmt() {
    try {
        const search = document.getElementById("event_search") ? document.getElementById("event_search").value : "";
        const type = document.getElementById("event_filter_type") ? document.getElementById("event_filter_type").value : "";
        const status = document.getElementById("event_filter_status") ? document.getElementById("event_filter_status").value : "";
        
        const url = `http://127.0.0.1:8000/events?search=${encodeURIComponent(search)}&event_type=${encodeURIComponent(type)}&status=${encodeURIComponent(status)}`;
        const response = await fetch(url);
        const data = await response.json();

        const list = document.getElementById("events-mgmt-list");
        if (!list) return;

        list.innerHTML = "";
        data.forEach(event => {
            // event is [event_id, event_name, event_date, location, invitation_status, description, time, event_type, registration_deadline]
            const eventId = event[0];
            const name = event[1];
            const dateVal = event[2];
            const loc = event[3];
            const statusVal = event[4];
            const desc = event[5] || "";
            const timeVal = event[6] || "";
            const typeVal = event[7] || "";
            const deadlineVal = event[8] || "";

            // Escape strings for onclick attributes
            const escName = name.replace(/'/g, "\\'");
            const escType = typeVal.replace(/'/g, "\\'");
            const escLoc = loc.replace(/'/g, "\\'");
            const escTime = timeVal.replace(/'/g, "\\'");
            const escDeadline = deadlineVal.replace(/'/g, "\\'");
            const escDesc = desc.replace(/'/g, "\\'").replace(/\n/g, "\\n");
            const escStatus = statusVal.replace(/'/g, "\\'");

            list.innerHTML += `
            <tr>
                <td><strong>${name}</strong></td>
                <td>${typeVal}</td>
                <td>${dateVal} ${timeVal}</td>
                <td>${loc}</td>
                <td>
                    <span class="badge ${statusVal === 'Active' ? 'badge-success' : 'badge-danger'}">
                        ${statusVal}
                    </span>
                </td>
                <td>
                    <button class="btn-action" style="background: #3b82f6; padding: 4px 8px; font-size: 11px; margin-right: 5px;" onclick="viewRegistrations(${eventId}, '${escName}')">Registrations</button>
                    <button class="btn-action" style="background: #eab308; padding: 4px 8px; font-size: 11px; margin-right: 5px;" onclick="editEvent(${eventId}, '${escName}', '${escType}', '${dateVal}', '${escTime}', '${escLoc}', '${escDeadline}', '${escDesc}', '${escStatus}')">Edit</button>
                    <button class="btn-action" style="background: #ef4444; padding: 4px 8px; font-size: 11px;" onclick="deleteEvent(${eventId}, '${escName}')">Delete</button>
                </td>
            </tr>
            `;
        });

        loadEventsStats();
    } catch (error) {
        console.log("Error loading events in mgmt:", error);
    }
}

async function viewRegistrations(eventId, eventName) {
    const modal = document.getElementById("event-registrations-modal");
    if (!modal) return;

    document.getElementById("event-registrations-modal-subtitle").innerText = `Event: ${eventName}`;
    modal.style.display = "flex";

    try {
        const response = await fetch(`http://127.0.0.1:8000/registrations?event_id=${eventId}`);
        const data = await response.json();

        const tbody = document.getElementById("event-registrations-modal-list");
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No registrations yet.</td></tr>`;
            return;
        }

        data.forEach(reg => {
            // reg is [registration_id, full_name, email, event_name, registered_at, event_id, user_id, registration_date, status]
            const regDate = reg[7] ? new Date(reg[7]).toLocaleString() : (reg[4] ? new Date(reg[4]).toLocaleString() : "N/A");
            const statusVal = reg[8] || "Confirmed";
            tbody.innerHTML += `
            <tr>
                <td>${reg[1]}</td>
                <td>${reg[2]}</td>
                <td>${regDate}</td>
                <td>
                    <span class="badge badge-success">${statusVal}</span>
                </td>
            </tr>
            `;
        });
    } catch (error) {
        console.log("Error loading event registrations:", error);
    }
}

function closeEventRegistrationsModal() {
    const modal = document.getElementById("event-registrations-modal");
    if (modal) modal.style.display = "none";
}

async function loadFeedbackResponses() {
    try {
        const response = await fetch("http://127.0.0.1:8000/feedback/all");
        const data = await response.json();

        const list = document.getElementById("feedback-mgmt-list");
        if (!list) return;

        list.innerHTML = "";
        data.forEach(fb => {
            // fb is [feedback_id, rating, comments, feedback_date]
            list.innerHTML += `
            <tr>
                <td>⭐ ${fb[1]} / 5</td>
                <td>${fb[2] || 'No comments'}</td>
                <td>${new Date(fb[3]).toLocaleString()}</td>
            </tr>
            `;
        });
    } catch (error) {
        console.log("Error loading feedback in mgmt:", error);
    }
}

// Hook onload
document.addEventListener("DOMContentLoaded", () => {
    loadEventsMgmt();
    loadFeedbackResponses();
});
