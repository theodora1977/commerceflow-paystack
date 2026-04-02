/**
 * CommerceFlow — Payment Verification Script (success.html)
 *
 * Flow:
 *   1. Paystack redirects here after payment with ?reference=xxx&trxref=xxx
 *   2. We extract the reference from the URL query string
 *   3. We call GET /payment/verify?reference=xxx on our backend
 *   4. Backend calls Paystack, updates the order in our DB, returns status
 *   5. We render the appropriate state card (success / failed / abandoned / error)
 *
 * Why verify server-side?
 *   Anyone can manually visit success.html with any reference string.
 *   Only a live server-to-server Paystack call tells us the *real* status.
 *   This is the second phase of the two-phase commit: Paystack commits first,
 *   we independently confirm before we fulfil.
 */

const API_BASE = 'http://127.0.0.1:8000';

// ---- DOM state cards ----
const stateLoading = document.getElementById('stateLoading');
const stateSuccess = document.getElementById('stateSuccess');
const stateFailed  = document.getElementById('stateFailed');
const stateError   = document.getElementById('stateError');

// ---- Helper: show one card, hide the rest ----
function showState(id) {
  [stateLoading, stateSuccess, stateFailed, stateError].forEach(el => {
    el.style.display = el.id === id ? 'flex' : 'none';
  });
}

// ---- Helper: extract a query param from the current URL ----
function getParam(key) {
  return new URLSearchParams(window.location.search).get(key);
}

// ---- Populate success card ----
function renderSuccess(data) {
  document.getElementById('detailRef').textContent    = data.reference || '—';
  document.getElementById('detailAmount').textContent = data.amount    || '—';
  document.getElementById('detailEmail').textContent  = data.email     || '—';
  showState('stateSuccess');
}

// ---- Populate failed/abandoned card ----
function renderFailed(data) {
  const ref    = data.reference || getParam('reference') || getParam('trxref') || '—';
  const status = data.status    || 'failed';

  document.getElementById('failedRef').textContent = ref;

  const pill = document.getElementById('failedStatus');
  if (status === 'abandoned') {
    pill.textContent = 'Abandoned';
    pill.classList.add('status-pill--abandoned');
    pill.classList.remove('status-pill--failed');

    document.getElementById('failedTitle').textContent = 'Payment Abandoned';
    document.getElementById('failedSub').textContent =
      'You closed the payment page before completing the transaction. No charge was made.';
  } else {
    pill.textContent = 'Failed';
  }

  showState('stateFailed');
}

// ---- Populate error card ----
function renderError(message) {
  if (message) {
    document.getElementById('errorMsg').textContent = message;
  }
  showState('stateError');
}

// ============================================================
// MAIN — verify the payment
// ============================================================
async function verifyPayment(reference) {
  try {
    const response = await fetch(
      `${API_BASE}/payment/verify?reference=${encodeURIComponent(reference)}`
    );

    // If the backend itself errored (500, 400, etc.)
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      renderError(errData.detail || `Verification failed (HTTP ${response.status}).`);
      return;
    }

    const data = await response.json();

    switch (data.status) {
      case 'success':
        renderSuccess(data);
        break;

      case 'failed':
      case 'abandoned':
        renderFailed(data);
        break;

      default:
        // Unknown status — treat as error
        renderError(`Unexpected payment status: "${data.status}". Contact support.`);
    }

  } catch (err) {
    console.error('[Verify Error]', err);
    renderError(
      'We could not connect to the verification server. ' +
      'Please check your internet connection and try again.'
    );
  }
}

// ============================================================
// BOOT
// ============================================================
(function init() {
  // Paystack appends both 'reference' and 'trxref' — handle both
  const reference = getParam('reference') || getParam('trxref');

  if (!reference) {
    renderError(
      'No payment reference found in the URL. ' +
      'Please return to the store and try again.'
    );
    return;
  }

  // Show the loading spinner immediately while we verify
  showState('stateLoading');
  verifyPayment(reference);
})();
        return;
    }

    try {
        // Call backend to verify status
        const response = await fetch(`/payment/verify?reference=${reference}`);
        const result = await response.json();

        if (result.status === 'success') {
            document.getElementById('detailRef').innerText = reference;
            document.getElementById('detailAmount').innerText = result.amount;
            document.getElementById('detailEmail').innerText = result.email;
            showState('stateSuccess');
        } else {
            document.getElementById('failedRef').innerText = reference;
            showState('stateFailed');
        }
    } catch (error) {
        showState('stateError', 'Failed to communicate with the verification server.');
    }
});

function showState(stateId, message = null) {
    // Hide all states
    ['stateLoading', 'stateSuccess', 'stateFailed', 'stateError'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });

    // Show active state
    const activeState = document.getElementById(stateId);
    activeState.style.display = 'block';
    if (message && stateId === 'stateError') {
        document.getElementById('errorMsg').innerText = message;
    }
}