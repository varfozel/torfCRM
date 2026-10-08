"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Package,
  Truck,
  Users,
  DollarSign,
  TrendingUp,
  PlusCircle,
  ArrowRight,
  MapPin,
  Eye,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { api } from "@/lib/api";
import { Order, OrderStatus } from "@/types";
import { formatCurrency, formatDateTime, STATUS_CONFIG } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CreateOrderModal } from "@/components/orders/CreateOrderModal";
import { OrderDetailModal } from "@/components/orders/OrderDetailModal";
import { EditOrderModal } from "@/components/orders/EditOrderModal";
import { CancelOrderDialog } from "@/components/orders/CancelOrderDialog";

// Dynamically import Leaflet Map to avoid SSR issues
const DeliveryMap = dynamic(
  () => import("@/components/map/DeliveryMap").then((mod) => mod.DeliveryMap),
  {
    ssr: false,
    loading: () => (
      <div className="h-[360px] w-full rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 text-xs">
        Завантаження карти доставок...
      </div>
    ),
  }
);

const PERIODS = [
  { id: "today", label: "Сьогодні" },
  { id: "week", label: "7 днів" },
  { id: "month", label: "30 днів" },
  { id: "year", label: "Рік" },
  { id: "all", label: "Весь час" },
];

const PIE_COLORS: Record<OrderStatus, string> = {
  new: "#3b82f6", // blue
  planned: "#8b5cf6", // purple
  in_delivery: "#f59e0b", // amber
  delivered: "#10b981", // emerald
  cancelled: "#f43f5e", // rose
};

export default function DashboardPage() {
  const [selectedPeriod, setSelectedPeriod] = useState("month");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [cancellingOrder, setCancellingOrder] = useState<Order | null>(null);

  // Fetch real analytics from backend
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard", selectedPeriod],
    queryFn: () => api.analytics.getDashboard(selectedPeriod),
  });

  const kpi = dashboard?.kpi;
  const recentOrders = dashboard?.recent_orders || [];
  const recentCustomers = dashboard?.recent_customers || [];
  const mapDeliveries = dashboard?.map_deliveries || [];
  const salesChart = dashboard?.sales_chart || [];
  const statusDistribution = dashboard?.status_distribution || [];

  // Filter distribution data for pie chart
  const pieData = statusDistribution
    .filter((s) => s.count > 0)
    .map((s) => ({
      name: STATUS_CONFIG[s.status]?.label || s.status,
      value: s.count,
      status: s.status,
      total_sum: s.total_sum,
    }));

  return (
    <div className="space-y-6">
      {/* Top Banner & Period Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
            Огляд діяльності
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Актуальні дані обліку та відвантажень торфобрикету
          </p>
        </div>

        {/* Period Selector Tabs */}
        <div className="flex items-center p-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs text-xs font-semibold">
          {PERIODS.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelectedPeriod(p.id)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedPeriod === p.id
                  ? "bg-emerald-600 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: New Orders */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Нові замовлення
            </span>
            <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center">
              <Package className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-black text-slate-900 dark:text-white">
              {isLoading ? "—" : kpi?.new_orders_count || 0}
            </span>
            <span className="text-xs text-slate-500 ml-1.5">очікують планування</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-blue-600 font-semibold">
            <Link href="/orders?status=new" className="hover:underline flex items-center gap-1">
              <span>Переглянути чергу</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* KPI 2: Today's Deliveries */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Доставки на сьогодні
            </span>
            <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 flex items-center justify-center">
              <Truck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-black text-slate-900 dark:text-white">
              {isLoading ? "—" : kpi?.today_deliveries_count || 0}
            </span>
            <span className="text-xs text-slate-500 ml-1.5">рейсів у роботі</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-amber-600 font-semibold">
            <Link href="/map" className="hover:underline flex items-center gap-1">
              <span>Карта маршрутів</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* KPI 3: Total Customers */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Всього клієнтів
            </span>
            <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-black text-slate-900 dark:text-white">
              {isLoading ? "—" : kpi?.total_customers || 0}
            </span>
            <span className="text-xs text-slate-500 ml-1.5">замовників у базі</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-purple-600 font-semibold">
            <Link href="/customers" className="hover:underline flex items-center gap-1">
              <span>База клієнтів</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* KPI 4: Period Revenue */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Виручка ({PERIODS.find((p) => p.id === selectedPeriod)?.label})
            </span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 flex items-center justify-center">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl sm:text-3xl font-black text-emerald-600 dark:text-emerald-400 truncate">
              {isLoading ? "—" : formatCurrency(kpi?.period_revenue || 0)}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              Відвантажено: <strong>{kpi?.period_quantity_tons || 0} т</strong> брикету
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-emerald-600 font-semibold">
            <Link href="/analytics" className="hover:underline flex items-center gap-1">
              <span>Детальна аналітика</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Charts Section: Sales over time & Status Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sales Chart (2 cols) */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                <span>Динаміка виручки та відвантажень</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Сума замовлень (грн) та обсяг торфу (т) за обраний період
              </p>
            </div>
          </div>

          <div className="h-[280px] w-full">
            {salesChart.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Немає даних за цей період
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={salesChart}
                  margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(val) => {
                      try {
                        const parts = val.split("-");
                        return `${parts[2]}.${parts[1]}`;
                      } catch {
                        return val;
                      }
                    }}
                    stroke="#94a3b8"
                    fontSize={11}
                  />
                  <YAxis
                    stroke="#94a3b8"
                    fontSize={11}
                    tickFormatter={(val) => `${val >= 1000 ? `${Math.round(val / 1000)}k` : val}`}
                  />
                  <Tooltip
                    formatter={(value: any, name: any) => {
                      if (name === "revenue") return [formatCurrency(Number(value)), "Виручка"];
                      if (name === "tons") return [`${value} т`, "Обсяг"];
                      return [value, name];
                    }}
                    labelFormatter={(label) => `Дата: ${label}`}
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderRadius: "12px",
                      color: "#fff",
                      fontSize: "12px",
                      border: "none",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    stroke="#059669"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#colorRevenue)"
                    name="revenue"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Order Status Distribution (1 col) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Package className="w-4 h-4 text-emerald-600" />
              <span>Розподіл статусів замовлень</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Кількість замовлень у системі</p>
          </div>

          <div className="h-[210px] w-full my-auto">
            {pieData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Замовлень ще немає
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry) => (
                      <Cell
                        key={`cell-${entry.status}`}
                        fill={PIE_COLORS[entry.status as OrderStatus] || "#94a3b8"}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: any, name: any) => [`${value} зам.`, name]}
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderRadius: "12px",
                      color: "#fff",
                      fontSize: "12px",
                      border: "none",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Status legend tags */}
          <div className="grid grid-cols-2 gap-1.5 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px]">
            {statusDistribution.map((st) => (
              <div key={st.status} className="flex items-center gap-1.5 truncate">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: PIE_COLORS[st.status] || "#94a3b8" }}
                />
                <span className="text-slate-600 dark:text-slate-400 truncate">
                  {STATUS_CONFIG[st.status]?.label}:
                </span>
                <span className="font-bold text-slate-900 dark:text-white">{st.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Delivery Map Preview Banner */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <MapPin className="w-4 h-4 text-emerald-600" />
              <span>Карта доставок торфобрикету</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Відображаються {mapDeliveries.length} замовлень з доступними координатами
            </p>
          </div>

          <Link
            href="/map"
            className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 hover:text-emerald-700"
          >
            <span>Розгорнути повну карту</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <DeliveryMap
          orders={mapDeliveries}
          warehouse={dashboard?.warehouse}
          onSelectOrder={(id) => {
            const ord = recentOrders.find((o) => o.id === id);
            if (ord) setSelectedOrder(ord);
          }}
          className="h-[340px]"
        />
      </div>

      {/* Bottom Grid: Recent Orders Table & Recent Customers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Orders Table (2 cols) */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Package className="w-4 h-4 text-emerald-600" />
                <span>Останні замовлення</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Останні зареєстровані заявки</p>
            </div>

            <Link
              href="/orders"
              className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 hover:text-emerald-700"
            >
              <span>Всі замовлення</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {recentOrders.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400">
              Немає замовлень. Створіть перше замовлення!
            </div>
          ) : (
            <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 text-slate-500 font-semibold uppercase">
                  <tr>
                    <th className="p-3">№</th>
                    <th className="p-3">Клієнт</th>
                    <th className="p-3">Обсяг</th>
                    <th className="p-3">Доставка</th>
                    <th className="p-3">Сума</th>
                    <th className="p-3">Статус</th>
                    <th className="p-3">Дата</th>
                    <th className="p-3 text-right">Дії</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {recentOrders.map((ord) => (
                    <tr
                      key={ord.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="p-3 font-bold text-slate-900 dark:text-white">
                        #{ord.id}
                      </td>
                      <td className="p-3">
                        <div className="font-semibold text-slate-800 dark:text-slate-200">
                          {ord.customer?.name || (ord as any).customer_name || "—"}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {ord.customer?.phone || (ord as any).customer_phone || "—"}
                        </div>
                      </td>
                      <td className="p-3 font-semibold text-slate-900 dark:text-white">
                        {ord.quantity} т
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">
                        {ord.delivery_price === 0 ? "Самовивіз" : formatCurrency(ord.delivery_price)}
                      </td>
                      <td className="p-3 font-bold text-emerald-600 dark:text-emerald-400">
                        <div className="flex items-center gap-1.5">
                          <span>{formatCurrency(ord.total_amount)}</span>
                          {ord.is_total_manual && (
                            <span
                              title="Встановлено вручну"
                              className="px-1.5 py-0.2 text-[9px] font-bold rounded bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300/80 dark:border-amber-700"
                            >
                              Вручну
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-3">
                        <StatusBadge status={ord.status} />
                      </td>
                      <td className="p-3 text-slate-500">
                        {formatDateTime(ord.created_at)}
                      </td>
                      <td className="p-3 text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedOrder(ord)}
                          className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                          title="Переглянути деталі"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Customers Card (1 col) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-600" />
                <span>Останні клієнти</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Нові контрагенти в системі</p>
            </div>

            <Link
              href="/customers"
              className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 hover:text-emerald-700"
            >
              <span>Всі</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2.5">
            {recentCustomers.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">Клієнтів ще немає</div>
            ) : (
              recentCustomers.map((cust) => (
                <div
                  key={cust.id}
                  className="p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-between"
                >
                  <div className="min-w-0">
                    <div className="font-bold text-xs text-slate-900 dark:text-white truncate">
                      {cust.name}
                    </div>
                    <div className="text-[11px] text-slate-500 truncate mt-0.5">
                      {cust.phone} • {cust.address}
                    </div>
                  </div>

                  <div className="text-right shrink-0 ml-3">
                    <div className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(cust.total_spent || 0)}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {cust.orders_count || 0} замовл.
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <button
            type="button"
            onClick={() => setIsCreateOpen(true)}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-colors"
          >
            <PlusCircle className="w-4 h-4 text-emerald-400" />
            <span>Швидке створення замовлення</span>
          </button>
        </div>
      </div>

      {/* Modals */}
      <CreateOrderModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />

      <OrderDetailModal
        order={selectedOrder}
        isOpen={!!selectedOrder}
        onClose={() => setSelectedOrder(null)}
        onEdit={(ord) => setEditingOrder(ord)}
        onCancelPrompt={(ord) => setCancellingOrder(ord)}
      />

      <EditOrderModal
        order={editingOrder}
        isOpen={!!editingOrder}
        onClose={() => setEditingOrder(null)}
      />

      <CancelOrderDialog
        order={cancellingOrder}
        isOpen={!!cancellingOrder}
        onClose={() => setCancellingOrder(null)}
      />
    </div>
  );
}
