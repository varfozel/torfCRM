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
  Edit3,
  RotateCcw,
} from "lucide-react";
import { format } from "date-fns";
import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { Customer, OrderCreatePayload, RouteCalculationResult } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { useToast } from "@/components/common/ToastProvider";
import { calculateOrderTotals } from "@/lib/pricing";

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

  // 4. Quantity (Tonnage in tons) - initial state empty "", no 0 defaults
  const [quantity, setQuantity] = useState<number | "">("");

  // 5. Price per ton (грн) - initial state empty "", no 0 defaults
  const [unitPrice, setUnitPrice] = useState<number | "">("");

  // 6. Distance (km) - initial state empty "", auto-filled from routing or manual
  const [distanceKm, setDistanceKm] = useState<number | "">("");

  // 7. Delivery price per km (грн/км) - initial state empty "", no 0 defaults
  const [deliveryPricePerKm, setDeliveryPricePerKm] = useState<number | "">("");

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
  const calculateRoute = useCallback(
    async (addr: string, lat?: number | null, lon?: number | null) => {
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
          setRouteError(
            res.message ||
              "Не вдалося визначити маршрут автоматично. Введіть кілометраж вручну."
          );
        }
      } catch {
        setRouteError(
          "Сервіс розрахунку маршруту тимчасово недоступний. Ви можете вказати кілометраж вручну."
        );
      } finally {
        setIsCalculatingRoute(false);
      }
    },
    [deliveryLat, deliveryLon]
  );

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

  // Calculations for summary at the bottom
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

  // Manual total amount override state
  const [isManualTotal, setIsManualTotal] = useState<boolean>(false);
  const [manualTotalAmount, setManualTotalAmount] = useState<number | "">("");

  const handleEnableManual = () => {
    setIsManualTotal(true);
    if (manualTotalAmount === "" && totalAmount > 0) {
      setManualTotalAmount(totalAmount);
    }
  };

  const handleResetToAuto = () => {
    setIsManualTotal(false);
    setManualTotalAmount("");
  };

  // Mutation to create order
  const createOrderMutation = useMutation({
    mutationFn: async () => {
      let finalCustomerId = selectedCustomerId;

      if (customerMode === "new") {
        if (
          !newCustomerName.trim() ||
          !newCustomerPhone.trim() ||
          !newCustomerAddress.trim()
        ) {
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
        throw new Error("Будь ласка, вкажіть кількість тонн (більше 0)");
      }

      if (unitPrice === "" || unitPrice < 0) {
        throw new Error("Ціна за тонну не може бути порожньою або від'ємною");
      }

      if (isManualTotal && (manualTotalAmount === "" || Number(manualTotalAmount) < 0)) {
        throw new Error("Будь ласка, вкажіть коректну фінальну суму замовлення (не менше 0)");
      }

      const payload: OrderCreatePayload = {
        customer_id: finalCustomerId,
        product_name: "Торф'яний брикет",
        quantity: Number(quantity),
        unit_price: Number(unitPrice),
        distance_km: typeof distanceKm === "number" ? distanceKm : null,
        delivery_price_per_km:
          typeof deliveryPricePerKm === "number" ? deliveryPricePerKm : null,
        delivery_price: typeof deliveryTotal === "number" ? deliveryTotal : 0,
        delivery_address: deliveryAddress.trim(),
        delivery_latitude: deliveryLat ? parseFloat(deliveryLat) : null,
        delivery_longitude: deliveryLon ? parseFloat(deliveryLon) : null,
        order_date: orderDate,
        notes: notes.trim() || undefined,
        is_total_manual: isManualTotal,
        manual_total_amount:
          isManualTotal && manualTotalAmount !== ""
            ? Number(manualTotalAmount)
            : undefined,
      };

      return await api.orders.create(payload);
    },
    onSuccess: (order) => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      toast.success(
        `Замовлення #${order.id} успішно створено!`,
        `Дата: ${order.order_date} • Сума: ${formatCurrency(order.total_amount)}`
      );
      onClose();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Помилка при створенні замовлення";
      toast.error("Не вдалося створити замовлення", msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createOrderMutation.mutate();
  };

  const isCustomerChosen = !!selectedCustomerId || customerMode === "new";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* 1. КЛІЄНТ */}
      <div className="space-y-3 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/40">
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <User className="w-4 h-4 text-emerald-600" />
            <span>Клієнт *</span>
          </label>

          <div className="flex bg-slate-200/70 dark:bg-slate-800 p-0.5 rounded-lg text-xs font-semibold">
            <button
              type="button"
              onClick={() => setCustomerMode("existing")}
              className={`px-3 py-1 rounded-md transition-all ${
                customerMode === "existing"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              Існуючий клієнт
            </button>
            <button
              type="button"
              onClick={() => {
                setCustomerMode("new");
                setSelectedCustomerId(null);
              }}
              className={`px-3 py-1 rounded-md transition-all ${
                customerMode === "new"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              + Новий клієнт
            </button>
          </div>
        </div>

        {customerMode === "existing" ? (
          <div className="space-y-2">
            {selectedCustomer ? (
              <div className="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-800 border border-emerald-500/50 shadow-xs">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-700 font-bold text-xs">
                    {selectedCustomer.name[0]?.toUpperCase()}
                  </div>
                  <div>
                    <div className="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-1.5">
                      <span>{selectedCustomer.name}</span>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {selectedCustomer.phone} • {selectedCustomer.address}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setSelectedCustomerId(null);
                    setDeliveryAddress("");
                    setDistanceKm("");
                    setRouteResult(null);
                  }}
                  className="text-xs text-slate-400 hover:text-rose-600 underline font-semibold px-2 py-1"
                >
                  Змінити
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Швидкий пошук замовника за ім'ям, телефоном або адресою..."
                    value={customerSearch}
                    onChange={(e) => setCustomerSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
                  />
                </div>

                <div className="max-h-40 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                  {filteredCustomers.length === 0 ? (
                    <div className="p-3 text-center text-xs text-slate-400">
                      Клієнтів не знайдено. Перейдіть у вкладку &quot;+ Новий клієнт&quot;.
                    </div>
                  ) : (
                    filteredCustomers.map((c) => (
                      <div
                        key={c.id}
                        onClick={() => handleSelectCustomer(c)}
                        className="p-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer flex items-center justify-between transition-colors"
                      >
                        <div>
                          <div className="font-bold text-xs text-slate-800 dark:text-slate-200">
                            {c.name}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            {c.phone} • {c.address}
                          </div>
                        </div>
                        <span className="text-[11px] text-emerald-600 font-bold">
                          Обрати
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div>
              <label className="text-xs text-slate-600 dark:text-slate-400">
                ПІБ / Назва *
              </label>
              <input
                type="text"
                required
                placeholder="Іванчук Петро"
                value={newCustomerName}
                onChange={(e) => setNewCustomerName(e.target.value)}
                className="mt-1 w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-600 dark:text-slate-400">
                Телефон *
              </label>
              <input
                type="tel"
                required
                placeholder="+380..."
                value={newCustomerPhone}
                onChange={(e) => setNewCustomerPhone(e.target.value)}
                className="mt-1 w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs text-slate-600 dark:text-slate-400">
                Основна адреса *
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

      {/* 2. АДРЕСА ВИВАНТАЖЕННЯ */}
      <div
        className={`space-y-2 p-3.5 rounded-xl border transition-all ${
          isCustomerChosen
            ? "border-emerald-300 dark:border-emerald-800 bg-emerald-50/20 dark:bg-emerald-950/10"
            : "border-slate-200 dark:border-slate-800 opacity-60"
        }`}
      >
        <div className="flex items-center justify-between">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <Truck className="w-4 h-4 text-emerald-600" />
            <span>Адреса вивантаження *</span>
          </label>

          {isCalculatingRoute && (
            <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-medium">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Розрахунок маршруту від складу...</span>
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
      </div>

      {/* 4. КІЛЬКІСТЬ ТОНН & 5. ЦІНА ЗА ТОННУ (Звичайні числові поля без 0 за замовчуванням) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 4. Кількість тонн */}
        <div className="space-y-1.5">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span>Кількість тонн *</span>
          </label>
          <div className="relative">
            <input
              type="number"
              step="any"
              min="0.01"
              required
              placeholder="Наприклад: 1, 1.5, 2, 3, 5..."
              value={quantity === "" ? "" : quantity}
              onChange={(e) =>
                setQuantity(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3.5 py-2.5 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              т
            </span>
          </div>
        </div>

        {/* 5. Ціна за тонну (грн) */}
        <div className="space-y-1.5">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-emerald-600" />
            <span>Ціна за тонну (грн) *</span>
          </label>
          <div className="relative">
            <input
              type="number"
              step="any"
              min="0"
              required
              placeholder="Наприклад: 12000, 12500..."
              value={unitPrice === "" ? "" : unitPrice}
              onChange={(e) =>
                setUnitPrice(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3.5 py-2.5 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              грн/т
            </span>
          </div>
        </div>
      </div>

      {/* 6. КІЛОМЕТРАЖ ДОСТАВКИ & 7. ЦІНА ДОСТАВКИ ЗА КМ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 6. Кілометраж доставки (км) */}
        <div className="space-y-1.5">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Navigation className="w-4 h-4 text-emerald-600" />
              <span>Кілометраж доставки (км)</span>
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
              step="any"
              min="0"
              placeholder={
                isCalculatingRoute
                  ? "Розраховується за адресою..."
                  : "Наприклад: 60.1"
              }
              value={distanceKm === "" ? "" : distanceKm}
              onChange={(e) =>
                setDistanceKm(e.target.value === "" ? "" : parseFloat(e.target.value))
              }
              className="w-full px-3.5 py-2.5 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              км
            </span>
          </div>
        </div>

        {/* 7. Ціна доставки за км (грн/км) */}
        <div className="space-y-1.5">
          <label className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <Truck className="w-4 h-4 text-emerald-600" />
            <span>Ціна доставки за км (грн/км)</span>
          </label>

          <div className="relative">
            <input
              type="number"
              step="any"
              min="0"
              placeholder="Наприклад: 350, 500..."
              value={deliveryPricePerKm === "" ? "" : deliveryPricePerKm}
              onChange={(e) =>
                setDeliveryPricePerKm(
                  e.target.value === "" ? "" : parseFloat(e.target.value)
                )
              }
              className="w-full px-3.5 py-2.5 text-sm font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
            />
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
              грн/км
            </span>
          </div>
        </div>
      </div>

      {/* Примітки до замовлення */}
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

      {/* 8. ПІДСУМОК ЗАМОВЛЕННЯ (В САМОМУ НИЗУ ВІКНА) */}
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
                : "Введіть тонни та ціну"}
            </div>
          </div>

          {/* Вартість доставки */}
          <div className="p-2.5 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-emerald-200/70 dark:border-emerald-900/60">
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Вартість доставки:</div>
            <div className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5">
              {hasDeliveryCalculation ? formatCurrency(deliveryTotal) : "— грн"}
            </div>
            <div className="text-[10px] text-slate-400">
              {hasDeliveryCalculation
                ? `${distanceKm} км × ${formatCurrency(deliveryPricePerKm)}/км`
                : "Введіть км та тариф"}
            </div>
          </div>

          {/* Загальна сума */}
          {!isManualTotal ? (
            <div className="p-2.5 rounded-xl bg-emerald-600 text-white shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between gap-1">
                <span className="text-[11px] font-semibold text-emerald-100">Загальна сума:</span>
                <button
                  type="button"
                  onClick={handleEnableManual}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-white/20 hover:bg-white/30 text-white transition-colors cursor-pointer"
                  title="Встановити суму замовлення вручну"
                >
                  <Edit3 className="w-2.5 h-2.5" />
                  <span>Змінити вручну</span>
                </button>
              </div>
              <div className="text-xl font-black text-white mt-0.5">
                {hasProductCalculation || hasDeliveryCalculation
                  ? formatCurrency(totalAmount)
                  : "— грн"}
              </div>
              <div className="text-[10px] text-emerald-100/90 font-medium">
                {hasProductCalculation && hasDeliveryCalculation
                  ? "Товар + доставка"
                  : hasProductCalculation
                  ? "Тільки товар"
                  : "Введіть дані для розрахунку"}
              </div>
            </div>
          ) : (
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-amber-600 to-amber-700 text-white shadow-sm flex flex-col justify-between border border-amber-400/40">
              <div className="flex items-center justify-between gap-1">
                <span className="text-[11px] font-semibold text-amber-100">Загальна сума:</span>
                <span className="px-1.5 py-0.5 text-[9px] font-black tracking-wide uppercase rounded bg-amber-950/50 text-amber-200 border border-amber-300/30">
                  Встановлено вручну
                </span>
              </div>
              <div className="text-xl font-black text-white mt-0.5">
                {manualTotalAmount !== "" ? formatCurrency(Number(manualTotalAmount)) : "0,00 грн"}
              </div>
              <div className="text-[10px] text-amber-100/90 font-medium">
                Автоматично: <strong>{formatCurrency(totalAmount)}</strong>
              </div>
            </div>
          )}
        </div>

        {/* Якщо сума встановлюється вручну — панель введення та скидання */}
        {isManualTotal && (
          <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800/80 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <label className="text-xs font-bold text-amber-950 dark:text-amber-200">
                  Фінальна сума (грн) *
                </label>
                <span className="text-[10px] font-medium text-amber-800 dark:text-amber-400">
                  (Автоматично: {formatCurrency(totalAmount)})
                </span>
              </div>
              <div className="relative max-w-xs">
                <input
                  type="number"
                  step="any"
                  min="0"
                  required
                  placeholder="Вкажіть фінальну суму..."
                  value={manualTotalAmount === "" ? "" : manualTotalAmount}
                  onChange={(e) =>
                    setManualTotalAmount(
                      e.target.value === "" ? "" : parseFloat(e.target.value)
                    )
                  }
                  className="w-full px-3 py-1.5 text-sm font-black text-slate-900 bg-white rounded-lg border border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-500 shadow-xs"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400 pointer-events-none">
                  грн
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end">
              <button
                type="button"
                onClick={handleResetToAuto}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-white dark:bg-slate-800 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-700 hover:bg-amber-100/60 dark:hover:bg-slate-700 transition-colors shadow-xs cursor-pointer"
                title="Повернути суму, розраховану автоматично"
              >
                <RotateCcw className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                <span>Повернути автоматичний розрахунок</span>
              </button>
            </div>
          </div>
        )}
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
                Створити замовлення
                {isManualTotal && manualTotalAmount !== ""
                  ? ` • ${formatCurrency(Number(manualTotalAmount))}`
                  : hasProductCalculation || hasDeliveryCalculation
                  ? ` • ${formatCurrency(totalAmount)}`
                  : ""}
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
      description="Введіть дані клієнта, адресу розвантаження, параметри замовлення та розрахунок"
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
