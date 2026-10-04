"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  TrendingUp,
  Package,
  DollarSign,
  Award,
  Truck,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { api } from "@/lib/api";
import { OrderStatus } from "@/types";
import { formatCurrency, STATUS_CONFIG } from "@/lib/utils";

const PERIODS = [
  { id: "today", label: "Сьогодні" },
  { id: "week", label: "7 днів" },
  { id: "month", label: "30 днів" },
  { id: "year", label: "Рік" },
  { id: "all", label: "Весь час" },
];

const STATUS_COLORS: Record<OrderStatus, string> = {
  new: "#3b82f6",
  planned: "#8b5cf6",
  in_delivery: "#f59e0b",
  delivered: "#10b981",
  cancelled: "#f43f5e",
};

export default function AnalyticsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState("month");

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard", "analytics", selectedPeriod],
    queryFn: () => api.analytics.getDashboard(selectedPeriod),
  });

  const kpi = dashboard?.kpi;
  const salesChart = dashboard?.sales_chart || [];
  const statusDistribution = dashboard?.status_distribution || [];
  const recentCustomers = dashboard?.recent_customers || [];

  const averageCheck =
    kpi && kpi.period_orders_count > 0
      ? Math.round(kpi.period_revenue / kpi.period_orders_count)
      : 0;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <BarChart3 className="w-6 h-6 text-emerald-600" />
            <span>Аналітика та фінансові звіти</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Показники реалізації торфобрикету, динаміка збуту та ключові клієнти
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

      {/* Key Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-bold uppercase tracking-wider">Загальний дохід</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-3 text-2xl font-black text-emerald-600 dark:text-emerald-400 truncate">
            {isLoading ? "—" : formatCurrency(kpi?.period_revenue || 0)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Без урахування скасованих заявок</div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-bold uppercase tracking-wider">Обсяг торфобрикету</span>
            <Package className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-3 text-2xl font-black text-slate-900 dark:text-white">
            {isLoading ? "—" : kpi?.period_quantity_tons || 0} тонн
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Реалізовано за вибраний період</div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-bold uppercase tracking-wider">Середній чек</span>
            <TrendingUp className="w-4 h-4 text-purple-600" />
          </div>
          <div className="mt-3 text-2xl font-black text-slate-900 dark:text-white truncate">
            {isLoading ? "—" : formatCurrency(averageCheck)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">На одне оформлене замовлення</div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-bold uppercase tracking-wider">Кількість замовлень</span>
            <Truck className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-3 text-2xl font-black text-slate-900 dark:text-white">
            {isLoading ? "—" : kpi?.period_orders_count || 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Успішних та активних угод</div>
        </div>
      </div>

      {/* Main Bar Chart: Volume & Revenue */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            <span>Щоденна динаміка реалізації (обсяг у тоннах та виручка)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Співвідношення проданого обсягу торфу до грошових надходжень
          </p>
        </div>

        <div className="h-[320px] w-full">
          {salesChart.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              Немає даних за обраний період
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={salesChart}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(val) => {
                    try {
                      const p = val.split("-");
                      return `${p[2]}.${p[1]}`;
                    } catch {
                      return val;
                    }
                  }}
                  stroke="#94a3b8"
                  fontSize={11}
                />
                <YAxis
                  yAxisId="left"
                  orientation="left"
                  stroke="#10b981"
                  fontSize={11}
                  tickFormatter={(val) => `${val >= 1000 ? `${Math.round(val / 1000)}k` : val}`}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="#3b82f6"
                  fontSize={11}
                  tickFormatter={(val) => `${val}т`}
                />
                <Tooltip
                  formatter={(value: any, name: any) => {
                    if (name === "revenue") return [formatCurrency(Number(value)), "Виручка"];
                    if (name === "tons") return [`${value} т`, "Обсяг"];
                    return [value, name];
                  }}
                  labelFormatter={(l) => `Дата: ${l}`}
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderRadius: "12px",
                    color: "#fff",
                    fontSize: "12px",
                    border: "none",
                  }}
                />
                <Legend
                  formatter={(val) => (val === "revenue" ? "Виручка (грн)" : "Обсяг (т)")}
                />
                <Bar
                  yAxisId="left"
                  dataKey="revenue"
                  fill="#10b981"
                  radius={[6, 6, 0, 0]}
                  name="revenue"
                />
                <Bar
                  yAxisId="right"
                  dataKey="tons"
                  fill="#3b82f6"
                  radius={[6, 6, 0, 0]}
                  name="tons"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Breakdown Row: Status Breakdown & Top Spenders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution Breakdown */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Package className="w-4 h-4 text-emerald-600" />
            <span>Структура замовлень за статусами</span>
          </h3>

          <div className="space-y-3">
            {statusDistribution.map((item) => {
              const conf = STATUS_CONFIG[item.status] || STATUS_CONFIG.new;
              const totalOrders = kpi?.period_orders_count || 1;
              const percent = Math.round((item.count / Math.max(1, totalOrders)) * 100);

              return (
                <div key={item.status} className="space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      {conf.label} ({item.count} зам.)
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white">
                      {formatCurrency(item.total_sum)}
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, Math.max(percent, item.count > 0 ? 5 : 0))}%`,
                        backgroundColor: STATUS_COLORS[item.status] || "#94a3b8",
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Active Clients */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Award className="w-4 h-4 text-emerald-600" />
              <span>Ключові клієнти</span>
            </h3>
            <span className="text-xs text-slate-400">За обсягом покупок</span>
          </div>

          <div className="space-y-2.5">
            {recentCustomers.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                Клієнтів ще не зафіксовано
              </div>
            ) : (
              recentCustomers.map((c, idx) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 text-xs"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 font-extrabold flex items-center justify-center text-[10px] shrink-0">
                      {idx + 1}
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-slate-900 dark:text-white truncate">
                        {c.name}
                      </div>
                      <div className="text-[11px] text-slate-400 truncate">{c.phone}</div>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="font-extrabold text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(c.total_spent || 0)}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {c.orders_count || 0} замовлень
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
