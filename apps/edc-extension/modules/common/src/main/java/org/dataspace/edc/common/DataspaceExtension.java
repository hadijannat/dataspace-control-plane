package org.dataspace.edc.common;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Provides;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Common extension providing shared utilities and constants for all Dataspace EDC modules.
 */
@Extension(value = DataspaceExtension.NAME)
@Provides(DataspaceExtensionService.class)
public class DataspaceExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Common Extension";

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info("Dataspace Common Extension initialized");
        context.registerService(DataspaceExtensionService.class, new DataspaceExtensionService());
    }
}
