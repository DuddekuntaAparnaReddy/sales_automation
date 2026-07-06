// Outbound calling and text chatbot conversations admin logic

let allConvsCache = [];

async function loadConversations() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/conversations/logs");
        const data = await response.json();
        
        allConvsCache = data;

        const list = document.getElementById("conversations-list");
        if (!list) return;
        list.innerHTML = "";

        if (data.length === 0) {
            list.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); font-style: italic;">No conversation records found.</td></tr>`;
            return;
        }

        data.forEach(conv => {
            // conv is { id, user_id, user_name, user_email, user_message, ai_response, timestamp }
            const dateStr = conv.timestamp ? new Date(conv.timestamp).toLocaleString() : "N/A";
            
            // Trim messages for clean table grid display
            const queryTrim = conv.user_message.length > 50 ? conv.user_message.substring(0, 50) + "..." : conv.user_message;
            const replyTrim = conv.ai_response.length > 50 ? conv.ai_response.substring(0, 50) + "..." : conv.ai_response;

            list.innerHTML += `
            <tr>
                <td>
                    <div style="font-weight: 600;">${conv.user_name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${conv.user_email}</div>
                </td>
                <td title="${conv.user_message}">${queryTrim}</td>
                <td title="${conv.ai_response}">${replyTrim}</td>
                <td style="font-size: 0.8rem; color: var(--text-secondary);">${dateStr}</td>
                <td>
                    <button class="btn-action" style="padding: 4px 8px; font-size: 11px;" onclick="viewConversationThread('${conv.user_email}', '${conv.user_name}')">
                        View Thread
                    </button>
                </td>
            </tr>
            `;
        });
    } catch (error) {
        console.error("Error loading conversations in admin:", error);
    }
}

async function loadConversationStats() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/conversations/stats");
        const data = await response.json();

        // Populate stats cards
        document.getElementById("conv-stat-total").innerText = data.total_conversations || 0;
        document.getElementById("conv-stat-users").innerText = data.unique_users || 0;
        
        const topFaq = data.faqs && data.faqs.length > 0 ? data.faqs[0].topic.replace(" Inquiry", "") : "None";
        document.getElementById("conv-stat-faq").innerText = topFaq;

        // Populate FAQs sidebar
        const faqList = document.getElementById("conv-faq-list");
        if (!faqList) return;
        faqList.innerHTML = "";

        if (!data.faqs || data.faqs.length === 0) {
            faqList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; font-style: italic;">No trends identified yet.</div>`;
            return;
        }

        data.faqs.forEach(faq => {
            faqList.innerHTML += `
            <div style="background: var(--surface-primary); border: 1px solid var(--border-color); border-radius: 0.5rem; padding: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 0.85rem; font-weight: 500; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 170px;">
                    ${faq.topic}
                </div>
                <span class="badge" style="background: rgba(99, 102, 241, 0.15); color: var(--primary); font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">
                    ${faq.count} hits
                </span>
            </div>
            `;
        });
    } catch (error) {
        console.error("Error loading conversation stats:", error);
    }
}

function viewConversationThread(email, name) {
    // Filter conversations for the specific email
    const userConvs = allConvsCache.filter(c => c.user_email === email);
    
    // Sort chronological (oldest first for chat thread view)
    userConvs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    document.getElementById("thread-modal-user-info").innerText = `Customer: ${name} (${email === 'N/A' ? 'Guest' : email})`;
    
    const chatBox = document.getElementById("thread-chat-box");
    if (!chatBox) return;
    chatBox.innerHTML = "";

    if (userConvs.length === 0) {
        chatBox.innerHTML = `<div style="color: var(--text-muted); font-style: italic; text-align: center; margin: auto;">No messages in thread.</div>`;
    }

    userConvs.forEach(c => {
        // Message turn bubble rendering
        const timeStr = c.timestamp ? new Date(c.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "";
        
        // 1. User query bubble (Right aligned)
        chatBox.innerHTML += `
        <div style="align-self: flex-end; max-width: 80%; display: flex; flex-direction: column; align-items: flex-end;">
            <div style="background: var(--gradient-primary); color: white; padding: 0.65rem 1rem; border-radius: 0.75rem 0.75rem 0 0.75rem; font-size: 0.9rem; line-height: 1.4; word-break: break-word;">
                ${c.user_message}
            </div>
            <span style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem;">You (${timeStr})</span>
        </div>
        `;

        // 2. Bot reply bubble (Left aligned)
        chatBox.innerHTML += `
        <div style="align-self: flex-start; max-width: 80%; display: flex; flex-direction: column; align-items: flex-start;">
            <div style="background: var(--surface-secondary); border: 1px solid var(--border-color); color: var(--text-primary); padding: 0.65rem 1rem; border-radius: 0.75rem 0.75rem 0.75rem 0; font-size: 0.9rem; line-height: 1.4; word-break: break-word;">
                ${c.ai_response}
            </div>
            <span style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem;">Salesbot (${timeStr})</span>
        </div>
        `;
    });

    document.getElementById("conversation-thread-modal").style.display = "flex";
    
    // Auto-scroll chat box to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function closeConversationThreadModal() {
    document.getElementById("conversation-thread-modal").style.display = "none";
}

// Hook onload and refresh on showSection
document.addEventListener("DOMContentLoaded", () => {
    // Intercept showSection to load conversations when tab becomes active
    const originalShowSection = window.showSection;
    if (typeof originalShowSection === "function") {
        window.showSection = function(section, element) {
            originalShowSection(section, element);
            if (section === "conversations") {
                loadConversations();
                loadConversationStats();
            }
        };
    }
});
