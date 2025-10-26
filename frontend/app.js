// frontend/app.js
const API_BASE = window.location.origin;
const CUSTOMER_ID = 1; // demo

let PRODUCTS = [];
let CART = [];
let ORDER_ITEMS_SNAPSHOT = []; // items congelados al crear la orden
let alertedOrders = {};  // orderId -> toast ya mostrado
let CURRENT_ORDER = null; // { id, status }

/* -------- Traducciones de estado -------- */
const STATUS_ES = {
  pending: "Pendiente",
  paid: "Pagada",
  cancelled: "Cancelada",
  error: "Error"
};

/* -------- Toasts -------- */
const toastContainer = document.createElement('div');
toastContainer.id = 'toastContainer';
document.body.appendChild(toastContainer);

function showToast(msg, type='info', duration=3500){
  const toast = document.createElement('div');
  toast.className = 'toast ' + (type === 'success' ? 'success' : type === 'error' ? 'error' : 'info');
  toast.textContent = msg;
  toast.style.opacity = '0';
  toastContainer.appendChild(toast);
  requestAnimationFrame(()=>toast.classList.add('show'));
  setTimeout(()=>{ toast.classList.remove('show'); setTimeout(()=>toast.remove(), 300); }, duration);
}

/* -------- Banner resultado -------- */
function showResultBar(text, type='info', ms=4000){
  const bar = document.getElementById('resultBar');
  const msg = document.getElementById('resultBarMsg');
  if (!bar || !msg) return;
  msg.textContent = text;
  bar.classList.remove('hidden','success','error','info');
  bar.classList.add(type);
  // autohide
  setTimeout(()=>bar.classList.add('hidden'), ms);
}

/* -------- Productos -------- */
async function fetchProducts() {
  try {
    const res = await fetch(`${API_BASE}/products`);
    if (!res.ok) throw new Error(`Error ${res.status}`);
    PRODUCTS = await res.json();
    renderProducts();
  } catch (err) {
    console.error(err);
    document.getElementById('products').innerHTML = '<div class="product-card muted">No se pudieron cargar los productos.</div>';
  }
}

function renderProducts() {
  const el = document.getElementById('products');
  el.innerHTML = '';
  if (!PRODUCTS.length) {
    el.innerHTML = '<div class="product-card muted">No hay productos.</div>';
    return;
  }

  PRODUCTS.forEach(p => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
      ${p.imagen ? `<img src="${escapeHtml(p.imagen)}" alt="${escapeHtml(p.nombre)}" style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:8px"/>` : ''}
      <h3>${escapeHtml(p.nombre)}</h3>
      <div class="muted small">${escapeHtml(p.tipo || 'General')}</div>
      <div style="margin:6px 0; font-size:13px; color:#444; min-height:36px">${escapeHtml(p.descripcion || '')}</div>
      <div class="muted small">ID: ${p.id}</div>
      <div style="margin:8px 0;"><span class="price">${formatMoney(p.precio)}</span></div>
      <div class="qty-row">
        <input class="qty-input" type="number" min="1" value="1" id="q_${p.id}" />
        <button class="btn btn-primary add-btn" data-product="${p.id}" onclick="addToCart(${p.id})">Agregar</button>
      </div>
    `;
    el.appendChild(card);
  });

  setAddButtonsEnabled(!hasActiveOrder());
}

/* -------- Carrito (UI) -------- */
function addToCart(productId) {
  if (hasActivePendingOrder()) {
    showToast('Hay una orden pendiente. Finalizá o cancelá antes de agregar más.', 'error');
    return;
  }
  const qtyInput = document.getElementById(`q_${productId}`);
  let qty = parseInt(qtyInput?.value || "1") || 1;
  const prod = PRODUCTS.find(p => p.id === productId);
  if (!prod) return;
  const inCart = CART.find(i => i.product_id === productId);
  if (inCart) inCart.cantidad += qty;
  else CART.push({ product_id: prod.id, nombre: prod.nombre, precio: prod.precio, cantidad: qty });
  updateCartUI();
}

function renderCartControls(item) {
  if (hasActivePendingOrder()) {
    return `
      <div style="margin-top:6px">
        <button class="btn btn-outline" disabled>-</button>
        <button class="btn btn-outline" disabled>+</button>
        <button class="btn btn-outline" disabled>Quitar</button>
      </div>
    `;
  } else {
    return `
      <div style="margin-top:6px">
        <button class="btn btn-outline" onclick="decQty(${item.product_id})">-</button>
        <button class="btn btn-outline" onclick="incQty(${item.product_id})">+</button>
        <button class="btn btn-outline" onclick="removeItem(${item.product_id})">Quitar</button>
      </div>
    `;
  }
}

function updateCartUI() {
  const container = document.getElementById('cartItems');
  container.innerHTML = '';
  if (!CART.length) {
    container.innerHTML = '<div class="muted small">Carrito vacío</div>';
    document.getElementById('btnCheckout').disabled = true;
    document.getElementById('cartTotal').textContent = formatMoney(0);
    const badgeEmpty = document.getElementById('cartCount');
    if (badgeEmpty) { badgeEmpty.textContent = '0'; badgeEmpty.style.display = 'none'; }
    return;
  }

  CART.forEach(item => {
    const div = document.createElement('div');
    div.className = 'cart-item';
    div.innerHTML = `
      <div style="min-width:0">
        <div style="font-weight:700; overflow:hidden; text-overflow:ellipsis">${escapeHtml(item.nombre)}</div>
        <div class="muted small">x${item.cantidad} · ${formatMoney(item.precio)}</div>
      </div>
      <div style="text-align:right; min-width:90px">
        <div style="font-weight:700">${formatMoney(item.precio * item.cantidad)}</div>
        ${renderCartControls(item)}
      </div>
    `;
    container.appendChild(div);
  });

  const checkoutBtn = document.getElementById('btnCheckout');
  checkoutBtn.disabled = hasActiveOrder() || !CART.length;
  document.getElementById('btnClear').disabled = hasActiveOrder();
  document.getElementById('cartTotal').textContent = formatMoney(calcTotal());

  const totalCount = CART.reduce((s, i) => s + (Number(i.cantidad) || 0), 0);
  const badge = document.getElementById('cartCount');
  if (badge) {
    badge.textContent = String(totalCount);
    badge.style.display = totalCount > 0 ? 'inline-block' : 'none';
  }
}

function calcTotal() { return CART.reduce((s, i) => s + i.precio * i.cantidad, 0); }
function incQty(pid) { if (hasActivePendingOrder()) return; const it = CART.find(i => i.product_id === pid); if(it) it.cantidad++; updateCartUI(); }
function decQty(pid) { if (hasActivePendingOrder()) return; const it = CART.find(i => i.product_id === pid); if(it) it.cantidad=Math.max(1,it.cantidad-1); updateCartUI(); }
function removeItem(pid) { if (hasActivePendingOrder()) return; CART = CART.filter(i=>i.product_id!==pid); updateCartUI(); }

/* -------- Helpers para estado de orden -------- */
function hasActivePendingOrder() { return CURRENT_ORDER && CURRENT_ORDER.status === 'pending'; }
function hasActiveOrder() { return CURRENT_ORDER !== null; }
function setAddButtonsEnabled(enabled) { document.querySelectorAll('.add-btn').forEach(b => b.disabled = !enabled); }

/* -------- Orden / AdamsPay (flujo sin modal) -------- */
async function createOrder() {
  if (hasActivePendingOrder()) { showToast('Ya tenés una orden pendiente. Verificá su estado.', 'info'); return; }
  if (!CART.length) return showToast('Carrito vacío', 'error');

  const body = { customer_id:CUSTOMER_ID, items:CART.map(i=>({product_id:i.product_id,cantidad:i.cantidad})) };
  try {
    const res = await fetch(`${API_BASE}/orders`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
    if (!res.ok) { const error=await res.json().catch(()=>null); throw new Error(error?.detail||`HTTP ${res.status}`); }
    const data = await res.json();

    CURRENT_ORDER = { id: data.order_id, status: 'pending' };
    // guardo para poder resolver al volver por Url de retorno
    localStorage.setItem('last_order_id', String(data.order_id));

    ORDER_ITEMS_SNAPSHOT = CART.map(i => ({ ...i })); // congelar
    enterCheckout(data.order_id, data.payment_url);
  } catch(err) {
    console.error(err);
    showToast('Error creando la orden: '+err.message, 'error');
  }
}

/* Entra al workspace de pago y arma ambas columnas */
function enterCheckout(orderId, paymentUrl) {
  // Ocultar catálogo + carrito, mostrar checkout
  document.getElementById('catalogView').classList.add('hidden');
  const ws = document.getElementById('checkoutWorkspace');
  ws.classList.remove('hidden');

  // Render ticket
  document.getElementById('ckOrderId').textContent = orderId;
  document.getElementById('ckOrderTotal').textContent = formatMoney(calcSnapshotTotal());
  updateStatusBadge('pending');

  renderTicketItems();

  // Bloquear edición del carrito
  setAddButtonsEnabled(false);

  // Cargar pago embebido y arrancar polling
  if (paymentUrl) showPaymentInline(paymentUrl, orderId);
}

function renderTicketItems() {
  const tbody = document.getElementById('ticketItems');
  tbody.innerHTML = '';
  if (!ORDER_ITEMS_SNAPSHOT.length) {
    tbody.innerHTML = '<div class="muted small">Sin items.</div>';
    return;
  }
  ORDER_ITEMS_SNAPSHOT.forEach(it => {
    const row = document.createElement('div');
    row.className = 'ticket-row';
    row.innerHTML = `
      <div class="t-name">${escapeHtml(it.nombre)}</div>
      <div class="t-qty">x${it.cantidad}</div>
      <div class="t-price">${formatMoney(it.precio)}</div>
      <div class="t-sub">${formatMoney(it.precio * it.cantidad)}</div>
    `;
    tbody.appendChild(row);
  });
}

function calcSnapshotTotal() {
  return ORDER_ITEMS_SNAPSHOT.reduce((s, i) => s + i.precio * i.cantidad, 0);
}

function updateStatusBadge(status) {
  const el = document.getElementById('ckOrderStatus');
  el.textContent = STATUS_ES[status] || '—';
  el.className = 'order-badge ' + (status || '');
}

/* Verificación de estado */
async function checkOrderStatus(orderId) {
  try {
    const res = await fetch(`${API_BASE}/orders/${orderId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (CURRENT_ORDER && CURRENT_ORDER.id === orderId) CURRENT_ORDER.status = data.status;
    updateStatusBadge(data.status || '');

    return data.status;
  } catch(err) {
    console.error(err);
    showToast('Error verificando estado: ' + err.message, 'error');
    return null;
  }
}

/* Eliminar deuda en AdamsPay (para cancelar pendientes al salir) */
async function deleteOrder(orderId) {
  if (!orderId) return;
  try {
    const res = await fetch(`${API_BASE}/orders/${orderId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) {
      let detail = null;
      try { detail = (await res.json()).detail; } catch {}
      if (res.status === 404 || (res.status === 400 && typeof detail === 'string' && detail.toLowerCase().includes('orden pagada'))) {
        console.warn('deleteOrder silenciado:', res.status, detail);
        return;
      }
      throw new Error(detail || `HTTP ${res.status}`);
    }
    await res.json();
    showToast('Deuda eliminada correctamente', 'success');
  } catch(err) {
    console.error('Error eliminando deuda:', err);
    showToast('Error eliminando deuda: '+err.message, 'error');
  }
}

/* Reinicia el flujo para una nueva compra (usado internamente tras volver del pago) */
async function resetForNewPurchase() {
  CURRENT_ORDER = null;
  CART = [];
  ORDER_ITEMS_SNAPSHOT = [];

  // UI
  document.getElementById('checkoutWorkspace').classList.add('hidden');
  document.getElementById('catalogView').classList.remove('hidden');

  const frame = document.getElementById('paymentFrameInline');
  stopInlinePolling(frame);
  frame.src = '';

  setAddButtonsEnabled(true);
  updateCartUI();
}

/* Limpiar carrito (pre-orden). Si hay orden pendiente, elimina deuda y resetea. */
async function clearCart() {
  if (hasActivePendingOrder()) {
    showToast('No podés limpiar el carrito con una orden pendiente. Eliminando deuda...', 'info');
    try { await deleteOrder(CURRENT_ORDER.id); } catch {}
    if (alertedOrders[CURRENT_ORDER?.id]) delete alertedOrders[CURRENT_ORDER.id];
    CURRENT_ORDER = null;
  }
  CART = [];
  updateCartUI();
  setAddButtonsEnabled(true);
}

/* -------- Pago embebido (iframe) con retorno same-origin + polling --------
   - Si el iframe vuelve a la misma origin (Url de retorno), redirigimos la página
     completa al inicio y mostramos un banner con el resultado real (consultando API).
---------------------------------------------------------------- */
function showPaymentInline(paymentUrl, orderId){
  const frame = document.getElementById('paymentFrameInline');

  // limpiar handlers / timers previos
  cleanupInlineHandlers(frame);

  // setear URL
  frame.src = '';
  requestAnimationFrame(()=>{ frame.src = paymentUrl; });

  // Handler de retorno same-origin
  frame._onLoadHandler = async () => {
    try {
      const origin = frame.contentWindow.location.origin; // cross-origin lanza excepción si aún está en AdamsPay
      const sameOrigin = origin === window.location.origin;
      if (sameOrigin) {
        // ya estás en tu dominio dentro del iframe → resolvemos estado y redireccionamos la app completa
        const status = await checkOrderStatus(orderId);
        // guardamos resultado temporal en sessionStorage para mostrar banner en el home
        if (status) {
          sessionStorage.setItem('payment_result', JSON.stringify({ orderId, status }));
        }
        // redirige al home (nuevo flujo limpio)
        window.location.replace(window.location.origin + '/');
        return;
      }
    } catch (_) {
      // Primer load (cross-origin): no pasa nada; seguimos.
    }
  };
  frame.addEventListener('load', frame._onLoadHandler);

  // Polling por si el PSP no vuelve por iframe (3 min máx)
  const POLL_MS = 1500;
  const MAX_MS = 3 * 60 * 1000;
  const deadline = Date.now() + MAX_MS;

  frame._statusPoll = setInterval(async () => {
    try {
      const status = await checkOrderStatus(orderId);
      if (['paid','cancelled','error'].includes(status)) {
        sessionStorage.setItem('payment_result', JSON.stringify({ orderId, status }));
        window.location.replace(window.location.origin + '/');
      }
      if (Date.now() > deadline) stopInlinePolling(frame);
    } catch { /* silencioso */ }
  }, POLL_MS);

  frame._statusPollDeadlineTimer = setTimeout(() => {
    stopInlinePolling(frame);
  }, MAX_MS + 500);
}

function cleanupInlineHandlers(frame){
  if (!frame) return;
  if (frame._onLoadHandler) {
    frame.removeEventListener('load', frame._onLoadHandler);
    frame._onLoadHandler = null;
  }
  stopInlinePolling(frame);
  frame._armed = false;
}

function stopInlinePolling(frame){
  if (!frame) return;
  if (frame._statusPoll) { clearInterval(frame._statusPoll); frame._statusPoll = null; }
  if (frame._statusPollDeadlineTimer) { clearTimeout(frame._statusPollDeadlineTimer); frame._statusPollDeadlineTimer = null; }
}

/* -------- Helpers -------- */
function formatMoney(n){
  return (Number(n) || 0).toLocaleString('es-PY', { style: 'currency', currency: 'PYG', maximumFractionDigits: 0 });
}
function escapeHtml(s){ return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m]); }

/* -------- On load: botones y retorno de pago -------- */
document.getElementById('btnCheckout').addEventListener('click', createOrder);
document.getElementById('btnClear').addEventListener('click', () => { clearCart(); if (!hasActivePendingOrder()) setAddButtonsEnabled(true); });

(async function init(){
  // Si venimos de Url de retorno y el backend no redirigió, mostramos banner según sessionStorage
  const pr = sessionStorage.getItem('payment_result');
  if (pr) {
    try {
      const { orderId, status } = JSON.parse(pr);
      const text = status === 'paid'
        ? `¡Pago de la orden #${orderId} confirmado!`
        : status === 'cancelled'
          ? `Pago de la orden #${orderId} cancelado.`
          : status === 'error'
            ? `Hubo un error con la orden #${orderId}.`
            : `Estado de la orden #${orderId}: ${status}`;
      showResultBar(text, status === 'paid' ? 'success' : (status === 'error' ? 'error' : 'info'));
    } catch {}
    sessionStorage.removeItem('payment_result');
    // limpiar estado local para nuevo flujo
    await resetForNewPurchase();
    // además olvidar referencia de última orden
    localStorage.removeItem('last_order_id');
  }

  await fetchProducts();
  updateCartUI();
})();
