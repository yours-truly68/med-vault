import { apiClient } from "@/lib/api/client";
import type {
  AuthResponse,
  MessageResponse,
  SessionUser,
} from "@/types/api";

export type RegisterPayload = {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export function register(payload: RegisterPayload) {
  return apiClient<AuthResponse>("/auth/register", {
    method: "POST",
    body: payload,
  });
}

export function login(payload: LoginPayload) {
  return apiClient<AuthResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function refreshSession() {
  return apiClient<AuthResponse>("/auth/refresh", {
    method: "POST",
  });
}

export function logout(token: string | null) {
  return apiClient<MessageResponse>("/auth/logout", {
    method: "POST",
    token,
  });
}

export function getMe(token: string | null) {
  return apiClient<SessionUser>("/auth/me", { token });
}
