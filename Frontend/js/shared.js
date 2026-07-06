// Shared Javascript for Salesbot Sales & Marketing Bot UI
// Execute theme check immediately to prevent flicker before CSS/HTML loads
(function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
    document.body.classList.add('dark');
  } else {
    document.body.classList.remove('dark');
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initial Theme Set on Loaded Body
  const themeToggleButtons = document.querySelectorAll('.theme-toggle');
  themeToggleButtons.forEach(btn => {
    btn.addEventListener('click', toggleTheme);
  });

  // 2. Load Header and Footer Dynamically (if containers exist)
  renderHeader();
  renderFooter();

  // 3. Highlight Active Navigation Links
  highlightActiveLink();

  // 4. Initialize Lucide Icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }

  // 5. Route protection (Admin page guard)
  protectAdminRoute();
});

// Theme toggle logic
function toggleTheme() {
  const isDark = document.body.classList.toggle('dark');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Get current session
function getSession() {
  try {
    const sessionStr = localStorage.getItem('session');
    return sessionStr ? JSON.parse(sessionStr) : null;
  } catch (e) {
    return null;
  }
}

// Logout logic
function handleLogout() {
  localStorage.removeItem('session');
  window.location.href = 'index.html';
}

// Route Protection for Admin Dashboard & AI Assistant
function protectAdminRoute() {
  const session = getSession();
  const path = window.location.pathname;

  if (path.endsWith('admin.html')) {
    if (!session || session.role !== 'admin') {
      document.body.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; text-align: center; padding: 2rem; background-color: #0b0813; color: #f3f4f6;">
          <h1 style="font-size: 3rem; margin-bottom: 1rem; color: #ef4444;">Access Denied</h1>
          <p style="font-size: 1.2rem; margin-bottom: 2rem; color: #9ca3af;">You do not have permission to view the Admin Dashboard. Please log in as an administrator.</p>
          <a href="login.html?redirect=admin.html" style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #fff; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; font-weight: bold;">Login as Admin</a>
        </div>
      `;
    }
  }

  if (path.endsWith('ai-assistant.html')) {
    if (!session || session.role !== 'user') {
      document.body.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; text-align: center; padding: 2rem; background-color: #0b0813; color: #f3f4f6;">
          <h1 style="font-size: 3rem; margin-bottom: 1rem; color: #ef4444;">Access Denied</h1>
          <p style="font-size: 1.2rem; margin-bottom: 2rem; color: #9ca3af;">Only registered users are permitted to access the AI Assistant page. Administrators should navigate to the Admin Dashboard.</p>
          <a href="login.html?redirect=ai-assistant.html" style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #fff; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; font-weight: bold;">Login as User</a>
        </div>
      `;
    }
  }
}

// Dynamically generate the Navbar Header based on Session State
function renderHeader() {
  const headerContainer = document.getElementById('site-header');
  if (!headerContainer) return;

  const session = getSession();
  let menuHtml = '';
  let actionHtml = '';

  // Common Theme Toggle button
  const themeToggleBtn = `
    <button class="theme-toggle" aria-label="Toggle Theme">
      <i data-lucide="moon" class="moon-icon" style="width: 1.25rem; height: 1.25rem;"></i>
      <i data-lucide="sun" class="sun-icon" style="width: 1.25rem; height: 1.25rem;"></i>
    </button>
  `;

  if (!session) {
    // 1. GUEST / PUBLIC NAVIGATION
    menuHtml = `
      <li><a href="index.html" class="nav-link" id="nav-home"><i data-lucide="home" style="width: 1rem; height: 1rem;"></i> Home</a></li>
      <li><a href="about.html" class="nav-link" id="nav-about"><i data-lucide="info" style="width: 1rem; height: 1rem;"></i> About Us</a></li>
      <li><a href="contact.html" class="nav-link" id="nav-contact"><i data-lucide="mail" style="width: 1rem; height: 1rem;"></i> Contact Us</a></li>
      
      <li class="nav-item-dropdown">
        <a class="nav-link"><i data-lucide="user" style="width: 1rem; height: 1rem;"></i> AI Portal <i data-lucide="chevron-down" style="width: 0.8rem; height: 0.8rem;"></i></a>
        <div class="dropdown-menu">
          <a href="ai-assistant.html" class="dropdown-link">
            <span class="dropdown-link-title">AI Telesales</span>
          </a>
          <a href="promotions.html" class="dropdown-link">
            <span class="dropdown-link-title">Promotions & Offers</span>
          </a>
          <a href="events.html" class="dropdown-link">
            <span class="dropdown-link-title">Event Invitations</span>
          </a>
          <a href="profile.html" class="dropdown-link">
            <span class="dropdown-link-title">Profile</span>
          </a>
        </div>
      </li>
    `;
    actionHtml = `
      <a href="login.html" class="btn btn-secondary"><i data-lucide="log-in" style="width: 1rem; height: 1rem;"></i> Login</a>
      <a href="register.html" class="btn btn-primary"><i data-lucide="user-plus" style="width: 1rem; height: 1rem;"></i> Register</a>
    `;

  } else if (session.role === 'user') {
    // 2. LOGGED-IN USER NAVIGATION
    menuHtml = `
      <li><a href="index.html" class="nav-link" id="nav-home"><i data-lucide="home" style="width: 1rem; height: 1rem;"></i> Home</a></li>
      <li><a href="about.html" class="nav-link" id="nav-about"><i data-lucide="info" style="width: 1rem; height: 1rem;"></i> About Us</a></li>
      <li><a href="contact.html" class="nav-link" id="nav-contact"><i data-lucide="mail" style="width: 1rem; height: 1rem;"></i> Contact Us</a></li>
      
      <li class="nav-item-dropdown">
        <a class="nav-link"><i data-lucide="user" style="width: 1rem; height: 1rem;"></i> AI Portal <i data-lucide="chevron-down" style="width: 0.8rem; height: 0.8rem;"></i></a>
        <div class="dropdown-menu">
          <a href="ai-assistant.html" class="dropdown-link">
            <span class="dropdown-link-title">AI Telesales</span>
          </a>
          <a href="promotions.html" class="dropdown-link">
            <span class="dropdown-link-title">Promotions & Offers</span>
          </a>
          <a href="events.html" class="dropdown-link">
            <span class="dropdown-link-title">Event Invitations</span>
          </a>
          <a href="profile.html" class="dropdown-link">
            <span class="dropdown-link-title">Profile</span>
          </a>
        </div>
      </li>
    `;

    const initials = session.name ? session.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U';
    actionHtml = `
      <div class="user-profile-header-badge" onclick="showProfileModal()" style="display: flex; align-items: center; gap: 0.75rem; border: 1px solid var(--border-color); padding: 0.35rem 0.75rem 0.35rem 0.5rem; border-radius: 2rem; background-color: var(--surface-primary); cursor: pointer;">
        <div style="width: 2rem; height: 2rem; border-radius: 50%; background: var(--gradient-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem;">
          ${initials}
        </div>
        <div style="display: flex; flex-direction: column; text-align: left; line-height: 1.2;">
          <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">${session.name}</span>
          <span style="font-size: 0.7rem; color: var(--text-muted);">${session.email}</span>
        </div>
      </div>
      <button onclick="handleLogout()" class="btn btn-secondary" style="padding: 0.5rem 1rem;"><i data-lucide="log-out" style="width: 1rem; height: 1rem;"></i> Logout</button>
    `;

  } else if (session.role === 'admin') {
    // 3. LOGGED-IN ADMIN NAVIGATION (ON PUBLIC PAGES)
    menuHtml = `
      <li><a href="index.html" class="nav-link" id="nav-home"><i data-lucide="home" style="width: 1rem; height: 1rem;"></i> Home</a></li>
      <li><a href="about.html" class="nav-link" id="nav-about"><i data-lucide="info" style="width: 1rem; height: 1rem;"></i> About Us</a></li>
      <li><a href="contact.html" class="nav-link" id="nav-contact"><i data-lucide="mail" style="width: 1rem; height: 1rem;"></i> Contact Us</a></li>
      <li><a href="admin.html" class="nav-link" id="nav-admin-shortcut" style="color: var(--primary); font-weight: bold;"><i data-lucide="layout-dashboard" style="width: 1rem; height: 1rem;"></i> Dashboard</a></li>
    `;

    const initials = session.name ? session.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'AD';
    actionHtml = `
      <div class="user-profile-header-badge" onclick="showProfileModal()" style="display: flex; align-items: center; gap: 0.75rem; border: 1px solid var(--border-color); padding: 0.35rem 0.75rem 0.35rem 0.5rem; border-radius: 2rem; background-color: var(--surface-primary); cursor: pointer;">
        <div style="width: 2rem; height: 2rem; border-radius: 50%; background: var(--gradient-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem;">
          ${initials}
        </div>
        <div style="display: flex; flex-direction: column; text-align: left; line-height: 1.2;">
          <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">${session.name}</span>
          <span style="font-size: 0.7rem; color: var(--text-muted);">${session.email}</span>
        </div>
      </div>
      <button onclick="handleLogout()" class="btn btn-secondary" style="padding: 0.5rem 1rem;"><i data-lucide="log-out" style="width: 1rem; height: 1rem;"></i> Logout</button>
    `;
  }

  // Construct Header HTML
  headerContainer.innerHTML = `
    <div class="nav-container">
      <div class="logo" onclick="window.location.href='index.html'">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
        Salesbot
      </div>

      <nav>
        <ul class="nav-menu" id="nav-menu">
          ${menuHtml}
          <!-- Mobile Actions (Theme + Auth buttons) -->
          <div class="nav-actions-mobile">
            <div class="nav-actions-mobile-row">
              <span style="font-weight: 600;">Switch Theme</span>
              ${themeToggleBtn}
            </div>
            ${session ? `
            <div class="nav-actions-mobile-row" onclick="showProfileModal()" style="margin-top: 1rem; border-top: 1px solid var(--border-color); padding-top: 1rem; display: flex; align-items: center; gap: 0.75rem; cursor: pointer;">
              <div style="width: 2.25rem; height: 2.25rem; border-radius: 50%; background: var(--gradient-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem;">
                ${session.name ? session.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U'}
              </div>
              <div style="display: flex; flex-direction: column; text-align: left; line-height: 1.2;">
                <span style="font-size: 0.9rem; font-weight: 600; color: var(--text-primary);">${session.name}</span>
                <span style="font-size: 0.75rem; color: var(--text-muted);">${session.email}</span>
              </div>
            </div>
            ` : ''}
            <div class="nav-actions-mobile-row" style="margin-top: 1rem;">
              ${session ? `<button onclick="handleLogout()" class="btn btn-secondary" style="width: 100%;"><i data-lucide="log-out" style="width: 1rem; height: 1rem;"></i> Logout</button>` : `
                <a href="login.html" class="btn btn-secondary" style="width: 48%;"><i data-lucide="log-in" style="width: 1rem; height: 1rem;"></i> Login</a>
                <a href="register.html" class="btn btn-primary" style="width: 48%;"><i data-lucide="user-plus" style="width: 1rem; height: 1rem;"></i> Register</a>
              `}
            </div>
          </div>
        </ul>
      </nav>

      <div class="nav-actions">
        ${themeToggleBtn}
        ${actionHtml}
      </div>

      <div class="mobile-nav-toggle" id="mobile-nav-toggle">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;

  // Attach event listener for mobile menu toggle
  const mobileNavToggle = document.getElementById('mobile-nav-toggle');
  const navMenu = document.getElementById('nav-menu');
  if (mobileNavToggle && navMenu) {
    mobileNavToggle.addEventListener('click', () => {
      navMenu.classList.toggle('active');
      mobileNavToggle.classList.toggle('active');
      // Hamburger animation
      const spans = mobileNavToggle.querySelectorAll('span');
      if (navMenu.classList.contains('active')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px, -6px)';
      } else {
        spans[0].style.transform = 'none';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'none';
      }
    });
  }

  // Hook up event listeners for newly added theme toggle button inside header
  const newThemeToggles = headerContainer.querySelectorAll('.theme-toggle');
  newThemeToggles.forEach(btn => {
    btn.addEventListener('click', toggleTheme);
  });
}

// Dynamically generate the footer
function renderFooter() {
  const footerContainer = document.getElementById('site-footer');
  if (!footerContainer) return;

  footerContainer.innerHTML = `
    <div class="container">
      <div class="footer-grid">
        <div>
          <div class="footer-logo">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
            Salesbot
          </div>
          <p class="footer-desc">Empowering sales and marketing processes through advanced, self-improving AI bots. Automate lead qualification, campaign messaging, and outbound calling with ease.</p>
          <div class="social-links">
            <a class="social-icon" aria-label="Facebook"><i data-lucide="facebook" style="width: 1.1rem; height: 1.1rem;"></i></a>
            <a class="social-icon" aria-label="Twitter"><i data-lucide="twitter" style="width: 1.1rem; height: 1.1rem;"></i></a>
            <a class="social-icon" aria-label="LinkedIn"><i data-lucide="linkedin" style="width: 1.1rem; height: 1.1rem;"></i></a>
            <a class="social-icon" aria-label="GitHub"><i data-lucide="github" style="width: 1.1rem; height: 1.1rem;"></i></a>
          </div>
        </div>

        <div>
          <h3 class="footer-title">Quick Links</h3>
          <ul class="footer-links">
            <li><a href="index.html">Home</a></li>
            <li><a href="about.html">About Us</a></li>
            <li><a href="contact.html">Contact Us</a></li>
            <li><a href="login.html">Demo Login</a></li>
            <li><a href="register.html">User Registration</a></li>
          </ul>
        </div>

        <div>
          <ul class="footer-links" style="pointer-events: none; opacity: 0.8;">
            <li><a>Lead Qualification</a></li>
            <li><a>Telesales Assistant</a></li>
            <li><a>Promotional Campaigns</a></li>
            <li><a>Customer Re-engagement</a></li>
            <li><a>Event Invitations</a></li>
          </ul>
        </div>

        <div>
          <h3 class="footer-title">Stay Updated</h3>
          <div class="newsletter-form">
            <p class="newsletter-desc">Subscribe to our monthly product roadmap and newsletter updates.</p>
            <div class="newsletter-input-group">
              <input type="email" placeholder="Your work email" class="newsletter-input" aria-label="Work Email">
              <button class="btn btn-primary" style="padding: 0.5rem 1rem;" onclick="alert('Demo subscription successful!')"><i data-lucide="send" style="width: 1rem; height: 1rem;"></i></button>
            </div>
          </div>
          <div style="margin-top: 1.5rem; font-size: 0.8rem; color: var(--text-muted);">
            <strong>Contact Info:</strong><br>
            Email: salesautomatione4@gmail.com<br>
            Phone: +19599491429
          </div>
        </div>
      </div>

      <div class="footer-bottom">
        <p>&copy; 2026 Salesbot Automation Bot. All rights reserved.</p>
        <div class="footer-bottom-links">
          <a onclick="alert('This is a demo privacy policy statement.')" style="cursor: pointer;">Privacy Policy</a>
          <a onclick="alert('This is a demo terms and conditions statement.')" style="cursor: pointer;">Terms & Conditions</a>
        </div>
      </div>
    </div>
  `;
}

// Highlight the currently active link based on pathname
function highlightActiveLink() {
  const path = window.location.pathname;
  let activeId = 'nav-home';

  if (path.endsWith('about.html')) {
    activeId = 'nav-about';
  } else if (path.endsWith('contact.html')) {
    activeId = 'nav-contact';
  } else if (path.endsWith('admin.html')) {
    activeId = 'nav-admin-shortcut';
  }

  const activeLink = document.getElementById(activeId);
  if (activeLink) {
    activeLink.classList.add('active');
  }
}


// Dynamic injection of Profile Modal Styles
(function injectModalCSS() {
  const style = document.createElement('style');
  style.textContent = `
    .profile-modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: rgba(11, 8, 19, 0.65);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      opacity: 0;
      transition: opacity 0.3s ease;
      pointer-events: none;
    }
    .profile-modal-overlay.active {
      opacity: 1;
      pointer-events: auto;
    }
    .profile-modal-card {
      background-color: var(--surface-primary);
      border: 1px solid var(--border-color);
      border-radius: 1.5rem;
      padding: 2.5rem;
      width: 90%;
      max-width: 400px;
      box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.4);
      transform: translateY(20px);
      transition: transform 0.3s ease;
      text-align: center;
      position: relative;
      color: var(--text-primary);
    }
    .profile-modal-overlay.active .profile-modal-card {
      transform: translateY(0);
    }
    .profile-modal-close {
      position: absolute;
      top: 1.25rem;
      right: 1.25rem;
      cursor: pointer;
      color: var(--text-secondary);
      transition: all 0.2s;
      background: none;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 2rem;
      height: 2rem;
      border-radius: 50%;
      border: 1px solid var(--border-color);
    }
    .profile-modal-close:hover {
      color: var(--primary);
      background-color: var(--bg-secondary);
    }
    .profile-modal-avatar {
      width: 5rem;
      height: 5rem;
      border-radius: 50%;
      background: var(--gradient-primary);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 2rem;
      font-weight: bold;
      margin: 0 auto 1.25rem auto;
      box-shadow: 0 8px 16px rgba(139, 92, 246, 0.2);
    }
    .profile-modal-name {
      font-size: 1.35rem;
      font-weight: 800;
      margin-bottom: 0.25rem;
    }
    .profile-modal-role {
      font-size: 0.75rem;
      color: var(--primary);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 1.5rem;
      display: inline-block;
      padding: 0.2rem 0.6rem;
      background-color: rgba(99, 102, 241, 0.08);
      border-radius: 0.25rem;
    }
    .profile-modal-details {
      text-align: left;
      background-color: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 0.75rem;
      padding: 1.25rem;
      margin-bottom: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }
    .profile-modal-detail-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 0.6rem;
    }
    .profile-modal-detail-row:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }
    .profile-modal-detail-label {
      font-weight: 500;
      color: var(--text-secondary);
      font-size: 0.85rem;
    }
    .profile-modal-detail-value {
      font-weight: 600;
      color: var(--text-primary);
      font-size: 0.9rem;
    }
  `;
  document.head.appendChild(style);
})();

function showProfileModal() {
  const session = getSession();
  if (!session) return;

  let overlay = document.getElementById('profile-modal-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'profile-modal-overlay';
    overlay.className = 'profile-modal-overlay';
    overlay.innerHTML = `
      <div class="profile-modal-card">
        <button class="profile-modal-close" onclick="closeProfileModal()">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
        <div class="profile-modal-avatar" id="modal-avatar">U</div>
        <h3 class="profile-modal-name" id="modal-name">User Name</h3>
        <span class="profile-modal-role" id="modal-role">User</span>
        
        <div class="profile-modal-details">
          <div class="profile-modal-detail-row">
            <span class="profile-modal-detail-label">Username/Email</span>
            <span class="profile-modal-detail-value" id="modal-email">user@gmail.com</span>
          </div>
          <div class="profile-modal-detail-row">
            <span class="profile-modal-detail-label">Phone No</span>
            <span class="profile-modal-detail-value" id="modal-phone">9876543210</span>
          </div>
          <div class="profile-modal-detail-row">
            <span class="profile-modal-detail-label">Status</span>
            <span class="profile-modal-detail-value" style="color: var(--success); display: flex; align-items: center; gap: 0.25rem;">
              <span style="width: 0.45rem; height: 0.45rem; border-radius: 50%; background-color: var(--success); display: inline-block;"></span> Active
            </span>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    
    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        closeProfileModal();
      }
    });
  }

  // Populate data
  const avatarEl = document.getElementById('modal-avatar');
  const nameEl = document.getElementById('modal-name');
  const roleEl = document.getElementById('modal-role');
  const emailEl = document.getElementById('modal-email');
  const phoneEl = document.getElementById('modal-phone');

  if (nameEl) nameEl.textContent = session.name || 'User';
  if (roleEl) roleEl.textContent = session.role === 'admin' ? 'Administrator' : 'User';
  if (emailEl) emailEl.textContent = session.email || 'N/A';
  if (phoneEl) phoneEl.textContent = session.phone || 'Not Provided';
  if (avatarEl && session.name) {
    avatarEl.textContent = session.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  }

  // Show
  overlay.classList.add('active');
}

function closeProfileModal() {
  const overlay = document.getElementById('profile-modal-overlay');
  if (overlay) {
    overlay.classList.remove('active');
  }
}
