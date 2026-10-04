"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Boxes,
  Flame,
  Droplets,
  Sparkles,
  Package,
  Layers,
  CheckCircle2,
  Truck,
} from "lucide-react";
import { api } from "@/lib/api";
import { ProductSpec } from "@/types";
import { formatCurrency } from "@/lib/utils";
import { CreateOrderModal } from "@/components/orders/CreateOrderModal";

export default function ProductsPage() {
  const [selectedProduct, setSelectedProduct] = useState<ProductSpec | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const { data: products = [], isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: () => api.products.list(),
  });

  const handleOrderProduct = (prod: ProductSpec) => {
    setSelectedProduct(prod);
    setIsCreateOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Boxes className="w-6 h-6 text-emerald-600" />
            <span>Каталог продукції торфобрикету</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Специфікація твердого палива, складські запаси та ціни від виробника в смт Маневичі
          </p>
        </div>
      </div>

      {/* Products Grid */}
      {isLoading ? (
        <div className="py-20 flex justify-center items-center text-slate-400 text-xs">
          <div className="w-8 h-8 border-3 border-emerald-500/20 border-t-emerald-600 rounded-full animate-spin mb-2" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {products.map((prod) => (
            <div
              key={prod.id}
              className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs hover:shadow-lg transition-all flex flex-col justify-between space-y-5 group"
            >
              <div className="space-y-4">
                {/* Title & Badge */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
                      {prod.category}
                    </span>
                    <h3 className="text-lg font-black text-slate-900 dark:text-white mt-1.5 leading-snug">
                      {prod.name}
                    </h3>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="text-xl font-black text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(prod.base_price_per_ton)}
                    </div>
                    <div className="text-[10px] text-slate-400 font-semibold">за 1 {prod.unit}</div>
                  </div>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {prod.description}
                </p>

                {/* Technical Specifications Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                  <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-center">
                    <Droplets className="w-4 h-4 mx-auto text-sky-500 mb-1" />
                    <span className="text-[10px] text-slate-400 block">Вологість</span>
                    <strong className="text-xs text-slate-800 dark:text-slate-200">
                      {prod.moisture}
                    </strong>
                  </div>

                  <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-center">
                    <Sparkles className="w-4 h-4 mx-auto text-amber-500 mb-1" />
                    <span className="text-[10px] text-slate-400 block">Зольність</span>
                    <strong className="text-xs text-slate-800 dark:text-slate-200">
                      {prod.ash_content}
                    </strong>
                  </div>

                  <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-center">
                    <Flame className="w-4 h-4 mx-auto text-rose-500 mb-1" />
                    <span className="text-[10px] text-slate-400 block">Тепловіддача</span>
                    <strong className="text-xs text-slate-800 dark:text-slate-200">
                      {prod.calorific_value.split(" ")[0]}
                    </strong>
                  </div>

                  <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-center">
                    <Layers className="w-4 h-4 mx-auto text-emerald-500 mb-1" />
                    <span className="text-[10px] text-slate-400 block">На складі</span>
                    <strong className="text-xs text-emerald-600 dark:text-emerald-400">
                      {prod.in_stock_tons} т
                    </strong>
                  </div>
                </div>

                <div className="text-xs text-slate-500 flex items-center gap-1.5 pt-1">
                  <Package className="w-4 h-4 text-slate-400 shrink-0" />
                  <span>
                    Упаковка: <strong>{prod.packaging}</strong>
                  </span>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <span className="inline-flex items-center gap-1 text-xs text-emerald-700 dark:text-emerald-400 font-semibold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>В наявності на складі</span>
                </span>

                <button
                  type="button"
                  onClick={() => handleOrderProduct(prod)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition-colors"
                >
                  <Truck className="w-3.5 h-3.5" />
                  <span>Оформити доставку</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Order Modal with Pre-filled unit price */}
      <CreateOrderModal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false);
          setSelectedProduct(null);
        }}
        initialUnitPrice={selectedProduct?.base_price_per_ton || 3800}
      />
    </div>
  );
}
