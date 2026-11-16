from app.bot.widgets.templates.base_styles import COMMON_CRM_CSS


def build_order_card_html() -> str:
    """
    Generates self-contained HTML + CSS + JS for an interactive Order Card widget.
    Executed in Telegram's sandboxed environment.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
{COMMON_CRM_CSS}

.order-stepper {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  margin: 10px 0;
}}
.order-stepper::before {{
  content: "";
  position: absolute;
  top: 14px;
  left: 10px;
  right: 10px;
  height: 2px;
  background: var(--border-color);
  z-index: 1;
}}
.step-item {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  position: relative;
  z-index: 2;
}}
.step-dot {{
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--text-muted);
  transition: all 0.2s;
}}
.step-item.active .step-dot {{
  background: var(--primary);
  border-color: var(--accent);
  color: #fff;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}}
.step-item.completed .step-dot {{
  background: var(--success);
  border-color: var(--success);
  color: #fff;
}}
.step-label {{
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 500;
}}
.step-item.active .step-label {{
  color: var(--accent);
  font-weight: 700;
}}

.info-table {{
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
}}
.info-row {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  padding-bottom: 4px;
}}
.info-label {{
  color: var(--text-muted);
}}
.info-val {{
  font-weight: 600;
  color: var(--text-main);
  text-align: right;
}}

/* Confirmation modal inside widget */
.modal-overlay {{
  display: none;
  background: rgba(11, 19, 41, 0.95);
  position: fixed;
  inset: 0;
  z-index: 100;
  padding: 16px;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}}
.modal-overlay.active {{
  display: flex;
}}
</style>
</head>
<body>
<div class="crm-container">
  <div class="crm-header">
    <div class="crm-brand">
      <span>📦 Замовлення #<span id="order-id-title">—</span></span>
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
      <span id="order-status-badge" class="status-pill status-new">—</span>
      <button class="crm-refresh-btn" onclick="sendAction('refresh_order')" title="Оновити">🔄</button>
    </div>
  </div>

  <!-- Stepper -->
  <div class="crm-card" style="padding: 8px 12px;">
    <div class="order-stepper" id="order-stepper">
      <div class="step-item" id="step-new">
        <div class="step-dot">1</div>
        <div class="step-label">Нове</div>
      </div>
      <div class="step-item" id="step-planned">
        <div class="step-dot">2</div>
        <div class="step-label">План</div>
      </div>
      <div class="step-item" id="step-in_delivery">
        <div class="step-dot">3</div>
        <div class="step-label">В дорозі</div>
      </div>
      <div class="step-item" id="step-delivered">
        <div class="step-dot">4</div>
        <div class="step-label">Вручено</div>
      </div>
    </div>
  </div>

  <!-- Client & Financial Info -->
  <div class="crm-card">
    <div class="crm-card-header">
      <span class="crm-card-title">👤 Клієнт</span>
      <button class="crm-btn crm-btn-ghost crm-btn-sm" onclick="sendAction('order_open_customer')">Картка клієнта</button>
    </div>
    <div class="info-table">
      <div class="info-row">
        <span class="info-label">ПІБ / Назва:</span>
        <span class="info-val" id="cust-name">—</span>
      </div>
      <div class="info-row">
        <span class="info-label">Телефон:</span>
        <span class="info-val" id="cust-phone">—</span>
      </div>
      <div class="info-row">
        <span class="info-label">Адреса доставки:</span>
        <span class="info-val" id="delivery-address" style="max-width:65%;">—</span>
      </div>
      <div class="info-row" id="coords-row" style="display:none;">
        <span class="info-label">Точка GPS:</span>
        <span class="info-val" id="delivery-coords" style="color:var(--accent);">—</span>
      </div>
    </div>
  </div>

  <div class="crm-card">
    <div class="crm-card-header">
      <span class="crm-card-title">🧱 Розрахунок замовлення</span>
      <span class="crm-badge" id="product-name">Торф'яний брикет</span>
    </div>
    <div class="info-table">
      <div class="info-row">
        <span class="info-label">Кількість:</span>
        <span class="info-val"><span id="order-qty">0</span> т</span>
      </div>
      <div class="info-row">
        <span class="info-label">Ціна за тонну:</span>
        <span class="info-val"><span id="order-price">0</span> грн/т</span>
      </div>
      <div class="info-row">
        <span class="info-label">Вартість товару:</span>
        <span class="info-val"><span id="product-total">0</span> грн</span>
      </div>
      <div class="info-row">
        <span class="info-label">Вартість доставки:</span>
        <span class="info-val"><span id="delivery-price">0</span> грн</span>
      </div>
      <div class="info-row" style="border-bottom:none; margin-top:2px;">
        <span class="info-label" style="font-weight:700; color:var(--text-main);">РАЗОМ ДО СПЛАТИ:</span>
        <span class="info-val" style="font-size:14px; color:var(--accent);"><span id="total-amount">0</span> грн</span>
      </div>
    </div>
  </div>

  <!-- Delivery times & Notes -->
  <div class="crm-card" id="details-block">
    <div class="info-table">
      <div class="info-row">
        <span class="info-label">Дата замовлення:</span>
        <span class="info-val" id="order-date">—</span>
      </div>
      <div class="info-row" id="departure-row" style="display:none;">
        <span class="info-label">Час виїзду:</span>
        <span class="info-val" id="departure-time" style="color:var(--warning);">—</span>
      </div>
      <div class="info-row" id="completed-row" style="display:none;">
        <span class="info-label">Час доставки:</span>
        <span class="info-val" id="completed-time" style="color:var(--success);">—</span>
      </div>
      <div class="info-row" id="notes-row" style="display:none; border-bottom:none;">
        <span class="info-label">Коментар:</span>
        <span class="info-val" id="order-notes" style="font-style:italic;">—</span>
      </div>
    </div>
  </div>

  <!-- Action buttons -->
  <div class="crm-card" style="padding:10px;">
    <div style="display:flex; flex-direction:column; gap:8px;" id="action-buttons-container">
      <!-- Dynamic action buttons -->
    </div>
  </div>
</div>

<!-- Modal Confirmation for Cancel -->
<div class="modal-overlay" id="confirm-modal">
  <div class="crm-card" style="width:100%; max-width:320px; padding:16px;">
    <div style="font-size:14px; font-weight:700; margin-bottom:8px; color:var(--danger);">⚠️ Підтвердження скасування</div>
    <div style="font-size:12px; color:var(--text-muted); margin-bottom:14px;">
      Ви дійсно бажаєте скасувати це замовлення? Цю дію буде зафіксовано в системі CRM.
    </div>
    <div style="display:flex; gap:8px; justify-content:center;">
      <button class="crm-btn crm-btn-danger" style="flex:1;" onclick="executeCancelOrder()">Так, скасувати</button>
      <button class="crm-btn crm-btn-ghost" style="flex:1;" onclick="closeConfirmModal()">Ні, повернутися</button>
    </div>
  </div>
</div>

<script>
(function() {{
  var orderData = null;

  function getTW() {{
    return window.TelegramWidget || window.Telegram?.WebApp || null;
  }}

  window.sendAction = function(action, extra) {{
    var payload = Object.assign({{
      action: action,
      order_id: orderData ? orderData.id : null
    }}, extra || {{}});

    var tw = getTW();
    if (tw && typeof tw.request === 'function') {{
      tw.request(JSON.stringify(payload));
    }} else if (tw && typeof tw.sendData === 'function') {{
      tw.sendData(JSON.stringify(payload));
    }}
  }};

  window.openWaze = function() {{
    if (!orderData || !orderData.waze_url) return;
    var tw = getTW();
    if (tw && typeof tw.openLink === 'function') {{
      tw.openLink(orderData.waze_url);
    }} else {{
      window.open(orderData.waze_url, '_blank');
    }}
  }};

  window.promptCancelOrder = function() {{
    document.getElementById('confirm-modal').classList.add('active');
  }};

  window.closeConfirmModal = function() {{
    document.getElementById('confirm-modal').classList.remove('active');
  }};

  window.executeCancelOrder = function() {{
    closeConfirmModal();
    sendAction('order_change_status', {{ status: 'cancelled' }});
  }};

  window.changeStatus = function(newStatus) {{
    sendAction('order_change_status', {{ status: newStatus }});
  }};

  function parseChatData(raw) {{
    if (!raw) return null;
    if (typeof raw === 'object') return raw;
    try {{ return JSON.parse(raw); }} catch(e) {{ return null; }}
  }}

  function updateStepper(status) {{
    var steps = ['new', 'planned', 'in_delivery', 'delivered'];
    var currentIdx = steps.indexOf(status);

    steps.forEach(function(s, idx) {{
      var el = document.getElementById('step-' + s);
      if (!el) return;
      el.classList.remove('active', 'completed');
      if (status === 'cancelled') {{
        // Cancelled state
      }} else if (idx < currentIdx) {{
        el.classList.add('completed');
      }} else if (idx === currentIdx) {{
        el.classList.add('active');
      }}
    }});
  }}

  function renderOrder() {{
    if (!orderData) return;

    document.getElementById('order-id-title').textContent = orderData.id;
    var badge = document.getElementById('order-status-badge');
    badge.className = 'status-pill status-' + (orderData.status || 'new');
    badge.textContent = getStatusLabel(orderData.status);

    updateStepper(orderData.status);

    // Client info
    document.getElementById('cust-name').textContent = orderData.customer_name || '—';
    document.getElementById('cust-phone').textContent = orderData.customer_phone || '—';
    document.getElementById('delivery-address').textContent = orderData.delivery_address || '—';

    if (orderData.delivery_latitude && orderData.delivery_longitude) {{
      document.getElementById('coords-row').style.display = 'flex';
      document.getElementById('delivery-coords').textContent = orderData.delivery_latitude.toFixed(5) + ', ' + orderData.delivery_longitude.toFixed(5);
    }} else {{
      document.getElementById('coords-row').style.display = 'none';
    }}

    // Financial
    document.getElementById('order-qty').textContent = orderData.quantity;
    document.getElementById('order-price').textContent = orderData.unit_price;
    document.getElementById('product-total').textContent = orderData.product_total;
    document.getElementById('delivery-price').textContent = orderData.delivery_price;
    document.getElementById('total-amount').textContent = orderData.total_amount;

    // Details
    document.getElementById('order-date').textContent = orderData.order_date || '—';

    if (orderData.delivery_started_at) {{
      document.getElementById('departure-row').style.display = 'flex';
      document.getElementById('departure-time').textContent = orderData.delivery_started_at;
    }} else {{
      document.getElementById('departure-row').style.display = 'none';
    }}

    if (orderData.delivery_completed_at) {{
      document.getElementById('completed-row').style.display = 'flex';
      document.getElementById('completed-time').textContent = orderData.delivery_completed_at;
    }} else {{
      document.getElementById('completed-row').style.display = 'none';
    }}

    if (orderData.notes) {{
      document.getElementById('notes-row').style.display = 'flex';
      document.getElementById('order-notes').textContent = orderData.notes;
    }} else {{
      document.getElementById('notes-row').style.display = 'none';
    }}

    // Action buttons
    renderActionButtons();
  }}

  function renderActionButtons() {{
    var container = document.getElementById('action-buttons-container');
    var st = orderData.status;
    var html = '';

    // Primary delivery progression buttons
    if (st === 'new') {{
      html += '<button class="crm-btn crm-btn-primary" onclick="changeStatus(\\'planned\\')">🗓 Запланувати виїзд</button>';
      html += '<button class="crm-btn crm-btn-primary" onclick="changeStatus(\\'in_delivery\\')">🚚 Розпочати доставку зараз</button>';
    }} else if (st === 'planned') {{
      html += '<button class="crm-btn crm-btn-primary" onclick="changeStatus(\\'in_delivery\\')">🚚 Почати доставку (Виїзд)</button>';
    }} else if (st === 'in_delivery') {{
      html += '<button class="crm-btn crm-btn-success" onclick="changeStatus(\\'delivered\\')">✅ Доставлено клієнту</button>';
    }}

    // Navigation Waze button
    if (orderData.waze_url && (st === 'new' || st === 'planned' || st === 'in_delivery')) {{
      html += '<button class="crm-btn crm-btn-ghost" onclick="openWaze()">🧭 Відкрити маршрут у Waze</button>';
    }}

    // Cancellation button
    if (st !== 'delivered' && st !== 'cancelled') {{
      html += '<button class="crm-btn crm-btn-danger crm-btn-sm" style="margin-top:4px;" onclick="promptCancelOrder()">❌ Скасувати замовлення</button>';
    }}

    container.innerHTML = html;
  }}

  function getStatusLabel(status) {{
    switch(status) {{
      case 'new': return '🆕 Нове';
      case 'planned': return '🗓 Заплановано';
      case 'in_delivery': return '🚚 В дорозі';
      case 'delivered': return '✅ Доставлено';
      case 'cancelled': return '❌ Скасовано';
      default: return status || '—';
    }}
  }}

  function loadInitial() {{
    var tw = getTW();
    if (tw && tw.chatData) {{
      var parsed = parseChatData(tw.chatData);
      if (parsed) {{
        orderData = parsed.order || parsed;
        renderOrder();
      }}
    }}
    if (tw && typeof tw.ready === 'function') {{
      tw.ready();
    }}
  }}

  function onDataChanged() {{
    var tw = getTW();
    if (tw && tw.chatData) {{
      var parsed = parseChatData(tw.chatData);
      if (parsed) {{
        orderData = parsed.order || parsed;
        renderOrder();
      }}
    }}
  }}

  var tw = getTW();
  if (tw && typeof tw.onEvent === 'function') {{
    tw.onEvent('chatDataChanged', onDataChanged);
  }}
  window.addEventListener('message', function(e) {{
    if (e.data && e.data.type === 'chatDataChanged') {{
      onDataChanged();
    }}
  }});

  document.addEventListener('DOMContentLoaded', loadInitial);
  setTimeout(loadInitial, 50);
}})();
</script>
</body>
</html>"""
    return html
