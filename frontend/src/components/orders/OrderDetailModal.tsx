"use client";

import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Package,
  User,
  Phone,
  MapPin,
  Calendar,
  Clock,
  Navigation,
  CheckCircle2,
  Truck,
  XCircle,
  Trash2,
  ExternalLink,
  Edit,
} from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Order } from "@/types";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { api } from "@/lib/api";
import { useToast } from "@/components/common/ToastProvider";

interface OrderDetailModalProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (order: Order) => void;
  onCancelPrompt?: (order: Order) => void;
}

export function OrderDetailModal({
  order,
  isOpen,
  onClose,
  onEdit,
  onCancelPrompt,
}: OrderDetailModalProps) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [isDeleting, setIsDeleting] = useState(false);

  // Status transitions mutations
  const planMutation = useMutation({
    mutationFn: () => api.orders.plan(order!.id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Замовлення #${updated.id} заплановано!`);
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка планування";
      toast.error("Не вдалося запланувати замовлення", msg);
    },
  });

  const startDeliveryMutation = useMutation({
    mutationFn: () => api.orders.startDelivery(order!.id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Доставку #${updated.id} розпочато!`, "Статус змінено на 'У дорозі'");
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка початку доставки";
      toast.error("Не вдалося розпочати доставку", msg);
    },
  });

  const completeDeliveryMutation = useMutation({
    mutationFn: () => api.orders.completeDelivery(order!.id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Замовлення #${updated.id} успішно доставлено!`, "Вивантаження зафіксовано в базі");
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка завершення доставки";
      toast.error("Не вдалося завершити доставку", msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.orders.delete(order!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Замовлення #${order!.id} видалено`);
      setIsDeleting(false);
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка видалення";
      toast.error("Не вдалося видалити замовлення", msg);
      setIsDeleting(false);
    },
  });

  if (!order) return null;

  const googleMapsUrl =
    order.delivery_latitude && order.delivery_longitude
      ? `https://www.google.com/maps/search/?api=1&query=${order.delivery_latitude},${order.delivery_longitude}`
      : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
          order.delivery_address
        )}`;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Замовлення #${order.id}`}
      description={
        order.order_date
          ? `Дата замовлення: ${order.order_date} • Оформлено: ${formatDateTime(order.created_at)}`
          : `Оформлено: ${formatDateTime(order.created_at)}`
      }
      maxWidth="2xl"
    >
      <div className="space-y-6">
        {/* Top Status & Summary Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Поточний статус:</div>
            <div className="mt-1">
              <StatusBadge status={order.status} className="text-sm px-3 py-1" />
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs text-slate-500 dark:text-slate-400">Загальна вартість:</div>
            <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 leading-tight">
              {formatCurrency(order.total_amount)}
            </div>
          </div>
        </div>

        {/* Customer Information Card */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <User className="w-4 h-4 text-emerald-600" />
              <span>Інформація про клієнта</span>
            </h4>

            {order.customer?.phone && (
              <a
                href={`tel:${order.customer.phone}`}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-xs font-semibold hover:bg-emerald-100 transition-colors"
              >
                <Phone className="w-3 h-3" />
                <span>Зателефонувати</span>
              </a>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-xs text-slate-500">ПІБ / Назва:</span>
              <p className="font-semibold text-slate-900 dark:text-white">
                {order.customer?.name || "—"}
              </p>
            </div>

            <div>
              <span className="text-xs text-slate-500">Контактний телефон:</span>
              <p className="font-semibold text-slate-900 dark:text-white">
                {order.customer?.phone || "—"}
              </p>
            </div>

            <div className="sm:col-span-2">
              <span className="text-xs text-slate-500">Адреса клієнта:</span>
              <p className="text-slate-700 dark:text-slate-300">
                {order.customer?.address || "—"}
              </p>
            </div>
          </div>
        </div>

        {/* Financial & Volume Breakdown Card */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
          <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Package className="w-4 h-4 text-emerald-600" />
            <span>Параметри замовлення та фінанси</span>
          </h4>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
              <span className="text-[11px] text-slate-500">Кількість:</span>
              <p className="font-bold text-slate-900 dark:text-white">
                {order.quantity} т
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
              <span className="text-[11px] text-slate-500">Ціна товару:</span>
              <p className="font-bold text-slate-900 dark:text-white">
                {formatCurrency(order.unit_price)}
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
              <span className="text-[11px] text-slate-500">Кілометраж:</span>
              <p className="font-bold text-slate-900 dark:text-white">
                {order.distance_km ? `${order.distance_km} км` : "—"}
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
              <span className="text-[11px] text-slate-500">Доставка:</span>
              <p className="font-bold text-slate-900 dark:text-white">
                {formatCurrency(order.delivery_price)}
              </p>
            </div>
          </div>

          <div className="flex justify-between items-center p-3 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900 text-xs">
            <span className="text-slate-600 dark:text-slate-400">
              Вартість товару ({order.quantity} т):
            </span>
            <span className="font-bold text-slate-900 dark:text-white">
              {formatCurrency(order.product_total ?? order.total_amount - order.delivery_price)}
            </span>
          </div>
        </div>

        {/* Delivery Destination & Navigation Card */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
          <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-emerald-600" />
            <span>Адреса вивантаження та навігація</span>
          </h4>

          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-white">
              {order.delivery_address}
            </p>
            {order.distance_km && (
              <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-0.5 font-medium">
                Відстань від складу: {order.distance_km} км
              </p>
            )}
            {order.delivery_latitude && order.delivery_longitude && (
              <p className="text-xs text-slate-500 mt-0.5">
                Координати: {order.delivery_latitude}, {order.delivery_longitude}
              </p>
            )}
          </div>

          {/* Quick Route Buttons */}
          <div className="flex flex-wrap gap-2 pt-1">
            {order.waze_url && (
              <a
                href={order.waze_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800 text-xs font-semibold hover:bg-sky-100 transition-colors"
              >
                <Navigation className="w-3.5 h-3.5" />
                <span>Маршрут у Waze</span>
                <ExternalLink className="w-3 h-3 ml-0.5 opacity-60" />
              </a>
            )}

            <a
              href={googleMapsUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 text-xs font-semibold hover:bg-slate-200 transition-colors"
            >
              <MapPin className="w-3.5 h-3.5 text-rose-500" />
              <span>Google Maps</span>
              <ExternalLink className="w-3 h-3 ml-0.5 opacity-60" />
            </a>
          </div>
        </div>

        {/* Timestamps and Notes */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-400" />
            <span>
              Виїзд:{" "}
              <strong className="text-slate-700 dark:text-slate-300">
                {order.delivery_started_at ? formatDateTime(order.delivery_started_at) : "Ще не виїхав"}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-slate-400" />
            <span>
              Доставлено:{" "}
              <strong className="text-slate-700 dark:text-slate-300">
                {order.delivery_completed_at ? formatDateTime(order.delivery_completed_at) : "В процесі"}
              </strong>
            </span>
          </div>

          {order.notes && (
            <div className="sm:col-span-2 p-2.5 rounded-lg bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/50 dark:border-amber-900/40 text-amber-900 dark:text-amber-200">
              <span className="font-semibold block text-[11px] mb-0.5">Примітки:</span>
              <p className="whitespace-pre-line">{order.notes}</p>
            </div>
          )}
        </div>

        {/* Dynamic Action Buttons based on current Order Status */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            {order.status !== "delivered" && order.status !== "cancelled" && onEdit && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onEdit(order);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 transition-colors"
              >
                <Edit className="w-3.5 h-3.5" />
                <span>Редагувати</span>
              </button>
            )}

            {order.status !== "cancelled" && order.status !== "delivered" && onCancelPrompt && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onCancelPrompt(order);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-rose-600 bg-rose-50 dark:bg-rose-950/30 hover:bg-rose-100 transition-colors"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Скасувати</span>
              </button>
            )}

            {/* Delete button (with confirm check) */}
            {isDeleting ? (
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate()}
                  disabled={deleteMutation.isPending}
                  className="px-2.5 py-1 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg"
                >
                  Підтвердити видалення
                </button>
                <button
                  type="button"
                  onClick={() => setIsDeleting(false)}
                  className="px-2 py-1 text-xs text-slate-500 hover:text-slate-800"
                >
                  Ні
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsDeleting(true)}
                title="Видалити запис замовлення"
                className="p-2 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Forward status transitions */}
          <div className="flex items-center gap-2">
            {order.status === "new" && (
              <button
                type="button"
                onClick={() => planMutation.mutate()}
                disabled={planMutation.isPending}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 transition-colors"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>Запланувати</span>
              </button>
            )}

            {(order.status === "new" || order.status === "planned") && (
              <button
                type="button"
                onClick={() => startDeliveryMutation.mutate()}
                disabled={startDeliveryMutation.isPending}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 shadow-xs transition-colors"
              >
                <Truck className="w-3.5 h-3.5" />
                <span>Виїхати на доставку</span>
              </button>
            )}

            {order.status === "in_delivery" && (
              <button
                type="button"
                onClick={() => completeDeliveryMutation.mutate()}
                disabled={completeDeliveryMutation.isPending}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md transition-colors"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Завершити доставку</span>
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
            >
              Закрити
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
