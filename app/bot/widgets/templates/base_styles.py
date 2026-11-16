COMMON_CRM_CSS = """
:root {
  --bg-main: var(--tg-theme-bg-color, #0b1329);
  --bg-card: var(--tg-theme-secondary-bg-color, #152238);
  --bg-card-hover: #1e2f4d;
  --bg-input: #101c30;
  --border-color: rgba(255, 255, 255, 0.08);
  --border-active: #38bdf8;
  --text-main: var(--tg-theme-text-color, #f1f5f9);
  --text-muted: var(--tg-theme-hint-color, #94a3b8);
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --primary-light: rgba(37, 99, 235, 0.2);
  --accent: #38bdf8;
  --success: #10b981;
  --success-bg: rgba(16, 185, 129, 0.15);
  --warning: #f59e0b;
  --warning-bg: rgba(245, 158, 11, 0.15);
  --danger: #ef4444;
  --danger-bg: rgba(239, 68, 68, 0.15);
  --purple: #8b5cf6;
  --purple-bg: rgba(139, 92, 246, 0.15);
  --radius: 10px;
  --radius-sm: 6px;
  --radius-pill: 9999px;
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

body {
  font-family: var(--font-family);
  background: var(--bg-main);
  color: var(--text-main);
  font-size: 13px;
  line-height: 1.45;
  padding: 10px;
  overflow-x: hidden;
}

.crm-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 520px;
  margin: 0 auto;
}

/* Header */
.crm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  padding: 8px 12px;
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
}

.crm-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 14px;
  color: var(--text-main);
}

.crm-badge {
  font-size: 10px;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background: var(--primary-light);
  color: var(--accent);
  font-weight: 600;
  letter-spacing: 0.5px;
}

.crm-refresh-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  transition: color 0.2s;
}
.crm-refresh-btn:active {
  color: var(--accent);
  transform: rotate(90deg);
}

/* Nav Tabs */
.crm-tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-card);
  padding: 4px;
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
  overflow-x: auto;
  scrollbar-width: none;
}
.crm-tabs::-webkit-scrollbar {
  display: none;
}

.crm-tab-btn {
  flex: 1;
  min-width: 65px;
  padding: 6px 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  white-space: nowrap;
  text-align: center;
  transition: all 0.2s ease;
}

.crm-tab-btn.active {
  background: var(--primary);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
}

/* Filter Chips / Subnav */
.crm-filters {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}
.crm-filters::-webkit-scrollbar {
  display: none;
}

.crm-filter-chip {
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 500;
  background: var(--bg-card);
  color: var(--text-muted);
  border: 1px solid var(--border-color);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.crm-filter-chip.active {
  background: var(--accent);
  color: #0b1329;
  border-color: var(--accent);
  font-weight: 700;
}

/* Cards */
.crm-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: background 0.15s;
}

.crm-card.clickable:active {
  background: var(--bg-card-hover);
  border-color: var(--accent);
}

.crm-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.crm-card-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 6px;
}

.crm-card-meta {
  font-size: 11px;
  color: var(--text-muted);
}

/* Grid & KPI */
.crm-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.crm-kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.crm-kpi-label {
  font-size: 11px;
  color: var(--text-muted);
}

.crm-kpi-val {
  font-size: 16px;
  font-weight: 700;
  color: var(--accent);
}

/* Status Badges */
.status-pill {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--radius-pill);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.status-new { background: var(--primary-light); color: var(--accent); }
.status-planned { background: var(--purple-bg); color: var(--purple); }
.status-in_delivery { background: var(--warning-bg); color: var(--warning); }
.status-delivered { background: var(--success-bg); color: var(--success); }
.status-cancelled { background: var(--danger-bg); color: var(--danger); }

/* Progress bar */
.crm-progress-bar {
  display: flex;
  height: 8px;
  border-radius: var(--radius-pill);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
  margin: 6px 0;
}
.crm-progress-segment {
  height: 100%;
  transition: width 0.3s;
}

/* Buttons */
.crm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.crm-btn-primary { background: var(--primary); color: #fff; }
.crm-btn-primary:active { background: var(--primary-hover); transform: scale(0.98); }
.crm-btn-success { background: var(--success); color: #fff; }
.crm-btn-success:active { transform: scale(0.98); }
.crm-btn-danger { background: var(--danger); color: #fff; }
.crm-btn-ghost { background: transparent; border: 1px solid var(--border-color); color: var(--text-main); }
.crm-btn-ghost:active { background: var(--bg-card-hover); }

.crm-btn-sm {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: var(--radius-sm);
}

/* Search bar */
.crm-search-box {
  display: flex;
  gap: 6px;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  align-items: center;
}
.crm-search-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-main);
  font-size: 12px;
  width: 100%;
}
.crm-search-input::placeholder {
  color: var(--text-muted);
}

/* Empty state & loader */
.crm-empty {
  text-align: center;
  padding: 24px 12px;
  color: var(--text-muted);
  font-size: 12px;
}
.crm-loader {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  color: var(--accent);
  font-size: 12px;
}
"""
