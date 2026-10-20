"use client";

import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Plus,
  AlertCircle,
  Loader2,
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
import { Order, UnavailableDate } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import { OrderDetailModal } from "@/components/orders/OrderDetailModal";
import { CreateOrderModal } from "@/components/orders/CreateOrderModal";
import { EditOrderModal } from "@/components/orders/EditOrderModal";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/common/ToastProvider";

const QUICK_REASONS = [
  "Вихідний водія",
  "Немає доставки",
  "Технічне обслуговування",
  "Свято",
  "Ремонт автопарку",
];

export default function CalendarPage() {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // Modal for marking an undesirable date
  const [isReasonModalOpen, setIsReasonModalOpen] = useState(false);
  const [reasonText, setReasonText] = useState("");

  // Fetch orders
  const { data: ordersData } = useQuery({
    queryKey: ["orders", "calendar"],
    queryFn: () => api.orders.list({ limit: 100 }),
  });

  // Fetch unavailable dates
  const { data: unavailableDates = [] } = useQuery({
    queryKey: ["unavailable-dates"],
    queryFn: () => api.calendar.listUnavailableDates(),
  });

  const orders = useMemo(() => ordersData?.orders || [], [ordersData?.orders]);

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

  // Map of unavailable dates by "yyyy-MM-dd"
  const unavailableMap = useMemo(() => {
    const map = new Map<string, UnavailableDate>();
    unavailableDates.forEach((item) => {
      map.set(item.date, item);
    });
    return map;
  }, [unavailableDates]);

  // Mutations for marking/unmarking undesirable dates
  const addUnavailableMutation = useMutation({
    mutationFn: (payload: { date: string; reason?: string | null }) =>
      api.calendar.addUnavailableDate(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["unavailable-dates"] });
      toast.success("День позначено як небажаний");
      setIsReasonModalOpen(false);
      setReasonText("");
    },
    onError: (err: any) => {
      toast.error("Помилка", err?.message || "Не вдалося позначити день");
    },
  });

  const removeUnavailableMutation = useMutation({
    mutationFn: (dateStr: string) => api.calendar.removeUnavailableDate(dateStr),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["unavailable-dates"] });
      toast.success("Позначку небажаного дня успішно знято");
    },
    onError: (err: any) => {
      toast.error("Помилка", err?.message || "Не вдалося зняти позначку");
    },
  });

  // Days in month grid
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart, { weekStartsOn: 1 });
  const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });
  const calendarDays = eachDayOfInterval({ start: startDate, end: endDate });

  const selectedDateKey = format(selectedDate, "yyyy-MM-dd");
  const selectedDayOrders = ordersByDate.get(selectedDateKey) || [];
  const selectedDayUnavailable = unavailableMap.get(selectedDateKey);

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
            Графік доставок та позначення небажаних днів для торфобрикету
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Legend */}
          <div className="hidden xl:flex items-center gap-3 px-3 py-1.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              Звичайний
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              🔴 Небажаний
            </span>
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
            <button
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Попередній місяць"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-xs font-bold text-slate-800 dark:text-slate-200 min-w-32 text-center uppercase tracking-wider">
              {format(currentMonth, "LLLL yyyy", { locale: uk })}
            </span>
            <button
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Наступний місяць"
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
              const unavailableInfo = unavailableMap.get(dayKey);
              const isUnavailable = !!unavailableInfo;
              const isSelected = isSameDay(day, selectedDate);
              const isCurMonth = isSameMonth(day, currentMonth);
              const isCurrentDay = isToday(day);

              let cellStyle =
                "min-h-[88px] p-2 rounded-xl border text-left flex flex-col justify-between transition-all relative ";

              if (isSelected) {
                if (isUnavailable) {
                  cellStyle +=
                    "border-rose-500 ring-2 ring-rose-500/25 bg-rose-50/90 dark:bg-rose-950/40";
                } else {
                  cellStyle +=
                    "border-emerald-600 ring-2 ring-emerald-500/20 bg-emerald-50/40 dark:bg-emerald-950/20";
                }
              } else if (isUnavailable) {
                cellStyle += isCurMonth
                  ? "border-rose-300 dark:border-rose-800 bg-rose-50/70 dark:bg-rose-950/30 hover:border-rose-400"
                  : "border-rose-200/60 dark:border-rose-950/40 bg-rose-50/30 dark:bg-rose-950/15 opacity-60";
              } else if (isCurMonth) {
                cellStyle +=
                  "border-slate-200/70 dark:border-slate-800 bg-white dark:bg-slate-800/40 hover:border-slate-300";
              } else {
                cellStyle +=
                  "border-slate-100 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/40 opacity-40";
              }

              const tooltipText = isUnavailable
                ? `🔴 Небажаний день для створення замовлень${
                    unavailableInfo?.reason ? `: ${unavailableInfo.reason}` : ""
                  }`
                : undefined;

              return (
                <button
                  type="button"
                  key={day.toISOString()}
                  onClick={() => setSelectedDate(day)}
                  title={tooltipText}
                  className={cellStyle}
                >
                  <div className="flex items-center justify-between w-full">
                    <span
                      className={`text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full ${
                        isCurrentDay
                          ? isUnavailable
                            ? "bg-rose-600 text-white"
                            : "bg-emerald-600 text-white"
                          : isSelected
                          ? isUnavailable
                            ? "text-rose-700 dark:text-rose-300 font-extrabold"
                            : "text-emerald-700 font-extrabold"
                          : isUnavailable
                          ? "text-rose-900 dark:text-rose-200 font-bold"
                          : "text-slate-800 dark:text-slate-200"
                      }`}
                    >
                      {format(day, "d")}
                    </span>

                    <div className="flex items-center gap-1">
                      {isUnavailable && (
                        <span
                          className="w-2 h-2 rounded-full bg-rose-500 ring-2 ring-rose-200 dark:ring-rose-900"
                          title={`Небажаний день${unavailableInfo?.reason ? `: ${unavailableInfo.reason}` : ""}`}
                        />
                      )}
                      {dayOrders.length > 0 && (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-slate-900 text-white">
                          {dayOrders.length}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Reason label if marked undesirable */}
                  {isUnavailable && (
                    <div className="w-full mt-1">
                      <div className="truncate text-[9px] font-bold text-rose-700 dark:text-rose-300 px-1 py-0.5 rounded bg-rose-100/80 dark:bg-rose-900/40 border border-rose-200/60 dark:border-rose-800/40">
                        🔴 {unavailableInfo?.reason || "Небажаний"}
                      </div>
                    </div>
                  )}

                  {/* Day Mini badges for orders */}
                  <div className="space-y-1 w-full mt-1">
                    {dayOrders.slice(0, isUnavailable ? 1 : 2).map((o) => (
                      <div
                        key={o.id}
                        className="truncate text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium"
                      >
                        #{o.id} • {o.quantity}т
                      </div>
                    ))}
                    {dayOrders.length > (isUnavailable ? 1 : 2) && (
                      <div className="text-[9px] text-slate-400 font-bold pl-1">
                        +{dayOrders.length - (isUnavailable ? 1 : 2)} ще
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Date Orders List & Undesirable Day Controls (1 col) */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            {/* Date Header */}
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

            {/* Undesirable day toggle banner */}
            {selectedDayUnavailable ? (
              <div className="p-3.5 rounded-xl bg-rose-50/90 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <span className="text-lg leading-none mt-0.5 select-none">🔴</span>
                  <div>
                    <div className="text-xs font-bold text-rose-900 dark:text-rose-200">
                      Небажаний день для доставки
                    </div>
                    {selectedDayUnavailable.reason ? (
                      <div className="text-[11px] text-rose-700 dark:text-rose-300 mt-0.5">
                        Причина: <span className="font-semibold">{selectedDayUnavailable.reason}</span>
                      </div>
                    ) : (
                      <div className="text-[11px] text-rose-600/80 dark:text-rose-400 mt-0.5">
                        Причину не вказано
                      </div>
                    )}
                    <div className="text-[10px] text-rose-500/90 mt-1 leading-tight">
                      Створення замовлень не заборонено, але виводиться попередження.
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeUnavailableMutation.mutate(selectedDateKey)}
                  disabled={removeUnavailableMutation.isPending}
                  className="shrink-0 text-xs font-bold text-slate-700 hover:text-rose-700 dark:text-slate-300 dark:hover:text-rose-300 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors shadow-2xs disabled:opacity-50"
                >
                  {removeUnavailableMutation.isPending ? "Зняття..." : "🟢 Зняти позначку"}
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-xs">
                <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>Звичайний робочий день</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setReasonText("");
                    setIsReasonModalOpen(true);
                  }}
                  className="px-2.5 py-1.5 text-xs font-bold rounded-lg border border-rose-200 dark:border-rose-900/60 bg-white dark:bg-slate-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors flex items-center gap-1.5 shadow-2xs"
                >
                  <span>🔴</span>
                  <span>Позначити як небажаний</span>
                </button>
              </div>
            )}

            {/* List of orders */}
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
              {selectedDayOrders.length === 0 ? (
                <div className="py-14 text-center text-xs text-slate-400 space-y-2">
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

      {/* Undesirable Date Reason Modal */}
      <Modal
        isOpen={isReasonModalOpen}
        onClose={() => setIsReasonModalOpen(false)}
        title="Позначити день як небажаний"
        description={`Дата: ${format(selectedDate, "d MMMM yyyy, EEEE", { locale: uk })}`}
        maxWidth="md"
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200/80 dark:border-amber-900/40 text-xs text-amber-800 dark:text-amber-300">
            <div className="font-semibold flex items-center gap-1.5 mb-1">
              <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
              Інформаційна позначка
            </div>
            Ця позначка слугує попередженням для менеджерів. Створення замовлень на цей день <strong>НЕ блокується</strong>.
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
              Швидкий вибір причини:
            </label>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_REASONS.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setReasonText(r)}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                    reasonText === r
                      ? "bg-rose-100 border-rose-300 text-rose-800 dark:bg-rose-900/60 dark:border-rose-700 dark:text-rose-200 font-bold"
                      : "bg-slate-100/70 border-slate-200 hover:bg-slate-200/70 dark:bg-slate-800 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
              Причина або коментар (опціонально):
            </label>
            <input
              type="text"
              value={reasonText}
              onChange={(e) => setReasonText(e.target.value)}
              placeholder="Наприклад: Вихідний водія, Ремонт автопарку..."
              maxLength={255}
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <button
              type="button"
              onClick={() => setIsReasonModalOpen(false)}
              className="px-3.5 py-2 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Скасувати
            </button>
            <button
              type="button"
              disabled={addUnavailableMutation.isPending}
              onClick={() =>
                addUnavailableMutation.mutate({
                  date: selectedDateKey,
                  reason: reasonText.trim() || null,
                })
              }
              className="px-4 py-2 text-xs font-bold rounded-xl bg-rose-600 hover:bg-rose-700 text-white transition-colors flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              {addUnavailableMutation.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <span>🔴</span>
              )}
              <span>Позначити як небажаний</span>
            </button>
          </div>
        </div>
      </Modal>

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
