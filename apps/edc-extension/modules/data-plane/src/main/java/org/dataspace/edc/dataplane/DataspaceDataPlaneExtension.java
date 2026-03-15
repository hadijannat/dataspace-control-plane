package org.dataspace.edc.dataplane;

import org.dataspace.edc.common.DataspaceExtensionService;
import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Inject;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * EDC data-plane extension wiring transfer hooks.
 * Contains NO business logic — thin wiring only.
 */
@Extension(value = DataspaceDataPlaneExtension.NAME)
public class DataspaceDataPlaneExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Data-Plane Extension";

    @Inject
    private DataspaceExtensionService commonService;

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info(NAME + " initialized — common version: " + commonService.getVersion());
        // TODO: Register transfer process listeners when core/ transfer contracts are available
    }
}
