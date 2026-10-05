"use client";

import React from "react";
import { Menu, Plus, MapPin } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { uk } from "date-fns/locale";
import { api } from "@/lib/api";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onOpenSidebar: () => void;
  onOpenCreateOrder?: () => void;
  actions?: React.ReactNode;
}

export function Header({
  title,
  subtitle,
  onOpenSidebar,
  onOpenCreateOrder,
  actions,
}: HeaderProps) {
  const todayFormatted = format(new Date(), "d MMMM yyyy", { locale: uk });
  const { data: warehouse } = useQuery({
    queryKey: ["warehouse"],
    queryFn: () => api.settings.getWarehouse(),
    staleTime: 1000 * 60 * 10,
  });

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-8 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl lg:hidden"
          aria-label="Відкрити меню"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Date chip */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-600 dark:text-slate-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>{todayFormatted}</span>
        </div>

        {/* Warehouse chip */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
          <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>
            {warehouse?.name || "Склад торфу"}
            {warehouse?.latitude && warehouse?.longitude
              ? ` (${warehouse.latitude}, ${warehouse.longitude})`
              : ""}
          </span>
        </div>

        {actions}

        {onOpenCreateOrder && (
          <button
            onClick={onOpenCreateOrder}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm shadow-xs transition-colors active:scale-98"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Створити замовлення</span>
          </button>
        )}
      </div>
    </header>
  );
}
