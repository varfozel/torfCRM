"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  User,
  Phone,
  Calendar,
  ShoppingBag,
  DollarSign,
  PlusCircle,
  Edit,
  Trash2,
} from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { StatusBadge } from "@/components/common/StatusBadge";
import { api } from "@/lib/api";
import { Customer, Order } from "@/types";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { useToast } from "@/components/common/ToastProvider";

interface CustomerDetailModalProps {
  customerId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onEditCustomer: (customer: Customer) => void;
  onCreateOrderForCustomer: (customerId: number) => void;
  onViewOrder: (order: Order) => void;
}

export function CustomerDetailModal({
  customerId,
  isOpen,
  onClose,
  onEditCustomer,
  onCreateOrderForCustomer,
  onViewOrder,
}: CustomerDetailModalProps) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [isDeleting, setIsDeleting] = useState(false);

  const { data: customer, isLoading } = useQuery({
    queryKey: ["customer", customerId],
    queryFn: () => (customerId ? api.customers.getDetail(customerId) : null),
    enabled: isOpen && !!customerId,
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!customerId) return;
      await api.customers.delete(customerId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Клієнта видалено");
      setIsDeleting(false);
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка видалення клієнта";
      toast.error("Не вдалося видалити клієнта", msg);
      setIsDeleting(false);
    },
  });

  if (!isOpen || !customerId) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={customer?.name || "Профіль клієнта"}
      description={`ID клієнта: #${customerId} • Зареєстровано: ${
        customer ? formatDateTime(customer.created_at) : "—"
      }`}
      maxWidth="3xl"
    >
      {isLoading ? (
        <div className="py-12 flex justify-center items-center">
          <div className="w-8 h-8 border-3 border-emerald-500/20 border-t-emerald-600 rounded-full animate-spin" />
        </div>
      ) : !customer ? (
        <div className="py-8 text-center text-slate-500">Клієнта не знайдено</div>
      ) : (
        <div className="space-y-6">
          {/* Quick Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                <ShoppingBag className="w-4 h-4 text-emerald-600" />
                <span>Всього замовлень</span>
              </div>
              <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">
                {customer.orders_count || customer.orders?.length || 0}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <span>Загальна сума покупок</span>
              </div>
              <div className="mt-2 text-2xl font-black text-emerald-600 dark:text-emerald-400">
                {formatCurrency(customer.total_spent || 0)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                <Calendar className="w-4 h-4 text-emerald-600" />
                <span>Перше звернення</span>
              </div>
              <div className="mt-2 text-sm font-bold text-slate-700 dark:text-slate-300">
                {formatDateTime(customer.created_at)}
              </div>
            </div>
          </div>

          {/* Contact Details Card */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <User className="w-4 h-4 text-emerald-600" />
                <span>Контактна інформація</span>
              </h4>

              <div className="flex items-center gap-2">
                <a
                  href={`tel:${customer.phone}`}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold hover:bg-emerald-100 transition-colors"
                >
                  <Phone className="w-3.5 h-3.5" />
                  <span>{customer.phone}</span>
                </a>

                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onEditCustomer(customer);
                  }}
                  className="p-1 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100"
                  title="Редагувати"
                >
                  <Edit className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-xs text-slate-500">Адреса доставки:</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200">
                  {customer.address}
                </p>
                {customer.latitude && customer.longitude && (
                  <p className="text-xs text-slate-500 mt-0.5">
                    Координати: {customer.latitude}, {customer.longitude}
                  </p>
                )}
              </div>

              {customer.notes && (
                <div className="sm:col-span-2 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                  <span className="font-semibold block text-slate-500 mb-0.5">Примітки:</span>
                  <p>{customer.notes}</p>
                </div>
              )}
            </div>
          </div>

          {/* Orders History Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShoppingBag className="w-4 h-4 text-emerald-600" />
                <span>Історія замовлень ({customer.orders?.length || 0})</span>
              </h4>

              <button
                type="button"
                onClick={() => {
                  onClose();
                  onCreateOrderForCustomer(customer.id);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Нове замовлення</span>
              </button>
            </div>

            {!customer.orders || customer.orders.length === 0 ? (
              <div className="p-8 text-center rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-500">
                Замовлень для цього клієнта ще не оформлено.
              </div>
            ) : (
              <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="p-3">№</th>
                      <th className="p-3">Дата</th>
                      <th className="p-3">Обсяг</th>
                      <th className="p-3">Сума</th>
                      <th className="p-3">Статус</th>
                      <th className="p-3 text-right">Дії</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {customer.orders.map((ord) => (
                      <tr
                        key={ord.id}
                        className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                      >
                        <td className="p-3 font-bold text-slate-900 dark:text-white">
                          #{ord.id}
                        </td>
                        <td className="p-3 text-slate-600 dark:text-slate-400">
                          {formatDateTime(ord.created_at)}
                        </td>
                        <td className="p-3 font-semibold text-slate-800 dark:text-slate-200">
                          {ord.quantity} т
                        </td>
                        <td className="p-3 font-bold text-emerald-600 dark:text-emerald-400">
                          {formatCurrency(ord.total_amount)}
                        </td>
                        <td className="p-3">
                          <StatusBadge status={ord.status} />
                        </td>
                        <td className="p-3 text-right">
                          <button
                            type="button"
                            onClick={() => {
                              onClose();
                              onViewOrder(ord);
                            }}
                            className="px-2.5 py-1 rounded-lg text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 font-semibold"
                          >
                            Деталі
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Delete Customer & Footer Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-800">
            <div>
              {isDeleting ? (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-rose-600 font-semibold">
                    Видалити клієнта та всі його замовлення?
                  </span>
                  <button
                    type="button"
                    onClick={() => deleteMutation.mutate()}
                    disabled={deleteMutation.isPending}
                    className="px-2.5 py-1 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg"
                  >
                    Так, видалити
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsDeleting(false)}
                    className="px-2 py-1 text-xs text-slate-500"
                  >
                    Скасувати
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsDeleting(true)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-rose-600 hover:bg-rose-50 text-xs font-semibold transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Видалити клієнта</span>
                </button>
              )}
            </div>

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 rounded-xl"
            >
              Закрити
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
