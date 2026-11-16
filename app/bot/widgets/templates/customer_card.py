from app.bot.widgets.templates.base_styles import COMMON_CRM_CSS


def build_customer_card_html() -> str:
    """
    Generates self-contained HTML + CSS + JS for an interactive Customer Card widget.
    Executed in Telegram's sandboxed environment.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
{COMMON_CRM_CSS}

.history-item {{
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: background 0.15s;
}}
.history-item:active {{
  background: var(--bg-card-hover);
  border-color: var(--accent);
}}
.history-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.history-title {{
  font-weight: 600;
  font-size: 12px;
}}
.history-meta {{
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
}}
</style>
</head>
<body>
<div class="crm-container">
  <div class="crm-header">
    <div class="crm-brand">
      <span>👤 <span id="cust-name-title">Клієнт</span></span>
      <span class="crm-badge">ID: #<span id="cust-id-badge">—</span></span>
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
      <button class="crm-refresh-btn" onclick="sendAction('refresh_customer')" title="Оновити">🔄</button>
    </div>
  </div>

  <!-- KPI summary -->
  <div class="crm-grid-2">
    <div class="crm-kpi-card">
      <div class="crm-kpi-label">📋 Замовлень</div>
      <div class="crm-kpi-val" id="cust-orders-count">0</div>
    </div>
    <div class="crm-kpi-card">
      <div class="crm-kpi-label">💰 Всього сплачено</div>
      <div class="crm-kpi-val" style="color:var(--success);"><span id="cust-total-spent">0</span> <span style="font-size:11px;">грн</span></div>
    </div>
  </div>

  <!-- Contact details -->
  <div class="crm-card">
    <div class="crm-card-header">
      <span class="crm-card-title">📞 Контактна інформація</span>
    </div>
    <div style="display:flex; flex-direction:column; gap:6px; font-size:12px;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="color:var(--text-muted);">Телефон:</span>
        <span style="font-weight:700; color:var(--accent);" id="cust-phone">—</span>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <span style="color:var(--text-muted);">Адреса:</span>
        <span style="font-weight:600; max-width:65%; text-align:right;" id="cust-address">—</span>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center;" id="coords-row" style="display:none;">
        <span style="color:var(--text-muted);">GPS:</span>
        <span style="color:var(--accent); font-weight:600;" id="cust-coords">—</span>
      </div>
      <div id="notes-row" style="display:none; border-top:1px solid rgba(255,255,255,0.04); padding-top:4px;">
        <span style="color:var(--text-muted);">Примітки: </span>
        <span style="font-style:italic;" id="cust-notes">—</span>
      </div>
    </div>
    <div style="display:flex; gap:6px; margin-top:6px;">
      <button class="crm-btn crm-btn-ghost crm-btn-sm" style="flex:1;" id="call-btn" onclick="callPhone()">📞 Виклик</button>
      <button class="crm-btn crm-btn-ghost crm-btn-sm" style="flex:1;" id="map-btn" onclick="openMap()">📍 На карті</button>
    </div>
  </div>

  <!-- Fast Actions -->
  <div class="crm-card" style="padding:10px;">
    <button class="crm-btn crm-btn-primary" style="width:100%;" onclick="sendAction('cust_new_order')">
      ➕ Оформити нове замовлення
    </button>
  </div>

  <!-- Orders history -->
  <div class="crm-card">
    <div class="crm-card-header">
      <span class="crm-card-title">📦 Історія замовлень</span>
      <span class="crm-card-meta" id="history-count">0 замовл.</span>
    </div>
    <div style="display:flex; flex-direction:column; gap:6px;" id="history-container">
      <div class="crm-empty">Історія замовлень порожня</div>
    </div>
  </div>
</div>

<script>
(function() {{
  var customerData = null;

  function getTW() {{
    return window.TelegramWidget || window.Telegram?.WebApp || null;
  }}

  window.sendAction = function(action, extra) {{
    var payload = Object.assign({{
      action: action,
      customer_id: customerData ? customerData.id : null
    }}, extra || {{}});

    var tw = getTW();
    if (tw && typeof tw.request === 'function') {{
      tw.request(JSON.stringify(payload));
    }} else if (tw && typeof tw.sendData === 'function') {{
      tw.sendData(JSON.stringify(payload));
    }}
  }};

  window.openOrder = function(orderId) {{
    sendAction('open_order', {{ order_id: orderId }});
  }};

  window.callPhone = function() {{
    if (customerData && customerData.phone) {{
      window.location.href = 'tel:' + customerData.phone;
    }}
  }};

  window.openMap = function() {{
    if (!customerData) return;
    var url = customerData.map_url;
    if (!url && customerData.address) {{
      url = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(customerData.address);
    }}
    if (url) {{
      var tw = getTW();
      if (tw && typeof tw.openLink === 'function') {{
        tw.openLink(url);
      }} else {{
        window.open(url, '_blank');
      }}
    }}
  }};

  function parseChatData(raw) {{
    if (!raw) return null;
    if (typeof raw === 'object') return raw;
    try {{ return JSON.parse(raw); }} catch(e) {{ return null; }}
  }}

  function getStatusPill(status) {{
    switch(status) {{
      case 'new': return '<span class="status-pill status-new">🆕 Нове</span>';
      case 'planned': return '<span class="status-pill status-planned">🗓 Заплановано</span>';
      case 'in_delivery': return '<span class="status-pill status-in_delivery">🚚 В дорозі</span>';
      case 'delivered': return '<span class="status-pill status-delivered">✅ Доставлено</span>';
      case 'cancelled': return '<span class="status-pill status-cancelled">❌ Скасовано</span>';
      default: return '<span class="status-pill status-new">' + (status || '—') + '</span>';
    }}
  }}

  function renderCustomer() {{
    if (!customerData) return;

    document.getElementById('cust-name-title').textContent = customerData.name || 'Клієнт';
    document.getElementById('cust-id-badge').textContent = customerData.id;
    document.getElementById('cust-phone').textContent = customerData.phone || '—';
    document.getElementById('cust-address').textContent = customerData.address || '—';

    document.getElementById('cust-orders-count').textContent = customerData.orders_count || 0;
    document.getElementById('cust-total-spent').textContent = customerData.total_spent || 0;

    if (customerData.latitude && customerData.longitude) {{
      document.getElementById('coords-row').style.display = 'flex';
      document.getElementById('cust-coords').textContent = customerData.latitude.toFixed(5) + ', ' + customerData.longitude.toFixed(5);
    }} else {{
      document.getElementById('coords-row').style.display = 'none';
    }}

    if (customerData.notes) {{
      document.getElementById('notes-row').style.display = 'block';
      document.getElementById('cust-notes').textContent = customerData.notes;
    }} else {{
      document.getElementById('notes-row').style.display = 'none';
    }}

    // History
    var historyContainer = document.getElementById('history-container');
    var orders = customerData.orders || [];
    document.getElementById('history-count').textContent = orders.length + ' замовл.';

    if (!orders.length) {{
      historyContainer.innerHTML = '<div class="crm-empty">Історія замовлень порожня</div>';
      return;
    }}

    var html = '';
    orders.forEach(function(o) {{
      var stPill = getStatusPill(o.status);
      html += '' +
        '<div class="history-item" onclick="openOrder(' + o.id + ')">' +
          '<div class="history-header">' +
            '<span class="history-title">Замовлення #' + o.id + '</span>' +
            stPill +
          '</div>' +
          '<div class="history-meta">' +
            '<span>🧱 ' + o.quantity + ' т | ' + (o.order_date || '') + '</span>' +
            '<span style="font-weight:700; color:var(--accent);">' + o.total_amount + ' грн</span>' +
          '</div>' +
        '</div>';
    }});
    historyContainer.innerHTML = html;
  }}

  function loadInitial() {{
    var tw = getTW();
    if (tw && tw.chatData) {{
      var parsed = parseChatData(tw.chatData);
      if (parsed) {{
        customerData = parsed.customer || parsed;
        renderCustomer();
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
        customerData = parsed.customer || parsed;
        renderCustomer();
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
