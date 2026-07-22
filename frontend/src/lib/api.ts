import { getToken, removeToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  json?: any;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: any) {
    let formattedDetail = "Request failed";
    if (typeof detail === "string") {
      formattedDetail = detail;
    } else if (Array.isArray(detail)) {
      formattedDetail = detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
    } else if (detail && typeof detail === "object") {
      formattedDetail = detail.msg || detail.message || JSON.stringify(detail);
    }
    super(`API Error ${status}: ${formattedDetail}`);
    this.status = status;
    this.detail = formattedDetail;
  }
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const url = `${API_URL}/api/v1${path}`;
  const headers = new Headers(options.headers || {});

  // Inject Authorization token if present
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Handle json payload shortcut
  let body = options.body;
  if (options.json) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    body,
  });

  if (response.status === 204) {
    return {} as T;
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    data = null;
  }

  if (!response.ok) {
    // If unauthorized, clear token and redirect to login if in browser
    if (response.status === 401) {
      removeToken();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/signup") && window.location.pathname !== "/") {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
    }
    const errMsg = data?.detail || response.statusText || "Request failed";
    throw new ApiError(response.status, errMsg);
  }

  return data as T;
}

export const api = {
  get: <T>(path: string, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: any, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "POST", json: body }),
  put: <T>(path: string, body?: any, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "PUT", json: body }),
  delete: <T>(path: string, options?: FetchOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
  upload: async <T>(path: string, file: File): Promise<T> => {
    const formData = new FormData();
    formData.append("file", file);
    return request<T>(path, {
      method: "POST",
      body: formData,
    });
  },
};
export default api;
export { API_URL };
