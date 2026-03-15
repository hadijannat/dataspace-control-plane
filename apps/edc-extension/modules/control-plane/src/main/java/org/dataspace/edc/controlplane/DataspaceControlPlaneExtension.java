package org.dataspace.edc.controlplane;

import org.dataspace.edc.common.DataspaceExtensionService;
import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Inject;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * EDC control-plane extension wiring dataspace policy and catalog hooks.
 * Contains NO business logic — delegates to core/ domain services.
 */
@Extension(value = DataspaceControlPlaneExtension.NAME)
public class DataspaceControlPlaneExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Control-Plane Extension";

    @Inject
    private DataspaceExtensionService commonService;

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info(NAME + " initialized — common version: " + commonService.getVersion());
        // TODO: Register policy functions, catalog augmentors when core/ contracts are available
    }
}
