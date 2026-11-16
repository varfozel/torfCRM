import json
from typing import Any, Dict
from app.bot.widgets.templates.base_styles import COMMON_CRM_CSS


def build_dashboard_html() -> str:
    """
    Generates the self-contained HTML + CSS + JS interactive dashboard widget.
    Executed in Telegram's sandboxed QuickJS/Web environment.
    Interacts via TelegramWidget.request() and updates dynamically on chatData changes.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
{COMMON_CRM_CSS}
</style>
</head>
<body>
<div class="crm-container">
  <div class="crm-header">
    <div class="crm-brand">
      <span>🪵 Peat CRM</span>
      <span class="crm-badge">PRO CRM</span>
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
      <span id="user-badge" class="crm-badge" style="background:rgba(56,189,248,0.15); color:var(--accent);">Співробітник</span>
      <button class="crm-refresh-btn" onclick="sendAction('refresh')" title="Оновити">🔄</button>
    </div>
  </div>

  <div class="crm-tabs">
    <button class="crm-tab-btn active" id="tab-btn-orders" onclick="switchTab('orders')">📋 Замовлення</button>
    <button class="crm-tab-btn" id="tab-btn-customers" onclick="switchTab('customers')">👥 Клієнти</button>
    <button class="crm-tab-btn" id="tab-btn-deliveries" onclick="switchTab('deliveries')">🚚 Доставки</button>
    <button class="crm-tab-btn" id="tab-btn-calendar" onclick="switchTab('calendar')">📅 Календар</button>
    <button class="crm-tab-btn" id="tab-btn-stats" onclick="switchTab('stats')">📊 Аналітика</button>
  </div>

  <div id="subnav-container"></div>
  <div id="view-content"><div class="crm-loader">Завантаження даних...</div></div>
</div>

<script>
(function() {{
  var state = {{
    activeTab: 'orders',
    orderFilter: 'all',
    searchQuery: '',
    period: 'month',
    data: null
  }};

  function getTW() {{
    return window.TelegramWidget || window.Telegram?.WebApp || null;
  }}

  window.sendAction = function(action, extra) {{
    var payload = Object.assign({{
      action: action,
      tab: state.activeTab,
      filter: state.orderFilter,
      period: state.period,
      query: state.searchQuery
    }}, extra || {{}});

    var tw = getTW();
    if (tw && typeof tw.request === 'function') {{
      tw.request(JSON.stringify(payload));
    }} else if (tw && typeof tw.sendData === 'function') {{
      tw.sendData(JSON.stringify(payload));
    }} else {{
      console.log('Action dispatched:', payload);
    }}
  }};

  window.switchTab = function(tabName) {{
    state.activeTab = tabName;
    updateTabButtons();
    sendAction('switch_tab', {{ tab: tabName }});
    renderView();
  }};

  window.setOrderFilter = function(filterName) {{
    state.orderFilter = filterName;
    sendAction('filter_orders', {{ filter: filterName }});
    renderView();
  }};

  window.setPeriod = function(period) {{
    state.period = period;
    sendAction('change_period', {{ period: period }});
    renderView();
  }};

  window.openOrder = function(orderId) {{
    sendAction('open_order', {{ order_id: orderId }});
  }};

  window.openCustomer = function(customerId) {{
    sendAction('open_customer', {{ customer_id: customerId }});
  }};

  window.quickStatusChange = function(orderId, newStatus) {{
    sendAction('change_order_status', {{ order_id: orderId, status: newStatus }});
  }};

  window.openWaze = function(url) {{
    var tw = getTW();
    if (tw && typeof tw.openLink === 'function') {{
      tw.openLink(url);
    }} else {{
      window.open(url, '_blank');
    }}
  }};

  function updateTabButtons() {{
    var tabs = ['orders', 'customers', 'deliveries', 'calendar', 'stats'];
    tabs.forEach(function(t) {{
      var btn = document.getElementById('tab-btn-' + t);
      if (btn) {{
        if (t === state.activeTab) btn.classList.add('active');
        else btn.classList.remove('active');
      }}
    }});
  }}

  function parseChatData(raw) {{
    if (!raw) return null;
    if (typeof raw === 'object') return raw;
    try {{ return JSON.parse(raw); }} catch(e) {{ return null; }}
  }}

  function loadInitialData() {{
    var tw = getTW();
    var chatData = null;
    if (tw && tw.chatData) {{
      chatData = parseChatData(tw.chatData);
    }}
    if (chatData) {{
      state.data = chatData;
      if (chatData.activeTab) state.activeTab = chatData.activeTab;
      if (chatData.orderFilter) state.orderFilter = chatData.orderFilter;
      if (chatData.period) state.period = chatData.period;
      updateTabButtons();
      renderView();
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
        state.data = parsed;
        if (parsed.activeTab) state.activeTab = parsed.activeTab;
        if (parsed.orderFilter) state.orderFilter = parsed.orderFilter;
        if (parsed.period) state.period = parsed.period;
        updateTabButtons();
        renderView();
      }}
    }}
  }}

  var tw = getTW();
  if (tw) {{
    if (typeof tw.onEvent === 'function') {{
      tw.onEvent('chatDataChanged', onDataChanged);
    }}
  }}
  window.addEventListener('message', function(e) {{
    if (e.data && e.data.type === 'chatDataChanged') {{
      onDataChanged();
    }}
  }});

  // Rendering
  function renderView() {{
    var content = document.getElementById('view-content');
    var subnav = document.getElementById('subnav-container');
    if (!state.data) {{
      content.innerHTML = '<div class="crm-loader">Завантаження даних...</div>';
      return;
    }}

    if (state.activeTab === 'orders') {{
      renderOrdersView(subnav, content);
    }} else if (state.activeTab === 'customers') {{
      renderCustomersView(subnav, content);
    }} else if (state.activeTab === 'deliveries') {{
      renderDeliveriesView(subnav, content);
    }} else if (state.activeTab === 'calendar') {{
      renderCalendarView(subnav, content);
    }} else if (state.activeTab === 'stats') {{
      renderStatsView(subnav, content);
    }}
  }}

  function renderOrdersView(subnav, content) {{
    var f = state.orderFilter;
    subnav.innerHTML = '' +
      '<div class="crm-filters">' +
        '<button class="crm-filter-chip ' + (f === 'all' ? 'active' : '') + '" onclick="setOrderFilter(\\'all\\')">Усі</button>' +
        '<button class="crm-filter-chip ' + (f === 'new' ? 'active' : '') + '" onclick="setOrderFilter(\\'new\\')">🆕 Нові</button>' +
        '<button class="crm-filter-chip ' + (f === 'in_work' ? 'active' : '') + '" onclick="setOrderFilter(\\'in_work\\')">🚚 В роботі</button>' +
        '<button class="crm-filter-chip ' + (f === 'delivered' ? 'active' : '') + '" onclick="setOrderFilter(\\'delivered\\')">✅ Завершені</button>' +
        '<button class="crm-filter-chip ' + (f === 'cancelled' ? 'active' : '') + '" onclick="setOrderFilter(\\'cancelled\\')">❌ Скасовані</button>' +
      '</div>';

    var orders = (state.data && state.data.orders) ? state.data.orders : [];
    if (!orders.length) {{
      content.innerHTML = '<div class="crm-card"><div class="crm-empty">Замовлень не знайдено</div></div>';
      return;
    }}

    var html = '<div style="display:flex; flex-direction:column; gap:8px;">';
    orders.forEach(function(o) {{
      var stPill = getStatusPill(o.status);
      html += '' +
        '<div class="crm-card clickable" onclick="openOrder(' + o.id + ')">' +
          '<div class="crm-card-header">' +
            '<div class="crm-card-title">📦 Замовлення #' + o.id + '</div>' +
            stPill +
          '</div>' +
          '<div style="font-weight:600; color:var(--text-main); font-size:12px;">' + (o.customer_name || '—') + ' <span class="crm-card-meta">(' + (o.customer_phone || '') + ')</span></div>' +
          '<div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted);">' +
            '<span>🧱 ' + o.quantity + ' т | Доставка: ' + o.delivery_price + ' грн</span>' +
            '<span style="font-weight:700; color:var(--accent); font-size:12px;">' + o.total_amount + ' грн</span>' +
          '</div>' +
          '<div class="crm-card-meta" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">📍 ' + (o.delivery_address || 'Адреса клієнта') + '</div>' +
        '</div>';
    }});
    html += '</div>';
    content.innerHTML = html;
  }}

  function renderCustomersView(subnav, content) {{
    subnav.innerHTML = '' +
      '<div style="display:flex; gap:6px;">' +
        '<div class="crm-search-box" style="flex:1;">' +
          '<span>🔍</span>' +
          '<input class="crm-search-input" id="cust-search" placeholder="Пошук за ім\'ям чи телефоном..." onkeyup="handleCustomerSearch(event)" value="' + (state.searchQuery || '') + '">' +
        '</div>' +
        '<button class="crm-btn crm-btn-primary crm-btn-sm" onclick="sendAction(\\'trigger_new_customer\\')">➕ Клієнт</button>' +
      '</div>';

    var customers = (state.data && state.data.customers) ? state.data.customers : [];
    if (!customers.length) {{
      content.innerHTML = '<div class="crm-card"><div class="crm-empty">Клієнтів не знайдено</div></div>';
      return;
    }}

    var html = '<div style="display:flex; flex-direction:column; gap:8px;">';
    customers.forEach(function(c) {{
      html += '' +
        '<div class="crm-card clickable" onclick="openCustomer(' + c.id + ')">' +
          '<div class="crm-card-header">' +
            '<div class="crm-card-title">👤 ' + c.name + '</div>' +
            '<span class="crm-badge">' + (c.orders_count || 0) + ' замовлень</span>' +
          '</div>' +
          '<div class="crm-card-meta">📞 ' + c.phone + '</div>' +
          '<div class="crm-card-meta">🏠 ' + (c.address || '—') + '</div>' +
          (c.total_spent ? '<div style="font-size:11px; color:var(--success); font-weight:600;">Всього замовлень на: ' + c.total_spent + ' грн</div>' : '') +
        '</div>';
    }});
    html += '</div>';
    content.innerHTML = html;
  }}

  window.handleCustomerSearch = function(e) {{
    if (e.key === 'Enter' || e.keyCode === 13) {{
      var q = e.target.value.trim();
      state.searchQuery = q;
      sendAction('search_customers', {{ query: q }});
    }}
  }};

  function renderDeliveriesView(subnav, content) {{
    subnav.innerHTML = '' +
      '<div class="crm-card" style="padding:6px 10px; background:rgba(37,99,235,0.1); border-color:var(--primary);">' +
        '<div style="display:flex; justify-content:space-between; align-items:center;">' +
          '<span style="font-weight:600; font-size:12px; color:var(--accent);">🚛 Доставки на сьогодні: ' + ((state.data && state.data.today_deliveries_count) || 0) + '</span>' +
          '<button class="crm-btn crm-btn-ghost crm-btn-sm" onclick="sendAction(\\'deliveries_all\\')">Всі активні</button>' +
        '</div>' +
      '</div>';

    var deliveries = (state.data && state.data.deliveries) ? state.data.deliveries : [];
    if (!deliveries.length) {{
      content.innerHTML = '<div class="crm-card"><div class="crm-empty">На сьогодні немає запланованих доставок</div></div>';
      return;
    }}

    var html = '<div style="display:flex; flex-direction:column; gap:8px;">';
    deliveries.forEach(function(d) {{
      var stPill = getStatusPill(d.status);
      var wazeBtn = d.waze_url ? '<button class="crm-btn crm-btn-ghost crm-btn-sm" onclick="openWaze(\\'' + d.waze_url + '\\')">🧭 Waze</button>' : '';
      var actionBtn = '';
      if (d.status === 'new' || d.status === 'planned') {{
        actionBtn = '<button class="crm-btn crm-btn-primary crm-btn-sm" onclick="quickStatusChange(' + d.id + ', \\'in_delivery\\')">🚚 Виїзд</button>';
      }} else if (d.status === 'in_delivery') {{
        actionBtn = '<button class="crm-btn crm-btn-success crm-btn-sm" onclick="quickStatusChange(' + d.id + ', \\'delivered\\')">✅ Доставлено</button>';
      }}

      html += '' +
        '<div class="crm-card">' +
          '<div class="crm-card-header">' +
            '<div class="crm-card-title">📦 #' + d.id + ' — ' + (d.customer_name || '') + '</div>' +
            stPill +
          '</div>' +
          '<div style="font-size:11px; color:var(--text-muted);">' +
            '<div>📞 ' + (d.customer_phone || '') + '</div>' +
            '<div>🏠 ' + (d.delivery_address || '') + '</div>' +
            '<div>⚖️ ' + d.quantity + ' т | Сума: <b>' + d.total_amount + ' грн</b></div>' +
          '</div>' +
          '<div style="display:flex; justify-content:flex-end; gap:6px; margin-top:4px;">' +
            wazeBtn + actionBtn +
            '<button class="crm-btn crm-btn-ghost crm-btn-sm" onclick="openOrder(' + d.id + ')">Деталі</button>' +
          '</div>' +
        '</div>';
    }});
    html += '</div>';
    content.innerHTML = html;
  }}

  function renderCalendarView(subnav, content) {{
    var calendarDays = (state.data && state.data.calendar_days) ? state.data.calendar_days : [];
    subnav.innerHTML = '<div style="font-size:11px; color:var(--text-muted); padding:2px 4px;">📅 Розклад доставок та завантаженість по днях</div>';

    if (!calendarDays.length) {{
      content.innerHTML = '<div class="crm-card"><div class="crm-empty">Немає запланованих дат</div></div>';
      return;
    }}

    var html = '<div style="display:flex; flex-direction:column; gap:8px;">';
    calendarDays.forEach(function(day) {{
      var isBlocked = day.is_blocked;
      var badgeHtml = '';
      if (isBlocked) {{
        badgeHtml = '<span class="crm-badge" style="background:var(--danger-bg); color:var(--danger);">⛔️ Недоступний для доставки</span>';
      }} else if (day.orders_count >= 3) {{
        badgeHtml = '<span class="crm-badge" style="background:var(--warning-bg); color:var(--warning);">🔥 Високе завантаження (' + day.orders_count + ')</span>';
      }} else if (day.orders_count > 0) {{
        badgeHtml = '<span class="crm-badge" style="background:var(--primary-light); color:var(--accent);">' + day.orders_count + ' рейсів | ' + day.tons + ' т</span>';
      }} else {{
        badgeHtml = '<span class="crm-badge" style="background:var(--success-bg); color:var(--success);">Вільний день</span>';
      }}

      var bgHighlight = day.is_today ? 'border:1px solid var(--accent); background:rgba(56,189,248,0.06);' : '';
      if (isBlocked) {{
        bgHighlight = 'border:1px dashed var(--danger); opacity:0.85;';
      }}

      var dayOrdersHtml = '';
      if (day.orders && day.orders.length) {{
        dayOrdersHtml += '<div style="margin-top:6px; display:flex; flex-direction:column; gap:4px;">';
        day.orders.forEach(function(o) {{
          dayOrdersHtml += '<div class="crm-card clickable" style="padding:4px 8px; font-size:11px;" onclick="openOrder(' + o.id + ')">' +
            '<div style="display:flex; justify-content:space-between;">' +
              '<span>📦 #' + o.id + ' ' + (o.customer_name || '') + '</span>' +
              '<span style="font-weight:700; color:var(--accent);">' + o.quantity + ' т</span>' +
            '</div>' +
          '</div>';
        }});
        dayOrdersHtml += '</div>';
      }}

      var blockBtnText = isBlocked ? '🟢 Зробити доступним' : '⛔️ Позначити небажаним';
      html += '' +
        '<div class="crm-card" style="' + bgHighlight + '">' +
          '<div class="crm-card-header">' +
            '<span style="font-weight:700; font-size:13px;">' + day.date_label + (day.is_today ? ' (Сьогодні)' : '') + '</span>' +
            badgeHtml +
          '</div>' +
          '<div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:var(--text-muted); margin-top:2px;">' +
            '<span>' + (day.deliveries_text || '') + '</span>' +
            '<button class="crm-btn crm-btn-ghost crm-btn-sm" style="font-size:10px; padding:2px 6px;" onclick="toggleDayBlocked(\\'' + day.date + '\\')">' + blockBtnText + '</button>' +
          '</div>' +
          dayOrdersHtml +
        '</div>';
    }});
    html += '</div>';
    content.innerHTML = html;
  }}

  window.toggleDayBlocked = function(dateStr) {{
    sendAction('calendar_toggle_blocked', {{ date: dateStr }});
  }};

  function renderStatsView(subnav, content) {{
    var p = state.period;
    subnav.innerHTML = '' +
      '<div class="crm-filters">' +
        '<button class="crm-filter-chip ' + (p === 'today' ? 'active' : '') + '" onclick="setPeriod(\\'today\\')">Сьогодні</button>' +
        '<button class="crm-filter-chip ' + (p === 'week' ? 'active' : '') + '" onclick="setPeriod(\\'week\\')">Тиждень</button>' +
        '<button class="crm-filter-chip ' + (p === 'month' ? 'active' : '') + '" onclick="setPeriod(\\'month\\')">Місяць</button>' +
        '<button class="crm-filter-chip ' + (p === 'year' ? 'active' : '') + '" onclick="setPeriod(\\'year\\')">Рік</button>' +
        '<button class="crm-filter-chip ' + (p === 'all' ? 'active' : '') + '" onclick="setPeriod(\\'all\\')">Весь час</button>' +
      '</div>';

    var stats = (state.data && state.data.stats) ? state.data.stats : {{}};
    var breakdown = stats.status_breakdown || [];
    var totalOrders = stats.orders_count || 0;

    var progressSegments = '';
    var breakdownList = '';
    breakdown.forEach(function(item) {{
      var pct = totalOrders > 0 ? Math.round((item.count / totalOrders) * 100) : 0;
      var color = '#94a3b8';
      var label = item.status;
      if (item.status === 'new') {{ color = '#38bdf8'; label = '🆕 Нові'; }}
      else if (item.status === 'planned') {{ color = '#8b5cf6'; label = '🗓 Заплановано'; }}
      else if (item.status === 'in_delivery') {{ color = '#f59e0b'; label = '🚚 В дорозі'; }}
      else if (item.status === 'delivered') {{ color = '#10b981'; label = '✅ Доставлено'; }}
      else if (item.status === 'cancelled') {{ color = '#ef4444'; label = '❌ Скасовано'; }}

      if (pct > 0) {{
        progressSegments += '<div class="crm-progress-segment" style="width:' + pct + '%; background:' + color + ';" title="' + label + ': ' + item.count + '"></div>';
      }}
      breakdownList += '' +
        '<div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; padding:2px 0;">' +
          '<span style="display:flex; align-items:center; gap:6px;">' +
            '<span style="width:8px; height:8px; border-radius:50%; background:' + color + ';"></span>' +
            '<span>' + label + '</span>' +
          '</span>' +
          '<span style="font-weight:600;">' + item.count + ' <span style="color:var(--text-muted); font-size:10px;">(' + pct + '%)</span></span>' +
        '</div>';
    }});

    var progressBarHtml = progressSegments ? '<div class="crm-progress-bar">' + progressSegments + '</div>' : '';

    var html = '' +
      '<div class="crm-grid-2">' +
        '<div class="crm-kpi-card">' +
          '<div class="crm-kpi-label">💰 Загальна вартість</div>' +
          '<div class="crm-kpi-val">' + (stats.revenue || 0) + ' <span style="font-size:11px;">грн</span></div>' +
        '</div>' +
        '<div class="crm-kpi-card">' +
          '<div class="crm-kpi-label">🧱 Обсяг товару</div>' +
          '<div class="crm-kpi-val" style="color:var(--success);">' + (stats.quantity || 0) + ' <span style="font-size:11px;">т</span></div>' +
        '</div>' +
        '<div class="crm-kpi-card">' +
          '<div class="crm-kpi-label">📋 Всього замовлень</div>' +
          '<div class="crm-kpi-val">' + totalOrders + '</div>' +
        '</div>' +
        '<div class="crm-kpi-card">' +
          '<div class="crm-kpi-label">🚚 В роботі зараз</div>' +
          '<div class="crm-kpi-val" style="color:var(--warning);">' + (stats.in_work_count || 0) + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="crm-card" style="margin-top:6px;">' +
        '<div class="crm-card-header">' +
          '<span class="crm-card-title">📊 Розподіл замовлень за статусами</span>' +
        '</div>' +
        progressBarHtml +
        '<div style="margin-top:4px;">' + breakdownList + '</div>' +
      '</div>' +
      '<div class="crm-card" style="margin-top:4px;">' +
        '<div class="crm-card-title">👥 Всього клієнтів у базі: ' + (stats.total_customers || 0) + '</div>' +
        '<div class="crm-card-meta">Базовий склад: ' + (stats.warehouse_address || 'Волинська обл.') + '</div>' +
      '</div>';

    content.innerHTML = html;
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

  // Initialize
  document.addEventListener('DOMContentLoaded', loadInitialData);
  setTimeout(loadInitialData, 50);
}})();
</script>
</body>
</html>"""
    return html
