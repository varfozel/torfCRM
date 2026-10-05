export type OrderStatus = "new" | "planned" | "in_delivery" | "delivered" | "cancelled";

export interface Customer {
  id: number;
  name: string;
  phone: string;
  address: string;
  latitude?: number | null;
  longitude?: number | null;
  notes?: string | null;
  created_at: string;
  orders_count?: number;
  total_spent?: number;
}

export interface CustomerDetail extends Customer {
  orders: Order[];
}

export interface Order {
  id: number;
  customer_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  delivery_price: number;
  total_amount: number;
  product_total?: number;
  delivery_address: string;
  delivery_latitude?: number | null;
  delivery_longitude?: number | null;
  distance_km?: number | null;
  order_date?: string;
  status: OrderStatus;
  notes?: string | null;
  delivery_started_at?: string | null;
  delivery_completed_at?: string | null;
  created_at: string;
  waze_url?: string | null;
  google_maps_url?: string | null;
  customer?: Customer | null;
}

export interface OrderCreatePayload {
  customer_id: number;
  product_name?: string;
  quantity: number;
  unit_price: number;
  delivery_price: number;
  delivery_address?: string;
  delivery_latitude?: number | null;
  delivery_longitude?: number | null;
  distance_km?: number | null;
  order_date?: string;
  notes?: string | null;
}

export interface OrderUpdatePayload {
  quantity?: number;
  unit_price?: number;
  delivery_price?: number;
  delivery_address?: string;
  delivery_latitude?: number | null;
  delivery_longitude?: number | null;
  distance_km?: number | null;
  order_date?: string;
  status?: OrderStatus;
  notes?: string | null;
}

export interface RouteCalculationResult {
  success: boolean;
  distance_km?: number | null;
  duration_min?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  waze_url?: string | null;
  google_maps_url?: string | null;
  is_estimated?: boolean;
  message?: string | null;
}

export interface CustomerCreatePayload {
  name: string;
  phone: string;
  address: string;
  latitude?: number | null;
  longitude?: number | null;
  notes?: string | null;
}

export interface CustomerUpdatePayload {
  name?: string;
  phone?: string;
  address?: string;
  latitude?: number | null;
  longitude?: number | null;
  notes?: string | null;
}

export interface ManagerUser {
  username: string;
  role: string;
  name: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  manager: ManagerUser;
}

export interface WarehouseInfo {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
}

export interface DashboardKPI {
  new_orders_count: number;
  today_deliveries_count: number;
  total_customers: number;
  period_revenue: number;
  period_quantity_tons: number;
  period_orders_count: number;
}

export interface StatusDistributionItem {
  status: OrderStatus;
  count: number;
  total_sum: number;
}

export interface SalesChartItem {
  date: string;
  revenue: number;
  orders_count: number;
  tons: number;
}

export interface MapDeliveryItem {
  id: number;
  customer_name: string;
  customer_phone: string;
  delivery_address: string;
  latitude: number;
  longitude: number;
  quantity: number;
  total_amount: number;
  status: OrderStatus;
  created_at: string;
  waze_url?: string;
  google_maps_url?: string;
}

export interface DashboardData {
  period: string;
  kpi: DashboardKPI;
  status_distribution: StatusDistributionItem[];
  sales_chart: SalesChartItem[];
  recent_orders: Order[];
  recent_customers: Customer[];
  map_deliveries: MapDeliveryItem[];
  warehouse: WarehouseInfo;
}

export interface ProductSpec {
  id: number;
  name: string;
  category: string;
  base_price_per_ton: number;
  unit: string;
  moisture: string;
  ash_content: string;
  calorific_value: string;
  packaging: string;
  description: string;
  stock_status: "in_stock" | "low_stock" | "out_of_stock";
  in_stock_tons: number;
  image_url?: string | null;
}

export interface SystemSettings {
  project_name: string;
  currency: string;
  currency_symbol: string;
  default_unit_price: number;
  default_delivery_price: number;
  warehouse: WarehouseInfo;
  manager_username: string;
  version: string;
}
