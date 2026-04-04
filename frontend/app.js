/**
 * CommerceFlow — Main Application Script
 *
 * Architecture:
 *   State  → single source of truth (no scattered globals)
 *   Render → pure function: state → DOM
 *   Events → modify state then re-render (like a mini flux loop)
 *
 * Data flow:
 *   API fetch → state.products
 *   User adds item → state.cart updates → renderCart()
 *   User checks out → POST /payment/initialize → redirect to Paystack
 */

// ============================================================
// CONFIG
// ============================================================
const API_BASE = 'https://commerceflow-paystack-n5ur.onrender.com';

// USD → NGN exchange rate for display purposes
// In a real system this would come from an FX API
const EXCHANGE_RATE = 1600;

// ============================================================
// STATE — single source of truth
// ============================================================
const state = {
  products:    [],    // all products from the API
  filtered:    [],    // products currently displayed (after category filter)
  cart:        {},    // { productId: { product, qty } }
  activeFilter: 'all',
};

// ============================================================
// DOM REFERENCES
// ============================================================
const dom = {
  grid:         document.getElementById('productsGrid'),
  emptyState:   document.getElementById('emptyState'),
  sectionTitle: document.getElementById('sectionTitle'),
  productCount: document.getElementById('productCount'),
  cartBadge:    document.getElementById('cartBadge'),
  cartDrawer:   document.getElementById('cartDrawer'),
  cartClose:    document.getElementById('cartClose'),
  cartTrigger:  document.getElementById('cartTrigger'),
  cartBody:     document.getElementById('cartBody'),
  cartEmpty:    document.getElementById('cartEmpty'),
  cartItems:    document.getElementById('cartItems'),
  cartFooter:   document.getElementById('cartFooter'),
  cartTotal:    document.getElementById('cartTotal'),
  emailInput:   document.getElementById('emailInput'),
  checkoutBtn:  document.getElementById('checkoutBtn'),
  overlay:      document.getElementById('overlay'),
  toast:        document.getElementById('toast'),
  navLinks:     document.querySelectorAll('.nav-link'),
};

// ============================================================
// UTILITY HELPERS
// ============================================================

/**
 * Format a price in Naira.
 * Products are priced in USD from the scrape source — we convert for display.
 * For checkout, we round to the nearest whole Naira.
 */
function formatNaira(usdPrice) {
  const naira = Math.round(usdPrice * EXCHANGE_RATE);
  return `₦${naira.toLocaleString()}`;
}

function toNairaInt(usdPrice) {
  return Math.round(usdPrice * EXCHANGE_RATE);
}

/** Flash a toast notification */
let toastTimer = null;
function showToast(message, type = '') {
  clearTimeout(toastTimer);
  dom.toast.textContent = message;
  dom.toast.className = `toast ${type} show`;
  toastTimer = setTimeout(() => {
    dom.toast.classList.remove('show');
  }, 2800);
}

/** Shallow validate an email address */
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

// ============================================================
// CART UTILS
// ============================================================

function getCartItems() {
  return Object.values(state.cart);
}

function getCartCount() {
  return getCartItems().reduce((acc, { qty }) => acc + qty, 0);
}

function getCartTotalNaira() {
  return getCartItems().reduce((acc, { product, qty }) => {
    return acc + toNairaInt(product.price) * qty;
  }, 0);
}

function addToCart(product) {
  const id = product.id;
  if (state.cart[id]) {
    state.cart[id].qty += 1;
  } else {
    state.cart[id] = { product, qty: 1 };
  }
  syncCartUI();
  showToast(`${product.name.split(',')[0].trim()} added to cart`, 'success');
}

function removeFromCart(productId) {
  delete state.cart[productId];
  syncCartUI();
}

function changeQty(productId, delta) {
  if (!state.cart[productId]) return;
  state.cart[productId].qty += delta;
  if (state.cart[productId].qty <= 0) {
    removeFromCart(productId);
  } else {
    syncCartUI();
  }
}

// ============================================================
// RENDER — Products
// ============================================================
function renderProducts(products) {
  // Clear the grid (removes skeleton cards too)
  dom.grid.innerHTML = '';

  if (products.length === 0) {
    dom.emptyState.style.display = 'block';
    dom.productCount.textContent = '0 items';
    return;
  }

  dom.emptyState.style.display = 'none';
  dom.productCount.textContent = `${products.length} item${products.length !== 1 ? 's' : ''}`;

  products.forEach((product, index) => {
    const card = buildProductCard(product, index);
    dom.grid.appendChild(card);
  });
}

function buildProductCard(product, index) {
  const inCart = !!state.cart[product.id];

  const card = document.createElement('div');
  card.className = 'product-card';
  card.style.animationDelay = `${index * 0.05 + 0.05}s`;
  card.dataset.id = product.id;

  card.innerHTML = `
    <div class="card-image">
      <img
        src="${product.image_url || ''}"
        alt="${product.full_name}"
        loading="lazy"
        onerror="this.style.opacity='0.2'"
      />
      <span class="card-category">${product.category || 'General'}</span>
    </div>
    <div class="card-body">
      <p class="card-name">${product.full_name}</p>
      <div class="card-footer">
        <span class="card-price">${formatNaira(product.price)}</span>
        <button
          class="card-add-btn ${inCart ? 'added' : ''}"
          data-id="${product.id}"
          aria-label="Add to cart"
          title="${inCart ? 'In cart' : 'Add to cart'}"
        >
          ${inCart ? '✓' : '+'}
        </button>
      </div>
    </div>
  `;

  // Add to cart button
  card.querySelector('.card-add-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    addToCart(product);
    // Update just this button (cheaper than re-rendering all cards)
    const btn = e.currentTarget;
    btn.textContent = '✓';
    btn.classList.add('added');
  });

  return card;
}

// ============================================================
// RENDER — Cart
// ============================================================
function syncCartUI() {
  const items = getCartItems();
  const count = getCartCount();
  const total = getCartTotalNaira();

  // Update badge
  dom.cartBadge.textContent = count;
  if (count > 0) {
    dom.cartBadge.classList.add('bump');
    setTimeout(() => dom.cartBadge.classList.remove('bump'), 300);
  }

  // Toggle empty / items view
  const isEmpty = items.length === 0;
  dom.cartEmpty.style.display  = isEmpty ? 'flex'  : 'none';
  dom.cartItems.style.display  = isEmpty ? 'none'  : 'flex';
  dom.cartFooter.style.display = isEmpty ? 'none'  : 'flex';

  // Render items
  dom.cartItems.innerHTML = '';
  items.forEach(({ product, qty }) => {
    const item = buildCartItem(product, qty);
    dom.cartItems.appendChild(item);
  });

  // Update total
  dom.cartTotal.textContent = `₦${total.toLocaleString()}`;
}

function buildCartItem(product, qty) {
  const el = document.createElement('div');
  el.className = 'cart-item';
  el.dataset.id = product.id;

  el.innerHTML = `
    <div class="cart-item-image">
      <img src="${product.image_url || ''}" alt="${product.name}" loading="lazy" />
    </div>
    <div class="cart-item-info">
      <p class="cart-item-name">${product.name}</p>
      <p class="cart-item-price">${formatNaira(product.price)}</p>
    </div>
    <div class="cart-item-qty">
      <button class="qty-btn remove-btn" data-id="${product.id}" data-action="decrease" title="Remove one">−</button>
      <span class="qty-count">${qty}</span>
      <button class="qty-btn" data-id="${product.id}" data-action="increase" title="Add one">+</button>
    </div>
  `;

  el.querySelector('[data-action="decrease"]').addEventListener('click', () => {
    changeQty(product.id, -1);
    // If we removed it, also reset the card button in the grid
    if (!state.cart[product.id]) resetCardButton(product.id);
  });

  el.querySelector('[data-action="increase"]').addEventListener('click', () => {
    changeQty(product.id, +1);
  });

  return el;
}

function resetCardButton(productId) {
  const btn = dom.grid.querySelector(`.card-add-btn[data-id="${productId}"]`);
  if (btn) {
    btn.textContent = '+';
    btn.classList.remove('added');
  }
}

// ============================================================
// FILTER LOGIC
// ============================================================
function applyFilter(filter) {
  state.activeFilter = filter;

  // Update nav UI
  dom.navLinks.forEach(link => {
    const isActive = link.dataset.filter === filter;
    link.classList.toggle('active', isActive);
  });

  // Filter products
  if (filter === 'all') {
    state.filtered = [...state.products];
    dom.sectionTitle.textContent = 'All Products';
  } else {
    state.filtered = state.products.filter(
      p => p.category?.toLowerCase() === filter.toLowerCase()
    );
    // Capitalise label
    dom.sectionTitle.textContent = filter.charAt(0).toUpperCase() + filter.slice(1);
  }

  renderProducts(state.filtered);
}

// ============================================================
// CHECKOUT FLOW
// ============================================================
async function handleCheckout() {
  const email = dom.emailInput.value.trim();

  if (!isValidEmail(email)) {
    dom.emailInput.focus();
    dom.emailInput.style.borderColor = 'var(--error)';
    showToast('Please enter a valid email address.', 'error');
    setTimeout(() => {
      dom.emailInput.style.borderColor = '';
    }, 2000);
    return;
  }

  const items  = getCartItems();
  const total  = getCartTotalNaira();

  if (items.length === 0) {
    showToast('Your cart is empty.', 'error');
    return;
  }

  // ---- Show loading state ----
  const btnText    = dom.checkoutBtn.querySelector('.btn-text');
  const btnSpinner = dom.checkoutBtn.querySelector('.btn-spinner');
  dom.checkoutBtn.disabled = true;
  btnText.textContent      = 'Redirecting…';
  btnSpinner.style.display = 'inline-flex';

  try {
    const payload = {
      email,
      amount:     total,
      // We send all item IDs and quantities for backend verification
      cart_items: items.map(i => ({ id: i.product.id, qty: i.qty })),
      metadata:   { cart_count: items.length }
    };

    const response = await fetch(`${API_BASE}/payment/initialize`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Payment initialization failed.');
    }

    // Paystack returns a hosted checkout URL — redirect the user there
    window.location.href = data.authorization_url;

  } catch (err) {
    console.error('[Checkout Error]', err);
    showToast(err.message || 'Something went wrong. Please try again.', 'error');

    // Reset button
    dom.checkoutBtn.disabled  = false;
    btnText.textContent       = 'Checkout with Paystack';
    btnSpinner.style.display  = 'none';
  }
}

// ============================================================
// API — Fetch Products
// ============================================================
async function fetchProducts() {
  try {
    const response = await fetch(`${API_BASE}/products/`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const products = await response.json();
    state.products = products;
    state.filtered = [...products];

    renderProducts(state.filtered);

  } catch (err) {
    console.error('[Products Error]', err);
    dom.grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:60px 20px;color:var(--text-muted);">
        <p style="font-size:14px;">Could not load products.</p>
        <p style="font-size:12px;margin-top:6px;">Is the API server running at <code>${API_BASE}</code>?</p>
        <button onclick="fetchProducts()" style="
          margin-top:16px;padding:8px 20px;
          background:var(--surface-2);border:1px solid var(--border);
          color:var(--text-primary);border-radius:100px;cursor:pointer;font-size:13px;
        ">Retry</button>
      </div>
    `;
  }
}

// ============================================================
// DRAWER — open / close
// ============================================================
function openCart() {
  dom.cartDrawer.classList.add('open');
  dom.overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeCart() {
  dom.cartDrawer.classList.remove('open');
  dom.overlay.classList.remove('active');
  document.body.style.overflow = '';
}

// ============================================================
// BIND EVENTS
// ============================================================
dom.cartTrigger.addEventListener('click', openCart);
dom.cartClose.addEventListener('click', closeCart);
dom.overlay.addEventListener('click', closeCart);
dom.checkoutBtn.addEventListener('click', handleCheckout);

// Email input — clear error styling on input
dom.emailInput.addEventListener('input', () => {
  dom.emailInput.style.borderColor = '';
});

// Category filter nav links
dom.navLinks.forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    applyFilter(link.dataset.filter);
  });
});

// ============================================================
// MOBILE FILTER — inject a horizontal scroll filter bar
// because the header nav is hidden on small screens
// ============================================================
function injectMobileFilters() {
  if (window.innerWidth > 768) return;

  const categories = ['all', 'electronics', 'jewelery', "men's clothing", "women's clothing"];
  const bar = document.createElement('div');
  bar.className = 'mobile-filter-bar';
  bar.style.cssText = `
    display:flex;gap:8px;padding:12px 24px;overflow-x:auto;
    scrollbar-width:none;border-bottom:1px solid var(--border);
    -webkit-overflow-scrolling:touch;
  `;

  categories.forEach(cat => {
    const btn = document.createElement('button');
    const label = cat === 'all' ? 'All' :
                  cat === "men's clothing" ? 'Men' :
                  cat === "women's clothing" ? 'Women' :
                  cat.charAt(0).toUpperCase() + cat.slice(1);

    btn.textContent = label;
    btn.style.cssText = `
      flex-shrink:0;padding:6px 16px;border-radius:100px;border:1px solid var(--border);
      background:var(--surface);color:var(--text-muted);font-family:var(--font-body);
      font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap;transition:all 0.2s;
    `;

    if (cat === 'all') {
      btn.style.color = 'var(--accent)';
      btn.style.background = 'var(--accent-dim)';
      btn.style.borderColor = 'transparent';
    }

    btn.addEventListener('click', () => {
      bar.querySelectorAll('button').forEach(b => {
        b.style.color = 'var(--text-muted)';
        b.style.background = 'var(--surface)';
        b.style.borderColor = 'var(--border)';
      });
      btn.style.color = 'var(--accent)';
      btn.style.background = 'var(--accent-dim)';
      btn.style.borderColor = 'transparent';
      applyFilter(cat);
    });

    bar.appendChild(btn);
  });

  document.querySelector('.hero').insertAdjacentElement('afterend', bar);
}

// ============================================================
// BOOT
// ============================================================
(function init() {
  injectMobileFilters();
  fetchProducts();
  syncCartUI();
})();