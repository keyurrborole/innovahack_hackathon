/* eslint-disable @typescript-eslint/no-explicit-any */

// In CodeSandbox/Vite, configure this in `.env` as:
// VITE_API_BASE_URL=https://<your-backend-host>
const API_BASE_URL = "";
const API_V1 = `/api/v1`;

export type User = {
  id?: string;
  name: string;
  email: string;
  avatar?: string;
};

export type Upload = {
  id: string;
  filename?: string;
  name?: string;
  created_at?: string;
  date?: string;
  uploadedAt?: string;
  status?: "completed" | "processing" | "failed" | string;
  records?: number;
};

export type Report = {
  id: string;
  report_type: string;
  created_at: string;
  status: "completed" | "processing" | "failed" | string;
  format: "pdf" | "excel" | "csv" | "json" | string;
};

export type Pattern = {
  id: string;
  type: string;
  description?: string;
  severity: string;
  confidence: number; // 0..1
  transactions?: number;
  addresses?: string[];
  detectedAt?: string;
};

export type SuspiciousAddress = {
  address: string;
  transactionCount: number;
  totalAmount?: number;
  firstSeen?: string;
  lastSeen?: string;
  riskLevel: string;
  suspiciousScore: number; // 0..1
  flags?: string[];
};

export type GraphData = any;

function getToken(): string | null {
  try {
    return localStorage.getItem("authToken");
  } catch {
    return null;
  }
}

async function fetchJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_V1}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `API error (${res.status})`);
  }
  return (await res.json()) as T;
}

async function fetchBlob(path: string, options: RequestInit = {}): Promise<Blob> {
  const token = getToken();
  const res = await fetch(`${API_V1}${path}`, {
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  return await res.blob();
}

export const dashboardApi = {
  getStats: () => fetchJson<any>("/dashboard/stats"),
};

export const uploadApi = {
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return await fetchJson<any>("/uploads", { method: "POST", body: formData });
  },
  getHistory: (page = 1, limit = 50, status?: string) =>
    fetchJson<any>(`/uploads?page=${page}&page_size=${limit}${status ? `&status=${encodeURIComponent(status)}` : ""}`),
};

export const analysisApi = {
  getPatterns: (uploadId?: string) =>
    fetchJson<any>(`/analysis/patterns${uploadId ? `?upload_id=${encodeURIComponent(uploadId)}` : ""}`).then(
      (r) => (r?.patterns || r || []) as Pattern[]
    ),
  getSuspiciousAddresses: (uploadId?: string, _ignored?: any, page = 1, limit = 100) =>
    fetchJson<any>(
      `/analysis/suspicious-addresses?page=${page}&page_size=${limit}${uploadId ? `&upload_id=${encodeURIComponent(uploadId)}` : ""}`
    ).then((r) => ({ addresses: r?.addresses || r?.data || [], pagination: r?.pagination || {} })),
};

export const graphApi = {
  getSuspiciousSubgraph: (uploadId: string, topK: number, hop: number) =>
    fetchJson<any>(
      `/graph/suspicious-subgraph?upload_id=${encodeURIComponent(uploadId)}&top_k=${topK}&hop=${hop}`
    ),
};

export const reportsApi = {
  getHistory: (_uploadId?: string, page = 1, limit = 20) =>
    fetchJson<any>(`/reports?page=${page}&page_size=${limit}`).then((r) => ({
      reports: r?.reports || r?.items || [],
      pagination: r?.pagination || {},
    })),
  generate: (data: any) =>
    fetchJson<any>("/reports/generate", { method: "POST", body: JSON.stringify(data) }),
  downloadReport: async (reportId: string) => fetchBlob(`/reports/${encodeURIComponent(reportId)}/download`),
};

export const settingsApi = {
  getApiKeys: async () => fetchJson<any>("/settings/api-keys").then((r) => r?.api_keys || r?.keys || r || []),
  createApiKey: async (name: string) =>
    fetchJson<any>("/settings/api-keys", { method: "POST", body: JSON.stringify({ name }) }),
  deleteApiKey: async (id: string) =>
    fetchJson<any>(`/settings/api-keys/${encodeURIComponent(id)}`, { method: "DELETE" }),
  updateSettings: async (settings: any) =>
    fetchJson<any>("/settings/update", { method: "POST", body: JSON.stringify(settings) }),
};

export const authApi = {
  getGoogleAuthUrl: async () => {
    return await fetchJson<{ authorization_url: string }>("/auth/google");
  },
  handleCallback: async (code: string, provider: string) =>
    fetchJson<any>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ code, provider }),
    }),
  logout: async () => {
    try {
      await fetchJson<any>("/auth/logout", { method: "POST" });
    } catch {
      // ignore
    }
  },
};
