"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Settings as SettingsIcon,
  MapPin,
  Shield,
  Server,
  ExternalLink,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function SettingsPage() {
  const { user } = useAuth();

  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: () => api.settings.get(),
  });

  const warehouse = settings?.warehouse;

  const warehouseGmapsUrl = warehouse
    ? `https://www.google.com/maps/search/?api=1&query=${warehouse.latitude},${warehouse.longitude}`
    : "#";

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-emerald-600" />
          <span>Налаштування системи Peat CRM</span>
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Конфігурація базового складу, обліковий запис менеджера та параметри сервера
        </p>
      </div>

      {/* Warehouse Origin Card */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 flex items-center justify-center">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Базовий пункт відвантаження (Склад)
              </h3>
              <p className="text-xs text-slate-500">
                Централізована точка відліку для розрахунку навігації Waze та доставок
              </p>
            </div>
          </div>

          <a
            href={warehouseGmapsUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-200 transition-colors"
          >
            <span>Карта</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-2 border-t border-slate-100 dark:border-slate-800">
          <div>
            <span className="text-slate-400 font-medium block">Назва підприємства / складу:</span>
            <strong className="text-sm text-slate-800 dark:text-slate-200 mt-0.5 block">
              {warehouse?.name || "Маневицький склад торфу"}
            </strong>
          </div>

          <div>
            <span className="text-slate-400 font-medium block">Фактична адреса:</span>
            <strong className="text-sm text-slate-800 dark:text-slate-200 mt-0.5 block">
              {warehouse?.address || "смт Маневичі, Волинська область, Україна"}
            </strong>
          </div>

          <div>
            <span className="text-slate-400 font-medium block">Широта (Latitude):</span>
            <code className="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold">
              {warehouse?.latitude || 51.2981}
            </code>
          </div>

          <div>
            <span className="text-slate-400 font-medium block">Довгота (Longitude):</span>
            <code className="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold">
              {warehouse?.longitude || 25.5532}
            </code>
          </div>
        </div>
      </div>

      {/* Manager Account & Security Card */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 flex items-center justify-center">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Обліковий запис менеджера панелі
            </h3>
            <p className="text-xs text-slate-500">Авторизація та безпека вебпанелі</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs pt-2 border-t border-slate-100 dark:border-slate-800">
          <div>
            <span className="text-slate-400 font-medium block">Користувач:</span>
            <strong className="text-sm text-slate-800 dark:text-slate-200 mt-0.5 block">
              {user?.username || "admin"}
            </strong>
          </div>

          <div>
            <span className="text-slate-400 font-medium block">Роль у системі:</span>
            <span className="inline-block mt-0.5 px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-bold">
              Головний менеджер
            </span>
          </div>

          <div>
            <span className="text-slate-400 font-medium block">Статус сесії:</span>
            <span className="inline-flex items-center gap-1 text-emerald-600 font-bold mt-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Активна (JWT Bearer)</span>
            </span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400 flex items-start gap-2.5">
          <Lock className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
          <div>
            <strong>Безпека та зміна пароля:</strong> Пароль менеджера задається в конфігурації
            сервера через змінну середовища <code className="font-mono text-emerald-600">MANAGER_PASSWORD</code> у файлі <code className="font-mono">.env</code>.
          </div>
        </div>
      </div>

      {/* Infrastructure & Services Status */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 flex items-center justify-center">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Сервіси та інфраструктура
            </h3>
            <p className="text-xs text-slate-500">Стан підключення компонентів системи</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">FastAPI Backend</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <strong className="text-emerald-600 font-bold">Онлайн (HTTP 200)</strong>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">PostgreSQL DB</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <strong className="text-emerald-600 font-bold">Підключено (Docker vol)</strong>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-slate-600 dark:text-slate-400">Telegram Bot</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <strong className="text-emerald-600 font-bold">Aiogram v3 Polling</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
