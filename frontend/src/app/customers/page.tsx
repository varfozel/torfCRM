"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Search,
  Plus,
  Phone,
  Eye,
  Edit,
  X,
  PlusCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Customer, Order } from "@/types";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { CreateCustomerModal } from "@/components/customers/CreateCustomerModal";
import { EditCustomerModal } from "@/components/customers/EditCustomerModal";
import { CustomerDetailModal } from "@/components/customers/CustomerDetailModal";
import { CreateOrderModal } from "@/components/orders/CreateOrderModal";
import { OrderDetailModal } from "@/components/orders/OrderDetailModal";

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);

  // Cross-modal: create order for this specific customer
  const [createOrderCustomerId, setCreateOrderCustomerId] = useState<number | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  const { data: customers = [], isLoading } = useQuery({
    queryKey: ["customers", searchQuery],
    queryFn: () => api.customers.list({ q: searchQuery.trim() || undefined, limit: 100 }),
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Users className="w-6 h-6 text-emerald-600" />
            <span>База клієнтів</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Реєстр замовників, історія відвантажень торфобрикету та контакти
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-950/20 active:scale-98 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Додати клієнта</span>
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Пошук клієнта за назвою, ПІБ або номером телефону..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="text-xs text-slate-500 shrink-0 font-medium">
          Всього: <strong>{customers.length}</strong> контрагентів
        </div>
      </div>

      {/* Customers Grid / Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-xs overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400 text-xs">
            <div className="w-8 h-8 border-3 border-emerald-500/20 border-t-emerald-600 rounded-full animate-spin mb-2" />
            <span>Завантаження бази клієнтів...</span>
          </div>
        ) : customers.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
              <Users className="w-6 h-6" />
            </div>
            <div className="font-bold text-sm text-slate-800 dark:text-slate-200">
              Клієнтів не знайдено
            </div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Спробуйте змінити пошуковий запит або створіть картку нового клієнта.
            </p>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 text-white font-bold text-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Додати нового клієнта</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 text-slate-500 font-bold uppercase tracking-wider">
                <tr>
                  <th className="p-3.5 pl-5">Клієнт</th>
                  <th className="p-3.5">Телефон</th>
                  <th className="p-3.5">Адреса доставки</th>
                  <th className="p-3.5 text-center">Замовлень</th>
                  <th className="p-3.5">Сума покупок</th>
                  <th className="p-3.5">Реєстрація</th>
                  <th className="p-3.5 pr-5 text-right">Дії</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {customers.map((cust) => (
                  <tr
                    key={cust.id}
                    className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors group cursor-pointer"
                    onClick={() => setSelectedCustomerId(cust.id)}
                  >
                    <td className="p-3.5 pl-5">
                      <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <span>{cust.name}</span>
                      </div>
                      {cust.notes && (
                        <div className="text-[11px] text-slate-400 truncate max-w-xs">
                          {cust.notes}
                        </div>
                      )}
                    </td>

                    <td className="p-3.5" onClick={(e) => e.stopPropagation()}>
                      <a
                        href={`tel:${cust.phone}`}
                        className="font-semibold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
                      >
                        <Phone className="w-3 h-3" />
                        <span>{cust.phone}</span>
                      </a>
                    </td>

                    <td className="p-3.5 max-w-sm truncate text-slate-600 dark:text-slate-400">
                      {cust.address}
                    </td>

                    <td className="p-3.5 text-center font-bold text-slate-800 dark:text-slate-200">
                      <span className="inline-block px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {cust.orders_count || 0}
                      </span>
                    </td>

                    <td className="p-3.5 font-extrabold text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(cust.total_spent || 0)}
                    </td>

                    <td className="p-3.5 text-slate-500 whitespace-nowrap">
                      {formatDateTime(cust.created_at)}
                    </td>

                    <td className="p-3.5 pr-5 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => setCreateOrderCustomerId(cust.id)}
                          title="Оформити замовлення"
                          className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                        >
                          <PlusCircle className="w-4 h-4" />
                        </button>

                        <button
                          type="button"
                          onClick={() => setSelectedCustomerId(cust.id)}
                          title="Переглянути профіль"
                          className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        <button
                          type="button"
                          onClick={() => setEditingCustomer(cust)}
                          title="Редагувати дані"
                          className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      <CreateCustomerModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />

      <EditCustomerModal
        customer={editingCustomer}
        isOpen={!!editingCustomer}
        onClose={() => setEditingCustomer(null)}
      />

      <CustomerDetailModal
        customerId={selectedCustomerId}
        isOpen={!!selectedCustomerId}
        onClose={() => setSelectedCustomerId(null)}
        onEditCustomer={(cust) => setEditingCustomer(cust)}
        onCreateOrderForCustomer={(cid) => setCreateOrderCustomerId(cid)}
        onViewOrder={(ord) => setSelectedOrder(ord)}
      />

      <CreateOrderModal
        isOpen={!!createOrderCustomerId}
        preselectedCustomerId={createOrderCustomerId || undefined}
        onClose={() => setCreateOrderCustomerId(null)}
      />

      <OrderDetailModal
        order={selectedOrder}
        isOpen={!!selectedOrder}
        onClose={() => setSelectedOrder(null)}
      />
    </div>
  );
}
