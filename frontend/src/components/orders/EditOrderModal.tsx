"use client";

import React, { useState, useMemo, useCallback } from "react";
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
  User,
} from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Order, OrderStatus, OrderUpdatePayload, RouteCalculationResult } from "@/types";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useToast } from "@/components/common/ToastProvider";
import { calculateOrderTotals } from "@/lib/pricing";

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

  // 4. Quantity (Tonnage in tons) - no default 0
  const [quantity, setQuantity] = useState<number | "">(
    order.quantity != null ? Number(order.quantity) : ""
  );

  // 5. Price per ton (грн) - no default 0
  const [unitPrice, setUnitPrice] = useState<number | "">(
    order.unit_price != null ? Number(order.unit_price) : ""
  );

  // 6. Mileage (km)
  const [distanceKm, setDistanceKm] = useState<number | "">(
    order.distance_km != null ? Number(order.distance_km) : ""
  );

  // 7. Delivery price per km (грн/км)
  const initialPerKmRate = useMemo(() => {
    if (order.delivery_price_per_km != null) {
      return Number(order.delivery_price_per_km);
    }
    // If existing order has delivery_price and distance_km > 0, estimate rate
    if (
      order.delivery_price != null &&
      Number(order.delivery_price) > 0 &&
      order.distance_km != null &&
      Number(order.distance_km) > 0
    ) {
      return (
        Math.round((Number(order.delivery_price) / Number(order.distance_km)) * 100) /
        100
      );
    }
    return "";
  }, [order.delivery_price_per_km, order.delivery_price, order.distance_km]);

  const [deliveryPricePerKm, setDeliveryPricePerKm] = useState<number | "">(
    initialPerKmRate
  );

  const [status, setStatus] = useState<OrderStatus>(order.status);
  const [notes, setNotes] = useState(order.notes || "");

  const [isCalculatingRoute, setIsCalculatingRoute] = useState(false);
  const [routeResult, setRouteResult] = useState<RouteCalculationResult | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);

  const calculateRoute = useCallback(
    async (addr: string) => {
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
    },
    [deliveryLat, deliveryLon]
  );

  // Live order calculations
  const {
    productTotal,
    deliveryTotal,
    totalAmount,
    hasProductCalculation,
    hasDeliveryCalculation,
    isComplete,
  } = useMemo(
    () =>
      calculateOrderTotals({
        quantityTons: quantity,
        pricePerTon: unitPrice,
        distanceKm,
        deliveryPricePerKm,
      }),
    [quantity, unitPrice, distanceKm, deliveryPricePerKm]
  );

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (quantity === "" || Number(quantity) <= 0) {
        throw new Error("Будь ласка, вкажіть кількість тонн (більше 0)");
      }
      if (unitPrice === "" || Number(unitPrice) < 0) {
        throw new Error("Ціна за тонну не може бути порожньою або від'ємною");
      }

      const payload: OrderUpdatePayload = {
        quantity: Number(quantity),
        unit_price: Number(unitPrice),
        distance_km: distanceKm !== "" ? Number(distanceKm) : null,
        delivery_price_per_km:
          deliveryPricePerKm !== "" ? Number(deliveryPricePerKm) : null,
        delivery_price:
          typeof deliveryTotal === "number"
            ? deliveryTotal
            : order.delivery_price != null
            ? Number(order.delivery_price)
            : 0,
        delivery_address: deliveryAddress.trim(),
        delivery_latitude: deliveryLat ? parseFloat(deliveryLat) : null,
        delivery_longitude: deliveryLon ? parseFloat(deliveryLon) : null,
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
      {/* Клієнт (Інформаційний блок) */}
      <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/40 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <User className="w-4 h-4 text-emerald-600" />
          <div>
            <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
              {order.customer?.name || "Клієнт"}
            </div>
            <div className="text-[11px] text-slate-500">
              {order.customer?.phone || "Немає телефону"}
            </div>
          </div>
        </div>
        <span className="text-[11px] font-semibold text-slate-400">
          Замовлення #{order.id}
        </span>
      </div>

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
            className="text-[11px] text-emerald-600 font-bold hover:underline disabled:opacity-50"
          >
            {isCalculatingRoute ? "Розрахунок..." : "Перерахувати маршрут"}
          </button>
        </div>

        <div className="relative">
          <input
            type="text"
            required
            value={deliveryAddress}
            onChange={(e) => setDeliveryAddress(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
          />
        </div>

        {routeResult?.success && (
          <div className="flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300 p-2 rounded-lg bg-emerald-100/50 dark:bg-emerald-950/30">
            <span>
              Маршрут: <strong>{routeResult.distance_km} км</strong>
              {routeResult.duration_min ? ` (~${routeResult.duration_min} хв)` : ""}
            </span>
            {routeResult.waze_url && (
              <a
                href={routeResult.waze_url}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] underline font-bold"
              >
                Waze →
              </a>
            )}
          </div>
        )}

        {routeError && (
          <div className="flex items-center gap-1.5 text-xs text-amber-700 dark:text-amber-300">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{routeError}</span>
          </div>
        )}
      </div>

      {/* 2. Дата замовлення & 3. Статус */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
            className="w-full px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
            Статус замовлення
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as OrderStatus)}
            className="w-full px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
          >
            <option value="new">Нове</option>
            <option value="planned">Заплановане</option>
            <option value="in_delivery">У дорозі</option>
            <option value="delivered">Доставлене</option>
            <option value="cancelled">Скасоване</option>
          </select>
        </div>
      </div>

      {/* 4. Кількість тонн & 5. Ціна за тонну */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Кількість тонн */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
            Кількість тонн *
          </label>
          <div className="relative">
            <input
              type="number"
              step="any"
              min="0.01"
              required
              placeholder="Наприклад: 2"
              value={quantity === "" ? "" : quantity}
              onChange={(e) =>
                setQuantity(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3 py-2 text-sm font-bold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              т
            </span>
          </div>
        </div>

        {/* Ціна за тонну */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
            <span>Ціна за тонну (грн) *</span>
          </label>
          <div className="relative">
            <input
              type="number"
              step="any"
              min="0"
              required
              placeholder="Наприклад: 12500"
              value={unitPrice === "" ? "" : unitPrice}
              onChange={(e) =>
                setUnitPrice(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3 py-2 text-sm font-bold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              грн/т
            </span>
          </div>
        </div>
      </div>

      {/* 6. Кілометраж доставки & 7. Ціна доставки за км */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Кілометраж доставки */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span className="flex items-center gap-1">
              <Navigation className="w-3.5 h-3.5 text-emerald-600" />
              <span>Кілометраж доставки (км)</span>
            </span>
            {routeResult?.duration_min && (
              <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
                <Clock className="w-3 h-3" />
                ~{routeResult.duration_min} хв
              </span>
            )}
          </label>
          <div className="relative">
            <input
              type="number"
              step="any"
              min="0"
              placeholder="60.1"
              value={distanceKm === "" ? "" : distanceKm}
              onChange={(e) =>
                setDistanceKm(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              км
            </span>
          </div>
        </div>

        {/* Ціна доставки за км */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Truck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Ціна доставки за км (грн/км)</span>
          </label>
          <div className="relative">
            <input
              type="number"
              step="any"
              min="0"
              placeholder="350"
              value={deliveryPricePerKm === "" ? "" : deliveryPricePerKm}
              onChange={(e) =>
                setDeliveryPricePerKm(
                  e.target.value === "" ? "" : parseFloat(e.target.value)
                )
              }
              className="w-full px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              грн/км
            </span>
          </div>
        </div>
      </div>

      {/* Примітки */}
      <div className="space-y-1">
        <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-slate-400" />
          <span>Примітки до замовлення</span>
        </label>
        <textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Особливості замовлення або адреси..."
          className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 resize-none"
        />
      </div>

      {/* 8. ПІДСУМОК ЗАМОВЛЕННЯ */}
      <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-50 via-teal-50/60 to-emerald-100/40 dark:from-emerald-950/40 dark:via-teal-950/30 dark:to-slate-900 border border-emerald-300 dark:border-emerald-800/70 shadow-xs space-y-3">
        <div className="flex items-center justify-between text-xs font-extrabold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
            <span>Підсумок замовлення:</span>
          </div>
          <span className="text-[10px] normal-case font-medium text-emerald-700 dark:text-emerald-400">
            {isComplete ? "Розраховано повністю" : "Миттєвий розрахунок"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Вартість товару */}
          <div className="p-2.5 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-emerald-200/70 dark:border-emerald-900/60">
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Вартість товару:</div>
            <div className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5">
              {hasProductCalculation ? formatCurrency(productTotal) : "— грн"}
            </div>
            <div className="text-[10px] text-slate-400">
              {hasProductCalculation
                ? `${quantity} т × ${formatCurrency(unitPrice)}`
                : "Вкажіть кількість та ціну"}
            </div>
          </div>

          {/* Вартість доставки */}
          <div className="p-2.5 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-emerald-200/70 dark:border-emerald-900/60">
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Вартість доставки:</div>
            <div className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5">
              {hasDeliveryCalculation
                ? formatCurrency(deliveryTotal)
                : order.delivery_price
                ? formatCurrency(order.delivery_price)
                : "— грн"}
            </div>
            <div className="text-[10px] text-slate-400">
              {hasDeliveryCalculation
                ? `${distanceKm} км × ${formatCurrency(deliveryPricePerKm)}/км`
                : "Вкажіть км та тариф"}
            </div>
          </div>

          {/* Загальна сума */}
          <div className="p-2.5 rounded-xl bg-emerald-600 text-white shadow-sm flex flex-col justify-between">
            <div className="text-[11px] font-semibold text-emerald-100">Загальна сума:</div>
            <div className="text-xl font-black text-white mt-0.5">
              {formatCurrency(totalAmount)}
            </div>
            <div className="text-[10px] text-emerald-100/90 font-medium">
              {hasProductCalculation && hasDeliveryCalculation
                ? "Товар + доставка"
                : "Сума до сплати"}
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          Скасувати
        </button>
        <button
          type="submit"
          disabled={updateMutation.isPending}
          className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md disabled:opacity-50"
        >
          {updateMutation.isPending ? "Збереження..." : "Зберегти зміни"}
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
      description="Змініть параметри замовлення, адресу, кілометраж або тариф доставки"
      maxWidth="xl"
    >
      <EditOrderForm key={`edit-order-${order.id}`} order={order} onClose={onClose} />
    </Modal>
  );
}
