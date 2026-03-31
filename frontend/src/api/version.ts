import client from "./client";

export interface VersionInfo {
  version: string;
  version_name: string;
  build_date: string;
}

export const versionApi = {
  get: () => client.get<VersionInfo>("/version"),
};
