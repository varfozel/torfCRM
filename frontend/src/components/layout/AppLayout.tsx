"use client";

import React, { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { CreateOrderModal } from "@/components/orders/CreateOrderModal";
import { useAuth } from "@/lib/auth-context";
import { Flame } from "lucide-react";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCreateOrderOpen, setIsCreateOrderOpen] = useState(false);

  // If on login page, render children directly without dashboard shell
  if (pathname === "/login") {
    return <>{children}</>;
  }

  // Authentication Loading Screen
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-900 text-white">
        <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-600 shadow-xl shadow-emerald-500/20 mb-4 animate-pulse">
          <Flame className="w-8 h-8 text-white" />
        </div>
        <div className="text-lg font-bold tracking-tight">Peat CRM</div>
        <p className="text-xs text-slate-400 mt-1">Завантаження сесії менеджера...</p>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated && !isLoading) {
    router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    return null;
  }

  // Determine Title & Subtitle based on path
  const getHeaderMeta = () => {
    switch (pathname) {
      case "/":
        return {
          title: "Панель керування",
          subtitle: "Огляд ключових показників, продажів та доставок торф'яного брикету",
        };
      case "/orders":
        return {
          title: "Замовлення",
          subtitle: "Повний реєстр замовлень, статусів та логістики доставок",
        };
      case "/customers":
        return {
          title: "Клієнти",
          subtitle: "База замовників, історія купівель та контакти",
        };
      case "/map":
        return {
          title: "Карта доставок",
          subtitle: "Географічне розміщення адрес розвантаження та маршрути Waze",
        };
      case "/calendar":
        return {
          title: "Календар доставок",
          subtitle: "Графік відвантажень зі складу за датами",
        };
      case "/analytics":
        return {
          title: "Аналітика та звіти",
          subtitle: "Фінансові підсумки, тоннаж та динаміка збуту",
        };
      case "/settings":
        return {
          title: "Налаштування системи",
          subtitle: "Координати базового складу, реквізити та параметри",
        };
      default:
        return {
          title: "Peat CRM",
          subtitle: "Система управління торф'яним бізнесом",
        };
    }
  };

  const { title, subtitle } = getHeaderMeta();

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950 font-sans antialiased text-slate-900 dark:text-slate-100">
      {/* Dark Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onOpenCreateOrder={() => setIsCreateOrderOpen(true)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={title}
          subtitle={subtitle}
          onOpenSidebar={() => setIsSidebarOpen(true)}
          onOpenCreateOrder={() => setIsCreateOrderOpen(true)}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Global Quick Create Order Modal */}
      <CreateOrderModal
        isOpen={isCreateOrderOpen}
        onClose={() => setIsCreateOrderOpen(false)}
      />
    </div>
  );
}
