import type { ApiErrorBody } from "@/types/api";

import { ApiError } from "./errors";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  token?: string | null;
};

type LegacyErrorBody = {
  detail?: string | { msg?: string }[];
  message?: string;
  code?: string;
};

type ErrorBody = ApiErrorBody & LegacyErrorBody;

function resolveErrorMessage(payload: ErrorBody | null, status: number): string {
  if (!payload) {
    return `Request failed with status ${status}`;
  }

  if (payload.error?.message) {
    return payload.error.message;
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

function resolveErrorCode(payload: ErrorBody | null): string | undefined {
  return payload?.error?.code ?? payload?.code;
}

function resolveErrorDetails(payload: ErrorBody | null): unknown {
  return payload?.error?.details ?? payload;
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
      code: resolveErrorCode(payload),
      details: resolveErrorDetails(payload),
    });
  }

  return payload as T;
}

export { API_BASE_URL };
