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

/* -------- Transición entre vistas -------- */
function transitionTo(showId, hideId){
  const showEl = document.getElementById(showId);
  const hideEl = document.getElementById(hideId);
  if (hideEl && !hideEl.classList.contains('hidden')) {
    hideEl.classList.remove('fade-in'); hideEl.classList.add('fade-out');
    hideEl.addEventListener('animationend', function onEnd(){
      hideEl.removeEventListener('animationend', onEnd);
      hideEl.classList.add('hidden'); hideEl.classList.remove('fade-out');
      if (showEl){
        showEl.classList.remove('hidden'); showEl.classList.add('fade-in');
        showEl.addEventListener('animationend', function onEnd2(){
          showEl.removeEventListener('animationend', onEnd2);
          showEl.classList.remove('fade-in');
        });
      }
    });
  } else if (showEl){
    showEl.classList.remove('hidden'); showEl.classList.add('fade-in');
    showEl.addEventListener('animationend', function onEnd3(){
      showEl.removeEventListener('animationend', onEnd3);
      showEl.classList.remove('fade-in');
    });
  }
}

/* -------- Modal ligero en checkout -------- */
function showCheckoutResult(status){
  const modal = document.getElementById('resultModal');
  const panel = modal?.querySelector('.result-modal__panel');
  const title = document.getElementById('resultTitle');
  const text  = document.getElementById('resultText');
  const goHomeLink = document.getElementById('linkGoHome');

  const cls = status === 'paid' ? 'success' :
              status === 'cancelled' ? 'info' :
              status === 'error' ? 'error' : 'info';

  // Limpia clases previas y aplica la actual
  if (panel){
    panel.classList.remove('success','info','error');
    panel.classList.add(cls);
  }

  title.textContent = status === 'paid'      ? '¡Gracias por tu compra!' :
                      status === 'cancelled' ? 'Pago cancelado' :
                      status === 'error'     ? 'Ocurrió un error' :
                                               `Estado: ${status}`;

  // Texto con buen contraste (el CSS ya fuerza color blanco)
  text.textContent  = status === 'paid'      ? 'El pago fue confirmado.' :
                      status === 'cancelled' ? 'La deuda fue anulada correctamente.' :
                      status === 'error'     ? 'No pudimos completar el pago.' :
                                               'Volvemos al inicio.';

  // Enlace "Ir al inicio" que ejecuta el mismo flujo de limpiado
  if (goHomeLink){
    goHomeLink.onclick = async (e) => {
      e.preventDefault();
      modal.classList.add('hidden');
      await resetForNewPurchase();
    };
  }

  modal.classList.remove('hidden');

  // Cierre automático hacia un nuevo flujo limpio (2.4s)
  setTimeout(async () => {
    modal.classList.add('hidden');
    await resetForNewPurchase();
  }, 2400);
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
    ORDER_ITEMS_SNAPSHOT = CART.map(i => ({ ...i })); // congelar
    enterCheckout(data.order_id, data.payment_url);
  } catch(err) {
    console.error(err);
    showToast('Error creando la orden: '+err.message, 'error');
  }
}

/* Entra al workspace de pago y arma ambas columnas */
function enterCheckout(orderId, paymentUrl) {
  transitionTo('checkoutWorkspace','catalogView');

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

/* Eliminar deuda en AdamsPay (cancelación inmediata) */
async function cancelOrderAndMark(orderId){
  try{
    const res = await fetch(`${API_BASE}/orders/${orderId}`, {
      method:'DELETE',
      headers:{'Content-Type':'application/json'}
    });
    if (!res.ok){
      try{
        const j = await res.json();
        const d = (j && j.detail || '').toString().toLowerCase();
        if (res.status===404 || (res.status===400 && (d.includes('pagada') || d.includes('paid')))) return 'paid';
      }catch{}
      return null;
    }
    return 'cancelled';
  }catch(e){
    console.warn('cancelOrderAndMark:', e);
    return null;
  }
}

/* Reinicia el flujo para una nueva compra (volver a catálogo) */
async function resetForNewPurchase() {
  CURRENT_ORDER = null;
  CART = [];
  ORDER_ITEMS_SNAPSHOT = [];

  transitionTo('catalogView','checkoutWorkspace');

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
    try { await cancelOrderAndMark(CURRENT_ORDER.id); } catch {}
    if (alertedOrders[CURRENT_ORDER?.id]) delete alertedOrders[CURRENT_ORDER.id];
    CURRENT_ORDER = null;
  }
  CART = [];
  updateCartUI();
  setAddButtonsEnabled(true);
}

/* -------- Pago embebido (iframe) con retorno + polling --------
   - Si vuelve same-origin:
       * Si no es "paid": cancelar deuda, actualizar badge y mostrar modal.
       * Si es "paid": actualizar badge y mostrar modal de éxito.
   - Plan B con polling durante 3 min.
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
      const origin = frame.contentWindow.location.origin; // lanza si sigue en AdamsPay
      const sameOrigin = origin === window.location.origin;
      if (sameOrigin) {
        let status = await checkOrderStatus(orderId);

        if (status !== 'paid') {
          // cancelar de inmediato para no dejar deuda colgando
          const res = await cancelOrderAndMark(orderId);
          status = res || status || 'cancelled';
        }

        // reflejo en ticket y feedback local
        updateStatusBadge(status);
        showToast(status === 'paid' ? 'Orden pagada ✅' :
                  status === 'cancelled' ? 'Pago cancelado. Deuda anulada.' :
                  'No se completó el pago.', status === 'paid' ? 'success' : (status === 'cancelled' ? 'info' : 'error'));

        // modal y autoredirección a catálogo limpio
        showCheckoutResult(status);
      }
    } catch (_) {
      // Primer load (cross-origin): nada.
    }
  };
  frame.addEventListener('load', frame._onLoadHandler);

  // Polling (plan B) por 3 min máx
  const POLL_MS = 1500;
  const MAX_MS = 3 * 60 * 1000;
  const deadline = Date.now() + MAX_MS;

  frame._statusPoll = setInterval(async () => {
    try {
      let status = await checkOrderStatus(orderId);
      if (['paid','cancelled','error'].includes(status)) {
        if (status !== 'paid') {
          const res = await cancelOrderAndMark(orderId);
          status = res || status;
        }
        updateStatusBadge(status);
        showToast(status === 'paid' ? 'Orden pagada ✅' :
                  status === 'cancelled' ? 'Pago cancelado. Deuda anulada.' :
                  'No se completó el pago.', status === 'paid' ? 'success' : (status === 'cancelled' ? 'info' : 'error'));
        showCheckoutResult(status);
        stopInlinePolling(frame);
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

/* -------- Init -------- */
document.getElementById('btnCheckout').addEventListener('click', createOrder);
document.getElementById('btnClear').addEventListener('click', () => { clearCart(); if (!hasActivePendingOrder()) setAddButtonsEnabled(true); });

(async function init(){
  await fetchProducts();
  updateCartUI();
})();
