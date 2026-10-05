/**
 * Calculation logic for Peat CRM orders.
 *
 * Formula:
 * - Product total = quantity_tons * price_per_ton
 * - Delivery total = distance_km * delivery_price_per_km
 * - Total amount = Product total + Delivery total
 */

export interface OrderCalculationInput {
  quantityTons: number | "" | null;
  pricePerTon: number | "" | null;
  distanceKm: number | "" | null;
  deliveryPricePerKm: number | "" | null;
}

export interface OrderCalculationResult {
  quantityTons: number;
  pricePerTon: number;
  distanceKm: number;
  deliveryPricePerKm: number;
  productTotal: number;
  deliveryTotal: number;
  totalAmount: number;
  hasProductCalculation: boolean;
  hasDeliveryCalculation: boolean;
  isComplete: boolean;
}

export function calculateOrderTotals({
  quantityTons,
  pricePerTon,
  distanceKm,
  deliveryPricePerKm,
}: OrderCalculationInput): OrderCalculationResult {
  const hasQty =
    typeof quantityTons === "number" && !isNaN(quantityTons) && quantityTons > 0;
  const hasPrice =
    typeof pricePerTon === "number" && !isNaN(pricePerTon) && pricePerTon >= 0;
  const hasDist =
    typeof distanceKm === "number" && !isNaN(distanceKm) && distanceKm >= 0;
  const hasRate =
    typeof deliveryPricePerKm === "number" &&
    !isNaN(deliveryPricePerKm) &&
    deliveryPricePerKm >= 0;

  const q = hasQty ? quantityTons : 0;
  const p = hasPrice ? pricePerTon : 0;
  const dist = hasDist ? distanceKm : 0;
  const rate = hasRate ? deliveryPricePerKm : 0;

  // Use precise cents rounding to avoid JavaScript floating point errors:
  // (e.g. 60.1 * 350 = 21035)
  const productTotal =
    hasQty && hasPrice ? Math.round(q * p * 100) / 100 : 0;

  const deliveryTotal =
    hasDist && hasRate ? Math.round(dist * rate * 100) / 100 : 0;

  const totalAmount = Math.round((productTotal + deliveryTotal) * 100) / 100;

  return {
    quantityTons: q,
    pricePerTon: p,
    distanceKm: dist,
    deliveryPricePerKm: rate,
    productTotal,
    deliveryTotal,
    totalAmount,
    hasProductCalculation: hasQty && hasPrice,
    hasDeliveryCalculation: hasDist && hasRate,
    isComplete: hasQty && hasPrice && hasDist && hasRate,
  };
}
