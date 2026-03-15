/**
 * Runtime configuration fetched from /ui/runtime-config.json at startup.
 * This allows a single immutable image to be deployed across environments —
 * the container/Helm chart injects the JSON; we never hardcode these values
 * at build time via import.meta.env.
 */
export interface RuntimeConfig {
  apiBaseUrl: string;
  keycloakUrl: string;
  keycloakRealm: string;
  keycloakClientId: string;
  tenantBanner?: string;
}

let _config: RuntimeConfig | null = null;

export async function loadRuntimeConfig(): Promise<RuntimeConfig> {
  const response = await fetch('/ui/runtime-config.json');
  if (!response.ok) {
    throw new Error(`Failed to load runtime config: ${response.status}`);
  }
  _config = await response.json() as RuntimeConfig;
  return _config;
}

export function getRuntimeConfig(): RuntimeConfig {
  if (!_config) {
    throw new Error('Runtime config not loaded — call loadRuntimeConfig() first');
  }
  return _config;
}
