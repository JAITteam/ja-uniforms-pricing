function getCSRFToken() {
    return document.querySelector('input[name="csrf_token"]')?.value || '';
}
// ===== REGISTRATION FORM SCRIPT =====

const form = document.getElementById('registrationForm');
const modal = document.getElementById('verificationModal');
const verificationInputs = document.querySelectorAll('.verification-input');
const verifyBtn = document.getElementById('verifyBtn');
const changeEmailBtn = document.getElementById('changeEmailBtn');
const resendLink = document.getElementById('resendLink');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const strengthBar = document.getElementById('strengthBar');
const strengthText = document.getElementById('strengthText');
const modalEmail = document.getElementById('modalEmail');
const modalError = document.getElementById('modalError');
const successMessage = document.getElementById('successMessage');
const errorMessage = document.getElementById('errorMessage');

let resendTimer = 60;
let timerInterval;

// Password Strength Checker
passwordInput.addEventListener('input', function() {
    const password = this.value;
    let strength = 0;

    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    strengthBar.className = 'password-strength-bar';
    strengthText.className = 'password-strength-text';

    if (password.length === 0) {
        strengthBar.style.width = '0';
        strengthText.textContent = '';
    } else if (strength <= 2) {
        strengthBar.classList.add('strength-weak');
        strengthText.classList.add('strength-text-weak');
        strengthText.textContent = 'Weak password';
    } else if (strength === 3) {
        strengthBar.classList.add('strength-medium');
        strengthText.classList.add('strength-text-medium');
        strengthText.textContent = 'Medium password';
    } else {
        strengthBar.classList.add('strength-strong');
        strengthText.classList.add('strength-text-strong');
        strengthText.textContent = 'Strong password';
    }
});

// Form Submission
form.addEventListener('submit', function(e) {
    e.preventDefault();

    errorMessage.classList.remove('show');
    successMessage.classList.remove('show');

    if (passwordInput.value !== confirmPasswordInput.value) {
        showError('Passwords do not match');
        return;
    }

    if (passwordInput.value.length < 8) {
        showError('Password must be at least 8 characters long');
        return;
    }

    const submitBtn = document.querySelector('.auth-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="modal-loading"></span> Sending Code...';

    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCSRFToken()  // Add this line
        },
        body: new URLSearchParams({
            'csrf_token': getCSRFToken(),  // Add this line
            'firstName': document.getElementById('firstName').value,
            'lastName': document.getElementById('lastName').value,
            'email': emailInput.value,
            'password': passwordInput.value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            modalEmail.textContent = emailInput.value;
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            verificationInputs[0].focus();
            startResendTimer();
            feather.replace();
        } else {
            showError(data.error || 'Registration failed');
        }
    })
    .catch(error => {
        showError('Network error. Please try again.');
        console.error('Error:', error);
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Create Account</span><i data-feather="arrow-right" style="width: 20px; height: 20px;"></i>';
        feather.replace();
    });
});

// Verification Input Handling
verificationInputs.forEach((input, index) => {
    input.addEventListener('input', function(e) {
        if (this.value.length === 1) {
            this.classList.add('filled');
            if (index < verificationInputs.length - 1) {
                verificationInputs[index + 1].focus();
            }
        } else {
            this.classList.remove('filled');
        }

        const code = getVerificationCode();
        verifyBtn.disabled = code.length !== 6;
    });

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Backspace' && this.value === '' && index > 0) {
            verificationInputs[index - 1].focus();
        }
    });

    input.addEventListener('paste', function(e) {
        e.preventDefault();
        const pasteData = e.clipboardData.getData('text').slice(0, 6);
        pasteData.split('').forEach((char, i) => {
            if (i < verificationInputs.length && /[0-9]/.test(char)) {
                verificationInputs[i].value = char;
                verificationInputs[i].classList.add('filled');
            }
        });
        if (pasteData.length === 6) {
            verificationInputs[5].focus();
            verifyBtn.disabled = false;
        }
    });
});

// Get Verification Code
function getVerificationCode() {
    let code = '';
    verificationInputs.forEach(input => {
        code += input.value;
    });
    return code;
}

// Verify Button
verifyBtn.addEventListener('click', function() {
    const code = getVerificationCode();
    
    if (code.length !== 6) {
        showModalError('Please enter the complete 6-digit code');
        return;
    }

    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<span class="modal-loading"></span> Verifying...';

    fetch('/api/verify-code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            email: emailInput.value,
            code: code
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            modalError.classList.remove('show');
            
            const modalIcon = document.getElementById('modalIcon');
            modalIcon.className = 'modal-icon success-icon';
            modalIcon.innerHTML = '<i data-feather="check-circle" class="success-checkmark"></i>';
            feather.replace();
            
            document.getElementById('modalTitle').textContent = 'Email Verified!';
            document.getElementById('modalSubtitle').textContent = 'Your account has been successfully created.';
            
            document.getElementById('verificationInputs').style.display = 'none';
            document.getElementById('changeEmailBtn').style.display = 'none';
            document.querySelector('.resend-code').style.display = 'none';
            
            verifyBtn.textContent = 'Continue to Login';
            verifyBtn.disabled = false;
            verifyBtn.onclick = function() {
                window.location.href = data.redirect || '/login';
            };
        } else {
            showModalError(data.error || 'Invalid verification code');
            clearVerificationInputs();
            verificationInputs[0].focus();
            verifyBtn.disabled = false;
            verifyBtn.textContent = 'Verify Email';
        }
    })
    .catch(error => {
        showModalError('Network error. Please try again.');
        console.error('Error:', error);
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'Verify Email';
    });
});

// Change Email Button
changeEmailBtn.addEventListener('click', function() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
    emailInput.focus();
    clearVerificationInputs();
});

// Resend Code
resendLink.addEventListener('click', function(e) {
    e.preventDefault();
    if (!this.classList.contains('disabled')) {
        fetch('/api/resend-verification-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                email: emailInput.value
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('New verification code sent');
                startResendTimer();
                clearVerificationInputs();
                verificationInputs[0].focus();
            } else {
                showModalError(data.error || 'Failed to resend code');
            }
        })
        .catch(error => {
            showModalError('Network error. Please try again.');
            console.error('Error:', error);
        });
    }
});

// Start Resend Timer
function startResendTimer() {
    resendTimer = 60;
    resendLink.classList.add('disabled');
    document.getElementById('resendTimer').textContent = `(${resendTimer}s)`;
    
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        resendTimer--;
        document.getElementById('resendTimer').textContent = `(${resendTimer}s)`;
        
        if (resendTimer <= 0) {
            clearInterval(timerInterval);
            resendLink.classList.remove('disabled');
            document.getElementById('resendTimer').textContent = '';
        }
    }, 1000);
}

// Clear Verification Inputs
function clearVerificationInputs() {
    verificationInputs.forEach(input => {
        input.value = '';
        input.classList.remove('filled', 'error');
    });
    verifyBtn.disabled = true;
}

// Show Error Message
function showError(message) {
    document.getElementById('errorText').textContent = message;
    errorMessage.classList.add('show');
    feather.replace();
    setTimeout(() => {
        errorMessage.classList.remove('show');
    }, 5000);
}

// Show Modal Error
function showModalError(message) {
    document.getElementById('modalErrorText').textContent = message;
    modalError.classList.add('show');
    feather.replace();
    verificationInputs.forEach(input => {
        input.classList.add('error');
    });
    setTimeout(() => {
        verificationInputs.forEach(input => {
            input.classList.remove('error');
        });
    }, 500);
}

// Close modal on escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
        changeEmailBtn.click();
    }
});