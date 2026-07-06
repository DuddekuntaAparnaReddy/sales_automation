// Authentication and Validation Logic for Salesbot

document.addEventListener('DOMContentLoaded', () => {
  initLoginCard();
  initRegisterCard();
});

// LOGIN CARD INITIALIZATION & LOGIC
function initLoginCard() {
  const loginForm = document.getElementById('login-form');
  if (!loginForm) return;

  const roleTabs = document.querySelectorAll('.role-tab');
  const loginTitle = document.getElementById('login-role-title');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const errorMsg = document.getElementById('login-error');

  let activeRole = 'user'; // default role

  // Handle Tab Switch
  roleTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      roleTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeRole = tab.dataset.role;
      
      // Update UI texts
      if (activeRole === 'admin') {
        loginTitle.textContent = 'Admin Dashboard Login';
        emailInput.placeholder = 'admin@gmail.com';
      } else {
        loginTitle.textContent = 'User Space Login';
        emailInput.placeholder = 'user@gmail.com';
      }
      // Reset error state
      if (errorMsg) errorMsg.style.display = 'none';
    });
  });

  // Handle Form Submit
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    
    if (errorMsg) errorMsg.style.display = 'none';

    // Demo credentials verification
try {

  const response = await fetch("http://127.0.0.1:8000/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      email: email,
      password: password
    })
  });

  const data = await response.json();

  if (data.message === "Login Successful") {

    const session = {
      user_id: data.user ? data.user.user_id : null,
      role: data.user ? data.user.role : activeRole,
      email: data.user ? data.user.email : email,
      name: data.user ? data.user.full_name : (activeRole === "admin" ? "System Admin" : "User"),
      phone: data.user ? data.user.phone : ""
    };

    localStorage.setItem("session", JSON.stringify(session));
    // Also store under "user" for legacy compatibility
    localStorage.setItem("user", JSON.stringify(session));

    if (activeRole === "admin") {
      window.location.href = "admin.html";
    } else {
      window.location.href = "index.html";
    }

  } else {
    showLoginError(data.message);
  }

} catch (error) {
  showLoginError("Backend Connection Error");
}
  });

  function showLoginError(msg) {
    if (errorMsg) {
      errorMsg.textContent = msg;
      errorMsg.className = 'validation-msg error';
      errorMsg.style.display = 'flex';
      
      // Shake effect
      const card = document.querySelector('.form-card');
      card.style.transform = 'translateX(6px)';
      setTimeout(() => card.style.transform = 'translateX(-6px)', 80);
      setTimeout(() => card.style.transform = 'translateX(4px)', 160);
      setTimeout(() => card.style.transform = 'translateX(-4px)', 240);
      setTimeout(() => card.style.transform = 'none', 320);
    }
  }
}

// REGISTER CARD INITIALIZATION & LOGIC (User Registration only)
function initRegisterCard() {
  const registerForm = document.getElementById('register-form');
  if (!registerForm) return;

  const fullName = document.getElementById('fullname');
  const email = document.getElementById('email');
  const phone = document.getElementById('phone');
  const password = document.getElementById('password');
  const confirmPassword = document.getElementById('confirm-password');

  // Real-time input listener hooks
  fullName.addEventListener('input', () => validateField(fullName, checkName));
  email.addEventListener('input', () => validateField(email, checkEmail));
  phone.addEventListener('input', () => validateField(phone, checkPhone));
  password.addEventListener('input', () => {
    validateField(password, checkPassword);
    // Re-check confirm password if already filled
    if (confirmPassword.value) {
      validateField(confirmPassword, () => checkConfirmPassword(password.value, confirmPassword.value));
    }
  });
  confirmPassword.addEventListener('input', () => validateField(confirmPassword, () => checkConfirmPassword(password.value, confirmPassword.value)));

  // Field validation helper
  function validateField(element, validationFn) {
    const errorEl = document.getElementById(`${element.id}-error`);
    const result = validationFn(element.value);
    
    if (element.value === '') {
      element.classList.remove('valid', 'invalid');
      if (errorEl) errorEl.style.display = 'none';
      return false;
    }

    if (result.isValid) {
      element.classList.remove('invalid');
      element.classList.add('valid');
      if (errorEl) {
        errorEl.style.display = 'none';
      }
      return true;
    } else {
      element.classList.remove('valid');
      element.classList.add('invalid');
      if (errorEl) {
        errorEl.textContent = result.message;
        errorEl.className = 'validation-msg error';
        errorEl.style.display = 'flex';
      }
      return false;
    }
  }

  // Validators
  function checkName(val) {
    // Only alphabets and spaces
    const nameRegex = /^[A-Za-z\s]+$/;
    if (!nameRegex.test(val)) {
      return { isValid: false, message: 'Name can only contain alphabets and spaces.' };
    }
    return { isValid: true };
  }

  function checkEmail(val) {
    // Valid email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(val)) {
      return { isValid: false, message: 'Please enter a valid email address.' };
    }
    return { isValid: true };
  }

  function checkPhone(val) {
    // Exactly 10 digits
    const phoneRegex = /^\d{10}$/;
    if (!phoneRegex.test(val)) {
      return { isValid: false, message: 'Phone number must be exactly 10 digits.' };
    }
    return { isValid: true };
  }

  function checkPassword(val) {
    // Minimum 8 characters
    if (val.length < 8) {
      return { isValid: false, message: 'Password must be at least 8 characters long.' };
    }
    // At least 1 uppercase letter
    if (!/[A-Z]/.test(val)) {
      return { isValid: false, message: 'Password must include at least one uppercase letter.' };
    }
    // At least 1 lowercase letter
    if (!/[a-z]/.test(val)) {
      return { isValid: false, message: 'Password must include at least one lowercase letter.' };
    }
    // At least 1 number
    if (!/[0-9]/.test(val)) {
      return { isValid: false, message: 'Password must include at least one digit.' };
    }
    // At least 1 special character
    if (!/[\W_]/.test(val)) {
      return { isValid: false, message: 'Password must include at least one special character.' };
    }
    return { isValid: true };
  }

  function checkConfirmPassword(pass, confPass) {
    if (pass !== confPass) {
      return { isValid: false, message: 'Passwords do not match.' };
    }
    return { isValid: true };
  }

  // Handle Register submit
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Trigger validation on all fields
    const isNameValid = validateField(fullName, checkName);
    const isEmailValid = validateField(email, checkEmail);
    const isPhoneValid = validateField(phone, checkPhone);
    const isPasswordValid = validateField(password, checkPassword);
    const isConfirmValid = validateField(confirmPassword, () => checkConfirmPassword(password.value, confirmPassword.value));

   if (isNameValid && isEmailValid && isPhoneValid && isPasswordValid && isConfirmValid) {

  try {

    const response = await fetch("http://127.0.0.1:8000/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        full_name: fullName.value.trim(),
        email: email.value.trim(),
        password: password.value,
        phone: phone.value.trim()
      })
    });

    const data = await response.json();

    if (data.message) {
      alert(data.message);
      window.location.href = "login.html";
    } else {
      alert("Registration Failed");
    }

  } catch (error) {
    alert("Backend Connection Error");
  }

} else {
      // Find the first invalid element and focus it
      const invalidInput = registerForm.querySelector('.invalid');
      if (invalidInput) {
        invalidInput.focus();
      }
    }
  });
}
