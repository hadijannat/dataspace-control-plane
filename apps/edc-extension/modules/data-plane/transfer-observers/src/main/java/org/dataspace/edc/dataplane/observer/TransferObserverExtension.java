package org.dataspace.edc.dataplane.observer;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Observes transfer process lifecycle events (STARTED, COMPLETED, FAILED)
 * and forwards them to the management-webhooks module for control-api notification.
 */
@Extension(value = TransferObserverExtension.NAME)
public class TransferObserverExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Transfer Observer";

    @Override
    public String name() { return NAME; }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info(NAME + " initialized");
        // TODO: register TransferProcessObservable listener
    }
}
