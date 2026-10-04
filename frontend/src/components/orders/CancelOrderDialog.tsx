"use client";

import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, XCircle } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Order } from "@/types";
import { api } from "@/lib/api";
import { useToast } from "@/components/common/ToastProvider";

interface CancelOrderDialogProps {
  order: Order | null;
  isOpen: boolean;
  onClose: () => void;
}

export function CancelOrderDialog({ order, isOpen, onClose }: CancelOrderDialogProps) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [reason, setReason] = useState("");

  const cancelMutation = useMutation({
    mutationFn: async () => {
      if (!order) return;
      return await api.orders.cancel(order.id, reason.trim() || undefined);
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.info(`Замовлення #${updated?.id} скасовано`);
      setReason("");
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка скасування";
      toast.error("Не вдалося скасувати замовлення", msg);
    },
  });

  const handleConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    cancelMutation.mutate();
  };

  if (!order) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Скасування замовлення #${order.id}`}
      maxWidth="md"
    >
      <form onSubmit={handleConfirm} className="space-y-4">
        <div className="flex items-start gap-3 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-200">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            Ви впевнені, що бажаєте скасувати це замовлення? Статус буде змінено на{" "}
            <strong>Скасовано</strong>. Цю дію можна виконати лише за згодою клієнта або форс-мажору.
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Причина скасування (необов&apos;язково)
          </label>
          <input
            type="text"
            placeholder="Клієнт змінив плани / відсутній під'їзд вантажівки..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-rose-500 focus:border-rose-500"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
          >
            Назад
          </button>

          <button
            type="submit"
            disabled={cancelMutation.isPending}
            className="px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl shadow-xs disabled:opacity-50 flex items-center gap-1.5"
          >
            <XCircle className="w-4 h-4" />
            <span>{cancelMutation.isPending ? "Скасування..." : "Підтвердити скасування"}</span>
          </button>
        </div>
      </form>
    </Modal>
  );
}
