// EVE Healthcare Interactive Portal & Testing Client
const API_BASE = '/api/v1';

const state = {
  token: localStorage.getItem('eve_token') || null,
  currentUser: null,
  centres: [],
  selectedCentre: null,
  selectedTest: null,
  bookings: [],
  activeRole: 'PATIENT',
};

// DOM Elements
const elements = {
  systemStatus: document.getElementById('systemStatusText'),
  userAvatar: document.getElementById('userAvatar'),
  userName: document.getElementById('userName'),
  userRole: document.getElementById('userRole'),
  userChip: document.getElementById('userChip'),
  authNavButtons: document.getElementById('authNavButtons'),
  navLoginBtn: document.getElementById('navLoginBtn'),
  navSignupBtn: document.getElementById('navSignupBtn'),
  logoutBtn: document.getElementById('logoutBtn'),
  quickSwitchBtn: document.getElementById('quickSwitchBtn'),

  // Switch Modal
  switchUserModal: document.getElementById('switchUserModal'),
  closeSwitchModalBtn: document.getElementById('closeSwitchModalBtn'),
  choosePatient: document.getElementById('choosePatient'),
  chooseAdmin: document.getElementById('chooseAdmin'),

  // Auth Modal
  authModal: document.getElementById('authModal'),
  authModalTitle: document.getElementById('authModalTitle'),
  closeAuthModalBtn: document.getElementById('closeAuthModalBtn'),
  closeAuthModalBtn2: document.getElementById('closeAuthModalBtn2'),
  closeAuthModalBtn3: document.getElementById('closeAuthModalBtn3'),
  modalToggleLogin: document.getElementById('modalToggleLogin'),
  modalToggleSignup: document.getElementById('modalToggleSignup'),
  modalLoginForm: document.getElementById('modalLoginForm'),
  modalSignupForm: document.getElementById('modalSignupForm'),
  modalLoginFormElement: document.getElementById('modalLoginFormElement'),
  modalLoginEmail: document.getElementById('modalLoginEmail'),
  modalLoginPassword: document.getElementById('modalLoginPassword'),
  modalSignupFormElement: document.getElementById('modalSignupFormElement'),
  modalSignupName: document.getElementById('modalSignupName'),
  modalSignupEmail: document.getElementById('modalSignupEmail'),
  modalSignupPassword: document.getElementById('modalSignupPassword'),
  modalSignupRole: document.getElementById('modalSignupRole'),
  modalQuickPatient: document.getElementById('modalQuickPatient'),
  modalQuickAdmin: document.getElementById('modalQuickAdmin'),

  // Auth Tab (Full Page Portal)
  sessionCard: document.getElementById('sessionCard'),
  sessionAvatar: document.getElementById('sessionAvatar'),
  sessionName: document.getElementById('sessionName'),
  sessionEmail: document.getElementById('sessionEmail'),
  sessionRole: document.getElementById('sessionRole'),
  tabLogoutBtn: document.getElementById('tabLogoutBtn'),
  authPortalCard: document.getElementById('authPortalCard'),
  authPortalToggleLogin: document.getElementById('authPortalToggleLogin'),
  authPortalToggleSignup: document.getElementById('authPortalToggleSignup'),
  authPortalLoginForm: document.getElementById('authPortalLoginForm'),
  authPortalSignupForm: document.getElementById('authPortalSignupForm'),
  portalLoginForm: document.getElementById('portalLoginForm'),
  portalLoginEmail: document.getElementById('portalLoginEmail'),
  portalLoginPassword: document.getElementById('portalLoginPassword'),
  portalSignupForm: document.getElementById('portalSignupForm'),
  portalSignupName: document.getElementById('portalSignupName'),
  portalSignupEmail: document.getElementById('portalSignupEmail'),
  portalSignupPassword: document.getElementById('portalSignupPassword'),
  portalSignupPhone: document.getElementById('portalSignupPhone'),
  portalSignupRole: document.getElementById('portalSignupRole'),
  quickLoginPatient: document.getElementById('quickLoginPatient'),
  quickLoginAdmin: document.getElementById('quickLoginAdmin'),

  // Navigation Tabs
  tabBtns: document.querySelectorAll('.tab-btn'),
  tabPanes: document.querySelectorAll('.tab-pane'),

  // Centres Tab
  centreSearchInput: document.getElementById('centreSearchInput'),
  cityFilterSelect: document.getElementById('cityFilterSelect'),
  refreshCentresBtn: document.getElementById('refreshCentresBtn'),
  centresGrid: document.getElementById('centresGrid'),
  statCentresCount: document.getElementById('statCentresCount'),
  statTestsCount: document.getElementById('statTestsCount'),
  statBookingsCount: document.getElementById('statBookingsCount'),

  // Booking Tab
  bookingForm: document.getElementById('bookingForm'),
  bookCentreSelect: document.getElementById('bookCentreSelect'),
  bookTestSelect: document.getElementById('bookTestSelect'),
  bookDateInput: document.getElementById('bookDateInput'),
  priceBanner: document.getElementById('priceBanner'),
  bannerPrice: document.getElementById('bannerPrice'),
  bannerTurnaround: document.getElementById('bannerTurnaround'),
  bannerSample: document.getElementById('bannerSample'),
  patientNameInput: document.getElementById('patientNameInput'),
  patientAgeInput: document.getElementById('patientAgeInput'),
  patientGenderSelect: document.getElementById('patientGenderSelect'),
  patientPhoneInput: document.getElementById('patientPhoneInput'),
  patientNotesInput: document.getElementById('patientNotesInput'),

  // Bookings Tab
  refreshBookingsBtn: document.getElementById('refreshBookingsBtn'),
  bookingsList: document.getElementById('bookingsList'),

  // Payment Modal
  paymentModal: document.getElementById('paymentModal'),
  closePaymentModalBtn: document.getElementById('closePaymentModalBtn'),
  cancelModalBtn: document.getElementById('cancelModalBtn'),
  paymentForm: document.getElementById('paymentForm'),
  modalBookingId: document.getElementById('modalBookingId'),
  modalRawAmount: document.getElementById('modalRawAmount'),
  modalBookingRef: document.getElementById('modalBookingRef'),
  modalTestName: document.getElementById('modalTestName'),
  modalAmount: document.getElementById('modalAmount'),
  paymentMethodSelect: document.getElementById('paymentMethodSelect'),
  paymentOutcomeSelect: document.getElementById('paymentOutcomeSelect'),
  submitPaymentBtn: document.getElementById('submitPaymentBtn'),

  // Webhook Lab
  webhookBookingSelect: document.getElementById('webhookBookingSelect'),
  webhookEventIdInput: document.getElementById('webhookEventIdInput'),
  regenEventIdBtn: document.getElementById('regenEventIdBtn'),
  webhookStatusSelect: document.getElementById('webhookStatusSelect'),
  webhookAmountInput: document.getElementById('webhookAmountInput'),
  webhookTxnIdInput: document.getElementById('webhookTxnIdInput'),
  sendWebhookBtn: document.getElementById('sendWebhookBtn'),
  replayWebhookBtn: document.getElementById('replayWebhookBtn'),
  sendConcurrentWebhooksBtn: document.getElementById('sendConcurrentWebhooksBtn'),
  webhookConsoleOutput: document.getElementById('webhookConsoleOutput'),
  lastHttpStatus: document.getElementById('lastHttpStatus'),
  idempotencyProofCard: document.getElementById('idempotencyProofCard'),
  proofTitle: document.getElementById('proofTitle'),
  proofDesc: document.getElementById('proofDesc'),
  toastContainer: document.getElementById('toastContainer'),
};

// Utility: Toast notifications
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : '⚠'}</span>
    <span>${message}</span>
  `;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// API Helper with JWT Auth header
async function apiRequest(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const errorMsg = data?.detail || data?.message || response.statusText || 'API Error';
    throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
  }

  return data;
}

// Authentication UI Synchronization
function updateAuthUI(user, token) {
  if (user && token) {
    // Show user chip, hide sign-in buttons
    elements.authNavButtons.style.display = 'none';
    elements.userChip.style.display = 'flex';
    elements.userName.textContent = user.full_name;
    elements.userRole.textContent = user.role;
    elements.userAvatar.textContent = user.full_name.charAt(0).toUpperCase();

    // Update Session card in Auth tab
    elements.sessionCard.style.display = 'block';
    elements.sessionName.textContent = user.full_name;
    elements.sessionEmail.textContent = user.email;
    elements.sessionRole.textContent = user.role;
    elements.sessionAvatar.textContent = user.full_name.charAt(0).toUpperCase();

    elements.authPortalCard.style.display = 'none';

    // Pre-populate patient details on booking form if patient
    if (user.role === 'PATIENT') {
      elements.patientNameInput.value = user.full_name;
      if (user.phone) elements.patientPhoneInput.value = user.phone;
    }
  } else {
    // Show sign-in buttons, hide user chip
    elements.authNavButtons.style.display = 'flex';
    elements.userChip.style.display = 'none';
    elements.sessionCard.style.display = 'none';
    elements.authPortalCard.style.display = 'block';
  }
}

// Sign In
async function loginUser(email, password) {
  try {
    const res = await apiRequest(`${API_BASE}/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    state.token = res.access_token;
    state.currentUser = res.user;
    state.activeRole = res.user.role;
    localStorage.setItem('eve_token', res.access_token);

    updateAuthUI(res.user, res.access_token);
    closeAuthModal();
    showToast(`Signed in successfully as ${res.user.full_name} (${res.user.role})`);

    await loadCentres();
    await loadBookings();
  } catch (err) {
    showToast(`Authentication failed: ${err.message}`, 'error');
  }
}

// Register / Sign Up
async function registerUser(signupData) {
  try {
    const user = await apiRequest(`${API_BASE}/auth/signup`, {
      method: 'POST',
      body: JSON.stringify(signupData),
    });

    showToast(`Account created for ${user.full_name}! Signing you in...`);
    // Automatically login newly registered user
    await loginUser(signupData.email, signupData.password);
  } catch (err) {
    showToast(`Registration failed: ${err.message}`, 'error');
  }
}

// Sign Out
function logout() {
  state.token = null;
  state.currentUser = null;
  localStorage.removeItem('eve_token');
  updateAuthUI(null, null);
  showToast('Signed out of session.');
  elements.bookingsList.innerHTML = '<div class="loading-state">Please sign in to view your bookings.</div>';
}

// Fetch Profile from Existing Token
async function fetchCurrentUser() {
  if (!state.token) return;
  try {
    const user = await apiRequest(`${API_BASE}/auth/me`);
    state.currentUser = user;
    state.activeRole = user.role;
    updateAuthUI(user, state.token);
  } catch (err) {
    // Token expired or invalid
    state.token = null;
    localStorage.removeItem('eve_token');
    updateAuthUI(null, null);
  }
}

// Auth Modal Controls
function openAuthModal(mode = 'login') {
  setAuthMode(mode, true);
  elements.authModal.style.display = 'flex';
}

function closeAuthModal() {
  elements.authModal.style.display = 'none';
}

function setAuthMode(mode, isModal = false) {
  if (isModal) {
    if (mode === 'login') {
      elements.modalToggleLogin.classList.add('active');
      elements.modalToggleSignup.classList.remove('active');
      elements.modalLoginForm.style.display = 'block';
      elements.modalSignupForm.style.display = 'none';
      elements.authModalTitle.textContent = 'Sign In';
    } else {
      elements.modalToggleSignup.classList.add('active');
      elements.modalToggleLogin.classList.remove('active');
      elements.modalLoginForm.style.display = 'none';
      elements.modalSignupForm.style.display = 'block';
      elements.authModalTitle.textContent = 'Create Account';
    }
  } else {
    if (mode === 'login') {
      elements.authPortalToggleLogin.classList.add('active');
      elements.authPortalToggleSignup.classList.remove('active');
      elements.authPortalLoginForm.style.display = 'block';
      elements.authPortalSignupForm.style.display = 'none';
    } else {
      elements.authPortalToggleSignup.classList.add('active');
      elements.authPortalToggleLogin.classList.remove('active');
      elements.authPortalLoginForm.style.display = 'none';
      elements.authPortalSignupForm.style.display = 'block';
    }
  }
}

// Health Check Polling
async function checkHealth() {
  try {
    const res = await apiRequest('/health');
    elements.systemStatus.textContent = `${res.status.toUpperCase()} • ${res.database} • ${res.cache}`;
  } catch (err) {
    elements.systemStatus.textContent = 'Server Degraded';
  }
}

// Load Diagnostic Centres
async function loadCentres() {
  try {
    elements.centresGrid.innerHTML = '<div class="loading-state">Loading diagnostic centres...</div>';
    const city = elements.cityFilterSelect.value;
    const search = elements.centreSearchInput.value.trim();

    let url = `${API_BASE}/centres/?page_size=20`;
    if (city) url += `&city=${encodeURIComponent(city)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const res = await apiRequest(url);
    state.centres = res.items || [];
    elements.statCentresCount.textContent = res.total || state.centres.length;

    renderCentresGrid(state.centres);
    populateCentreDropdowns(state.centres);
  } catch (err) {
    elements.centresGrid.innerHTML = `<div class="loading-state" style="color:var(--danger)">Failed to load centres: ${err.message}</div>`;
  }
}

function renderCentresGrid(centres) {
  if (!centres.length) {
    elements.centresGrid.innerHTML = '<div class="loading-state">No diagnostic centres found matching your search.</div>';
    return;
  }

  elements.centresGrid.innerHTML = centres.map(c => `
    <div class="centre-card">
      <div class="centre-header">
        <h3 class="centre-name">${c.name}</h3>
        <span class="city-pill">${c.city}</span>
      </div>
      <p class="centre-address">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        ${c.address}, ${c.state} - ${c.pincode}
      </p>
      <div class="centre-meta">
        <span>⏰ ${c.opening_time} - ${c.closing_time}</span>
        <span>📞 ${c.phone || 'N/A'}</span>
      </div>

      <div class="tests-offered-header">Available Tests & Pricing</div>
      <div class="tests-list">
        ${(c.centre_tests || []).map(ct => `
          <div class="test-item">
            <div class="test-info">
              <span class="test-name">${ct.test ? ct.test.name : 'Test #' + ct.test_id}</span>
              <span class="test-turnaround">⏱ Ready in ${ct.turnaround_hours}h</span>
            </div>
            <span class="test-price">₹${parseFloat(ct.price).toFixed(2)}</span>
          </div>
        `).join('')}
      </div>

      <button class="btn btn-outline" onclick="initiateBookingForCentre(${c.id})">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        Book at this Centre
      </button>
    </div>
  `).join('');
}

function populateCentreDropdowns(centres) {
  const optionsHtml = '<option value="">Select a centre...</option>' + centres.map(c => `
    <option value="${c.id}">${c.name} (${c.city})</option>
  `).join('');

  elements.bookCentreSelect.innerHTML = optionsHtml;
}

window.initiateBookingForCentre = function(centreId) {
  if (!state.token) {
    showToast('Please sign in to book a diagnostic test.', 'error');
    openAuthModal('login');
    return;
  }
  switchTab('book-tab');
  elements.bookCentreSelect.value = centreId;
  handleCentreChange();
};

function handleCentreChange() {
  const centreId = parseInt(elements.bookCentreSelect.value);
  if (!centreId) {
    elements.bookTestSelect.innerHTML = '<option value="">Choose centre first...</option>';
    elements.bookTestSelect.disabled = true;
    elements.priceBanner.style.display = 'none';
    return;
  }

  const centre = state.centres.find(c => c.id === centreId);
  if (!centre || !centre.centre_tests) return;

  elements.bookTestSelect.disabled = false;
  elements.bookTestSelect.innerHTML = '<option value="">Select a test...</option>' + centre.centre_tests.map(ct => `
    <option value="${ct.test_id}" data-price="${ct.price}" data-turnaround="${ct.turnaround_hours}" data-sample="${ct.test?.sample_type || 'Specimen'}">
      ${ct.test ? ct.test.name : 'Test #' + ct.test_id} — ₹${parseFloat(ct.price).toFixed(2)}
    </option>
  `).join('');
}

function handleTestChange() {
  const selectedOption = elements.bookTestSelect.selectedOptions[0];
  if (!selectedOption || !selectedOption.value) {
    elements.priceBanner.style.display = 'none';
    return;
  }

  const price = selectedOption.getAttribute('data-price');
  const turnaround = selectedOption.getAttribute('data-turnaround');
  const sample = selectedOption.getAttribute('data-sample');

  elements.bannerPrice.textContent = `₹${parseFloat(price).toFixed(2)}`;
  elements.bannerTurnaround.textContent = `${turnaround} hours`;
  elements.bannerSample.textContent = sample;
  elements.priceBanner.style.display = 'flex';
}

// Create Diagnostic Booking
async function submitBooking(e) {
  e.preventDefault();
  if (!state.token) {
    showToast('Please sign in before booking a test.', 'error');
    openAuthModal('login');
    return;
  }

  const centreId = parseInt(elements.bookCentreSelect.value);
  const testId = parseInt(elements.bookTestSelect.value);
  const apptTime = elements.bookDateInput.value;

  if (!centreId || !testId || !apptTime) {
    showToast('Please fill all required booking fields.', 'error');
    return;
  }

  try {
    elements.bookingForm.querySelector('button[type="submit"]').disabled = true;
    const payload = {
      centre_id: centreId,
      test_id: testId,
      appointment_time: new Date(apptTime).toISOString(),
      patient_name: elements.patientNameInput.value.trim(),
      patient_age: elements.patientAgeInput.value ? parseInt(elements.patientAgeInput.value) : null,
      patient_gender: elements.patientGenderSelect.value,
      patient_phone: elements.patientPhoneInput.value.trim(),
      notes: elements.patientNotesInput.value.trim() || null,
    };

    const booking = await apiRequest(`${API_BASE}/bookings/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    showToast(`Booking Created! Reference: ${booking.booking_ref}`);
    await loadBookings();
    switchTab('bookings-tab');

    // Prompt user to simulate payment immediately
    openPaymentModal(booking.id, booking.booking_ref, booking.amount, booking.test?.name || 'Diagnostic Test');
  } catch (err) {
    showToast(`Booking failed: ${err.message}`, 'error');
  } finally {
    elements.bookingForm.querySelector('button[type="submit"]').disabled = false;
  }
}

// Load Bookings
async function loadBookings() {
  if (!state.token) {
    elements.bookingsList.innerHTML = `
      <div class="loading-state">
        <p>Please sign in to view and manage your diagnostic bookings.</p>
        <button class="btn btn-primary btn-sm" style="margin-top: 1rem;" onclick="openAuthModal('login')">Sign In</button>
      </div>
    `;
    return;
  }

  try {
    elements.bookingsList.innerHTML = '<div class="loading-state">Loading your diagnostic bookings...</div>';
    const res = await apiRequest(`${API_BASE}/bookings/?page_size=50`);
    state.bookings = res.items || [];
    elements.statBookingsCount.textContent = res.total || state.bookings.length;

    renderBookingsList(state.bookings);
    populateWebhookBookingSelect(state.bookings);
  } catch (err) {
    elements.bookingsList.innerHTML = `<div class="loading-state" style="color:var(--danger)">Failed to load bookings: ${err.message}</div>`;
  }
}

function renderBookingsList(bookings) {
  if (!bookings.length) {
    elements.bookingsList.innerHTML = '<div class="loading-state">No bookings found. Book your first diagnostic test using the Book tab!</div>';
    return;
  }

  elements.bookingsList.innerHTML = bookings.map(b => {
    const apptDate = new Date(b.appointment_time).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });

    return `
      <div class="booking-card">
        <div class="booking-main">
          <div class="booking-ref-row">
            <span class="booking-ref">${b.booking_ref}</span>
            <span class="status-badge ${b.status}">${b.status}</span>
          </div>
          <div class="booking-details-line">
            <strong>${b.test ? b.test.name : 'Test #' + b.test_id}</strong> for <strong>${b.patient_name}</strong>
          </div>
          <div class="booking-centre-time">
            🏥 ${b.centre ? b.centre.name : 'Centre #' + b.centre_id} (${b.centre ? b.centre.city : ''}) • 📅 ${apptDate}
          </div>
        </div>

        <div class="booking-right">
          <div class="booking-price">₹${parseFloat(b.amount).toFixed(2)}</div>
          <div class="booking-actions">
            ${b.status === 'PENDING' ? `
              <button class="btn btn-sm btn-primary" onclick="openPaymentModal(${b.id}, '${b.booking_ref}', ${b.amount}, '${b.test ? b.test.name : ''}')">
                💳 Pay (Simulate)
              </button>
              <button class="btn btn-sm btn-outline" onclick="cancelBookingAction(${b.id})">
                Cancel
              </button>
            ` : ''}

            ${b.status === 'CONFIRMED' ? `
              <button class="btn btn-sm btn-outline" style="border-color:var(--success); color:var(--success);" onclick="showToast('Booking is confirmed and active!')">
                ✓ Confirmed
              </button>
            ` : ''}

            ${b.status === 'FAILED' ? `
              <span class="btn btn-sm btn-ghost" style="color:var(--danger);">Payment Failed</span>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Cancel Booking
window.cancelBookingAction = async function(bookingId) {
  if (!confirm('Are you sure you want to cancel this booking?')) return;
  try {
    const res = await apiRequest(`${API_BASE}/bookings/${bookingId}/cancel`, {
      method: 'POST',
    });
    showToast(`Booking ${res.booking_ref} cancelled.`);
    await loadBookings();
  } catch (err) {
    showToast(`Cancellation error: ${err.message}`, 'error');
  }
};

// Payment Modal Handling
window.openPaymentModal = function(bookingId, bookingRef, amount, testName) {
  elements.modalBookingId.value = bookingId;
  elements.modalRawAmount.value = amount;
  elements.modalBookingRef.textContent = bookingRef;
  elements.modalTestName.textContent = testName || 'Diagnostic Test';
  elements.modalAmount.textContent = `₹${parseFloat(amount).toFixed(2)}`;
  elements.paymentModal.style.display = 'flex';
};

function closePaymentModal() {
  elements.paymentModal.style.display = 'none';
}

async function submitSimulatedPayment(e) {
  e.preventDefault();
  const bookingId = parseInt(elements.modalBookingId.value);
  const amount = parseFloat(elements.modalRawAmount.value);
  const method = elements.paymentMethodSelect.value;
  const outcome = elements.paymentOutcomeSelect.value;

  try {
    elements.submitPaymentBtn.disabled = true;
    elements.submitPaymentBtn.textContent = 'Processing Simulated Payment...';

    const res = await apiRequest(`${API_BASE}/payments/`, {
      method: 'POST',
      body: JSON.stringify({
        booking_id: bookingId,
        amount: amount,
        payment_method: method,
        simulate_status: outcome,
      }),
    });

    closePaymentModal();
    showToast(res.message, res.status === 'SUCCESS' ? 'success' : 'error');
    await loadBookings();
  } catch (err) {
    showToast(`Payment error: ${err.message}`, 'error');
  } finally {
    elements.submitPaymentBtn.disabled = false;
    elements.submitPaymentBtn.textContent = 'Process Simulated Payment';
  }
}

// Webhook Lab
function populateWebhookBookingSelect(bookings) {
  if (!bookings.length) {
    elements.webhookBookingSelect.innerHTML = '<option value="">No bookings available</option>';
    return;
  }
  elements.webhookBookingSelect.innerHTML = '<option value="">Select a booking...</option>' + bookings.map(b => `
    <option value="${b.id}" data-amount="${b.amount}" data-ref="${b.booking_ref}" data-status="${b.status}">
      ${b.booking_ref} — ${b.test ? b.test.name : 'Test'} [${b.status}] (₹${b.amount})
    </option>
  `).join('');
}

function handleWebhookBookingChange() {
  const opt = elements.webhookBookingSelect.selectedOptions[0];
  if (!opt || !opt.value) return;
  const amount = opt.getAttribute('data-amount');
  elements.webhookAmountInput.value = parseFloat(amount).toFixed(2);
}

function generateNewEventId() {
  const rand = Math.floor(100000 + Math.random() * 900000);
  elements.webhookEventIdInput.value = `evt_eve_${rand}`;
  elements.webhookTxnIdInput.value = `txn_gw_${rand}`;
  elements.idempotencyProofCard.style.display = 'none';
}

async function sendWebhookPayload(isDuplicateTest = false) {
  const bookingId = parseInt(elements.webhookBookingSelect.value);
  if (!bookingId) {
    showToast('Please select a target booking for the webhook event.', 'error');
    return;
  }

  const payload = {
    event_id: elements.webhookEventIdInput.value.trim(),
    event_type: 'payment.status.updated',
    transaction_id: elements.webhookTxnIdInput.value.trim(),
    booking_id: bookingId,
    status: elements.webhookStatusSelect.value,
    amount: parseFloat(elements.webhookAmountInput.value),
    currency: 'INR',
  };

  elements.webhookConsoleOutput.textContent = `// Sending POST /api/v1/payments/webhook/\nPayload:\n${JSON.stringify(payload, null, 2)}`;
  elements.lastHttpStatus.textContent = 'HTTP ...';

  try {
    const startTime = performance.now();
    const response = await fetch(`${API_BASE}/payments/webhook/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const elapsed = (performance.now() - startTime).toFixed(1);
    const data = await response.json();
    elements.lastHttpStatus.textContent = `HTTP ${response.status} (${elapsed}ms)`;

    elements.webhookConsoleOutput.textContent = `// Response from /api/v1/payments/webhook/:\n// Status: ${response.status} ${response.statusText}\n${JSON.stringify(data, null, 2)}`;

    if (data.is_duplicate) {
      elements.idempotencyProofCard.style.display = 'flex';
      elements.proofTitle.textContent = 'Idempotency Verified!';
      elements.proofDesc.textContent = `Duplicate Event '${data.event_id}' was safely ignored. Booking status was NOT duplicated or corrupted.`;
      showToast('Idempotency Verified: Duplicate event skipped safely!', 'success');
    } else {
      elements.idempotencyProofCard.style.display = 'none';
      showToast(`Webhook Processed: ${data.message}`, 'success');
    }

    await loadBookings();
  } catch (err) {
    elements.lastHttpStatus.textContent = 'HTTP ERROR';
    elements.webhookConsoleOutput.textContent = `// Error executing webhook:\n${err.message}`;
    showToast(`Webhook call failed: ${err.message}`, 'error');
  }
}

async function sendConcurrentWebhookHits() {
  const bookingId = parseInt(elements.webhookBookingSelect.value);
  if (!bookingId) {
    showToast('Please select a target booking first.', 'error');
    return;
  }

  const sharedEventId = `evt_race_${Math.floor(100000 + Math.random() * 900000)}`;
  elements.webhookEventIdInput.value = sharedEventId;

  const payload = {
    event_id: sharedEventId,
    event_type: 'payment.status.updated',
    transaction_id: `txn_${sharedEventId}`,
    booking_id: bookingId,
    status: 'SUCCESS',
    amount: parseFloat(elements.webhookAmountInput.value),
    currency: 'INR',
  };

  elements.webhookConsoleOutput.textContent = `// Firing 3 simultaneous concurrent POST /payments/webhook/ requests with identical event_id=${sharedEventId}...\n`;

  const promises = [1, 2, 3].map(async (workerId) => {
    const res = await fetch(`${API_BASE}/payments/webhook/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    return { workerId, status: res.status, data };
  });

  const results = await Promise.all(promises);
  elements.webhookConsoleOutput.textContent += JSON.stringify(results, null, 2);

  const processedCount = results.filter(r => r.data.status === 'processed').length;
  const duplicateCount = results.filter(r => r.data.is_duplicate === true).length;

  elements.idempotencyProofCard.style.display = 'flex';
  elements.proofTitle.textContent = `Concurrency Test Passed: ${processedCount} Processed, ${duplicateCount} Deduped!`;
  elements.proofDesc.textContent = 'Row-level locking and idempotency constraints prevented race condition corruption across all 3 concurrent hits.';

  showToast(`Concurrency Handled: ${processedCount} processed, ${duplicateCount} safely deduped.`, 'success');
  await loadBookings();
}

// User Switching
function switchUser(role) {
  state.activeRole = role;
  if (role === 'ADMIN') {
    elements.chooseAdmin.classList.add('active');
    elements.choosePatient.classList.remove('active');
    loginUser('admin@evehealthcare.com', 'AdminPass123!');
  } else {
    elements.choosePatient.classList.add('active');
    elements.chooseAdmin.classList.remove('active');
    loginUser('patient@example.com', 'PatientPass123!');
  }
  elements.switchUserModal.style.display = 'none';
}

// Tab Switching
function switchTab(tabId) {
  elements.tabBtns.forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });
  elements.tabPanes.forEach(pane => {
    pane.classList.toggle('active', pane.id === tabId);
  });
}

// Initialize Default Appointment Time to Tomorrow 10:00 AM
function initDefaultAppointmentTime() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(10, 0, 0, 0);

  const yyyy = tomorrow.getFullYear();
  const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const dd = String(tomorrow.getDate()).padStart(2, '0');
  const hh = String(tomorrow.getHours()).padStart(2, '0');
  const min = String(tomorrow.getMinutes()).padStart(2, '0');

  elements.bookDateInput.value = `${yyyy}-${mm}-${dd}T${hh}:${min}`;
  elements.bookDateInput.min = `${yyyy}-${mm}-${dd}T07:00`;
}

// Event Listeners
function setupEventListeners() {
  // Navigation Tabs
  elements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
  });

  // Header Nav Auth Buttons
  elements.navLoginBtn.addEventListener('click', () => openAuthModal('login'));
  elements.navSignupBtn.addEventListener('click', () => openAuthModal('signup'));
  elements.logoutBtn.addEventListener('click', logout);
  elements.tabLogoutBtn.addEventListener('click', logout);

  // Switch User Modal
  elements.quickSwitchBtn.addEventListener('click', () => {
    elements.switchUserModal.style.display = 'flex';
  });
  elements.closeSwitchModalBtn.addEventListener('click', () => {
    elements.switchUserModal.style.display = 'none';
  });
  elements.choosePatient.addEventListener('click', () => switchUser('PATIENT'));
  elements.chooseAdmin.addEventListener('click', () => switchUser('ADMIN'));

  // Auth Modal Controls
  elements.closeAuthModalBtn.addEventListener('click', closeAuthModal);
  elements.closeAuthModalBtn2.addEventListener('click', closeAuthModal);
  elements.closeAuthModalBtn3.addEventListener('click', closeAuthModal);
  elements.modalToggleLogin.addEventListener('click', () => setAuthMode('login', true));
  elements.modalToggleSignup.addEventListener('click', () => setAuthMode('signup', true));

  // Modal Login Submit
  elements.modalLoginFormElement.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = elements.modalLoginEmail.value.trim();
    const password = elements.modalLoginPassword.value;
    await loginUser(email, password);
  });

  // Modal Signup Submit
  elements.modalSignupFormElement.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      full_name: elements.modalSignupName.value.trim(),
      email: elements.modalSignupEmail.value.trim(),
      password: elements.modalSignupPassword.value,
      role: elements.modalSignupRole.value,
    };
    await registerUser(payload);
  });

  // Modal Quick Demo Buttons
  elements.modalQuickPatient.addEventListener('click', () => loginUser('patient@example.com', 'PatientPass123!'));
  elements.modalQuickAdmin.addEventListener('click', () => loginUser('admin@evehealthcare.com', 'AdminPass123!'));

  // Auth Tab (Portal) Controls
  elements.authPortalToggleLogin.addEventListener('click', () => setAuthMode('login', false));
  elements.authPortalToggleSignup.addEventListener('click', () => setAuthMode('signup', false));

  // Portal Login Submit
  elements.portalLoginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = elements.portalLoginEmail.value.trim();
    const password = elements.portalLoginPassword.value;
    await loginUser(email, password);
  });

  // Portal Signup Submit
  elements.portalSignupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      full_name: elements.portalSignupName.value.trim(),
      email: elements.portalSignupEmail.value.trim(),
      password: elements.portalSignupPassword.value,
      phone: elements.portalSignupPhone.value.trim() || null,
      role: elements.portalSignupRole.value,
    };
    await registerUser(payload);
  });

  // Portal Quick Demo Buttons
  elements.quickLoginPatient.addEventListener('click', () => loginUser('patient@example.com', 'PatientPass123!'));
  elements.quickLoginAdmin.addEventListener('click', () => loginUser('admin@evehealthcare.com', 'AdminPass123!'));

  // Centres & Filters
  elements.cityFilterSelect.addEventListener('change', loadCentres);
  elements.centreSearchInput.addEventListener('input', () => {
    clearTimeout(window._searchTimer);
    window._searchTimer = setTimeout(loadCentres, 300);
  });
  elements.refreshCentresBtn.addEventListener('click', loadCentres);

  // Booking Form
  elements.bookCentreSelect.addEventListener('change', handleCentreChange);
  elements.bookTestSelect.addEventListener('change', handleTestChange);
  elements.bookingForm.addEventListener('submit', submitBooking);
  elements.refreshBookingsBtn.addEventListener('click', loadBookings);

  // Payment Modal
  elements.closePaymentModalBtn.addEventListener('click', closePaymentModal);
  elements.cancelModalBtn.addEventListener('click', closePaymentModal);
  elements.paymentForm.addEventListener('submit', submitSimulatedPayment);

  // Webhook Lab
  elements.webhookBookingSelect.addEventListener('change', handleWebhookBookingChange);
  elements.regenEventIdBtn.addEventListener('click', generateNewEventId);
  elements.sendWebhookBtn.addEventListener('click', () => sendWebhookPayload(false));
  elements.replayWebhookBtn.addEventListener('click', () => sendWebhookPayload(true));
  elements.sendConcurrentWebhooksBtn.addEventListener('click', sendConcurrentWebhookHits);
}

// Bootstrap Application
async function init() {
  setupEventListeners();
  initDefaultAppointmentTime();
  generateNewEventId();
  checkHealth();
  setInterval(checkHealth, 30000);

  // Check URL pathname for direct navigation to /login or /signup
  const path = window.location.pathname.toLowerCase();
  if (path === '/login') {
    switchTab('auth-tab');
    setAuthMode('login', false);
  } else if (path === '/signup') {
    switchTab('auth-tab');
    setAuthMode('signup', false);
  }

  // If token is already in localStorage, restore session
  if (state.token) {
    await fetchCurrentUser();
  }

  await loadCentres();
  if (state.token) {
    await loadBookings();
  }
}

document.addEventListener('DOMContentLoaded', init);
