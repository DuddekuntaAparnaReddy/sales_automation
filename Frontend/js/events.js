async function loadEvents() {
    try {
        // Fetch registrations first if user is logged in
        let registeredEventIds = new Set();
        const sessionStr = localStorage.getItem("session");
        if (sessionStr) {
            try {
                const session = JSON.parse(sessionStr);
                const userEmail = session.email || "";
                const userId = session.user_id || null;
                
                let regUrl = "";
                if (userId) {
                    regUrl = `http://127.0.0.1:8000/registrations?user_id=${userId}`;
                } else if (userEmail) {
                    regUrl = `http://127.0.0.1:8000/registrations?email=${encodeURIComponent(userEmail)}`;
                }
                
                if (regUrl) {
                    const regResponse = await fetch(regUrl);
                    if (regResponse.ok) {
                        const regs = await regResponse.json();
                        regs.forEach(r => {
                            if (r[5]) { // event_id is at index 5
                                registeredEventIds.add(parseInt(r[5], 10));
                            }
                        });
                    }
                }
            } catch (e) {
                console.error("Error loading user registrations:", e);
            }
        }

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
            const description = event[5];
            const time = event[6];
            const eventType = event[7] || "Special Event";
            const deadline = event[8] || "";

            // Format date if possible
            const formattedDate = eventDate ? new Date(eventDate).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' }) : "TBA";
            const formattedDeadline = deadline ? new Date(deadline).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' }) : "";

            // Fallback values to show them "for sure"
            const dateVal = formattedDate || "TBA";
            const timeVal = time ? time : "TBA";
            const venueVal = venue ? venue : "TBA";
            const descriptionVal = description ? description : "Join us for this exciting event!";

            // 1. Check if the event date is in the past
            let isCompleted = false;
            if (eventDate) {
                const parts = eventDate.split('-');
                if (parts.length === 3) {
                    const year = parseInt(parts[0], 10);
                    const month = parseInt(parts[1], 10) - 1; // 0-indexed
                    const day = parseInt(parts[2], 10);
                    
                    const eventDateObj = new Date(year, month, day);
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    isCompleted = eventDateObj < today;
                }
            }

            // 2. Check if the user has already registered
            const isRegistered = registeredEventIds.has(parseInt(eventId, 10));

            // 3. Render action button based on status
            let actionButtonHtml = "";
            if (isCompleted) {
                actionButtonHtml = `
                <button class="register-btn" disabled style="background: rgba(239, 68, 68, 0.08); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.25); cursor: not-allowed; font-weight: 600;">
                    Registration Closed
                </button>
                `;
            } else if (isRegistered) {
                actionButtonHtml = `
                <button class="register-btn" disabled style="background: rgba(34, 197, 94, 0.08); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.25); cursor: not-allowed; font-weight: 600;">
                    Already Registered
                </button>
                `;
            } else {
                actionButtonHtml = `
                <button class="register-btn" onclick="registerEvent(${eventId}, '${eventName.replace(/'/g, "\\'")}', '${eventDate}')">
                    Register Now
                </button>
                `;
            }

            grid.innerHTML += `
            <div class="event-card">
                <div>
                    <span class="event-type-badge">${eventType}</span>
                    <h2 class="event-title">${eventName}</h2>
                    
                    <div class="event-meta">
                        <div class="event-meta-item">
                            <i data-lucide="calendar" style="width: 1rem; height: 1rem; color: var(--primary);"></i>
                            <span>Date: ${dateVal}</span>
                        </div>
                        <div class="event-meta-item">
                            <i data-lucide="clock" style="width: 1rem; height: 1rem; color: var(--primary);"></i>
                            <span>Time: ${timeVal}</span>
                        </div>
                        <div class="event-meta-item">
                            <i data-lucide="map-pin" style="width: 1rem; height: 1rem; color: var(--primary);"></i>
                            <span>Place: ${venueVal}</span>
                        </div>
                        ${formattedDeadline ? `
                        <div class="event-meta-item" style="color: var(--danger); font-weight: 500;">
                            <i data-lucide="alert-circle" style="width: 1rem; height: 1rem;"></i>
                            <span>Register by: ${formattedDeadline}</span>
                        </div>
                        ` : ''}
                    </div>

                    <p class="event-description"><strong>Description:</strong> ${descriptionVal}</p>
                </div>

                ${actionButtonHtml}
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

// Step 1: Show confirmation dialog or popup if completed
function registerEvent(eventId, eventName, eventDateStr) {
    if (eventDateStr) {
        // Parse YYYY-MM-DD manually to avoid timezone shift
        const parts = eventDateStr.split('-');
        if (parts.length === 3) {
            const year = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1; // 0-indexed
            const day = parseInt(parts[2], 10);
            
            const eventDateObj = new Date(year, month, day);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (eventDateObj < today) {
                showPopup("Event Completed", "This event has already completed. Registration is closed.", false);
                return;
            }
        }
    }

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
            showPopup(
                "Registration Successful!", 
                `Successfully registered for "${eventName}". A confirmation email has been dispatched to ${email}.`, 
                true
            );
            // Reload the events display to update button states
            loadEvents();
        } else {
            showPopup("Registration Failed", data.error || "Registration failed. Please try again.", false);
        }

    } catch (error) {
        console.error("Registration error:", error);
        showPopup(
            "Connection Error", 
            "Backend Connection Error. Please make sure the server is running.", 
            false
        );
    }
}

// Custom Modal Popup Helper
function showPopup(title, message, isSuccess = true) {
    const titleEl = document.getElementById("popup-title");
    const msgEl = document.getElementById("popup-message");
    const iconContainer = document.getElementById("popup-icon-container");
    const iconEl = document.getElementById("popup-icon");
    const popup = document.getElementById("popup");
    
    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = message;
    
    if (iconContainer && iconEl) {
        if (isSuccess) {
            iconContainer.style.background = "rgba(34, 197, 94, 0.15)";
            iconEl.setAttribute("data-lucide", "check-circle");
            iconEl.style.color = "var(--success)";
        } else {
            iconContainer.style.background = "rgba(239, 68, 68, 0.15)";
            iconEl.setAttribute("data-lucide", "x-circle");
            iconEl.style.color = "#ef4444";
        }
    }
    
    if (popup) {
        popup.style.display = "flex";
        if (window.lucide) window.lucide.createIcons();
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