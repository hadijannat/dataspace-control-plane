package org.dataspace.edc.auth;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Setting;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * OIDC token validation extension for EDC API endpoints.
 * Reads JWKS URI from EDC Config — never from hardcoded values.
 */
@Extension(value = OidcTokenValidationExtension.NAME)
public class OidcTokenValidationExtension implements ServiceExtension {

    public static final String NAME = "Dataspace OIDC Auth Extension";

    @Setting(value = "JWKS URI for OIDC token validation", required = true)
    public static final String SETTING_JWKS_URI = "dataspace.auth.jwks.uri";

    @Setting(value = "Expected token issuer", required = true)
    public static final String SETTING_ISSUER = "dataspace.auth.issuer";

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public void initialize(ServiceExtensionContext context) {
        var jwksUri = context.getSetting(SETTING_JWKS_URI, null);
        var issuer = context.getSetting(SETTING_ISSUER, null);
        context.getMonitor().info(NAME + " initialized — JWKS URI: " + jwksUri + ", issuer: " + issuer);
        // TODO: Register TokenValidationService implementation using jwksUri + issuer
    }
}
