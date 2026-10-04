"use client";

import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Calculator,
  User,
  UserPlus,
  Truck,
  MapPin,
  FileText,
  DollarSign,
  Search,
  Check,
} from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { Customer, OrderCreatePayload } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { useToast } from "@/components/common/ToastProvider";

interface CreateOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedCustomerId?: number;
  initialUnitPrice?: number;
}

function CreateOrderForm({
  onClose,
  preselectedCustomerId,
  initialUnitPrice = 3800,
}: {
  onClose: () => void;
  preselectedCustomerId?: number;
  initialUnitPrice?: number;
}) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [customerMode, setCustomerMode] = useState<"existing" | "new">("existing");
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(
    preselectedCustomerId || null
  );
  const [customerSearch, setCustomerSearch] = useState("");

  const [newCustomerName, setNewCustomerName] = useState("");
  const [newCustomerPhone, setNewCustomerPhone] = useState("+380");
  const [newCustomerAddress, setNewCustomerAddress] = useState("");

  const [quantity, setQuantity] = useState<number>(10);
  const [unitPrice, setUnitPrice] = useState<number>(initialUnitPrice);
  const [deliveryPrice, setDeliveryPrice] = useState<number>(400);
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryLat, setDeliveryLat] = useState<string>("");
  const [deliveryLon, setDeliveryLon] = useState<string>("");
  const [notes, setNotes] = useState("");

  // Fetch customers for search/select
  const { data: customers = [] } = useQuery({
    queryKey: ["customers", "all"],
    queryFn: () => api.customers.list({ limit: 100 }),
  });

  // Filtered customer options
  const filteredCustomers = useMemo(() => {
    if (!customerSearch.trim()) return customers.slice(0, 8);
    const q = customerSearch.toLowerCase();
    return customers.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.phone.toLowerCase().includes(q) ||
        c.address.toLowerCase().includes(q)
    );
  }, [customers, customerSearch]);

  const selectedCustomer = useMemo(
    () => customers.find((c) => c.id === selectedCustomerId) || null,
    [customers, selectedCustomerId]
  );

  const handleSelectCustomer = (cust: Customer) => {
    setSelectedCustomerId(cust.id);
    setDeliveryAddress(cust.address);
    if (cust.latitude && cust.longitude) {
      setDeliveryLat(String(cust.latitude));
      setDeliveryLon(String(cust.longitude));
    }
  };

  // Live calculations (for preview display only; backend validates strictly)
  const productTotal = useMemo(() => {
    const q = Number(quantity) || 0;
    const p = Number(unitPrice) || 0;
    return Math.round(q * p * 100) / 100;
  }, [quantity, unitPrice]);

  const totalAmount = useMemo(() => {
    const d = Number(deliveryPrice) || 0;
    return Math.round((productTotal + d) * 100) / 100;
  }, [productTotal, deliveryPrice]);

  const createOrderMutation = useMutation({
    mutationFn: async () => {
      let finalCustomerId = selectedCustomerId;

      if (customerMode === "new") {
        if (!newCustomerName.trim() || !newCustomerPhone.trim() || !newCustomerAddress.trim()) {
          throw new Error("Будь ласка, заповніть усі обов'язкові поля для нового клієнта");
        }
        const createdCustomer = await api.customers.create({
          name: newCustomerName.trim(),
          phone: newCustomerPhone.trim(),
          address: newCustomerAddress.trim(),
          latitude: deliveryLat ? parseFloat(deliveryLat) : null,
          longitude: deliveryLon ? parseFloat(deliveryLon) : null,
        });
        finalCustomerId = createdCustomer.id;
      }

      if (!finalCustomerId) {
        throw new Error("Будь ласка, оберіть клієнта або створіть нового");
      }

      if (quantity <= 0) {
        throw new Error("Кількість торф'яного брикету повинна бути більшою за нуль");
      }

      if (unitPrice < 0) {
        throw new Error("Ціна за одиницю не може бути від'ємною");
      }

      if (deliveryPrice < 0) {
        throw new Error("Вартість доставки не може бути від'ємною");
      }

      const payload: OrderCreatePayload = {
        customer_id: finalCustomerId,
        product_name: "Торф'яний брикет",
        quantity: Number(quantity),
        unit_price: Number(unitPrice),
        delivery_price: Number(deliveryPrice),
        delivery_address: deliveryAddress.trim() || undefined,
        delivery_latitude: deliveryLat ? parseFloat(deliveryLat) : null,
        delivery_longitude: deliveryLon ? parseFloat(deliveryLon) : null,
        notes: notes.trim() || undefined,
      };

      return await api.orders.create(payload);
    },
    onSuccess: (order) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(
        `Замовлення #${order.id} успішно створено!`,
        `Сума: ${formatCurrency(order.total_amount)} для клієнта ${
          selectedCustomer?.name || newCustomerName
        }`
      );
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Не вдалося створити замовлення";
      toast.error("Помилка створення замовлення", msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createOrderMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Step 1: Customer Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
            <User className="w-4 h-4 text-emerald-600" />
            <span>Клієнт *</span>
          </label>

          <div className="flex items-center p-0.5 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs font-medium">
            <button
              type="button"
              onClick={() => setCustomerMode("existing")}
              className={`px-2.5 py-1 rounded-md transition-all ${
                customerMode === "existing"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              Вибрати існуючого
            </button>
            <button
              type="button"
              onClick={() => setCustomerMode("new")}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1 ${
                customerMode === "new"
                  ? "bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              <UserPlus className="w-3 h-3" />
              <span>Новий клієнт</span>
            </button>
          </div>
        </div>

        {customerMode === "existing" ? (
          <div className="space-y-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Пошук клієнта за ім'ям, телефоном чи адресою..."
                value={customerSearch}
                onChange={(e) => setCustomerSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
              />
            </div>

            <div className="max-h-40 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-xl divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-800/50">
              {filteredCustomers.length === 0 ? (
                <div className="p-3 text-xs text-center text-slate-500">
                  Клієнтів не знайдено. Перейдіть на вкладку &ldquo;Новий клієнт&rdquo;.
                </div>
              ) : (
                filteredCustomers.map((cust) => {
                  const isSelected = selectedCustomerId === cust.id;
                  return (
                    <button
                      type="button"
                      key={cust.id}
                      onClick={() => handleSelectCustomer(cust)}
                      className={`w-full text-left p-2.5 flex items-center justify-between text-xs transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 ${
                        isSelected ? "bg-emerald-50 dark:bg-emerald-950/30" : ""
                      }`}
                    >
                      <div className="min-w-0">
                        <div className="font-semibold text-slate-900 dark:text-white truncate">
                          {cust.name}
                        </div>
                        <div className="text-slate-500 truncate">{cust.phone} • {cust.address}</div>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-emerald-600 shrink-0 ml-2" />}
                    </button>
                  );
                })
              )}
            </div>

            {selectedCustomer && (
              <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-900 dark:text-emerald-200 flex items-center justify-between">
                <span>
                  Обрано: <strong>{selectedCustomer.name}</strong> ({selectedCustomer.phone})
                </span>
                <span className="text-[11px] text-emerald-700 dark:text-emerald-400">
                  {selectedCustomer.orders_count || 0} замовлень раніше
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
            <div>
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                ПІБ / Назва *
              </label>
              <input
                type="text"
                required
                placeholder="Іван Мельник"
                value={newCustomerName}
                onChange={(e) => setNewCustomerName(e.target.value)}
                className="mt-1 w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Телефон *
              </label>
              <input
                type="text"
                required
                placeholder="+380..."
                value={newCustomerPhone}
                onChange={(e) => setNewCustomerPhone(e.target.value)}
                className="mt-1 w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Адреса клієнта *
              </label>
              <input
                type="text"
                required
                placeholder="смт Маневичі, вул. Соборна 12"
                value={newCustomerAddress}
                onChange={(e) => {
                  setNewCustomerAddress(e.target.value);
                  if (!deliveryAddress) setDeliveryAddress(e.target.value);
                }}
                className="mt-1 w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Step 2: Pricing Parameters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Кількість (тонн) *
          </label>
          <div className="mt-1 relative">
            <input
              type="number"
              step="0.1"
              min="0.1"
              required
              value={quantity}
              onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
              т
            </span>
          </div>
          <div className="flex gap-1 mt-1.5">
            {[5, 10, 15, 22].map((tons) => (
              <button
                type="button"
                key={tons}
                onClick={() => setQuantity(tons)}
                className={`px-1.5 py-0.5 text-[10px] rounded border transition-colors ${
                  quantity === tons
                    ? "bg-emerald-600 text-white border-emerald-600"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700"
                }`}
              >
                {tons}т
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Ціна за 1 т (грн) *
          </label>
          <div className="mt-1 relative">
            <input
              type="number"
              step="10"
              min="0"
              required
              value={unitPrice}
              onChange={(e) => setUnitPrice(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
              грн
            </span>
          </div>
          <div className="flex gap-1 mt-1.5">
            {[3800, 4400, 4900].map((p) => (
              <button
                type="button"
                key={p}
                onClick={() => setUnitPrice(p)}
                className={`px-1.5 py-0.5 text-[10px] rounded border transition-colors ${
                  unitPrice === p
                    ? "bg-emerald-600 text-white border-emerald-600"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Доставка (грн)
          </label>
          <div className="mt-1 relative">
            <input
              type="number"
              step="10"
              min="0"
              value={deliveryPrice}
              onChange={(e) => setDeliveryPrice(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
              грн
            </span>
          </div>
          <div className="flex gap-1 mt-1.5">
            {[0, 350, 500, 750].map((d) => (
              <button
                type="button"
                key={d}
                onClick={() => setDeliveryPrice(d)}
                className={`px-1.5 py-0.5 text-[10px] rounded border transition-colors ${
                  deliveryPrice === d
                    ? "bg-emerald-600 text-white border-emerald-600"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700"
                }`}
              >
                {d === 0 ? "Самовивіз" : `${d} грн`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Live Calculation Preview Banner */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/40 dark:to-teal-950/30 border border-emerald-200 dark:border-emerald-800/60 shadow-xs">
        <div className="flex items-center gap-2 mb-2 text-xs font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider">
          <Calculator className="w-3.5 h-3.5" />
          <span>Автоматичний розрахунок замовлення:</span>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center sm:text-left">
          <div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Вартість товару:</div>
            <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
              {formatCurrency(productTotal)}
            </div>
            <div className="text-[10px] text-slate-400">
              {quantity} т × {unitPrice} грн
            </div>
          </div>

          <div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Доставка:</div>
            <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
              {formatCurrency(deliveryPrice)}
            </div>
            <div className="text-[10px] text-slate-400">
              {deliveryPrice === 0 ? "Безкоштовно / самовивіз" : "Транспорт підприємства"}
            </div>
          </div>

          <div className="bg-white/80 dark:bg-slate-900/80 p-2 rounded-lg border border-emerald-300 dark:border-emerald-700">
            <div className="text-[11px] font-semibold text-emerald-800 dark:text-emerald-300">
              Разом до сплати:
            </div>
            <div className="text-base font-extrabold text-emerald-700 dark:text-emerald-400">
              {formatCurrency(totalAmount)}
            </div>
          </div>
        </div>
      </div>

      {/* Step 3: Delivery Address & Coordinates */}
      <div className="space-y-3">
        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Truck className="w-4 h-4 text-emerald-600" />
            <span>Адреса вивантаження *</span>
          </label>
          <input
            type="text"
            required
            placeholder="Адреса вивантаження"
            value={deliveryAddress}
            onChange={(e) => setDeliveryAddress(e.target.value)}
            className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-slate-400" />
              <span>Широта (Lat)</span>
            </label>
            <input
              type="text"
              placeholder="51.298100"
              value={deliveryLat}
              onChange={(e) => setDeliveryLat(e.target.value)}
              className="mt-1 w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-slate-400" />
              <span>Довгота (Lon)</span>
            </label>
            <input
              type="text"
              placeholder="25.553200"
              value={deliveryLon}
              onChange={(e) => setDeliveryLon(e.target.value)}
              className="mt-1 w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>
      </div>

      {/* Step 4: Notes */}
      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <FileText className="w-4 h-4 text-slate-400" />
          <span>Примітки до замовлення</span>
        </label>
        <textarea
          rows={2}
          placeholder="В'їзд через великі ворота, контакт водія, спосіб оплати готівка/ФОП..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 resize-none"
        />
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          Скасувати
        </button>

        <button
          type="submit"
          disabled={createOrderMutation.isPending}
          className="px-5 py-2.5 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md shadow-emerald-950/20 disabled:opacity-50 transition-all flex items-center gap-2"
        >
          {createOrderMutation.isPending ? (
            <>
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Збереження...</span>
            </>
          ) : (
            <>
              <DollarSign className="w-4 h-4" />
              <span>Оформити замовлення • {formatCurrency(totalAmount)}</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}

export function CreateOrderModal({
  isOpen,
  onClose,
  preselectedCustomerId,
  initialUnitPrice = 3800,
}: CreateOrderModalProps) {
  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Оформлення нового замовлення"
      description="Введіть дані клієнта, обсяг торфобрикету та адресу доставки"
      maxWidth="2xl"
    >
      <CreateOrderForm
        key={preselectedCustomerId ? `order-cust-${preselectedCustomerId}` : "new-order"}
        onClose={onClose}
        preselectedCustomerId={preselectedCustomerId}
        initialUnitPrice={initialUnitPrice}
      />
    </Modal>
  );
}
