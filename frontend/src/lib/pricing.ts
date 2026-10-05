/**
 * Centralized pricing constants and utility functions for Peat CRM.
 * 
 * Configured Tiers:
 * 1 тонна -> 12 000 грн
 * 2 тонни -> 12 500 грн
 * 3 тонни -> 13 000 грн
 */

export interface TonnagePricingOption {
  tons: number;
  price: number;
  label: string;
  badge?: string;
}

export const TONNAGE_OPTIONS: TonnagePricingOption[] = [
  { tons: 1, price: 12000, label: "1 тонна" },
  { tons: 2, price: 12500, label: "2 тонни", badge: "Популярний" },
  { tons: 3, price: 13000, label: "3 тонни", badge: "Вигідний" },
];

/**
 * Returns the fixed tier price for the chosen tonnage.
 * Returns null if not in predefined tiers.
 */
export function getPriceForTons(tons: number | null | undefined): number | null {
  if (!tons) return null;
  const option = TONNAGE_OPTIONS.find((opt) => opt.tons === Number(tons));
  return option ? option.price : null;
}

/**
 * Calculates order totals: product price + delivery price.
 */
export function calculateOrderTotals({
  quantity,
  unitPrice,
  deliveryPrice,
}: {
  quantity: number | "" | null;
  unitPrice: number | "" | null;
  deliveryPrice: number | "" | null;
}) {
  const q = typeof quantity === "number" ? quantity : 0;
  const p = typeof unitPrice === "number" ? unitPrice : 0;
  const d = typeof deliveryPrice === "number" ? deliveryPrice : 0;

  // The unit price directly represents the tier price of the fuel
  const productTotal = p;
  const totalAmount = Math.round((productTotal + d) * 100) / 100;

  return {
    quantity: q,
    unitPrice: p,
    deliveryPrice: d,
    productTotal,
    totalAmount,
    hasProductPrice: typeof unitPrice === "number" && unitPrice > 0,
    hasDeliveryPrice: typeof deliveryPrice === "number",
  };
}
