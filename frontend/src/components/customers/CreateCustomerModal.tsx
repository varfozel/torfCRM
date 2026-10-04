"use client";

import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { UserPlus } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { CustomerCreatePayload } from "@/types";
import { useToast } from "@/components/common/ToastProvider";

interface CreateCustomerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateCustomerModal({ isOpen, onClose }: CreateCustomerModalProps) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+380");
  const [address, setAddress] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [notes, setNotes] = useState("");

  const createMutation = useMutation({
    mutationFn: async () => {
      if (!name.trim() || !phone.trim() || !address.trim()) {
        throw new Error("Заповніть усі обов'язкові поля: назва/ПІБ, телефон та адреса");
      }
      const payload: CustomerCreatePayload = {
        name: name.trim(),
        phone: phone.trim(),
        address: address.trim(),
        latitude: lat ? parseFloat(lat) : null,
        longitude: lon ? parseFloat(lon) : null,
        notes: notes.trim() || undefined,
      };
      return await api.customers.create(payload);
    },
    onSuccess: (cust) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      toast.success(`Клієнта "${cust.name}" успішно створено!`);
      setName("");
      setPhone("+380");
      setAddress("");
      setLat("");
      setLon("");
      setNotes("");
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка додавання клієнта";
      toast.error("Не вдалося створити клієнта", msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Додати нового клієнта"
      description="Введіть контактні дані та адресу постійної доставки"
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            ПІБ або назва організації *
          </label>
          <input
            type="text"
            required
            placeholder="ПП &ldquo;Тепло-Плюс&rdquo; / Ковальчук Олег"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Номер телефону *
          </label>
          <input
            type="text"
            required
            placeholder="+380 50 123 4567"
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
            placeholder="Волинська обл., Маневицький р-н, с. Оконськ, вул. Центральна 15"
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
              placeholder="51.298100"
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
              placeholder="25.553200"
              value={lon}
              onChange={(e) => setLon(e.target.value)}
              className="mt-1 w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Примітки про клієнта
          </label>
          <textarea
            rows={2}
            placeholder="Власник пилорами, бере по 20 тонн щомісяця..."
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
            disabled={createMutation.isPending}
            className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs disabled:opacity-50 flex items-center gap-1.5"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>{createMutation.isPending ? "Створення..." : "Зберегти клієнта"}</span>
          </button>
        </div>
      </form>
    </Modal>
  );
}
