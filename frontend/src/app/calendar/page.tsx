"use client";

import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Plus,
} from "lucide-react";
import {
  format,
  addMonths,
  subMonths,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
  parseISO,
} from "date-fns";
import { uk } from "date-fns/locale";
import { api } from "@/lib/api";
import { Order } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import { OrderDetailModal } from "@/components/orders/OrderDetailModal";
import { CreateOrderModal } from "@/components/orders/CreateOrderModal";
import { EditOrderModal } from "@/components/orders/EditOrderModal";

export default function CalendarPage() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // Fetch orders
  const { data } = useQuery({
    queryKey: ["orders", "calendar"],
    queryFn: () => api.orders.list({ limit: 100 }),
  });

  const orders = useMemo(() => data?.orders || [], [data?.orders]);

  // Group orders by order_date (fallback to created_at)
  const ordersByDate = useMemo(() => {
    const map = new Map<string, Order[]>();
    orders.forEach((o) => {
      try {
        const key = o.order_date
          ? o.order_date
          : format(parseISO(o.created_at), "yyyy-MM-dd");
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(o);
      } catch {}
    });
    return map;
  }, [orders]);

  // Days in month grid
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart, { weekStartsOn: 1 });
  const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });
  const calendarDays = eachDayOfInterval({ start: startDate, end: endDate });

  const selectedDateKey = format(selectedDate, "yyyy-MM-dd");
  const selectedDayOrders = ordersByDate.get(selectedDateKey) || [];

  return (
    <div className="space-y-6">
      {/* Header & Month Navigation */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <CalendarIcon className="w-6 h-6 text-emerald-600" />
            <span>Календар відвантажень</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Графік доставок та замовлень торфобрикету за днями місяця
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 p-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
            <button
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-xs font-bold text-slate-800 dark:text-slate-200 min-w-32 text-center uppercase tracking-wider">
              {format(currentMonth, "LLLL yyyy", { locale: uk })}
            </span>
            <button
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => {
              setCurrentMonth(new Date());
              setSelectedDate(new Date());
            }}
            className="px-3 py-2 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 text-slate-700 dark:text-slate-300"
          >
            Сьогодні
          </button>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Замовлення</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Calendar Month Matrix & Selected Day Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar Matrix (2 cols) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
          {/* Weekday headers */}
          <div className="grid grid-cols-7 gap-1 text-center font-bold text-xs text-slate-400 uppercase tracking-wider mb-2">
            {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"].map((d) => (
              <div key={d} className="py-1">
                {d}
              </div>
            ))}
          </div>

          {/* Days Grid */}
          <div className="grid grid-cols-7 gap-1.5">
            {calendarDays.map((day) => {
              const dayKey = format(day, "yyyy-MM-dd");
              const dayOrders = ordersByDate.get(dayKey) || [];
              const isSelected = isSameDay(day, selectedDate);
              const isCurMonth = isSameMonth(day, currentMonth);
              const isCurrentDay = isToday(day);

              return (
                <button
                  type="button"
                  key={day.toISOString()}
                  onClick={() => setSelectedDate(day)}
                  className={`min-h-[85px] p-2 rounded-xl border text-left flex flex-col justify-between transition-all ${
                    isSelected
                      ? "border-emerald-600 ring-2 ring-emerald-500/20 bg-emerald-50/40 dark:bg-emerald-950/20"
                      : isCurMonth
                      ? "border-slate-200/70 dark:border-slate-800 bg-white dark:bg-slate-800/40 hover:border-slate-300"
                      : "border-slate-100 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/40 opacity-40"
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span
                      className={`text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full ${
                        isCurrentDay
                          ? "bg-emerald-600 text-white"
                          : isSelected
                          ? "text-emerald-700 font-extrabold"
                          : "text-slate-800 dark:text-slate-200"
                      }`}
                    >
                      {format(day, "d")}
                    </span>

                    {dayOrders.length > 0 && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-900 text-white">
                        {dayOrders.length}
                      </span>
                    )}
                  </div>

                  {/* Day Mini badges */}
                  <div className="space-y-1 w-full mt-1">
                    {dayOrders.slice(0, 2).map((o) => (
                      <div
                        key={o.id}
                        className="truncate text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium"
                      >
                        #{o.id} • {o.quantity}т
                      </div>
                    ))}
                    {dayOrders.length > 2 && (
                      <div className="text-[9px] text-slate-400 font-bold pl-1">
                        +{dayOrders.length - 2} ще
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Date Orders List (1 col) */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white capitalize">
                  {format(selectedDate, "d MMMM yyyy, EEEE", { locale: uk })}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Замовлень на цю дату: <strong>{selectedDayOrders.length}</strong>
                </p>
              </div>

              {selectedDayOrders.length > 0 && (
                <div className="text-right">
                  <div className="text-[11px] text-slate-400">Разом:</div>
                  <div className="text-xs font-bold text-emerald-600">
                    {selectedDayOrders.reduce((sum, o) => sum + Number(o.quantity), 0)} тонн
                  </div>
                </div>
              )}
            </div>

            {/* List of orders */}
            <div className="mt-4 space-y-3 max-h-[460px] overflow-y-auto pr-1">
              {selectedDayOrders.length === 0 ? (
                <div className="py-16 text-center text-xs text-slate-400 space-y-2">
                  <Clock className="w-6 h-6 mx-auto text-slate-300" />
                  <p>На цю дату немає замовлень</p>
                  <button
                    onClick={() => setIsCreateOpen(true)}
                    className="text-emerald-600 font-semibold hover:underline"
                  >
                    Створити замовлення
                  </button>
                </div>
              ) : (
                selectedDayOrders.map((ord) => (
                  <div
                    key={ord.id}
                    onClick={() => setSelectedOrder(ord)}
                    className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:border-emerald-500/40 transition-all cursor-pointer space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-xs text-slate-900 dark:text-white">
                        Замовлення #{ord.id}
                      </span>
                      <StatusBadge status={ord.status} showDot={false} className="text-[10px]" />
                    </div>

                    <div className="text-xs">
                      <div className="font-semibold text-slate-800 dark:text-slate-200">
                        {ord.customer?.name || "Клієнт"}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate mt-0.5">
                        📍 {ord.delivery_address}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 dark:border-slate-700/60 text-xs">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {ord.quantity} т торфобрикету
                      </span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400">
                        {formatCurrency(ord.total_amount)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
          >
            <Plus className="w-4 h-4 text-emerald-400" />
            <span>Запланувати нове відвантаження</span>
          </button>
        </div>
      </div>

      {/* Modals */}
      <OrderDetailModal
        order={selectedOrder}
        isOpen={!!selectedOrder}
        onClose={() => setSelectedOrder(null)}
        onEdit={(ord) => {
          setSelectedOrder(null);
          setEditingOrder(ord);
        }}
      />

      <CreateOrderModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        initialOrderDate={selectedDate}
      />

      <EditOrderModal
        order={editingOrder}
        isOpen={!!editingOrder}
        onClose={() => setEditingOrder(null)}
      />
    </div>
  );
}
