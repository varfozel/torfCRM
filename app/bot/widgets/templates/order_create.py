from app.bot.widgets.templates.base_styles import COMMON_CRM_CSS


def build_order_create_html() -> str:
    """
    Generates self-contained HTML + CSS + JS for the interactive Order Creation widget.
    Executed in Telegram's sandboxed environment.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
{COMMON_CRM_CSS}

.form-group {{
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}}
.form-label {{
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
  display: flex;
  justify-content: space-between;
}}
.form-select, .form-input {{
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  padding: 8px 10px;
  font-size: 12px;
  outline: none;
  width: 100%;
}}
.form-select:focus, .form-input:focus {{
  border-color: var(--accent);
}}
.stepper-row {{
  display: flex;
  align-items: center;
  gap: 6px;
}}
.stepper-btn {{
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  border-radius: var(--radius-sm);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
}}
.stepper-btn:active {{
  background: var(--primary);
  border-color: var(--accent);
}}
.quick-chips {{
  display: flex;
  gap: 4px;
  margin-top: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}}
.quick-chip {{
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  cursor: pointer;
  white-space: nowrap;
}}
.quick-chip:active, .quick-chip.active {{
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}}
.calc-summary {{
  background: rgba(37, 99, 235, 0.1);
  border: 1px solid var(--primary);
  border-radius: var(--radius);
  padding: 10px 12px;
  margin: 8px 0;
}}
.calc-row {{
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 3px;
}}
.calc-total {{
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 700;
  color: var(--accent);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 6px;
  margin-top: 4px;
}}
</style>
</head>
<body>
<div class="crm-container">
  <div class="crm-header">
    <div class="crm-brand">
      <span>➕ Нове замовлення</span>
    </div>
    <span class="crm-badge">Калькулятор</span>
  </div>

  <div class="crm-card">
    <!-- 1. Customer Selection -->
    <div class="form-group">
      <div class="form-label">
        <span>👤 Вибір клієнта</span>
        <span style="color:var(--accent); cursor:pointer;" onclick="triggerNewCustomer()">+ Новий клієнт</span>
      </div>
      <select class="form-select" id="cust-select" onchange="onCustomerChange()">
        <option value="">-- Оберіть клієнта зі списку --</option>
      </select>
    </div>

    <!-- 2. Product (fixed) -->
    <div class="form-group">
      <div class="form-label">🧱 Товар</div>
      <input class="form-input" id="product-name" value="Торф'яний брикет" readonly style="opacity:0.8; cursor:not-allowed;">
    </div>

    <!-- 3. Quantity -->
    <div class="form-group">
      <div class="form-label">
        <span>⚖️ Кількість (тонн)</span>
        <span id="qty-label" style="color:var(--accent); font-weight:700;">10 т</span>
      </div>
      <div class="stepper-row">
        <button class="stepper-btn" onclick="adjustQty(-1)">-1</button>
        <button class="stepper-btn" onclick="adjustQty(-0.5)">-0.5</button>
        <input class="form-input" id="qty-input" type="number" step="0.1" min="0.1" value="10" oninput="recalc()" style="text-align:center; font-weight:700;">
        <button class="stepper-btn" onclick="adjustQty(0.5)">+0.5</button>
        <button class="stepper-btn" onclick="adjustQty(1)">+1</button>
      </div>
      <div class="quick-chips">
        <span class="quick-chip" onclick="setQty(3)">3 т</span>
        <span class="quick-chip" onclick="setQty(5)">5 т</span>
        <span class="quick-chip active" id="chip-10" onclick="setQty(10)">10 т</span>
        <span class="quick-chip" onclick="setQty(15)">15 т</span>
        <span class="quick-chip" onclick="setQty(22)">22 т (Фура)</span>
      </div>
    </div>

    <!-- 4. Unit Price -->
    <div class="form-group">
      <div class="form-label">💵 Ціна за тонну (грн)</div>
      <input class="form-input" id="price-input" type="number" step="10" min="0" value="200" oninput="recalc()">
      <div class="quick-chips">
        <span class="quick-chip" onclick="setPrice(180)">180 грн</span>
        <span class="quick-chip active" id="chip-p200" onclick="setPrice(200)">200 грн</span>
        <span class="quick-chip" onclick="setPrice(220)">220 грн</span>
        <span class="quick-chip" onclick="setPrice(250)">250 грн</span>
      </div>
    </div>

    <!-- 5. Delivery Price -->
    <div class="form-group">
      <div class="form-label">🚚 Вартість доставки (грн)</div>
      <input class="form-input" id="delivery-input" type="number" step="50" min="0" value="0" oninput="recalc()">
      <div class="quick-chips">
        <span class="quick-chip active" id="chip-d0" onclick="setDelivery(0)">0 грн (Самовивіз)</span>
        <span class="quick-chip" onclick="setDelivery(250)">250 грн</span>
        <span class="quick-chip" onclick="setDelivery(400)">400 грн</span>
        <span class="quick-chip" onclick="setDelivery(600)">600 грн</span>
      </div>
    </div>

    <!-- 6. Delivery Date -->
    <div class="form-group">
      <div class="form-label">🗓 Дата доставки</div>
      <input class="form-input" id="date-input" type="date">
      <div class="quick-chips" id="date-presets">
        <!-- Date presets filled by JS -->
      </div>
    </div>

    <!-- 7. Delivery Address -->
    <div class="form-group">
      <div class="form-label">🏠 Адреса вивантаження</div>
      <input class="form-input" id="address-input" placeholder="Вкажіть адресу доставки...">
    </div>

    <!-- 8. Notes -->
    <div class="form-group">
      <div class="form-label">📝 Примітки / Контакт на місці</div>
      <input class="form-input" id="notes-input" placeholder="Напр. дзвонити перед виїздом">
    </div>

    <!-- Calculation Summary -->
    <div class="calc-summary">
      <div class="calc-row">
        <span>Вартість товару:</span>
        <span id="sum-product">2000.00 грн</span>
      </div>
      <div class="calc-row">
        <span>Доставка:</span>
        <span id="sum-delivery">0.00 грн</span>
      </div>
      <div class="calc-total">
        <span>РАЗОМ ДО СПЛАТИ:</span>
        <span id="sum-total">2000.00 грн</span>
      </div>
    </div>

    <!-- Buttons -->
    <div style="display:flex; gap:8px;">
      <button class="crm-btn crm-btn-primary" style="flex:2;" onclick="submitOrder()">
        ✅ Створити замовлення
      </button>
      <button class="crm-btn crm-btn-ghost" style="flex:1;" onclick="cancelCreate()">
        Скасувати
      </button>
    </div>
  </div>
</div>

<script>
(function() {{
  var initialData = null;
  var customers = [];

  function getTW() {{
    return window.TelegramWidget || window.Telegram?.WebApp || null;
  }}

  function initDates() {{
    var today = new Date();
    var yyyy = today.getFullYear();
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var dd = String(today.getDate()).padStart(2, '0');
    var todayStr = yyyy + '-' + mm + '-' + dd;
    document.getElementById('date-input').value = todayStr;

    var presetsContainer = document.getElementById('date-presets');
    var html = '';
    for (var i = 0; i < 4; i++) {{
      var d = new Date();
      d.setDate(today.getDate() + i);
      var dStr = d.toISOString().split('T')[0];
      var label = (i === 0) ? 'Сьогодні' : (i === 1) ? 'Завтра' : (d.getDate() + '.' + String(d.getMonth() + 1).padStart(2, '0'));
      var activeClass = (i === 0) ? ' active' : '';
      html += '<span class="quick-chip' + activeClass + '" onclick="setDate(\\'' + dStr + '\\', this)">' + label + '</span>';
    }}
    presetsContainer.innerHTML = html;
  }}

  window.setDate = function(dStr, elem) {{
    document.getElementById('date-input').value = dStr;
    var chips = document.querySelectorAll('#date-presets .quick-chip');
    chips.forEach(function(c) {{ c.classList.remove('active'); }});
    if (elem) elem.classList.add('active');
  }};

  window.setQty = function(q) {{
    document.getElementById('qty-input').value = q;
    recalc();
  }};

  window.adjustQty = function(delta) {{
    var cur = parseFloat(document.getElementById('qty-input').value) || 0;
    var next = Math.max(0.5, cur + delta);
    document.getElementById('qty-input').value = next.toFixed(1);
    recalc();
  }};

  window.setPrice = function(p) {{
    document.getElementById('price-input').value = p;
    recalc();
  }};

  window.setDelivery = function(d) {{
    document.getElementById('delivery-input').value = d;
    recalc();
  }};

  window.recalc = function() {{
    var qty = parseFloat(document.getElementById('qty-input').value) || 0;
    var price = parseFloat(document.getElementById('price-input').value) || 0;
    var deliv = parseFloat(document.getElementById('delivery-input').value) || 0;

    var prodTotal = qty * price;
    var grandTotal = prodTotal + deliv;

    document.getElementById('qty-label').textContent = qty + ' т';
    document.getElementById('sum-product').textContent = prodTotal.toFixed(2) + ' грн';
    document.getElementById('sum-delivery').textContent = deliv.toFixed(2) + ' грн';
    document.getElementById('sum-total').textContent = grandTotal.toFixed(2) + ' грн';
  }};

  window.onCustomerChange = function() {{
    var select = document.getElementById('cust-select');
    var custId = select.value;
    if (!custId) return;

    for (var i = 0; i < customers.length; i++) {{
      if (String(customers[i].id) === String(custId)) {{
        var c = customers[i];
        if (c.address) {{
          document.getElementById('address-input').value = c.address;
        }}
        break;
      }}
    }}
  }};

  window.triggerNewCustomer = function() {{
    var tw = getTW();
    if (tw && typeof tw.request === 'function') {{
      tw.request(JSON.stringify({{ action: 'trigger_new_customer' }}));
    }}
  }};

  window.cancelCreate = function() {{
    var tw = getTW();
    if (tw && typeof tw.request === 'function') {{
      tw.request(JSON.stringify({{ action: 'cancel_order_create' }}));
    }}
  }};

  window.submitOrder = function() {{
    var custSelect = document.getElementById('cust-select');
    var custId = custSelect.value;
    if (!custId) {{
      alert('Будь ласка, оберіть клієнта');
      return;
    }}

    var qty = parseFloat(document.getElementById('qty-input').value) || 0;
    if (qty <= 0) {{
      alert('Вкажіть коректну кількість товару');
      return;
    }}

    var price = parseFloat(document.getElementById('price-input').value) || 0;
    var deliv = parseFloat(document.getElementById('delivery-input').value) || 0;
    var dateVal = document.getElementById('date-input').value;
    var address = document.getElementById('address-input').value.trim();
    var notes = document.getElementById('notes-input').value.trim();

    var payload = {{
      action: 'submit_new_order',
      customer_id: parseInt(custId),
      quantity: qty,
      unit_price: price,
      delivery_price: deliv,
      delivery_address: address,
      order_date: dateVal,
      notes: notes
    }};

    var tw = getTW();
    if (tw && typeof tw.request === 'function') {{
      tw.request(JSON.stringify(payload));
    }} else if (tw && typeof tw.sendData === 'function') {{
      tw.sendData(JSON.stringify(payload));
    }}
  }};

  function loadInitial() {{
    initDates();
    var tw = getTW();
    if (tw && tw.chatData) {{
      var parsed = null;
      try {{ parsed = (typeof tw.chatData === 'object') ? tw.chatData : JSON.parse(tw.chatData); }} catch(e) {{}}
      if (parsed) {{
        initialData = parsed;
        customers = parsed.customers || [];
        populateCustomers(parsed.selected_customer_id);
      }}
    }}
    recalc();
    if (tw && typeof tw.ready === 'function') {{
      tw.ready();
    }}
  }}

  function populateCustomers(selectedId) {{
    var select = document.getElementById('cust-select');
    select.innerHTML = '<option value="">-- Оберіть клієнта зі списку --</option>';
    customers.forEach(function(c) {{
      var opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name + ' (' + c.phone + ')';
      if (selectedId && String(c.id) === String(selectedId)) {{
        opt.selected = true;
      }}
      select.appendChild(opt);
    }});
    if (selectedId) {{
      onCustomerChange();
    }}
  }}

  var tw = getTW();
  if (tw && typeof tw.onEvent === 'function') {{
    tw.onEvent('chatDataChanged', loadInitial);
  }}
  window.addEventListener('message', function(e) {{
    if (e.data && e.data.type === 'chatDataChanged') {{
      loadInitial();
    }}
  }});

  document.addEventListener('DOMContentLoaded', loadInitial);
  setTimeout(loadInitial, 50);
}})();
</script>
</body>
</html>"""
    return html
