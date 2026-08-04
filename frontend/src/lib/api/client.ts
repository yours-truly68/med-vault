import { ApiError } from "./errors";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  token?: string | null;
};

type ErrorBody = {
  detail?: string | { msg?: string }[];
  message?: string;
  code?: string;
};

function resolveErrorMessage(payload: ErrorBody | null, status: number): string {
  if (!payload) {
    return `Request failed with status ${status}`;
  }

  if (typeof payload.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload.detail) && payload.detail[0]?.msg) {
    return payload.detail[0].msg;
  }

  if (payload.message) {
    return payload.message;
  }

  return `Request failed with status ${status}`;
}

async function parseJsonSafe<T>(response: Response): Promise<T | null> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

export async function apiClient<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, token, headers, ...rest } = options;
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;

  const requestHeaders = new Headers(headers);

  if (body !== undefined && !(body instanceof FormData)) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (token) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...rest,
    headers: requestHeaders,
    credentials: "include",
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = await parseJsonSafe<T & ErrorBody>(response);

  if (!response.ok) {
    throw new ApiError(resolveErrorMessage(payload, response.status), {
      status: response.status,
      code: payload?.code,
      details: payload,
    });
  }

  return payload as T;
}

export { API_BASE_URL };
