/**
 * Keycloak JS adapter initialization.
 * Always uses Authorization Code flow (PKCE). Never implicit flow.
 * Machine-trust material never touches this module — human IAM only.
 */
import Keycloak from 'keycloak-js';
import { getRuntimeConfig } from '../app/runtime-config';

let _keycloak: Keycloak | null = null;

export function createKeycloakInstance(): Keycloak {
  const config = getRuntimeConfig();
  _keycloak = new Keycloak({
    url: config.keycloakUrl,
    realm: config.keycloakRealm,
    clientId: config.keycloakClientId,
  });
  return _keycloak;
}

export function getKeycloak(): Keycloak {
  if (!_keycloak) {
    throw new Error('Keycloak not initialized');
  }
  return _keycloak;
}
