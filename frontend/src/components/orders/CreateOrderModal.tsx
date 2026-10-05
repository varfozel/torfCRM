"use client";

import React, { useState, useMemo, useEffect, useCallback } from "react";
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
  Calendar as CalendarIcon,
  Navigation,
  Loader2,
  AlertCircle,
  Clock,
  Sparkles,
} from "lucide-react";
import { format } from "date-fns";
import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { Customer, OrderCreatePayload, RouteCalculationResult } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { useToast } from "@/components/common/ToastProvider";
import { TONNAGE_OPTIONS, calculateOrderTotals } from "@/lib/pricing";

interface CreateOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedCustomerId?: number;
  initialOrderDate?: string | Date;
}

function CreateOrderForm({
  onClose,
  preselectedCustomerId,
  initialOrderDate,
}: {
  onClose: () => void;
  preselectedCustomerId?: number;
  initialOrderDate?: string | Date;
}) {
  const queryClient = useQueryClient();
  const toast = useToast();

  // 1. Customer Selection State
  const [customerMode, setCustomerMode] = useState<"existing" | "new">("existing");
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(
    preselectedCustomerId || null
  );
  const [customerSearch, setCustomerSearch] = useState("");

  const [newCustomerName, setNewCustomerName] = useState("");
  const [newCustomerPhone, setNewCustomerPhone] = useState("+380");
  const [newCustomerAddress, setNewCustomerAddress] = useState("");

  // 2. Delivery Address & Routing State
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryLat, setDeliveryLat] = useState<string>("");
  const [deliveryLon, setDeliveryLon] = useState<string>("");
  const [isCalculatingRoute, setIsCalculatingRoute] = useState(false);
  const [routeResult, setRouteResult] = useState<RouteCalculationResult | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);

  // 3. Order Date State (default to provided date or today)
  const defaultDateStr = useMemo(() => {
    if (!initialOrderDate) return format(new Date(), "yyyy-MM-dd");
    if (initialOrderDate instanceof Date) return format(initialOrderDate, "yyyy-MM-dd");
    return String(initialOrderDate).split("T")[0];
  }, [initialOrderDate]);

  const [orderDate, setOrderDate] = useState<string>(defaultDateStr);

  // 4. Quantity (Tonnage) & 5. Price (No 0 defaults)
  const [quantity, setQuantity] = useState<number | "">("");
  const [unitPrice, setUnitPrice] = useState<number | "">("");

  // 6. Mileage (Distance in km) & 7. Delivery Price (No 0 defaults)
  const [distanceKm, setDistanceKm] = useState<number | "">("");
  const [deliveryPrice, setDeliveryPrice] = useState<number | "">("");

  // Notes
  const [notes, setNotes] = useState("");

  // Fetch customers
  const { data: customers = [] } = useQuery({
    queryKey: ["customers", "all"],
    queryFn: () => api.customers.list({ limit: 100 }),
  });

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

  // Function to calculate route from warehouse to address
  const calculateRoute = useCallback(async (addr: string, lat?: number | null, lon?: number | null) => {
    if (!addr && (lat === undefined || lat === null)) {
      setRouteResult(null);
      return;
    }

    setIsCalculatingRoute(true);
    setRouteError(null);

    try {
      const res = await api.navigation.calculateRoute({
        address: addr.trim(),
        latitude: lat ?? (deliveryLat ? parseFloat(deliveryLat) : null),
        longitude: lon ?? (deliveryLon ? parseFloat(deliveryLon) : null),
      });

      setRouteResult(res);

      if (res.success && res.distance_km != null) {
        setDistanceKm(Number(res.distance_km));
        if (res.latitude && res.longitude) {
          setDeliveryLat(String(res.latitude));
          setDeliveryLon(String(res.longitude));
        }
      } else if (!res.success) {
        setRouteError(res.message || "Не вдалося визначити маршрут автоматично. Введіть кілометраж вручну.");
      }
    } catch {
      setRouteError("Сервіс розрахунку маршруту тимчасово недоступний. Ви можете вказати кілометраж вручну.");
    } finally {
      setIsCalculatingRoute(false);
    }
  }, [deliveryLat, deliveryLon]);

  // Handle selecting an existing customer
  const handleSelectCustomer = (cust: Customer) => {
    setSelectedCustomerId(cust.id);
    setDeliveryAddress(cust.address);
    if (cust.latitude && cust.longitude) {
      setDeliveryLat(String(cust.latitude));
      setDeliveryLon(String(cust.longitude));
      calculateRoute(cust.address, cust.latitude, cust.longitude);
    } else {
      setDeliveryLat("");
      setDeliveryLon("");
      calculateRoute(cust.address);
    }
  };

  // Debounced auto-calculation when user finishes typing a new delivery address
  useEffect(() => {
    if (!deliveryAddress || deliveryAddress.trim().length < 5) return;
    const timer = setTimeout(() => {
      calculateRoute(deliveryAddress);
    }, 900);
    return () => clearTimeout(timer);
  }, [deliveryAddress, calculateRoute]);

  // Handle tonnage selection: automatically sets the centralized tier price
  const handleSelectTons = (tons: number, price: number) => {
    setQuantity(tons);
    setUnitPrice(price);
  };

  // Calculations for preview at the bottom
  const { productTotal, totalAmount, hasProductPrice } = useMemo(
    () =>
      calculateOrderTotals({
        quantity,
        unitPrice,
        deliveryPrice,
      }),
    [quantity, unitPrice, deliveryPrice]
  );

  // Mutation to create order
  const createOrderMutation = useMutation({
    mutationFn: async () => {
      let finalCustomerId = selectedCustomerId;

      if (customerMode === "new") {
        if (!newCustomerName.trim() || !newCustomerPhone.trim() || !newCustomerAddress.trim()) {
          throw new Error("Будь ласка, заповніть ім'я, телефон та адресу нового клієнта");
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
        throw new Error("Будь ласка, оберіть клієнта або зареєструйте нового");
      }

      if (!deliveryAddress.trim()) {
        throw new Error("Будь ласка, вкажіть адресу вивантаження");
      }

      if (!orderDate) {
        throw new Error("Будь ласка, оберіть дату замовлення");
      }

      if (quantity === "" || quantity <= 0) {
        throw new Error("Будь ласка, оберіть кількість тонн (1, 2 або 3 т)");
      }

      if (unitPrice === "" || unitPrice < 0) {
        throw new Error("Ціна замовлення не може бути порожньою або від'ємною");
      }

      const payload: OrderCreatePayload = {
        customer_id: finalCustomerId,
        product_name: "Торф'яний брикет",
        quantity: Number(quantity),
        unit_price: Number(unitPrice),
        delivery_price: typeof deliveryPrice === "number" ? deliveryPrice : 0,
        delivery_address: deliveryAddress.trim(),
        delivery_latitude: deliveryLat ? parseFloat(deliveryLat) : null,
        delivery_longitude: deliveryLon ? parseFloat(deliveryLon) : null,
        distance_km: typeof distanceKm === "number" ? distanceKm : null,
        order_date: orderDate,
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
        `Дата: ${order.order_date || orderDate} • Сума: ${formatCurrency(order.total_amount)}`
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

  const isCustomerChosen = Boolean(
    customerMode === "existing" ? selectedCustomerId : newCustomerName.trim()
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 1. КЛІЄНТ */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
              1
            </span>
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
              Існуючий клієнт
            </button>
            <button
              type="button"
              onClick={() => {
                setCustomerMode("new");
                if (newCustomerAddress && !deliveryAddress) {
                  setDeliveryAddress(newCustomerAddress);
                }
              }}
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
                placeholder="Пошук клієнта за ім'ям, телефоном або адресою..."
                value={customerSearch}
                onChange={(e) => setCustomerSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
              />
            </div>

            <div className="max-h-36 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-xl divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-800/50">
              {filteredCustomers.length === 0 ? (
                <div className="p-3 text-xs text-center text-slate-500">
                  Клієнтів не знайдено. Скористайтеся вкладкою &ldquo;Новий клієнт&rdquo;.
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
                  Обрано клієнта: <strong>{selectedCustomer.name}</strong> ({selectedCustomer.phone})
                </span>
                <span className="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">
                  {selectedCustomer.orders_count || 0} замовлень раніше
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
            <div>
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                ПІБ / Назва *
              </label>
              <input
                type="text"
                required
                placeholder="Іван Коваль"
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
                Основна адреса клієнта *
              </label>
              <input
                type="text"
                required
                placeholder="м. Ковель, вул. Незалежності 25"
                value={newCustomerAddress}
                onChange={(e) => {
                  setNewCustomerAddress(e.target.value);
                  if (!deliveryAddress) {
                    setDeliveryAddress(e.target.value);
                  }
                }}
                className="mt-1 w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* 2. АДРЕСА ВИВАНТАЖЕННЯ (З'являється / доступна після вибору клієнта) */}
      <div
        className={`space-y-2 p-3.5 rounded-xl border transition-all ${
          isCustomerChosen
            ? "border-emerald-300 dark:border-emerald-800 bg-emerald-50/20 dark:bg-emerald-950/10"
            : "border-slate-200 dark:border-slate-800 opacity-60"
        }`}
      >
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
              2
            </span>
            <Truck className="w-4 h-4 text-emerald-600" />
            <span>Адреса вивантаження *</span>
          </label>

          {isCalculatingRoute && (
            <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-medium">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Визначення маршруту від складу...</span>
            </span>
          )}
        </div>

        <div className="relative">
          <input
            type="text"
            required
            disabled={!isCustomerChosen}
            placeholder={
              isCustomerChosen
                ? "Введіть або скоригуйте адресу розвантаження..."
                : "Спочатку оберіть клієнта вище"
            }
            value={deliveryAddress}
            onChange={(e) => setDeliveryAddress(e.target.value)}
            className="w-full px-3.5 py-2.5 text-sm font-medium rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 disabled:bg-slate-100 disabled:cursor-not-allowed"
          />
        </div>

        {/* Route status / feedback pill */}
        {routeResult?.success && (
          <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg bg-emerald-100/70 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-xs text-emerald-900 dark:text-emerald-200">
            <div className="flex items-center gap-1.5">
              <Navigation className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400 shrink-0" />
              <span>
                Маршрут зі складу: <strong>{routeResult.distance_km} км</strong>
                {routeResult.duration_min ? ` (~${routeResult.duration_min} хв по дорозі)` : ""}
              </span>
            </div>
            {routeResult.waze_url && (
              <a
                href={routeResult.waze_url}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] underline font-bold text-sky-700 dark:text-sky-300 hover:text-sky-900"
              >
                Перевірити у Waze →
              </a>
            )}
          </div>
        )}

        {routeError && (
          <div className="flex items-center gap-1.5 p-2 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-xs text-amber-800 dark:text-amber-200">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 text-amber-600" />
            <span>{routeError}</span>
          </div>
        )}
      </div>

      {/* 3. ДАТА ЗАМОВЛЕННЯ */}
      <div className="space-y-1.5">
        <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
            3
          </span>
          <CalendarIcon className="w-4 h-4 text-emerald-600" />
          <span>Дата замовлення *</span>
        </label>
        <div className="relative">
          <input
            type="date"
            required
            value={orderDate}
            onChange={(e) => setOrderDate(e.target.value)}
            className="w-full sm:w-72 px-3.5 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
          />
        </div>
        <p className="text-[11px] text-slate-500">
          Замовлення буде зафіксовано на цю дату в календарі відвантажень та базі даних
        </p>
      </div>

      {/* 4. КІЛЬКІСТЬ ТОНН & 5. ЦІНА (Централізований вибір та автоматична ціна) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 4. Кількість тонн */}
        <div className="space-y-2">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
              4
            </span>
            <span>Кількість тонн *</span>
          </label>

          <div className="grid grid-cols-3 gap-2">
            {TONNAGE_OPTIONS.map((opt) => {
              const isSelected = quantity === opt.tons;
              return (
                <button
                  type="button"
                  key={opt.tons}
                  onClick={() => handleSelectTons(opt.tons, opt.price)}
                  className={`p-2.5 rounded-xl border text-center transition-all flex flex-col items-center justify-center relative ${
                    isSelected
                      ? "border-emerald-600 bg-emerald-600 text-white shadow-md ring-2 ring-emerald-500/20"
                      : "border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-emerald-500/50 text-slate-800 dark:text-slate-200"
                  }`}
                >
                  {opt.badge && (
                    <span
                      className={`absolute -top-2 right-1 text-[9px] font-extrabold px-1.5 py-0.2 rounded-full ${
                        isSelected
                          ? "bg-amber-400 text-slate-950 font-bold"
                          : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                      }`}
                    >
                      {opt.badge}
                    </span>
                  )}
                  <span className="text-sm font-black">{opt.label}</span>
                  <span
                    className={`text-[11px] font-bold mt-0.5 ${
                      isSelected ? "text-emerald-100" : "text-emerald-600 dark:text-emerald-400"
                    }`}
                  >
                    {formatCurrency(opt.price)}
                  </span>
                </button>
              );
            })}
          </div>

          {quantity === "" && (
            <p className="text-[11px] text-amber-600 dark:text-amber-400 font-medium">
              Оберіть кількість торфобрикету (1, 2 або 3 т)
            </p>
          )}
        </div>

        {/* 5. Ціна замовлення */}
        <div className="space-y-2">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
              5
            </span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
            <span>Ціна товару (грн) *</span>
          </label>

          <div className="relative">
            <input
              type="text"
              readOnly
              placeholder="Ціна підставиться автоматично"
              value={unitPrice === "" ? "" : `${formatCurrency(unitPrice)}`}
              className="w-full px-3.5 py-2.5 text-sm font-black rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-850 text-slate-900 dark:text-white cursor-default focus:outline-none"
            />
          </div>

          <p className="text-[11px] text-slate-500">
            Встановлюється автоматично відповідно до обраного обсягу
          </p>
        </div>
      </div>

      {/* 6. КІЛОМЕТРАЖ ДОСТАВКИ & 7. ВАРТІСТЬ ДОСТАВКИ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 6. Кілометраж доставки */}
        <div className="space-y-1.5">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
                6
              </span>
              <Navigation className="w-4 h-4 text-emerald-600" />
              <span>Кілометраж доставки</span>
            </span>

            {routeResult?.duration_min && (
              <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-400" />
                ~{routeResult.duration_min} хв
              </span>
            )}
          </label>

          <div className="relative">
            <input
              type="number"
              step="0.1"
              min="0"
              placeholder="Розраховується за адресою..."
              value={distanceKm === "" ? "" : distanceKm}
              onChange={(e) =>
                setDistanceKm(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3.5 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              км
            </span>
          </div>
        </div>

        {/* 7. Вартість доставки */}
        <div className="space-y-1.5">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
              7
            </span>
            <Truck className="w-4 h-4 text-emerald-600" />
            <span>Вартість доставки (грн)</span>
          </label>

          <div className="relative">
            <input
              type="number"
              step="10"
              min="0"
              placeholder="Вкажіть суму доставки..."
              value={deliveryPrice === "" ? "" : deliveryPrice}
              onChange={(e) =>
                setDeliveryPrice(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3.5 py-2 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              грн
            </span>
          </div>

          <div className="flex gap-1.5 pt-0.5">
            <button
              type="button"
              onClick={() => setDeliveryPrice(0)}
              className={`px-2 py-0.5 text-[10px] font-bold rounded-lg border transition-colors ${
                deliveryPrice === 0
                  ? "bg-emerald-600 text-white border-emerald-600"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700"
              }`}
            >
              Самовивіз (0 грн)
            </button>
            {[350, 500, 750].map((cost) => (
              <button
                type="button"
                key={cost}
                onClick={() => setDeliveryPrice(cost)}
                className={`px-2 py-0.5 text-[10px] font-bold rounded-lg border transition-colors ${
                  deliveryPrice === cost
                    ? "bg-emerald-600 text-white border-emerald-600"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                }`}
              >
                {cost} грн
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Примітки */}
      <div>
        <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <FileText className="w-4 h-4 text-slate-400" />
          <span>Примітки до замовлення</span>
        </label>
        <textarea
          rows={2}
          placeholder="Особливості заїзду, контакти, спосіб оплати..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="mt-1 w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 resize-none"
        />
      </div>

      {/* 8. АВТОМАТИЧНИЙ РОЗРАХУНОК ЗАМОВЛЕННЯ (В САМОМУ НИЗУ ВІКНА) */}
      <div className="p-4.5 rounded-2xl bg-gradient-to-br from-emerald-50 via-teal-50/60 to-emerald-100/40 dark:from-emerald-950/40 dark:via-teal-950/30 dark:to-slate-900 border border-emerald-300 dark:border-emerald-800/70 shadow-xs space-y-3">
        <div className="flex items-center justify-between text-xs font-extrabold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white text-[11px] font-black">
              8
            </span>
            <Calculator className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
            <span>Автоматичний розрахунок замовлення:</span>
          </div>
          <span className="text-[10px] normal-case font-medium text-emerald-700 dark:text-emerald-400">
            Оновлюється автоматично
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-2.5 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-emerald-200/70 dark:border-emerald-900/60">
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Вартість товару:</div>
            <div className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5">
              {hasProductPrice ? formatCurrency(productTotal) : "— грн"}
            </div>
            <div className="text-[10px] text-slate-400">
              {quantity ? `${quantity} т торфобрикету` : "Обсяг не вибрано"}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-emerald-200/70 dark:border-emerald-900/60">
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Доставка:</div>
            <div className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5">
              {typeof deliveryPrice === "number"
                ? deliveryPrice === 0
                  ? "Безкоштовно (0 грн)"
                  : formatCurrency(deliveryPrice)
                : "— грн"}
            </div>
            <div className="text-[10px] text-slate-400">
              {distanceKm ? `${distanceKm} км від складу` : "Відстань не вказана"}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-emerald-600 text-white shadow-sm flex flex-col justify-between">
            <div className="text-[11px] font-semibold text-emerald-100">Разом до сплати:</div>
            <div className="text-xl font-black text-white mt-0.5">
              {hasProductPrice ? formatCurrency(totalAmount) : "— грн"}
            </div>
            <div className="text-[10px] text-emerald-100/90 font-medium">
              Товар + доставка
            </div>
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          Скасувати
        </button>

        <button
          type="submit"
          disabled={createOrderMutation.isPending}
          className="px-6 py-2.5 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md shadow-emerald-950/20 disabled:opacity-50 transition-all flex items-center gap-2 active:scale-98"
        >
          {createOrderMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Збереження...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>
                Оформити замовлення
                {hasProductPrice ? ` • ${formatCurrency(totalAmount)}` : ""}
              </span>
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
  initialOrderDate,
}: CreateOrderModalProps) {
  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Оформлення нового замовлення"
      description="Введіть дані клієнта, адресу розвантаження та оберіть кількість тонн"
      maxWidth="2xl"
    >
      <CreateOrderForm
        key={
          preselectedCustomerId
            ? `order-cust-${preselectedCustomerId}`
            : initialOrderDate
            ? `order-date-${String(initialOrderDate)}`
            : "new-order"
        }
        onClose={onClose}
        preselectedCustomerId={preselectedCustomerId}
        initialOrderDate={initialOrderDate}
      />
    </Modal>
  );
}
