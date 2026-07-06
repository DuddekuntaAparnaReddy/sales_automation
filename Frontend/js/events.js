async function loadEvents() {
    try {
        const response = await fetch("http://127.0.0.1:8000/events?status=Active");
        const data = await response.json();
        
        const grid = document.getElementById("events-grid-container");
        if (!grid) return;

        grid.innerHTML = "";

        if (!data || data.length === 0) {
            grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem; background: var(--bg-secondary); border: 1px dashed var(--border-color); border-radius: 1rem;">
                <i data-lucide="calendar" style="width: 3rem; height: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                <h3 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; color: white;">No Events Available</h3>
                <p style="color: var(--text-secondary); font-size: 0.95rem;">Please check back later for upcoming product summits and webinars.</p>
            </div>
            `;
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        data.forEach(event => {
            // event is [event_id, event_name, event_date, location, invitation_status, description, time, event_type, registration_deadline]
            const eventId = event[0];
            const eventName = event[1];
            const eventDate = event[2];
            const venue = event[3];
            const status = event[4];
            const description = event[5] || `Join us for this exciting ${event[7] || 'event'}!`;
            const time = event[6] || "";
            const eventType = event[7] || "Special Event";
            const deadline = event[8] || "";

            // Format date if possible
            const formattedDate = eventDate ? new Date(eventDate).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' }) : "TBA";
            const formattedDeadline = deadline ? new Date(deadline).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' }) : "";

            grid.innerHTML += `
            <div class="event-card">
                <div>
                    <span class="event-type-badge">${eventType}</span>
                    <h2 class="event-title">${eventName}</h2>
                    
                    <div class="event-meta">
                        <div class="event-meta-item">
                            <i data-lucide="calendar" style="width: 1rem; height: 1rem; color: var(--primary);"></i>
                            <span>${formattedDate}</span>
                        </div>
                        ${time ? `
                        <div class="event-meta-item">
                            <i data-lucide="clock" style="width: 1rem; height: 1rem; color: var(--primary);"></i>
                            <span>${time}</span>
                        </div>
                        ` : ''}
                        <div class="event-meta-item">
                            <i data-lucide="map-pin" style="width: 1rem; height: 1rem; color: var(--primary);"></i>
                            <span>${venue}</span>
                        </div>
                        ${formattedDeadline ? `
                        <div class="event-meta-item" style="color: var(--danger); font-weight: 500;">
                            <i data-lucide="alert-circle" style="width: 1rem; height: 1rem;"></i>
                            <span>Register by: ${formattedDeadline}</span>
                        </div>
                        ` : ''}
                    </div>

                    <p class="event-description">${description}</p>
                </div>

                <button class="register-btn" onclick="registerEvent(${eventId}, '${eventName.replace(/'/g, "\\'")}')">
                    Register Now
                </button>
            </div>
            `;
        });

        if (window.lucide) {
            window.lucide.createIcons();
        }
    } catch (error) {
        console.log("Error loading events from backend:", error);
    }
}

// Step 1: Show confirmation dialog
function registerEvent(eventId, eventName) {
    // Show confirmation dialog
    const msgEl = document.getElementById("confirm-message");
    if (msgEl) {
        msgEl.textContent = `Do you want to register for "${eventName}"?`;
    }

    // Store pending details on the Yes button
    const yesBtn = document.getElementById("confirm-yes-btn");
    if (yesBtn) {
        yesBtn.dataset.eventId   = eventId;
        yesBtn.dataset.eventName = eventName;
    }

    const confirmPopup = document.getElementById("confirm-popup");
    if (confirmPopup) {
        confirmPopup.style.display = "flex";
        if (window.lucide) window.lucide.createIcons();
    }
}

// Step 2: User clicked "Yes, Register" — do actual registration
async function confirmRegistration() {
    const yesBtn    = document.getElementById("confirm-yes-btn");
    const eventId   = yesBtn ? yesBtn.dataset.eventId   : null;
    const eventName = yesBtn ? yesBtn.dataset.eventName : "";

    // Close confirmation dialog immediately
    closeConfirmPopup();

    let full_name = "";
    let email     = "";
    let userId    = null;

    // Retrieve logged-in user info from localStorage
    const sessionStr = localStorage.getItem("session");
    if (sessionStr) {
        try {
            const session = JSON.parse(sessionStr);
            full_name = session.full_name || session.name || "";
            email     = session.email    || "";
            userId    = session.user_id  || null;
        } catch (e) {
            console.error("Error parsing session storage:", e);
        }
    }
    // Fallback to legacy "user" key
    if (!full_name || !email) {
        const userStr = localStorage.getItem("user");
        if (userStr) {
            try {
                const user = JSON.parse(userStr);
                full_name = user.full_name || user.name || "";
                email     = user.email    || "";
                userId    = user.user_id  || null;
            } catch (e) {
                console.error("Error parsing user storage:", e);
            }
        }
    }

    // Prompt if still missing (guest user)
    if (!full_name || !email) {
        full_name = prompt("Enter Your Name:");
        if (!full_name) return;
        email = prompt("Enter Your Email:");
        if (!email) return;
    }

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/event/register",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    full_name: full_name,
                    email:     email,
                    event_name: eventName,
                    event_id:   eventId,
                    user_id:    userId
                })
            }
        );

        const data = await response.json();
        if (response.ok) {
            const msgEl = document.getElementById("popup-message");
            if (msgEl) {
                msgEl.innerText = `Successfully registered for "${eventName}". A confirmation email has been dispatched to ${email}.`;
            }
            const popup = document.getElementById("popup");
            if (popup) popup.style.display = "flex";
            if (window.lucide) window.lucide.createIcons();
        } else {
            alert(data.error || "Registration failed. Please try again.");
        }

    } catch (error) {
        console.error("Registration error:", error);
        alert("Backend Connection Error. Please make sure the server is running.");
    }
}

function closeConfirmPopup() {
    const confirmPopup = document.getElementById("confirm-popup");
    if (confirmPopup) confirmPopup.style.display = "none";
}

function closePopup() {
    const popup = document.getElementById("popup");
    if (popup) popup.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
    // Ensure user is logged in before showing events
    if (!localStorage.getItem("session")) {
        window.location.href = "login.html";
        return;
    }
    loadEvents();
});