"use client";

import React, { useState, Suspense } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import {
  Package,
  Search,
  ArrowUpDown,
  Plus,
  Eye,
  Edit,
  Truck,
  CheckCircle2,
  Calendar,
  XCircle,
  X,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { api } from "@/lib/api";
import { Order, OrderStatus } from "@/types";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CreateOrderModal } from "@/components/orders/CreateOrderModal";
import { OrderDetailModal } from "@/components/orders/OrderDetailModal";
import { EditOrderModal } from "@/components/orders/EditOrderModal";
import { CancelOrderDialog } from "@/components/orders/CancelOrderDialog";
import { useToast } from "@/components/common/ToastProvider";

const STATUS_TABS: { id: OrderStatus | "all"; label: string }[] = [
  { id: "all", label: "Всі замовлення" },
  { id: "new", label: "Нові" },
  { id: "planned", label: "Заплановані" },
  { id: "in_delivery", label: "У дорозі" },
  { id: "delivered", label: "Доставлені" },
  { id: "cancelled", label: "Скасовані" },
];

function OrdersContent() {
  const searchParams = useSearchParams();
  const initialStatus = (searchParams.get("status") as OrderStatus) || "all";

  const queryClient = useQueryClient();
  const toast = useToast();

  // Filters & Pagination State
  const [activeStatus, setActiveStatus] = useState<OrderStatus | "all">(initialStatus);
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortBy, setSortBy] = useState<string>("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(15);

  // Modal States
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [cancellingOrder, setCancellingOrder] = useState<Order | null>(null);

  // Query orders
  const { data, isLoading } = useQuery({
    queryKey: [
      "orders",
      {
        activeStatus,
        searchQuery,
        dateFrom,
        dateTo,
        sortBy,
        sortDir,
        page,
        pageSize,
      },
    ],
    queryFn: () =>
      api.orders.list({
        status: activeStatus === "all" ? undefined : activeStatus,
        q: searchQuery.trim() || undefined,
        dateFrom: dateFrom ? `${dateFrom}T00:00:00` : undefined,
        dateTo: dateTo ? `${dateTo}T23:59:59` : undefined,
        sortBy,
        sortDir,
        skip: page * pageSize,
        limit: pageSize,
      }),
  });

  const orders = data?.orders || [];
  const totalCount = data?.totalCount || 0;
  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  // Quick Action Mutations
  const startDeliveryMutation = useMutation({
    mutationFn: (id: number) => api.orders.startDelivery(id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Доставку #${updated.id} розпочато!`);
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка";
      toast.error("Не вдалося почати доставку", msg);
    },
  });

  const completeDeliveryMutation = useMutation({
    mutationFn: (id: number) => api.orders.completeDelivery(id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Замовлення #${updated.id} доставлено!`);
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка";
      toast.error("Не вдалося завершити доставку", msg);
    },
  });

  const planMutation = useMutation({
    mutationFn: (id: number) => api.orders.plan(id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Замовлення #${updated.id} заплановано!`);
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка";
      toast.error("Не вдалося запланувати", msg);
    },
  });

  const resetFilters = () => {
    setActiveStatus("all");
    setSearchQuery("");
    setDateFrom("");
    setDateTo("");
    setSortBy("created_at");
    setSortDir("desc");
    setPage(0);
  };

  return (
    <div className="space-y-6">
      {/* Header and Create Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Package className="w-6 h-6 text-emerald-600" />
            <span>Реєстр замовлень</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Управління замовленнями торфобрикету, логістика доставок та зміна статусів
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-950/20 active:scale-98 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Створити замовлення</span>
        </button>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-200 dark:border-slate-800">
        {STATUS_TABS.map((tab) => {
          const isActive = activeStatus === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveStatus(tab.id);
                setPage(0);
              }}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                isActive
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Search & Advanced Filters Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search Input */}
          <div className="lg:col-span-2 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Пошук за № замовлення, клієнтом, телефоном..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(0);
              }}
              className="w-full pl-9 pr-8 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Date From */}
          <div>
            <div className="relative">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  setPage(0);
                }}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Date To */}
          <div>
            <div className="relative">
              <input
                type="date"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  setPage(0);
                }}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Sort & Reset */}
          <div className="flex items-center gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-2.5 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:ring-1 focus:ring-emerald-500"
            >
              <option value="created_at">За датою</option>
              <option value="total_amount">За сумою</option>
              <option value="quantity">За обсягом</option>
            </select>

            <button
              onClick={() => setSortDir(sortDir === "asc" ? "desc" : "asc")}
              title={`Напрямок: ${sortDir === "asc" ? "Зростання" : "Спадання"}`}
              className="p-2 border border-slate-300 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600"
            >
              <ArrowUpDown className="w-4 h-4" />
            </button>

            {(searchQuery || dateFrom || dateTo || activeStatus !== "all") && (
              <button
                onClick={resetFilters}
                title="Скинути всі фільтри"
                className="p-2 border border-slate-300 dark:border-slate-700 rounded-xl hover:bg-slate-50 text-slate-500 hover:text-rose-600"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-xs overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400 text-xs">
            <div className="w-8 h-8 border-3 border-emerald-500/20 border-t-emerald-600 rounded-full animate-spin mb-2" />
            <span>Завантаження замовлень...</span>
          </div>
        ) : orders.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
              <Package className="w-6 h-6" />
            </div>
            <div className="font-bold text-sm text-slate-800 dark:text-slate-200">
              Замовлень за вказаними фільтрами не знайдено
            </div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Спробуйте змінити фільтри або створіть нове замовлення на торфобрикет.
            </p>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 text-white font-bold text-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Створити замовлення</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 text-slate-500 font-bold uppercase tracking-wider">
                <tr>
                  <th className="p-3.5 pl-5">№</th>
                  <th className="p-3.5">Клієнт</th>
                  <th className="p-3.5">Обсяг (т)</th>
                  <th className="p-3.5">Товар</th>
                  <th className="p-3.5">Доставка / Відстань</th>
                  <th className="p-3.5">Загальна сума</th>
                  <th className="p-3.5">Статус</th>
                  <th className="p-3.5">Адреса вивантаження</th>
                  <th className="p-3.5">Дата замовлення</th>
                  <th className="p-3.5 pr-5 text-right">Дії</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {orders.map((ord) => (
                  <tr
                    key={ord.id}
                    className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors group"
                  >
                    <td className="p-3.5 pl-5 font-black text-slate-900 dark:text-white">
                      #{ord.id}
                    </td>

                    <td className="p-3.5">
                      <div className="font-bold text-slate-800 dark:text-slate-200">
                        {ord.customer?.name || "—"}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {ord.customer?.phone || "—"}
                      </div>
                    </td>

                    <td className="p-3.5 font-bold text-slate-900 dark:text-white">
                      {ord.quantity} т
                    </td>

                    <td className="p-3.5 text-slate-700 dark:text-slate-300 font-medium">
                      <div className="font-bold text-slate-900 dark:text-white">
                        {formatCurrency(ord.product_total ?? ord.quantity * ord.unit_price)}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {formatCurrency(ord.unit_price)}/т
                      </div>
                    </td>

                    <td className="p-3.5 text-slate-600 dark:text-slate-400">
                      <div>
                        {ord.delivery_price === 0 ? "Самовивіз" : formatCurrency(ord.delivery_price)}
                      </div>
                      {(ord.distance_km || ord.delivery_price_per_km) && (
                        <div className="text-[10px] text-slate-400">
                          {ord.distance_km ? `${ord.distance_km} км` : ""}
                          {ord.delivery_price_per_km ? ` (${ord.delivery_price_per_km} грн/км)` : ""}
                        </div>
                      )}
                    </td>

                    <td className="p-3.5 font-extrabold text-emerald-600 dark:text-emerald-400 text-sm">
                      {formatCurrency(ord.total_amount)}
                    </td>

                    <td className="p-3.5">
                      <StatusBadge status={ord.status} />
                    </td>

                    <td className="p-3.5 max-w-xs truncate text-slate-600 dark:text-slate-400" title={ord.delivery_address}>
                      {ord.delivery_address}
                    </td>

                    <td className="p-3.5 text-slate-600 dark:text-slate-300 whitespace-nowrap">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {ord.order_date || ord.created_at.split("T")[0]}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        ств: {formatDateTime(ord.created_at)}
                      </div>
                    </td>

                    <td className="p-3.5 pr-5 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1">
                        {/* Status transition quick shortcuts */}
                        {ord.status === "new" && (
                          <button
                            type="button"
                            onClick={() => planMutation.mutate(ord.id)}
                            title="Запланувати замовлення"
                            className="p-1.5 rounded-lg text-purple-600 hover:bg-purple-50"
                          >
                            <Calendar className="w-4 h-4" />
                          </button>
                        )}

                        {(ord.status === "new" || ord.status === "planned") && (
                          <button
                            type="button"
                            onClick={() => startDeliveryMutation.mutate(ord.id)}
                            title="Виїхати на доставку"
                            className="p-1.5 rounded-lg text-amber-600 hover:bg-amber-50"
                          >
                            <Truck className="w-4 h-4" />
                          </button>
                        )}

                        {ord.status === "in_delivery" && (
                          <button
                            type="button"
                            onClick={() => completeDeliveryMutation.mutate(ord.id)}
                            title="Завершити доставку"
                            className="p-1.5 rounded-lg text-emerald-600 hover:bg-emerald-50"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </button>
                        )}

                        {/* View Details */}
                        <button
                          type="button"
                          onClick={() => setSelectedOrder(ord)}
                          title="Переглянути деталі"
                          className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {/* Edit */}
                        {ord.status !== "delivered" && ord.status !== "cancelled" && (
                          <button
                            type="button"
                            onClick={() => setEditingOrder(ord)}
                            title="Редагувати"
                            className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}

                        {/* Cancel */}
                        {ord.status !== "cancelled" && ord.status !== "delivered" && (
                          <button
                            type="button"
                            onClick={() => setCancellingOrder(ord)}
                            title="Скасувати замовлення"
                            className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500">
          <div>
            Показано{" "}
            <strong>{orders.length > 0 ? page * pageSize + 1 : 0}</strong>–
            <strong>{Math.min((page + 1) * pageSize, totalCount)}</strong> із{" "}
            <strong>{totalCount}</strong> замовлень
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span>Рядків:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(0);
                }}
                className="px-2 py-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              >
                <option value={10}>10</option>
                <option value={15}>15</option>
                <option value={30}>30</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="flex items-center gap-1">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="p-1.5 rounded-lg border border-slate-300 dark:border-slate-700 disabled:opacity-30 hover:bg-slate-100"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-bold text-slate-700 dark:text-slate-300">
                {page + 1} / {totalPages}
              </span>
              <button
                disabled={page + 1 >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded-lg border border-slate-300 dark:border-slate-700 disabled:opacity-30 hover:bg-slate-100"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
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

export default function OrdersPage() {
  return (
    <Suspense fallback={<div className="text-xs text-slate-500">Завантаження замовлень...</div>}>
      <OrdersContent />
    </Suspense>
  );
}
