"use client";

import React, { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import {
  MapPin,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Order, OrderStatus } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import { OrderDetailModal } from "@/components/orders/OrderDetailModal";
import { EditOrderModal } from "@/components/orders/EditOrderModal";

const DeliveryMap = dynamic(
  () => import("@/components/map/DeliveryMap").then((mod) => mod.DeliveryMap),
  {
    ssr: false,
    loading: () => (
      <div className="h-[600px] w-full rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 text-xs">
        Завантаження карти доставок...
      </div>
    ),
  }
);

export default function MapPage() {
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "all">("all");
  const [dateFilter, setDateFilter] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);

  // Fetch all orders
  const { data } = useQuery({
    queryKey: ["orders", "map", statusFilter, dateFilter],
    queryFn: () =>
      api.orders.list({
        status: statusFilter === "all" ? undefined : statusFilter,
        dateFrom: dateFilter ? `${dateFilter}T00:00:00` : undefined,
        limit: 100,
      }),
  });

  // Fetch warehouse info
  const { data: warehouse } = useQuery({
    queryKey: ["warehouse"],
    queryFn: () => api.settings.getWarehouse(),
  });

  const allOrders = useMemo(() => data?.orders || [], [data?.orders]);

  // Split into orders with coordinates and without coordinates
  const { withCoords, withoutCoords } = useMemo(() => {
    const withC: any[] = [];
    const withoutC: Order[] = [];

    allOrders.forEach((o) => {
      if (o.delivery_latitude && o.delivery_longitude) {
        withC.push({
          id: o.id,
          customer_name: o.customer?.name || "—",
          customer_phone: o.customer?.phone || "—",
          delivery_address: o.delivery_address,
          latitude: Number(o.delivery_latitude),
          longitude: Number(o.delivery_longitude),
          quantity: Number(o.quantity),
          total_amount: Number(o.total_amount),
          status: o.status,
          waze_url: o.waze_url,
          google_maps_url: `https://www.google.com/maps/search/?api=1&query=${o.delivery_latitude},${o.delivery_longitude}`,
        });
      } else {
        withoutC.push(o);
      }
    });

    return { withCoords: withC, withoutCoords: withoutC };
  }, [allOrders]);

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <MapPin className="w-6 h-6 text-emerald-600" />
            <span>Географія та маршрути доставок</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Інтерактивна карта точок розвантаження торфобрикету зі складу в смт Маневичі
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as OrderStatus | "all")}
            className="px-3 py-1.5 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200"
          >
            <option value="all">Усі статуси ({allOrders.length})</option>
            <option value="new">Нові</option>
            <option value="planned">Заплановані</option>
            <option value="in_delivery">У дорозі</option>
            <option value="delivered">Доставлені</option>
            <option value="cancelled">Скасовані</option>
          </select>

          <input
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200"
          />

          {(statusFilter !== "all" || dateFilter) && (
            <button
              onClick={() => {
                setStatusFilter("all");
                setDateFilter("");
              }}
              className="px-2.5 py-1.5 text-xs text-slate-500 hover:text-rose-600 font-semibold"
            >
              Скинути
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Map & Side panel */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Interactive Map (3 cols) */}
        <div className="lg:col-span-3 bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>Склад (Маневичі)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
                <span>У дорозі</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
                <span>Заплановано</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                <span>Нові</span>
              </span>
            </div>

            <span className="font-semibold text-emerald-600">
              Позначок на карті: {withCoords.length}
            </span>
          </div>

          <DeliveryMap
            orders={withCoords}
            warehouse={warehouse}
            onSelectOrder={(id) => {
              const ord = allOrders.find((o) => o.id === id);
              if (ord) setSelectedOrder(ord);
            }}
            className="h-[600px]"
          />
        </div>

        {/* Side Panel: Orders Without Coordinates & Legend (1 col) */}
        <div className="space-y-4">
          {/* Deliveries on Map summary */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Статистика локацій
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-600">З координатами:</span>
                <strong className="text-emerald-600">{withCoords.length} точок</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Без координат:</span>
                <strong className="text-amber-600">{withoutCoords.length} замовл.</strong>
              </div>
            </div>
          </div>

          {/* Ungeocoded Orders Panel */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
            <div>
              <h3 className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <span>Замовлення без координат ({withoutCoords.length})</span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Мають текстову адресу, але GPS-координати ще не збережено:
              </p>
            </div>

            {withoutCoords.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
                Усі замовлення мають збережені GPS координати!
              </div>
            ) : (
              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {withoutCoords.map((ord) => (
                  <div
                    key={ord.id}
                    className="p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 dark:text-white">
                        #{ord.id} • {ord.customer?.name || "Клієнт"}
                      </span>
                      <StatusBadge status={ord.status} showDot={false} className="text-[10px]" />
                    </div>

                    <div className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2">
                      📍 {ord.delivery_address}
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <span className="font-bold text-emerald-600">
                        {formatCurrency(ord.total_amount)}
                      </span>
                      <button
                        type="button"
                        onClick={() => setEditingOrder(ord)}
                        className="text-[11px] font-bold text-emerald-600 hover:underline"
                      >
                        Додати координати
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <OrderDetailModal
        order={selectedOrder}
        isOpen={!!selectedOrder}
        onClose={() => setSelectedOrder(null)}
        onEdit={(ord) => setEditingOrder(ord)}
      />

      <EditOrderModal
        order={editingOrder}
        isOpen={!!editingOrder}
        onClose={() => setEditingOrder(null)}
      />
    </div>
  );
}
