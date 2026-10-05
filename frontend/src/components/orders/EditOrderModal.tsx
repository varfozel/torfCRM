"use client";

import React, { useState, useMemo, useEffect, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  DollarSign,
  Truck,
  Calendar as CalendarIcon,
  Navigation,
  Loader2,
  AlertCircle,
  Clock,
  Calculator,
  FileText,
} from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Order, OrderStatus, OrderUpdatePayload, RouteCalculationResult } from "@/types";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useToast } from "@/components/common/ToastProvider";
import { TONNAGE_OPTIONS, calculateOrderTotals } from "@/lib/pricing";

interface EditOrderModalProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
}

function EditOrderForm({ order, onClose }: { order: Order; onClose: () => void }) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [deliveryAddress, setDeliveryAddress] = useState(order.delivery_address || "");
  const [deliveryLat, setDeliveryLat] = useState(
    order.delivery_latitude ? String(order.delivery_latitude) : ""
  );
  const [deliveryLon, setDeliveryLon] = useState(
    order.delivery_longitude ? String(order.delivery_longitude) : ""
  );

  const initialDateStr = useMemo(() => {
    if (order.order_date) return order.order_date;
    if (order.created_at) return String(order.created_at).split("T")[0];
    return "";
  }, [order.order_date, order.created_at]);

  const [orderDate, setOrderDate] = useState<string>(initialDateStr);

  const [quantity, setQuantity] = useState<number | "">(
    order.quantity != null ? Number(order.quantity) : ""
  );
  const [unitPrice, setUnitPrice] = useState<number | "">(
    order.unit_price != null ? Number(order.unit_price) : ""
  );

  const [distanceKm, setDistanceKm] = useState<number | "">(
    order.distance_km != null ? Number(order.distance_km) : ""
  );
  const [deliveryPrice, setDeliveryPrice] = useState<number | "">(
    order.delivery_price != null ? Number(order.delivery_price) : ""
  );

  const [status, setStatus] = useState<OrderStatus>(order.status);
  const [notes, setNotes] = useState(order.notes || "");

  const [isCalculatingRoute, setIsCalculatingRoute] = useState(false);
  const [routeResult, setRouteResult] = useState<RouteCalculationResult | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);

  const calculateRoute = useCallback(async (addr: string) => {
    if (!addr || addr.trim().length < 5) return;
    setIsCalculatingRoute(true);
    setRouteError(null);

    try {
      const res = await api.navigation.calculateRoute({
        address: addr.trim(),
        latitude: deliveryLat ? parseFloat(deliveryLat) : null,
        longitude: deliveryLon ? parseFloat(deliveryLon) : null,
      });

      setRouteResult(res);

      if (res.success && res.distance_km != null) {
        setDistanceKm(Number(res.distance_km));
        if (res.latitude && res.longitude) {
          setDeliveryLat(String(res.latitude));
          setDeliveryLon(String(res.longitude));
        }
      } else if (!res.success) {
        setRouteError(res.message || "Не вдалося визначити маршрут автоматично");
      }
    } catch {
      setRouteError("Сервіс розрахунку маршруту тимчасово недоступний");
    } finally {
      setIsCalculatingRoute(false);
    }
  }, [deliveryLat, deliveryLon]);

  const handleSelectTons = (tons: number, price: number) => {
    setQuantity(tons);
    setUnitPrice(price);
  };

  const { productTotal, totalAmount, hasProductPrice } = useMemo(
    () =>
      calculateOrderTotals({
        quantity,
        unitPrice,
        deliveryPrice,
      }),
    [quantity, unitPrice, deliveryPrice]
  );

  const updateMutation = useMutation({
    mutationFn: async () => {
      const payload: OrderUpdatePayload = {
        quantity: quantity !== "" ? Number(quantity) : undefined,
        unit_price: unitPrice !== "" ? Number(unitPrice) : undefined,
        delivery_price: deliveryPrice !== "" ? Number(deliveryPrice) : 0,
        delivery_address: deliveryAddress.trim(),
        delivery_latitude: deliveryLat ? parseFloat(deliveryLat) : null,
        delivery_longitude: deliveryLon ? parseFloat(deliveryLon) : null,
        distance_km: distanceKm !== "" ? Number(distanceKm) : null,
        order_date: orderDate || undefined,
        status,
        notes: notes.trim() || undefined,
      };
      return await api.orders.update(order.id, payload);
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(
        `Замовлення #${updated?.id} оновлено!`,
        `Дата: ${updated?.order_date} • Нова сума: ${formatCurrency(updated?.total_amount)}`
      );
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка оновлення";
      toast.error("Не вдалося оновити замовлення", msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* 1. Адреса вивантаження */}
      <div className="space-y-2 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/40">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Truck className="w-4 h-4 text-emerald-600" />
            <span>Адреса вивантаження *</span>
          </label>

          <button
            type="button"
            onClick={() => calculateRoute(deliveryAddress)}
            disabled={isCalculatingRoute || !deliveryAddress}
            className="text-[11px] font-bold text-emerald-600 hover:text-emerald-700 disabled:opacity-40 flex items-center gap-1"
          >
            {isCalculatingRoute ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Navigation className="w-3 h-3" />
            )}
            <span>Розрахувати маршрут</span>
          </button>
        </div>

        <input
          type="text"
          required
          value={deliveryAddress}
          onChange={(e) => setDeliveryAddress(e.target.value)}
          className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
        />

        {routeResult?.success && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-800 dark:text-emerald-300">
            <Navigation className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>
              Маршрут: <strong>{routeResult.distance_km} км</strong>
              {routeResult.duration_min ? ` (~${routeResult.duration_min} хв)` : ""}
            </span>
          </div>
        )}

        {routeError && (
          <div className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{routeError}</span>
          </div>
        )}
      </div>

      {/* 2. Дата замовлення */}
      <div className="space-y-1.5">
        <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <CalendarIcon className="w-4 h-4 text-emerald-600" />
          <span>Дата замовлення *</span>
        </label>
        <input
          type="date"
          required
          value={orderDate}
          onChange={(e) => setOrderDate(e.target.value)}
          className="w-full sm:w-64 px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
        />
      </div>

      {/* 3. Кількість тонн & 4. Ціна */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
            Кількість (тонн) *
          </label>
          <div className="grid grid-cols-3 gap-2">
            {TONNAGE_OPTIONS.map((opt) => {
              const isSelected = quantity === opt.tons;
              return (
                <button
                  type="button"
                  key={opt.tons}
                  onClick={() => handleSelectTons(opt.tons, opt.price)}
                  className={`p-2 rounded-xl border text-center transition-all ${
                    isSelected
                      ? "border-emerald-600 bg-emerald-600 text-white font-bold shadow-xs"
                      : "border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200"
                  }`}
                >
                  <div className="text-xs font-black">{opt.label}</div>
                  <div className="text-[10px] opacity-90">{formatCurrency(opt.price)}</div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
            Ціна товару (грн) *
          </label>
          <input
            type="text"
            readOnly
            value={unitPrice !== "" ? `${formatCurrency(unitPrice)}` : ""}
            className="w-full px-3 py-2 text-sm font-black rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 cursor-default"
          />
        </div>
      </div>

      {/* 5. Кілометраж & 6. Вартість доставки */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Кілометраж доставки</span>
            {routeResult?.duration_min && (
              <span className="text-[10px] text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                ~{routeResult.duration_min} хв
              </span>
            )}
          </label>
          <div className="relative">
            <input
              type="number"
              step="0.1"
              min="0"
              placeholder="км..."
              value={distanceKm === "" ? "" : distanceKm}
              onChange={(e) =>
                setDistanceKm(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3 py-1.5 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
              км
            </span>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
            Вартість доставки (грн)
          </label>
          <div className="relative">
            <input
              type="number"
              step="10"
              min="0"
              placeholder="грн..."
              value={deliveryPrice === "" ? "" : deliveryPrice}
              onChange={(e) =>
                setDeliveryPrice(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3 py-1.5 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
              грн
            </span>
          </div>
        </div>
      </div>

      {/* 7. Статус замовлення */}
      <div>
        <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
          Статус замовлення
        </label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as OrderStatus)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
        >
          <option value="new">Нове (new)</option>
          <option value="planned">Заплановано (planned)</option>
          <option value="in_delivery">У дорозі (in_delivery)</option>
          <option value="delivered">Доставлено (delivered)</option>
          <option value="cancelled">Скасовано (cancelled)</option>
        </select>
      </div>

      {/* Примітки */}
      <div>
        <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-slate-400" />
          <span>Примітки</span>
        </label>
        <textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500 resize-none"
        />
      </div>

      {/* 8. АВТОМАТИЧНИЙ РОЗРАХУНОК ЗАМОВЛЕННЯ (В САМОМУ НИЗУ) */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-950/40 dark:to-slate-900 border border-emerald-300 dark:border-emerald-800/60 shadow-xs space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-black text-emerald-900 dark:text-emerald-300 uppercase tracking-wider">
          <Calculator className="w-4 h-4 text-emerald-600" />
          <span>Автоматичний розрахунок замовлення:</span>
        </div>

        <div className="grid grid-cols-3 gap-2 pt-1 text-xs">
          <div>
            <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Товар:</span>
            <span className="font-bold text-slate-900 dark:text-white">
              {hasProductPrice ? formatCurrency(productTotal) : "—"}
            </span>
          </div>

          <div>
            <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Доставка:</span>
            <span className="font-bold text-slate-900 dark:text-white">
              {typeof deliveryPrice === "number" ? formatCurrency(deliveryPrice) : "—"}
            </span>
          </div>

          <div className="text-right">
            <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Разом:</span>
            <span className="text-base font-black text-emerald-600 dark:text-emerald-400">
              {hasProductPrice ? formatCurrency(totalAmount) : "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 rounded-xl"
        >
          Скасувати
        </button>
        <button
          type="submit"
          disabled={updateMutation.isPending}
          className="px-5 py-2.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl disabled:opacity-50 flex items-center gap-1.5 shadow-md shadow-emerald-950/20 active:scale-98"
        >
          {updateMutation.isPending ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <DollarSign className="w-3.5 h-3.5" />
          )}
          <span>{updateMutation.isPending ? "Збереження..." : "Зберегти зміни"}</span>
        </button>
      </div>
    </form>
  );
}

export function EditOrderModal({ order, isOpen, onClose }: EditOrderModalProps) {
  if (!isOpen || !order) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Редагування замовлення #${order.id}`}
      description={`Клієнт: ${order.customer?.name || "ID " + order.customer_id}`}
      maxWidth="xl"
    >
      <EditOrderForm key={order.id} order={order} onClose={onClose} />
    </Modal>
  );
}
