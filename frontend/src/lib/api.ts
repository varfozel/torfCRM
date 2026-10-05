import {
  Customer,
  CustomerCreatePayload,
  CustomerDetail,
  CustomerUpdatePayload,
  DashboardData,
  LoginResponse,
  ManagerUser,
  Order,
  OrderCreatePayload,
  OrderStatus,
  OrderUpdatePayload,
  ProductSpec,
  RouteCalculationResult,
  SystemSettings,
  WarehouseInfo,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:8080/api/v1`
    : "http://localhost:8080/api/v1");

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("peat_crm_token");
}

export function setStoredToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem("peat_crm_token", token);
  } else {
    localStorage.removeItem("peat_crm_token");
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ data: T; totalCount?: number }> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getStoredToken();

  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err: unknown) {
    throw new ApiError(
      "Не вдалося з'єднатися з сервером API. Перевірте підключення.",
      0,
      err
    );
  }

  const totalCountHeader = response.headers.get("X-Total-Count");
  const totalCount = totalCountHeader ? parseInt(totalCountHeader, 10) : undefined;

  if (response.status === 204) {
    return { data: null as unknown as T, totalCount };
  }

  let body: unknown = null;
  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    body = await response.json();
  } else {
    body = await response.text();
  }

  if (!response.ok) {
    const errorDetail =
      (body as { detail?: string | string[] })?.detail ||
      (typeof body === "string" ? body : "Помилка запиту");

    const message = Array.isArray(errorDetail)
      ? errorDetail.map((e) => (typeof e === "object" ? JSON.stringify(e) : e)).join(", ")
      : String(errorDetail);

    // If 401 Unauthorized, dispatch event or clear token if needed
    if (response.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new Event("peat_crm_unauthorized"));
    }

    throw new ApiError(message, response.status, body);
  }

  return { data: body as T, totalCount };
}

export const api = {
  // Authentication
  auth: {
    login: async (username: string, password: string): Promise<LoginResponse> => {
      const res = await request<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      setStoredToken(res.data.access_token);
      return res.data;
    },
    getMe: async (): Promise<ManagerUser> => {
      const res = await request<ManagerUser>("/auth/me");
      return res.data;
    },
    logout: async () => {
      try {
        await request("/auth/logout", { method: "POST" });
      } finally {
        setStoredToken(null);
      }
    },
  },

  // Analytics & Dashboard
  analytics: {
    getDashboard: async (period = "month"): Promise<DashboardData> => {
      const res = await request<DashboardData>(`/analytics/dashboard?period=${period}`);
      return res.data;
    },
  },

  // Orders
  orders: {
    list: async (params?: {
      status?: OrderStatus;
      customerId?: number;
      q?: string;
      dateFrom?: string;
      dateTo?: string;
      sortBy?: string;
      sortDir?: "asc" | "desc";
      skip?: number;
      limit?: number;
    }): Promise<{ orders: Order[]; totalCount: number }> => {
      const query = new URLSearchParams();
      if (params?.status) query.set("status", params.status);
      if (params?.customerId) query.set("customer_id", String(params.customerId));
      if (params?.q) query.set("q", params.q);
      if (params?.dateFrom) query.set("date_from", params.dateFrom);
      if (params?.dateTo) query.set("date_to", params.dateTo);
      if (params?.sortBy) query.set("sort_by", params.sortBy);
      if (params?.sortDir) query.set("sort_dir", params.sortDir);
      if (params?.skip !== undefined) query.set("skip", String(params.skip));
      if (params?.limit !== undefined) query.set("limit", String(params.limit));

      const endpoint = `/orders/${query.toString() ? `?${query.toString()}` : ""}`;
      const res = await request<Order[]>(endpoint);
      return {
        orders: res.data,
        totalCount: res.totalCount ?? res.data.length,
      };
    },
    getById: async (id: number): Promise<Order> => {
      const res = await request<Order>(`/orders/${id}`);
      return res.data;
    },
    create: async (payload: OrderCreatePayload): Promise<Order> => {
      const res = await request<Order>("/orders/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return res.data;
    },
    update: async (id: number, payload: OrderUpdatePayload): Promise<Order> => {
      const res = await request<Order>(`/orders/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      return res.data;
    },
    plan: async (id: number): Promise<Order> => {
      const res = await request<Order>(`/orders/${id}/plan`, {
        method: "POST",
      });
      return res.data;
    },
    startDelivery: async (id: number): Promise<Order> => {
      const res = await request<Order>(`/orders/${id}/start-delivery`, {
        method: "POST",
      });
      return res.data;
    },
    completeDelivery: async (id: number): Promise<Order> => {
      const res = await request<Order>(`/orders/${id}/complete-delivery`, {
        method: "POST",
      });
      return res.data;
    },
    cancel: async (id: number, reason?: string): Promise<Order> => {
      const query = reason ? `?reason=${encodeURIComponent(reason)}` : "";
      const res = await request<Order>(`/orders/${id}/cancel${query}`, {
        method: "POST",
      });
      return res.data;
    },
    delete: async (id: number): Promise<void> => {
      await request<void>(`/orders/${id}`, {
        method: "DELETE",
      });
    },
  },

  // Customers
  customers: {
    list: async (params?: {
      q?: string;
      skip?: number;
      limit?: number;
    }): Promise<Customer[]> => {
      const query = new URLSearchParams();
      if (params?.q) query.set("q", params.q);
      if (params?.skip !== undefined) query.set("skip", String(params.skip));
      if (params?.limit !== undefined) query.set("limit", String(params.limit));

      const endpoint = `/customers/${query.toString() ? `?${query.toString()}` : ""}`;
      const res = await request<Customer[]>(endpoint);
      return res.data;
    },
    getById: async (id: number): Promise<Customer> => {
      const res = await request<Customer>(`/customers/${id}`);
      return res.data;
    },
    getDetail: async (id: number): Promise<CustomerDetail> => {
      const res = await request<CustomerDetail>(`/customers/${id}/detail`);
      return res.data;
    },
    create: async (payload: CustomerCreatePayload): Promise<Customer> => {
      const res = await request<Customer>("/customers/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return res.data;
    },
    update: async (id: number, payload: CustomerUpdatePayload): Promise<Customer> => {
      const res = await request<Customer>(`/customers/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      return res.data;
    },
    delete: async (id: number): Promise<void> => {
      await request<void>(`/customers/${id}`, {
        method: "DELETE",
      });
    },
  },

  // Products
  products: {
    list: async (category?: string): Promise<ProductSpec[]> => {
      const query = category ? `?category=${encodeURIComponent(category)}` : "";
      const res = await request<ProductSpec[]>(`/products/${query}`);
      return res.data;
    },
    getById: async (id: number): Promise<ProductSpec> => {
      const res = await request<ProductSpec>(`/products/${id}`);
      return res.data;
    },
  },

  // Settings & Warehouse
  settings: {
    get: async (): Promise<SystemSettings> => {
      const res = await request<SystemSettings>("/settings/");
      return res.data;
    },
    getWarehouse: async (): Promise<WarehouseInfo> => {
      const res = await request<WarehouseInfo>("/warehouse");
      return res.data;
    },
  },

  // Navigation & Routing
  navigation: {
    calculateRoute: async (payload: {
      address?: string;
      latitude?: number | null;
      longitude?: number | null;
    }): Promise<RouteCalculationResult> => {
      const res = await request<RouteCalculationResult>("/navigation/calculate-route", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return res.data;
    },
  },
};
