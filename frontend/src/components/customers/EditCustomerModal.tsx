"use client";

import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { Customer, CustomerUpdatePayload } from "@/types";
import { useToast } from "@/components/common/ToastProvider";

interface EditCustomerModalProps {
  customer: Customer | null;
  isOpen: boolean;
  onClose: () => void;
}

function EditCustomerForm({ customer, onClose }: { customer: Customer; onClose: () => void }) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [name, setName] = useState(customer.name);
  const [phone, setPhone] = useState(customer.phone);
  const [address, setAddress] = useState(customer.address);
  const [lat, setLat] = useState(customer.latitude ? String(customer.latitude) : "");
  const [lon, setLon] = useState(customer.longitude ? String(customer.longitude) : "");
  const [notes, setNotes] = useState(customer.notes || "");

  const updateMutation = useMutation({
    mutationFn: async () => {
      const payload: CustomerUpdatePayload = {
        name: name.trim(),
        phone: phone.trim(),
        address: address.trim(),
        latitude: lat ? parseFloat(lat) : null,
        longitude: lon ? parseFloat(lon) : null,
        notes: notes.trim() || undefined,
      };
      return await api.customers.update(customer.id, payload);
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast.success(`Клієнта "${updated?.name}" успішно оновлено!`);
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка оновлення";
      toast.error("Не вдалося оновити дані клієнта", msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          ПІБ / Назва *
        </label>
        <input
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
        />
      </div>

      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          Телефон *
        </label>
        <input
          type="text"
          required
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
        />
      </div>

      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          Адреса *
        </label>
        <input
          type="text"
          required
          value={address}
          onChange={(e) => setAddress(e.target.value)}
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
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
            Довгота (Lon)
          </label>
          <input
            type="text"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>
      </div>

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
          className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs disabled:opacity-50 flex items-center gap-1.5"
        >
          <Check className="w-3.5 h-3.5" />
          <span>{updateMutation.isPending ? "Збереження..." : "Зберегти"}</span>
        </button>
      </div>
    </form>
  );
}

export function EditCustomerModal({ customer, isOpen, onClose }: EditCustomerModalProps) {
  if (!isOpen || !customer) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Редагування клієнта: ${customer.name}`}
      maxWidth="lg"
    >
      <EditCustomerForm key={customer.id} customer={customer} onClose={onClose} />
    </Modal>
  );
}
