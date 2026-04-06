import client from "./client";

export interface SpeedTestRequest {
  download_size_mb?: number;
  upload_size_mb?: number;
  latency_samples?: number;
}

export interface LatencyResult {
  latency_ms: number;
  jitter_ms: number;
  samples: number;
}

export interface DownloadResult {
  speed_mbps: number;
  bytes_transferred: number;
  duration_ms: number;
}

export interface UploadResult {
  speed_mbps: number;
  bytes_transferred: number;
  duration_ms: number;
}

export interface SpeedTestResult {
  latency: LatencyResult;
  download: DownloadResult;
  upload: UploadResult;
  quality_score: number;
  quality_label: string;
}

export interface LatencyTestResult {
  latency_ms: number;
  jitter_ms: number;
  samples: number;
  quality_score: number;
  quality_label: string;
}

export const speedTestApi = {
  ping: () => client.get<{ t: number }>("/speedtest/ping"),
  download: (size: number) =>
    client.get("/speedtest/download", {
      params: { size },
      responseType: "arraybuffer",
    }),
  upload: (data: ArrayBuffer) =>
    client.post("/speedtest/upload", data, {
      headers: { "Content-Type": "application/octet-stream" },
    }),
};
