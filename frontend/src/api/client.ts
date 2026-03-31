import axios from "axios";
import { getCookie } from "@/lib/utils";

const client = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

// Attach CSRF token on every mutating request
client.interceptors.request.use((config) => {
  if (config.method && !["get", "head", "options"].includes(config.method.toLowerCase())) {
    const csrf = getCookie("csrf_token");
    if (csrf) {
      config.headers["x-csrf-token"] = csrf;
    }
  }
  return config;
});

// Redirect to login on 401
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Don't redirect if already on login page
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default client;
