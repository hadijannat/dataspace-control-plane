package org.dataspace.edc.auth.context;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Setting;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Registers custom web contexts for dataspace-specific API groups.
 * Security is configured via EDC's auth-configuration module:
 *   web.http.dataspace.auth.type=tokenbased
 *   web.http.dataspace.auth.key=<api-key-ref>
 *
 * Never hand-roll auth filters — use EDC's built-in auth-configuration pattern.
 * Per EDC official docs: auth-configuration secures API groups by web context name.
 */
@Extension(value = DataspaceWebContextExtension.NAME)
public class DataspaceWebContextExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Custom Web Contexts";

    /** EDC web context name — matches web.http.<name>.port in connector config */
    public static final String DATASPACE_CONTEXT = "dataspace";

    @Setting(value = "Port for the dataspace web context", required = false)
    public static final String SETTING_PORT = "web.http.dataspace.port";

    @Override
    public String name() { return NAME; }

    @Override
    public void initialize(ServiceExtensionContext context) {
        var port = context.getSetting(SETTING_PORT, "8090");
        context.getMonitor().info(NAME + " initialized — dataspace web context on port: " + port);
        // TODO: register web service and bind to DATASPACE_CONTEXT
    }
}
