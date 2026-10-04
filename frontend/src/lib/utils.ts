import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, parseISO } from "date-fns";
import { uk } from "date-fns/locale";
import { OrderStatus } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | string | undefined | null): string {
  if (amount === undefined || amount === null) return "0,00 грн";
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return "0,00 грн";

  return new Intl.NumberFormat("uk-UA", {
    style: "currency",
    currency: "UAH",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
    .format(num)
    .replace("UAH", "грн");
}

export function formatNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) return "0";
  return new Intl.NumberFormat("uk-UA").format(num);
}

export function formatDate(dateStr: string | undefined | null): string {
  if (!dateStr) return "—";
  try {
    const d = parseISO(dateStr);
    return format(d, "d MMMM yyyy", { locale: uk });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string | undefined | null): string {
  if (!dateStr) return "—";
  try {
    const d = parseISO(dateStr);
    return format(d, "d MMMM yyyy, HH:mm", { locale: uk });
  } catch {
    return dateStr;
  }
}

export function formatShortDate(dateStr: string | undefined | null): string {
  if (!dateStr) return "—";
  try {
    const d = parseISO(dateStr);
    return format(d, "dd.MM.yyyy", { locale: uk });
  } catch {
    return dateStr;
  }
}

export function formatTimeOnly(dateStr: string | undefined | null): string {
  if (!dateStr) return "—";
  try {
    const d = parseISO(dateStr);
    return format(d, "HH:mm", { locale: uk });
  } catch {
    return dateStr;
  }
}

export const STATUS_CONFIG: Record<
  OrderStatus,
  {
    label: string;
    description: string;
    bgClass: string;
    textClass: string;
    borderClass: string;
    dotClass: string;
  }
> = {
  new: {
    label: "Нове",
    description: "Замовлення оформлено та очікує планування",
    bgClass: "bg-blue-50 dark:bg-blue-950/40",
    textClass: "text-blue-700 dark:text-blue-300",
    borderClass: "border-blue-200 dark:border-blue-800",
    dotClass: "bg-blue-500",
  },
  planned: {
    label: "Заплановано",
    description: "Включено у графік доставки",
    bgClass: "bg-purple-50 dark:bg-purple-950/40",
    textClass: "text-purple-700 dark:text-purple-300",
    borderClass: "border-purple-200 dark:border-purple-800",
    dotClass: "bg-purple-500",
  },
  in_delivery: {
    label: "У дорозі",
    description: "Машина виїхала зі складу до клієнта",
    bgClass: "bg-amber-50 dark:bg-amber-950/40",
    textClass: "text-amber-700 dark:text-amber-300",
    borderClass: "border-amber-200 dark:border-amber-800",
    dotClass: "bg-amber-500 animate-pulse",
  },
  delivered: {
    label: "Доставлено",
    description: "Успішно вивантажено та оплачено",
    bgClass: "bg-emerald-50 dark:bg-emerald-950/40",
    textClass: "text-emerald-700 dark:text-emerald-300",
    borderClass: "border-emerald-200 dark:border-emerald-800",
    dotClass: "bg-emerald-500",
  },
  cancelled: {
    label: "Скасовано",
    description: "Замовлення скасовано менеджером чи клієнтом",
    bgClass: "bg-rose-50 dark:bg-rose-950/40",
    textClass: "text-rose-700 dark:text-rose-300",
    borderClass: "border-rose-200 dark:border-rose-800",
    dotClass: "bg-rose-500",
  },
};
