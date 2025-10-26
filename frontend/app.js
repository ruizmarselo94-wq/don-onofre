// frontend/app.js
const API_BASE = window.location.origin;
const CUSTOMER_ID = 1;

let PRODUCTS = [];
let CART = [];
let alertedOrders = {};
let CURRENT_ORDER = null;
let ORDER_STREAM = null;

const STATUS_ES = { pending: "Pendiente", paid: "Pagada", cancelled: "Cancelada", devuelta: "Devuelta", error: "Error" };

const toastContainer = document.createElement('div');
toastContainer.id = 'toastContainer';
document.body.appendChild(toastContainer);
function showToast(msg, type='info', duration=3500){
  const t=document.createElement('div'); t.className='toast '+(type==='success'?'success':type==='error'?'error':'info'); t.textContent=msg;
  t.style.opacity='0'; toastContainer.appendChild(t); requestAnimationFrame(()=>t.classList.add('show'));
  setTimeout(()=>{ t.classList.remove('show'); setTimeout(()=>t.remove(),300); }, duration);
}

/* Productos */
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
  const el = document.getElementById('products'); el.innerHTML = '';
  if (!PRODUCTS.length) { el.innerHTML = '<div class="product-card muted">No hay productos.</div>'; return; }
  PRODUCTS.forEach(p => {
    const c=document.createElement('div'); c.className='product-card';
    c.innerHTML = `
      ${p.imagen ? `<img src="${escapeHtml(p.imagen)}" alt="${escapeHtml(p.nombre)}" style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:8px"/>` : ''}
      <h3>${escapeHtml(p.nombre)}</h3>
      <div class="muted small">${escapeHtml(p.tipo || 'General')}</div>
      <div style="margin:6px 0; font-size:13px; color:#444; min-height:36px">${escapeHtml(p.descripcion || '')}</div>
      <div class="muted small">ID: ${p.id}</div>
      <div style="margin:8px 0;"><span class="price">${formatMoney(p.precio)}</span></div>
      <div style="display:flex;gap:8px;align-items:center">
        <input type="number" min="1" value="1" id="q_${p.id}" />
        <button class="btn btn-primary add-btn" data-product="${p.id}" onclick="addToCart(${p.id})">Agregar</button>
      </div>`;
    el.appendChild(c);
  });
  setAddButtonsEnabled(!hasActiveOrder());
}

/* Carrito */
function addToCart(productId) {
  if (hasActivePendingOrder()) { showToast('Hay una orden pendiente. Finalizá o cancelá antes de agregar más.', 'error'); return; }
  const qtyInput=document.getElementById(`q_${productId}`); let qty=parseInt(qtyInput?.value||"1")||1;
  const prod=PRODUCTS.find(p=>p.id===productId); if (!prod) return;
  const inCart=CART.find(i=>i.product_id===productId);
  if (inCart) inCart.cantidad+=qty; else CART.push({product_id:prod.id,nombre:prod.nombre,precio:prod.precio,cantidad:qty});
  updateCartUI();
}
function renderCartControls(item) {
  if (hasActivePendingOrder()) {
    return `<div style="margin-top:6px"><button class="btn btn-outline" disabled>-</button><button class="btn btn-outline" disabled>+</button><button class="btn btn-outline" disabled>Quitar</button></div>`;
  } else {
    return `<div style="margin-top:6px"><button class="btn btn-outline" onclick="decQty(${item.product_id})">-</button><button class="btn btn-outline" onclick="incQty(${item.product_id})">+</button><button class="btn btn-outline" onclick="removeItem(${item.product_id})">Quitar</button></div>`;
  }
}
function updateCartUI() {
  const container=document.getElementById('cartItems'); container.innerHTML='';
  if (!CART.length) {
    container.innerHTML='<div class="muted small">Carrito vacío</div>';
    document.getElementById('btnCheckout').disabled=true;
    document.getElementById('cartTotal').textContent=formatMoney(0);
    const b=document.getElementById('cartCount'); if (b){ b.textContent='0'; b.style.display='none'; }
    return;
  }
  CART.forEach(item=>{
    const d=document.createElement('div'); d.className='cart-item';
    d.innerHTML = `
      <div style="min-width:0">
        <div style="font-weight:700; overflow:hidden; text-overflow:ellipsis">${escapeHtml(item.nombre)}</div>
        <div class="muted small">x${item.cantidad} · ${formatMoney(item.precio)}</div>
      </div>
      <div style="text-align:right; min-width:90px">
        <div style="font-weight:700">${formatMoney(item.precio * item.cantidad)}</div>
        ${renderCartControls(item)}
      </div>`;
    container.appendChild(d);
  });
  const checkoutBtn=document.getElementById('btnCheckout');
  checkoutBtn.disabled=hasActiveOrder()||!CART.length;
  document.getElementById('btnClear').disabled=hasActiveOrder();
  document.getElementById('cartTotal').textContent=formatMoney(calcTotal());
  const totalCount=CART.reduce((s,i)=>s+(Number(i.cantidad)||0),0);
  const badge=document.getElementById('cartCount'); if (badge){ badge.textContent=String(totalCount); badge.style.display=totalCount>0?'inline-block':'none'; }
}
function calcTotal(){ return CART.reduce((s,i)=>s+i.precio*i.cantidad,0); }
function incQty(pid){ if (hasActivePendingOrder()) return; const it=CART.find(i=>i.product_id===pid); if(it) it.cantidad++; updateCartUI(); }
function decQty(pid){ if (hasActivePendingOrder()) return; const it=CART.find(i=>i.product_id===pid); if(it) it.cantidad=Math.max(1,it.cantidad-1); updateCartUI(); }
function removeItem(pid){ if (hasActivePendingOrder()) return; CART=CART.filter(i=>i.product_id!==pid); updateCartUI(); }

/* Estado orden */
function hasActivePendingOrder(){ return CURRENT_ORDER && CURRENT_ORDER.status==='pending'; }
function hasActiveOrder(){ return CURRENT_ORDER!==null; }
function setAddButtonsEnabled(enabled){ document.querySelectorAll('.add-btn').forEach(b=>b.disabled=!enabled); }

/* Orden / AdamsPay (sin polling) */
async function createOrder(){
  if (hasActivePendingOrder()){ showToast('Ya tienes una orden pendiente. Verificá su estado.', 'info'); return; }
  if (!CART.length) return showToast('Carrito vacío', 'error');
  const body={ customer_id:CUSTOMER_ID, items:CART.map(i=>({product_id:i.product_id,cantidad:i.cantidad})) };
  try{
    const res=await fetch(`${API_BASE}/orders`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(!res.ok){ const e=await res.json().catch(()=>null); throw new Error(e?.detail||`HTTP ${res.status}`); }
    const data=await res.json();
    CURRENT_ORDER={ id:data.order_id, status:'pending' };
    showOrderInfo(data.order_id, data.payment_url);
    setAddButtonsEnabled(false);
    document.getElementById('btnCheckout').disabled=true;
    document.getElementById('btnClear').disabled=true;
    startOrderStream(data.order_id);            // ← suscripción SSE
  }catch(err){
    console.error(err); showToast('Error creando la orden: '+err.message,'error');
  }
}

function startOrderStream(orderId){
  stopOrderStream();
  const url = `${API_BASE}/events/orders/${orderId}`;
  ORDER_STREAM = new EventSource(url);
  ORDER_STREAM.onmessage = (e)=>{
    const data = JSON.parse(e.data||"{}");
    if (!data || !data.status) return;
    applyOrderStatus(data.status, orderId);
  };
  ORDER_STREAM.onerror = ()=>{ /* silencioso */ };
}
function stopOrderStream(){
  if (ORDER_STREAM){ ORDER_STREAM.close(); ORDER_STREAM=null; }
}

function applyOrderStatus(status, orderId){
  const statusEl=document.getElementById('orderStatus');
  statusEl.textContent=STATUS_ES[status]||status||'—';
  statusEl.className=status||'';
  if (CURRENT_ORDER && CURRENT_ORDER.id===orderId) CURRENT_ORDER.status=status;

  if (status==='paid' && !alertedOrders[orderId]){
    alertedOrders[orderId]=true;
    showToast('Orden Pagada ✅','success');
    hidePaymentUI();
    closePaymentModal();                       // ← cerrar modal automáticamente
    document.getElementById('btnCheckout').disabled=true;
    updateCartUI();
    stopOrderStream();
    return;
  }
  if (status==='cancelled' || status==='devuelta'){
    showToast(`Estado: ${STATUS_ES[status]||status}`,'info');
    hidePaymentUI();
    closePaymentModal();                       // ← cerrar modal automáticamente
    stopOrderStream();
  }
}

function hidePaymentUI(){
  const btnCheck=document.getElementById('btnCheck'); if (btnCheck) btnCheck.classList.add('hidden');
  const link=document.getElementById('paymentLink'); if (link) link.classList.add('hidden');
  const btnNew=document.getElementById('btnNew'); if (btnNew) btnNew.style.display='inline-block';
}

/* Info de la orden */
function showOrderInfo(orderId,paymentUrl){
  document.getElementById('orderInfo').style.display='block';
  const statusEl=document.getElementById('orderStatus');
  statusEl.textContent=STATUS_ES['pending'];
  statusEl.className='pending';
  document.getElementById('orderId').textContent=orderId;
  document.getElementById('orderTotal').textContent=formatMoney(calcTotal());
  if (paymentUrl) showPayment(paymentUrl);

  const link=document.getElementById('paymentLink');
  link.href=paymentUrl||'#';
  link.style.display=paymentUrl?'inline-block':'none';
  link.classList.remove('hidden');
  link.textContent=paymentUrl?'Ir a pagar':'Abrir pago';
  link.onclick=(e)=>{ e.preventDefault(); if(paymentUrl) showPayment(paymentUrl); };

  const btnCheck=document.getElementById('btnCheck');
  btnCheck.style.display='inline-block';
  btnCheck.onclick=()=>checkOrderStatus(orderId);
  btnCheck.classList.remove('hidden');

  const btnNew=document.getElementById('btnNew');
  btnNew.style.display='none';
  btnNew.onclick=()=>resetForNewPurchase();

  const focusHandler=async()=>{
    await checkOrderStatus(orderId);
    if (document.getElementById('orderStatus').textContent===STATUS_ES['paid']){
      window.removeEventListener('focus', focusHandler);
    }
  };
  window.addEventListener('focus', focusHandler);
}

async function checkOrderStatus(orderId){
  try{
    const res=await fetch(`${API_BASE}/orders/${orderId}`);
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    const data=await res.json();
    applyOrderStatus(data.status, orderId);
  }catch(err){
    console.error(err); showToast('Error verificando estado: '+err.message,'error');
  }
}

/* Borrar deuda */
async function deleteOrder(orderId){
  if(!orderId) return;
  try{
    const res=await fetch(`${API_BASE}/orders/${orderId}`,{method:'DELETE',headers:{'Content-Type':'application/json'}});
    if(!res.ok){
      const e=await res.json().catch(()=>null);
      throw new Error(e?.detail||`HTTP ${res.status}`);
    }
    const data=await res.json();
    showToast('Deuda eliminada correctamente','success');
  }catch(err){
    console.error('Error eliminando deuda:',err);
    showToast('Error eliminando deuda: '+err.message,'error');
  }
}

/* Nueva compra */
async function resetForNewPurchase(){
  if (CURRENT_ORDER){
    if (alertedOrders[CURRENT_ORDER.id]) delete alertedOrders[CURRENT_ORDER.id];
    try{ await deleteOrder(CURRENT_ORDER.id); }catch(_){}
  }
  stopOrderStream();
  CURRENT_ORDER=null;
  CART=[];
  updateCartUI();
  setAddButtonsEnabled(true);

  const link=document.getElementById('paymentLink'); if (link){ link.classList.remove('hidden'); link.style.display='none'; link.href='#'; link.onclick=null; }
  const btnCheck=document.getElementById('btnCheck'); if (btnCheck){ btnCheck.classList.remove('hidden'); btnCheck.style.display='none'; btnCheck.onclick=null; }
  const btnNew=document.getElementById('btnNew'); if (btnNew) btnNew.style.display='none';

  document.getElementById('btnCheckout').disabled=CART.length===0;
  document.getElementById('btnClear').disabled=false;

  document.getElementById('orderInfo').style.display='none';
  document.getElementById('orderId').textContent='—';
  document.getElementById('orderTotal').textContent='—';
  const statusEl=document.getElementById('orderStatus'); statusEl.textContent='—'; statusEl.className='';
}

/* Limpiar carrito */
async function clearCart(){
  if (hasActivePendingOrder()){
    showToast('No podés limpiar el carrito con una orden pendiente. Eliminando deuda...','info');
    try{ await deleteOrder(CURRENT_ORDER.id); }catch(_){}
    if (alertedOrders[CURRENT_ORDER?.id]) delete alertedOrders[CURRENT_ORDER.id];
    CURRENT_ORDER=null;
    stopOrderStream();
  }
  CART=[]; updateCartUI(); setAddButtonsEnabled(true);
}

/* Utils & Init */
function formatMoney(n){ return (Number(n)||0).toLocaleString('es-PY',{style:'currency',currency:'PYG',maximumFractionDigits:0}); }
function escapeHtml(s){ return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m]); }

document.getElementById('btnCheckout').addEventListener('click', createOrder);
document.getElementById('btnClear').addEventListener('click', ()=>{ clearCart(); if (!hasActivePendingOrder()) setAddButtonsEnabled(true); });

fetchProducts();
updateCartUI();

/* Modal de pago */
function showPayment(paymentUrl){
  const modal=document.getElementById('paymentModal');
  const frame=document.getElementById('paymentFrame');
  frame.src=''; requestAnimationFrame(()=>{ frame.src=paymentUrl; });
  modal.style.display='block';
}
function closePaymentModal(){
  const modal=document.getElementById('paymentModal');
  const frame=document.getElementById('paymentFrame');
  frame.src=''; modal.style.display='none';
}
document.getElementById('closePaymentModal').addEventListener('click', closePaymentModal);
