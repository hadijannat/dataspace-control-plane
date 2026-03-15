package org.dataspace.edc.controlplane.participant;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Resolves participant context and DSP profile for each connector participant.
 * Delegates profile lookup to control-api via callback; does not embed business logic.
 */
@Extension(value = DataspaceParticipantContextExtension.NAME)
public class DataspaceParticipantContextExtension implements ServiceExtension {

    public static final String NAME = "Dataspace Participant Context";

    @Override
    public String name() { return NAME; }

    @Override
    public void initialize(ServiceExtensionContext context) {
        context.getMonitor().info(NAME + " initialized");
        // TODO: inject ParticipantContextService when EDC SPI stabilizes for participant profiles
    }
}
