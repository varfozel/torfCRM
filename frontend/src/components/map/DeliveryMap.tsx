"use client";

import React, { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { OrderStatus, WarehouseInfo } from "@/types";
import { formatCurrency, STATUS_CONFIG } from "@/lib/utils";

interface MapDeliveryOrder {
  id: number;
  customer_name: string;
  customer_phone: string;
  delivery_address: string;
  latitude: number;
  longitude: number;
  quantity: number;
  total_amount: number;
  status: OrderStatus;
  waze_url?: string;
  google_maps_url?: string;
}

interface DeliveryMapProps {
  orders: MapDeliveryOrder[];
  warehouse?: WarehouseInfo;
  onSelectOrder?: (orderId: number) => void;
  className?: string;
  center?: [number, number];
  zoom?: number;
}

const STATUS_COLORS: Record<OrderStatus, string> = {
  new: "#2563eb", // blue
  planned: "#7c3aed", // purple
  in_delivery: "#d97706", // amber
  delivered: "#059669", // emerald
  cancelled: "#e11d48", // rose
};

function createOrderPinIcon(status: OrderStatus, quantity: number) {
  const color = STATUS_COLORS[status] || "#059669";
  const html = `
    <div style="
      background-color: ${color};
      color: white;
      width: 32px;
      height: 32px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid white;
      box-shadow: 0 4px 10px rgba(0,0,0,0.3);
      cursor: pointer;
    ">
      <span style="
        transform: rotate(45deg);
        font-weight: 800;
        font-size: 11px;
        font-family: sans-serif;
      ">${quantity > 0 ? quantity : "📦"}</span>
    </div>
  `;
  return L.divIcon({
    className: "custom-delivery-pin",
    html,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
}

function createWarehouseIcon() {
  const html = `
    <div style="
      background-color: #0f172a;
      color: #34d399;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 3px solid #10b981;
      box-shadow: 0 6px 15px rgba(0,0,0,0.4);
      cursor: pointer;
    ">
      <span style="font-size: 18px;">🏭</span>
    </div>
  `;
  return L.divIcon({
    className: "custom-warehouse-pin",
    html,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });
}

export function DeliveryMap({
  orders,
  warehouse,
  onSelectOrder,
  className = "h-[500px]",
  center,
  zoom = 10,
}: DeliveryMapProps) {
  const mapCenter: [number, number] = center || (warehouse ? [warehouse.latitude, warehouse.longitude] : [50.7472, 25.3254]);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: mapCenter,
        zoom,
        zoomControl: true,
      });

      // High-quality OpenStreetMap carto tile layer
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(map);

      markersLayerRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();
    const bounds = L.latLngBounds([]);

    // 1. Warehouse Pin
    if (warehouse) {
      const whLatLng: [number, number] = [warehouse.latitude, warehouse.longitude];
      bounds.extend(whLatLng);

      const whMarker = L.marker(whLatLng, { icon: createWarehouseIcon() });
      whMarker.bindPopup(`
        <div style="font-family: system-ui, sans-serif; min-width: 180px; padding: 4px;">
          <div style="font-size: 10px; font-weight: 700; color: #059669; text-transform: uppercase;">Базовий склад</div>
          <div style="font-weight: 800; font-size: 14px; color: #0f172a; margin-top: 2px;">${warehouse.name}</div>
          <div style="font-size: 12px; color: #475569; margin-top: 4px;">${warehouse.address}</div>
        </div>
      `);
      markersLayer.addLayer(whMarker);
    }

    // 2. Order Pins
    orders.forEach((o) => {
      if (!o.latitude || !o.longitude) return;

      const latLng: [number, number] = [o.latitude, o.longitude];
      bounds.extend(latLng);

      const statusConf = STATUS_CONFIG[o.status] || STATUS_CONFIG.new;
      const marker = L.marker(latLng, {
        icon: createOrderPinIcon(o.status, Math.round(o.quantity)),
      });

      const wazeBtn = o.waze_url
        ? `<a href="${o.waze_url}" target="_blank" rel="noreferrer" style="
            display: inline-block;
            background: #0284c7;
            color: white;
            padding: 5px 9px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-decoration: none;
            margin-right: 4px;
          ">🚗 Waze</a>`
        : "";

      const gmapsBtn = `<a href="https://www.google.com/maps/search/?api=1&query=${o.latitude},${o.longitude}" target="_blank" rel="noreferrer" style="
        display: inline-block;
        background: #475569;
        color: white;
        padding: 5px 9px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-decoration: none;
      ">📍 Google</a>`;

      const detailBtn = onSelectOrder
        ? `<button id="order-detail-btn-${o.id}" style="
            display: block;
            width: 100%;
            margin-top: 8px;
            background: #059669;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
          ">Деталі замовлення #${o.id}</button>`
        : "";

      const popupContent = `
        <div style="font-family: system-ui, sans-serif; min-width: 220px; padding: 4px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: 800; font-size: 14px; color: #0f172a;">Замовлення #${o.id}</span>
            <span style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 9999px; background: #e0f2fe; color: #0369a1;">
              ${statusConf.label}
            </span>
          </div>
          <div style="font-weight: 700; font-size: 13px; color: #1e293b;">${o.customer_name}</div>
          <div style="font-size: 12px; color: #059669; font-weight: 600; margin: 2px 0;">
            <a href="tel:${o.customer_phone}" style="color: inherit; text-decoration: none;">📞 ${o.customer_phone}</a>
          </div>
          <div style="font-size: 12px; color: #64748b; margin-top: 2px;">📍 ${o.delivery_address}</div>
          <div style="display: flex; justify-content: space-between; margin-top: 6px; padding-top: 6px; border-top: 1px solid #e2e8f0; font-size: 12px;">
            <span>Обсяг: <strong>${o.quantity} т</strong></span>
            <span style="font-weight: 800; color: #059669;">${formatCurrency(o.total_amount)}</span>
          </div>
          <div style="margin-top: 8px;">
            ${wazeBtn}
            ${gmapsBtn}
          </div>
          ${detailBtn}
        </div>
      `;

      marker.bindPopup(popupContent);

      marker.on("popupopen", () => {
        if (onSelectOrder) {
          const btn = document.getElementById(`order-detail-btn-${o.id}`);
          if (btn) {
            btn.onclick = () => onSelectOrder(o.id);
          }
        }
      });

      markersLayer.addLayer(marker);
    });

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }
  }, [orders, warehouse, onSelectOrder, center, zoom]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div
      ref={mapContainerRef}
      className={`w-full rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm z-0 ${className}`}
    />
  );
}
