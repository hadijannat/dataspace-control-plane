package org.dataspace.edc.dataplane.aas;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Setting;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * AAS bridge: resolves AAS submodel descriptor URLs at transfer time.
 * Enables EDC to treat AAS submodels as addressable data assets.
 * Registry URL is read from EDC Config — never hardcoded.
 */
@Extension(value = AasBridgeExtension.NAME)
public class AasBridgeExtension implements ServiceExtension {

    public static final String NAME = "Dataspace AAS Bridge";

    @Setting(value = "BaSyx AAS registry base URL", required = false)
    public static final String SETTING_AAS_REGISTRY_URL = "dataspace.aas.registry.url";

    @Override
    public String name() { return NAME; }

    @Override
    public void initialize(ServiceExtensionContext context) {
        var registryUrl = context.getSetting(SETTING_AAS_REGISTRY_URL, null);
        context.getMonitor().info(NAME + " initialized — AAS registry: " + registryUrl);
        // TODO: register AAS descriptor resolver and data source provider
    }
}
