package org.dataspace.edc.controlplane.contract;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Listens to contract negotiation and agreement lifecycle events
 * and forwards them to the management-webhooks module.
 */
@Extension(value = ContractLifecycleListenerExtension.NAME)
public class ContractLifecycleListenerExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Contract Lifecycle Listener";

    @Override
    public String name() { return NAME; }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info(NAME + " initialized");
        // TODO: register ContractNegotiationObservable listener
    }
}
