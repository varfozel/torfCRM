"use client";

import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { DollarSign } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Order, OrderStatus, OrderUpdatePayload } from "@/types";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useToast } from "@/components/common/ToastProvider";

interface EditOrderModalProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
}

function EditOrderForm({ order, onClose }: { order: Order; onClose: () => void }) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [quantity, setQuantity] = useState<number>(order.quantity);
  const [unitPrice, setUnitPrice] = useState<number>(order.unit_price);
  const [deliveryPrice, setDeliveryPrice] = useState<number>(order.delivery_price);
  const [deliveryAddress, setDeliveryAddress] = useState(order.delivery_address || "");
  const [deliveryLat, setDeliveryLat] = useState(order.delivery_latitude ? String(order.delivery_latitude) : "");
  const [deliveryLon, setDeliveryLon] = useState(order.delivery_longitude ? String(order.delivery_longitude) : "");
  const [status, setStatus] = useState<OrderStatus>(order.status);
  const [notes, setNotes] = useState(order.notes || "");

  const productTotal = Math.round((Number(quantity) || 0) * (Number(unitPrice) || 0) * 100) / 100;
  const totalAmount = Math.round((productTotal + (Number(deliveryPrice) || 0)) * 100) / 100;

  const updateMutation = useMutation({
    mutationFn: async () => {
      const payload: OrderUpdatePayload = {
        quantity: Number(quantity),
        unit_price: Number(unitPrice),
        delivery_price: Number(deliveryPrice),
        delivery_address: deliveryAddress.trim(),
        delivery_latitude: deliveryLat ? parseFloat(deliveryLat) : null,
        delivery_longitude: deliveryLon ? parseFloat(deliveryLon) : null,
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
        `Нова сума: ${formatCurrency(updated?.total_amount)}`
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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Кількість (тонн) *
          </label>
          <input
            type="number"
            step="0.1"
            min="0.1"
            required
            value={quantity}
            onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
            className="mt-1 w-full px-3 py-1.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Ціна за 1 т (грн) *
          </label>
          <input
            type="number"
            step="10"
            min="0"
            required
            value={unitPrice}
            onChange={(e) => setUnitPrice(parseFloat(e.target.value) || 0)}
            className="mt-1 w-full px-3 py-1.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Доставка (грн)
          </label>
          <input
            type="number"
            step="10"
            min="0"
            value={deliveryPrice}
            onChange={(e) => setDeliveryPrice(parseFloat(e.target.value) || 0)}
            className="mt-1 w-full px-3 py-1.5 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* Calculation badge */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-xs">
        <span className="text-slate-600 dark:text-slate-400">
          Товар: {formatCurrency(productTotal)} + Доставка: {formatCurrency(deliveryPrice)}
        </span>
        <span className="font-extrabold text-emerald-600 dark:text-emerald-400 text-sm">
          Разом: {formatCurrency(totalAmount)}
        </span>
      </div>

      {/* Status */}
      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
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

      {/* Address */}
      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          Адреса вивантаження
        </label>
        <input
          type="text"
          required
          value={deliveryAddress}
          onChange={(e) => setDeliveryAddress(e.target.value)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
            Широта (Lat)
          </label>
          <input
            type="text"
            value={deliveryLat}
            onChange={(e) => setDeliveryLat(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
            Довгота (Lon)
          </label>
          <input
            type="text"
            value={deliveryLon}
            onChange={(e) => setDeliveryLon(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          Примітки
        </label>
        <textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500 resize-none"
        />
      </div>

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
          className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl disabled:opacity-50 flex items-center gap-1.5"
        >
          <DollarSign className="w-3.5 h-3.5" />
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
