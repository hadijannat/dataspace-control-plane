package org.dataspace.edc.controlplane.policy;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Inject;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Registers custom policy evaluation functions:
 * - tenant-membership: validates that the counterpart is a member of the requesting tenant's dataspace
 * - pack-compliance: validates that a transfer satisfies active pack constraints
 *
 * Business rules for these functions live in core/ and are called via webhook/HTTP;
 * this extension only wires the EDC SPI hook.
 */
@Extension(value = DataspacePolicyFunctionsExtension.NAME)
public class DataspacePolicyFunctionsExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Policy Functions";

    @Override
    public String name() {
        return NAME;
    }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info(NAME + " initialized — registering custom policy functions");
        // TODO: PolicyEngine registry injection and function registration
        // policyEngine.registerFunction(AtomicConstraintFunction.class, "dataspaceDataspace:tenantMembership", ...);
    }
}
