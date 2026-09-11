// AI Telephony Console client-side script for Salesbot
let callTimer = null;
let callDuration = 0;
let activeCallData = null;
let currentCallState = 'idle'; // idle, ringing, in-progress, completed
let activeCategory = 'General';

document.addEventListener('DOMContentLoaded', () => {
  // Check auth route protection
  const session = getSession();
  if (!session) {
    window.location.href = 'login.html?redirect=telephony.html';
    return;
  }
  
  // Render Lucide icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // Load initial logs table
  fetchCallHistory();
});

// Fetch historical call logs from SQL DB
async function fetchCallHistory() {
  const tableBody = document.getElementById('historyTableBody');
  if (!tableBody) return;
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/telephony/history');
    if (response.ok) {
      const data = await response.json();
      tableBody.innerHTML = '';
      
      if (!data || data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No call logs recorded.</td></tr>';
        return;
      }
      
      data.forEach(call => {
        const tr = document.createElement('tr');
        const formattedDate = call.created_at ? new Date(call.created_at).toLocaleString() : 'N/A';
        
        let badgeClass = 'simulated';
        if (call.status.toLowerCase() === 'ringing') badgeClass = 'ringing';
        if (call.status.toLowerCase() === 'completed') badgeClass = 'completed';
        if (call.status.toLowerCase() === 'failed') badgeClass = 'failed';
        
        tr.innerHTML = `
          <td>${formattedDate}</td>
          <td>${call.phone_number}</td>
          <td style="font-family: monospace; font-size: 0.8rem;">${call.call_sid || 'N/A'}</td>
          <td>${call.category}</td>
          <td><span class="status-badge ${badgeClass}">${call.status}</span></td>
          <td>
            <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="viewCallSummary('${call.call_sid}', '${call.phone_number}', '${call.category}')">
              <i data-lucide="eye" style="width: 0.75rem; height: 0.75rem; display: inline; vertical-align: middle; margin-right: 0.25rem;"></i> View
            </button>
          </td>
        `;
        tableBody.appendChild(tr);
      });
      
      if (typeof lucide !== 'undefined') {
        lucide.createIcons();
      }
    }
  } catch (error) {
    console.error('Error fetching call logs:', error);
  }
}

// Trigger outbound call
async function triggerOutboundCall() {
  const phoneInput = document.getElementById('phoneInput');
  const categorySelect = document.getElementById('categorySelect');
  const webhookInput = document.getElementById('webhookInput');
  const triggerBtn = document.getElementById('triggerCallBtn');
  
  const phoneNumber = phoneInput.value.trim();
  activeCategory = categorySelect.value;
  let webhookUrl = webhookInput.value.trim();
  if (webhookUrl.includes('127.0.0.1') || webhookUrl.includes('localhost')) {
    webhookUrl = '';
  }
  
  if (!phoneNumber || phoneNumber === '+91') {
    alert('Please enter a valid destination phone number.');
    return;
  }
  
  // Disable button while processing
  triggerBtn.disabled = true;
  triggerBtn.innerHTML = '<i class="chat-loading" style="display:inline-flex; width: 1.1rem; height: 1.1rem;"><span class="loading-dot"></span><span class="loading-dot"></span></i> Connecting...';
  
  const session = getSession();
  const userId = session ? session.user_id : null;
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/telephony/make-call', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone_number: phoneNumber,
        category: activeCategory,
        user_id: userId,
        webhook_url: webhookUrl
      })
    });
    
    const result = await response.json();
    if (response.ok) {
      activeCallData = result.call;
      startCallMonitorConsole(phoneNumber, result.simulation);
    } else {
      alert('Failed to initiate call: ' + (result.error || 'Unknown error'));
      triggerBtn.disabled = false;
      triggerBtn.innerHTML = '<i data-lucide="phone-outgoing"></i> Call Customer';
    }
  } catch (error) {
    console.error('Error triggering outbound call:', error);
    alert('Error connecting to backend server. Ensure Flask is active.');
    triggerBtn.disabled = false;
    triggerBtn.innerHTML = '<i data-lucide="phone-outgoing"></i> Call Customer';
  }
  
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

// Start visual console
function startCallMonitorConsole(phoneNumber, isSimulation) {
  // Hide Idle block, show Active block
  document.getElementById('stateIdle').style.display = 'none';
  document.getElementById('stateActive').style.display = 'block';
  
  document.getElementById('callStatusNumber').textContent = phoneNumber;
  document.getElementById('callStatusHeader').textContent = isSimulation ? 'Dialing Customer (Simulated)...' : 'Dialing Customer (Twilio)...';
  document.getElementById('callOrb').className = 'call-status-orb ringing';
  
  const simDialogBox = document.getElementById('simDialogBox');
  simDialogBox.innerHTML = '<div class="sim-msg sys">Dialing...</div>';
  
  callDuration = 0;
  document.getElementById('timerLabel').textContent = '00:00';
  
  // Transition to connected status after 3.5 seconds
  setTimeout(() => {
    connectCall(isSimulation);
  }, 3500);
}

// Connect Call state
function connectCall(isSimulation) {
  currentCallState = 'in-progress';
  document.getElementById('callOrb').className = 'call-status-orb';
  document.getElementById('callStatusHeader').textContent = isSimulation ? 'Call In-Progress (Simulated Console)' : 'Call Connected (Live Webhook)';
  document.getElementById('waveformWrapper').style.display = 'flex';
  
  // Start count-up timer
  callTimer = setInterval(() => {
    callDuration++;
    const minutes = String(Math.floor(callDuration / 60)).padStart(2, '0');
    const seconds = String(callDuration % 60).padStart(2, '0');
    document.getElementById('timerLabel').textContent = `${minutes}:${seconds}`;
  }, 1000);
  
  const simDialogBox = document.getElementById('simDialogBox');
  simDialogBox.innerHTML += '<div class="sim-msg sys">Call answered by customer.</div>';
  
  // Play Welcome Greeting based on category
  let welcomeGreeting = "Hello! I am your Salesbot Voice Assistant. ";
  const cat = activeCategory.toLowerCase();
  if (cat === 'real estate') {
    welcomeGreeting += "I can help you search for land, apartments, and houses in Hyderabad. What requirements do you have?";
  } else if (cat === 'vehicles') {
    welcomeGreeting += "I can recommend hatchbacks, sedans, and SUVs under your budget. What car are you looking for?";
  } else if (cat === 'construction') {
    welcomeGreeting += "I can quote pricing for TATA Tiscon and JSW Neosteel rods. What is your construction type?";
  } else if (cat === 'fashion') {
    welcomeGreeting += "I can recommend formal shirts, wear, and casual chinos. What is your style preference?";
  } else {
    welcomeGreeting += "I can answer queries about Real Estate, Vehicles, Construction, Fashion, or Laptops. What are you looking for today?";
  }
  
  simDialogBox.innerHTML += `<div class="sim-msg bot">Bot: ${welcomeGreeting}</div>`;
  simDialogBox.scrollTop = simDialogBox.scrollHeight;
  
  // Show manual simulation speech input row if running in simulated mode
  if (isSimulation) {
    document.getElementById('simInputRow').style.display = 'flex';
  } else {
    simDialogBox.innerHTML += '<div class="sim-msg sys">Twilio webhook routing active. User speaks into mobile to talk.</div>';
  }
}

// Speak entry keypress handler
function handleSimKeyPress(event) {
  if (event.key === 'Enter') {
    submitSimSpeech();
  }
}

// User speech simulator trigger
async function submitSimSpeech() {
  const input = document.getElementById('simTextInput');
  const userSpeech = input.value.trim();
  if (!userSpeech) return;
  
  input.value = '';
  
  const simDialogBox = document.getElementById('simDialogBox');
  simDialogBox.innerHTML += `<div class="sim-msg user">Customer: ${userSpeech}</div>`;
  simDialogBox.scrollTop = simDialogBox.scrollHeight;
  
  // Add system processing loader
  const loaderId = 'sim_loader_' + Date.now();
  simDialogBox.innerHTML += `<div class="sim-msg sys" id="${loaderId}">AI Assistant is typing/speaking...</div>`;
  simDialogBox.scrollTop = simDialogBox.scrollHeight;
  
  const session = getSession();
  const userId = session ? session.user_id : null;
  
  try {
    // Post to `/api/telephony/twiml` webhook directly with simulated SpeechResult payload
    const formData = new FormData();
    formData.append('SpeechResult', userSpeech);
    formData.append('CallSid', activeCallData ? activeCallData.call_sid : 'sim_test');
    
    const url = `http://127.0.0.1:8000/api/telephony/twiml?category=${activeCategory}` + (userId ? `&user_id=${userId}` : '');
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData
    });
    
    const twimlXml = await response.text();
    
    // Remove processing status loader
    const loader = document.getElementById(loaderId);
    if (loader) loader.remove();
    
    // Parse TwiML xml to extract <Say> response value
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(twimlXml, "text/xml");
    const sayTag = xmlDoc.getElementsByTagName("Say")[0];
    const botResponse = sayTag ? sayTag.textContent : "I could not generate a response. Please repeat.";
    
    simDialogBox.innerHTML += `<div class="sim-msg bot">Bot: ${botResponse}</div>`;
    simDialogBox.scrollTop = simDialogBox.scrollHeight;
    
  } catch (error) {
    console.error('Error posting speech result to simulated webhook:', error);
    const loader = document.getElementById(loaderId);
    if (loader) loader.remove();
    simDialogBox.innerHTML += '<div class="sim-msg sys">Communication link issue with AI backend.</div>';
    simDialogBox.scrollTop = simDialogBox.scrollHeight;
  }
}

// Hangup Call
function hangupCall() {
  clearInterval(callTimer);
  currentCallState = 'idle';
  
  document.getElementById('stateActive').style.display = 'none';
  document.getElementById('stateIdle').style.display = 'flex';
  document.getElementById('waveformWrapper').style.display = 'none';
  document.getElementById('simInputRow').style.display = 'none';
  
  // Re-enable settings block
  document.getElementById('triggerCallBtn').disabled = false;
  document.getElementById('triggerCallBtn').innerHTML = '<i data-lucide="phone-outgoing"></i> Call Customer';
  
  alert(`Call hung up. Duration: ${callDuration} seconds.`);
  
  // Refresh call list logs
  fetchCallHistory();
}

// View dialogue summary details
function viewCallSummary(callSid, phoneNumber, category) {
  alert(`Call Detail Summary:\n\nReference SID: ${callSid}\nDestination: ${phoneNumber}\nSales Domain: ${category}\nStatus: Active/Logged`);
}
