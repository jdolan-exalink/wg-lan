import client from "./client";
import type { User } from "@/types/auth";

export const authApi = {
  login: (username: string, password: string, authMethod: string = "auto") =>
    client.post<User>("/auth/login", { username, password, auth_method: authMethod }),

  logout: () => client.post("/auth/logout"),

  me: () => client.get<User>("/auth/me"),

  changePassword: (current_password: string, new_password: string) =>
    client.post("/auth/change-password", { current_password, new_password }),
};
